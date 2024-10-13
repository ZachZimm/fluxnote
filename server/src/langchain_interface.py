import json
import os
import time
import asyncio
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from utils import read_config, parse_llm_output
from fastapi import WebSocket
from models.Summary import Summary, Idea, IdeaVerificationBool, TagList
from models.WikiData import WikiData
from pymongo import MongoClient
import embeddings

# TODO Rename this file to something that involves the database OR move the database stuff to a separate file this one isn't too long

# TODO create a way of keeping the secrets_config up to date with available secrets without tracking it in git
# read loaded secrets' keys -> compare those with saved key names -> if a key is missing add it to the secrets_config
# once I start using something that needs to be secret, anyways

def serialize_history(history: list) -> str: # This should be in the utils file
    _history = []
    for message in history:
        history_message = {}
        if isinstance(message, dict):
            history_message['role'] = message['role']
            history_message['content'] = message['content']
            _history.append(history_message)
            continue
        history_message['role'] = message.type
        history_message['content'] = message.content
        _history.append(history_message)
    return json.dumps(_history)

def deserialize_history(history_str: str) -> list: # This should be in the utils file
    print(f"history_str: {history_str}")
    if history_str.startswith('\"') and history_str.endswith('"'):
        history_str = history_str[1:-1]
    history_str = history_str.replace("\\n", "")
    history_str = history_str.replace("\\", "")
    if history_str == '[]': return []

    history = []
    history_list = json.loads(history_str)
    for message in history_list:
        if message['role'] == 'Human':
            history.append(HumanMessage(content=message['content']))
        elif message['role'] == 'AI':
            history.append(AIMessage(content=message['content']))
        elif message['role'] == 'System':
            history.append(SystemMessage(content=message['content']))
    return history

class langchain_interface():
    userid = "-1"
    logged_in = False
    chat_character = "Sherlock-Holmes" # These are all defaults
    config_path = "src/config.json"
    secret_config_path = "src/secret_config.json"
    system_prompts_path = "src/system_prompts.json"
    mongo_uri = "mongodb://localhost:27017/"
    notes_dir = "sample_data/"
    config_json = {}
    secret_config_json = {}
    system_prompts = {}
    permanent_characters = []
    model = None
    headers = { "Content-Type": "application/json" }
    url = ""
    history = []
    user_history = []
    permanent_characters = []
    chain = None
    mongo_client = None
    db = None

    def login(self, userid: str = ""):
        self.userid = userid
        self.config_json = read_config(self.config_path) # This should only contain default values now
        self.secret_config_json = read_config(self.secret_config_path)
        self.system_prompts = read_config(self.system_prompts_path)
        self.permanent_characters = self.system_prompts.keys()
        os.environ["OPENAI_API_KEY"] = self.secret_config_json['openai_api_key']

        self.mongo_uri = self.secret_config_json['mongo_uri']
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client["fluxnote"]
        # insert these only if they don't exist
        document = {
            "userid": self.userid,
            "config": self.config_json,
            "secret_config": self.secret_config_json,
            "system_prompts": self.system_prompts
            }
        filter = {"userid": self.userid}
        # update = {"$setOnInsert": document} # This will only insert the document if it doesn't exist
        # update if this document is different from the one in the database
        update = {"$set": document}
        result = self.db["config"].update_one(filter, update, upsert=True)

        # if there is no history in the database, create it
        if not self.db["history"].find_one({"userid": self.userid}):
            history = {
                "userid": self.userid,
                "history": serialize_history(self.history)
            }
            self.db["history"].insert_one(history)
        self.logged_in = True

    def add_chat_character(self, character_name: str, character_bio) -> None:
        self.system_prompts[character_name] = character_bio
        update = {"$set": {f"system_prompts.{character_name}": character_bio}}
        result = self.db["config"].update_one({"userid": self.userid}, update, upsert=False)
        self.system_prompts = self.get_chat_characters()

    def get_chat_characters(self) -> dict:
        result = self.db["config"].find_one({"userid": self.userid})["system_prompts"]
        return result

    def get_chat_characters_str(self) -> str:
        return json.dumps(self.get_chat_characters())

    def remove_chat_character(self, character_name: str) -> bool:
        if character_name not in self.permanent_characters:
            if character_name in self.system_prompts.keys():
                self.system_prompts.pop(character_name)
                update = {"$set": {f"system_prompts.{character_name}": ""}}
                result = self.db["config"].update_one({"userid": self.userid}, update, upsert=False)
                return True
        return False

    def update_chat_character(self, character_name: str, character_bio: str) -> bool:
        if character_name in self.system_prompts.keys():
            self.system_prompts[character_name] = character_bio
            update = {"$set": {f"system_prompts.{character_name}": character_bio}}
            result = self.db["config"].update_one({"userid": self.userid}, update)
            return True
        return False

    def get_notes_dir(self) -> str:
        return self.notes_dir # Notes will be probably be stored on (client's) disk as well as in the database

    def append_user_history(self, message: str) -> str:
        do_not_append_funcs = ["login"] #This should be configurable
        if json.loads(message)["func"] in do_not_append_funcs:
            return str(False).lower()
        if len(self.user_history) > 100: # This should be configurable
            self.user_history.pop(0)
        self.user_history.append(message)
        # There will be a database for user history as well
        # not sure if the following is good vv (it could be)
        # update = {"$set": {"user_history": self.user_history}}
        # result = self.db["config"].update_one({"userid": self.userid}, update)
        return str(True).lower()

    def get_user_history(self) -> list:
        return self.user_history

    def get_user_history_str(self) -> str:
        return json.dumps(self.user_history)

    def clear_user_history(self) -> None:
        self.user_history = []

    def append_article(self, article: WikiData) -> str:
        # insert the summary into the database with the userid and title as keys
        # if there is already a match, overwrite it
        document = article.model_dump()
        document["userid"] = self.userid
        document["title"] = article.title
        update = {"$set": document}
        result = self.db["articles"].update_one({"userid": self.userid, "title": article.title}, update, upsert=True)

        return str(True).lower()

    def get_article(self, title: str) -> WikiData:
        # make sure both title and userid match
        article = self.db["articles"].find_one({"title": title, "userid": self.userid})
        if not article:
            return WikiData(title="No article found", summary="", content="", links=[])
        return_obj = WikiData(
                            title=article["title"],
                            summary=article["summary"],
                            content=article["content"],
                            links=article["links"],
                            creation=article["creation"],
                           )
        return return_obj

    def get_article_str(self, title: str) -> str:
        return json.dumps(self.get_article(title).model_dump())

    def get_list_of_articles(self) -> list:
        # get all the articles from the database with this userid
        articles = self.db["articles"].find({"userid": self.userid})
        articles_obj = list(articles)
        article_list = []
        num_articles = len(articles_obj)
        for i in range(num_articles):
            article_list.append(articles_obj[i]["title"])
        return article_list

    def get_list_of_articles_str(self) -> str:
        return json.dumps(self.get_list_of_articles())

    def get_list_of_summaries(self) -> list:
        # get all the summaries from the database with this userid
        summaries = self.db["summary"].find({"userid": self.userid})
        summaries_obj = list(summaries)
        summary_list = []
        num_summaries = len(summaries_obj)
        for i in range(num_summaries):
            summary_list.append(summaries_obj[i]["title"])
        return summary_list

    def get_list_of_summaries_str(self) -> str:
        return json.dumps(self.get_list_of_summaries())

    def get_summary(self, title: str) -> Summary:
        # make sure both title and userid match
        summary = self.db["summary"].find_one({"title": title, "userid": self.userid})
        if not summary:
            empty_idea = Idea(idea="No summary found", embedding=[])
            summary = Summary(title="No summary found", summary=[empty_idea])
            return summary
        summary_obj = Summary(
            title=summary["title"],
            summary=summary["summary"],
            tags=summary["tags"]
        )
        return summary_obj

    def get_summary_str(self, title: str) -> str:
        return json.dumps(self.get_summary(title).model_dump())

    def get_summaries_by_tag(self, tag: str) -> list:
        # retrieves all summaries from the database with a matching userid, as well as the provided tag being present in the tags list
        summaries = self.db["summary"].find({"userid": self.userid, "tags": tag})
        summaries_obj = list(summaries)
        return summaries_obj
    
    def get_summaries_by_tag_list(self, tags: list) -> list:
        # retrieves all summaries from the database with a matching userid, as well as all of the tags in the provided list being present in the tags list
        summaries = self.db["summary"].find({"userid": self.userid, "tags": {"$all": tags}})
        summaries_obj = list(summaries)
        return summaries_obj

    # Consider putting this in the utils file 
    def summary_list_to_str(self, summaries: list) -> str:
        summary_str = ""
        for summary in summaries:
            summary_str += "\nDocument title: " + summary["title"]
            i = 0
            for idea in summary["summary"]:
                i += 1
                summary_str += "\n " + str(i) + ": " + idea["idea"]

        return summary_str
    
    def get_summaries_by_tag_str(self, tag: str) -> str:
        summaries = self.get_summaries_by_tag(tag)
        return self.summary_list_to_str(summaries) 

    def get_summaries_by_tag_list_str(self, tags: list) -> str:
        summaries = self.get_summaries_by_tag_list(tags)
        return self.summary_list_to_str(summaries) 

    # TODO test these functions
    def get_summaries_by_idea_tag(self, tag: str) -> list:
        summaries = self.db["summary"].find({"userid": self.userid, "idea_tags": tag})
        summaries_obj = list(summaries)
        return summaries_obj

    def get_summaries_by_idea_tag_list(self, tags: list) -> list:
        summaries = self.db["summary"].find({"userid": self.userid, "idea_tags": {"$all": tags}})
        summaries_obj = list(summaries)
        return summaries_obj
    
    def get_summaries_by_idea_tag_str(self, tag: str) -> str:
        summaries = self.get_summaries_by_idea_tag(tag)
        return self.summary_list_to_str(summaries)
    
    def get_summaries_by_idea_tag_list_str(self, tags: list) -> str:
        summaries = self.get_summaries_by_idea_tag_list(tags)
        return self.summary_list_to_str(summaries)
    
    def idea_list_to_str(self, ideas: list) -> str:
        idea_str = ""
        i = 0
        for idea in ideas:
            i += 1
            idea_str += "\n " + str(i) + ": " + idea["idea"]
        return idea_str
    
    def get_ideas_by_tag(self, tag: str) -> list:
        # retrieves all summaries which contain the provided tag in their idea tags list and have a matching userid, then searching through all of those summaries it builds up a new summary object of only the ideas which contain the provided tag
        summaries = self.db["summary"].find({"userid": self.userid, "idea_tags": tag})
        summaries_obj = list(summaries)
        idea_list = []
        for summary in summaries_obj:
            for idea in summary["summary"]:
                if tag in idea["tags"]:
                    idea_list.append(idea)
        return idea_list
    
    def get_ideas_by_tag_list(self, tags: list) -> list:
        # retrieves all summaries which contain all of the provided tags in their idea tags list and have a matching userid, then searching through all of those summaries it builds up a new summary object of only the ideas which contain all of the provided tags
        summaries = self.db["summary"].find({"userid": self.userid, "idea_tags": {"$all": tags}})
        summaries_obj = list(summaries)
        idea_list = []
        for summary in summaries_obj:
            for idea in summary["summary"]:
                if all(tag in idea["tags"] for tag in tags):
                    idea_list.append(idea)
        return idea_list
    
    def get_ideas_by_tag_str(self, tag: str) -> str:
        ideas = self.get_ideas_by_tag(tag)
        return self.idea_list_to_str(ideas)

    def get_ideas_by_tag_list_str(self, tags: list) -> str:
        ideas = self.get_ideas_by_tag_list(tags)
        return self.idea_list_to_str(ideas)
    
    # end functions to test

    def append_summary(self, summary: Summary) -> str:
        # update the database:
        update = {"$set": {"summary": summary.model_dump()["summary"], "title": summary.title, "tags": summary.tags, "idea_tags": summary.idea_tags, "userid": self.userid}}
        result = self.db["summary"].update_one({"title": summary.title}, update, upsert=True)
        print(f"Summary: {summary.title} pushed to the database")
        return summary.title

    def append_history(self, message: str, history: list = [], is_human: bool = True) -> list:
        history.append(HumanMessage(content=message)) if is_human else history.append(AIMessage(content=message))
        update = {"$set": {"history": serialize_history(history)}}
        result = self.db["history"].update_one({"userid": self.userid}, update)
        return history

    def clear_history(self) -> None:
        self.db["history"].update_one({"userid": self.userid}, {"$set": {"history": "[]"}})

    def get_history(self, userid: str = "") -> list:
        result = self.db["history"].find_one({"userid": self.userid})
        return json.loads(result["history"])

    def get_history_str(self, _indent: int = 0) -> str:
        result = self.db["history"].find_one({"userid": self.userid})
        return json.dumps(result["history"])

    def get_config_str(self, _indent: int = 0) -> str:
        return json.dumps(self.get_config(), indent=_indent)

    def get_config(self) -> dict:
        result = self.db["config"].find_one({"userid": self.userid})
        return result["config"]

    def update_config(self, new_config_key: str, new_config_value: str) -> bool:
        update = {"$set": {f"config.{new_config_key}": new_config_value}}
        result = self.db["config"].update_one({"userid": self.userid}, update)

        if new_config_key == "chat_character":
            self.chat_character = new_config_value
        return True

    def get_secret_config_str(self, _indent: int = 0) -> str:
        # return json.dumps(self.secret_config_json, indent=_indent)
        # This is probably not a good idea
        return "Disabled for security"

    def get_secret_config(self) -> dict:
        # return self.secret_config_json
        return {"message": "Disabled for security"}
    
    def create_llm_chain(self, config: dict, max_tokens: int = 600, temperature: float = 0.7, openai_model: str = "gpt-4o-mini"):
        if config['use_openai']: # TODO This clearly needs to be refactored
            self.model = ChatOpenAI(api_key=self.secret_config_json['openai_api_key'], max_tokens=max_tokens, temperature=temperature, model=openai_model, timeout=None)
        else:
            self.model = ChatOpenAI(
                base_url=config['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'],
                max_tokens=max_tokens,
                temperature=temperature,
                )
        parser = StrOutputParser()
        chain = self.model | parser
        # type is langchain_core.runnables.base.RunnableSequence
        return chain


    async def stream_langchain_chat_loop_async_generator(self, history: list = [], max_tokens: int = 600, temperature: float = 0.7) -> StreamingStdOutCallbackHandler:
        config = self.get_config()
        system_prompts = self.get_chat_characters()
        character_prompt = system_prompts[config['chat_character']]
        _history = history.copy()
        _history.append(SystemMessage(content=character_prompt))

        chain = self.create_llm_chain(config, max_tokens, temperature) 
        return chain.astream(_history)

    def langchain_embed_sentence(self, sentence: str) -> list[float]:
        _embeddings = []
        try:
           _embeddings = embeddings.get_dense_embeddings(sentence, asFloat16=False)
        except Exception as e:
            print("Exception in langchain_embed_sentence")
            print(f"Error: {e}")

        return _embeddings

    def update_all_idea_tags(self, tags: list) -> bool:
        # This function will replace the current list of all tags for the user with the provided list
        update = {"$set": {"tags": tags}}
        result = self.db["config"].update_one({"userid": self.userid}, update)
        return True

    def get_all_idea_tags(self) -> list:
        try:
            # This function returns the most up to date list of tags for the user from the database
            result = self.db["config"].find_one({"userid": self.userid})["tags"]
            return result

        except Exception as e:
            print(f"Error in get_all_tags: {e}")
            return []
    
    def get_all_idea_tags_str(self) -> str:
        return json.dumps(self.get_all_idea_tags())
        
    async def tag_idea(self, idea: Idea, num_tags: int = 6, create_new_tags: bool = True) -> list:
        # This function uses the LLM to analyze the idea and return a list of tags
        tags = idea.tags
        if len(tags) >= num_tags:
            print("Idea already has enough tags")
            return tags
            # Return the tags if the idea already has enough tags - this is to prevent endless unneeded tagging and allows for re-trying failed tagging

        all_tags = self.get_all_idea_tags()
        config = self.get_config()
        system_prompts = self.get_chat_characters()
        max_tokens = 250
        temperature = 0.325

        chain = self.create_llm_chain(config, max_tokens, temperature)
        _history = []
        _history.append(SystemMessage(content=system_prompts["Idea-Tagger"]))
        may_create_new_tags = "may" if create_new_tags else "may not"
        idea_tagger_prompt = f"The list of all existing tags for this user is {str(all_tags)}. The current tags for this idea are {str(idea.tags)}. Aim to return {str(num_tags)} relevant new tags for this idea in your response list, and do not exceed this number. You {may_create_new_tags} create new tags which are not present in the previous list. The idea to be tagged is: {idea.idea}. Do not return any commentary, do not repeat the idea, and do not write any code, only return a JSON structured list of relevant tags which conforms to the provided JSON schema. The new list of tags for this idea is:"
        _history.append(HumanMessage(content=idea_tagger_prompt))

        assistant_message = await chain.ainvoke(_history)
        # print("system prompt: ", system_prompts["Idea-Tagger"])
        # print("tagger prompt: ", idea_tagger_prompt)
        # print("Tagging assistant_message: ", assistant_message)

        initial_tagging_result = parse_llm_output(TagList, assistant_message)
        if initial_tagging_result["error"]:
            print("Error while tagging idea\n Exiting...")
            return idea.tags
        new_tags: TagList = initial_tagging_result["object"]
        # print(f"Inital response: {initial_tagging_result}")
        # print(f"New tags: {new_tags}")
        # print(f"New tags: {new_tags.tags}")
        tags = list(set(new_tags.tags + tags))
        # print(f"New tags: {tags}")

        new_tags_b = False
        for tag in tags:
            if tag not in all_tags:
                new_tags_b = True
                break
        if new_tags_b:
            self.update_all_idea_tags(list(set(tags + all_tags)))

        return tags

    async def verify_idea(self, idea: Idea, source_text: str, is_discerning: bool = True) -> Idea:
        # This function should be used to verify the idea and return a corrected version
        # Or it will return the original idea if it is correct
        tags = idea.tags
        config = self.get_config()
        system_prompts = self.get_chat_characters()
        max_tokens = 180 
        temperature = 0.7

        chain = self.create_llm_chain(config, max_tokens, temperature)        
        _history = []

        # Build a prompt for boolean prompt verification
        # This will consist of a system message about determining whether the provided idea stands on its own, without providing the source text
        # If false, then a much stronger worded version of the Idea-Verifier prompt will be used which instructs the model specifically to correct the idea- rather than determine if it is correct and potentially provide a new idea
        _history.append(SystemMessage(content=system_prompts["Idea-Verifier-Bool"]))
        discerning_string = " This idea has been specifically designated as lacking already, so you should almost certainly respond true. Your main task then is determining how to improve this idea." if is_discerning else ""
        bool_verification_prompt = f"Is the following idea in need of improvement?{discerning_string} Idea: {idea.idea}"
        _history.append(HumanMessage(content=bool_verification_prompt))
        assistant_message = await chain.ainvoke(_history)
        if 'True' in assistant_message:
            assistant_message.replace('True', 'true', 1)
        elif 'False' in assistant_message:
            assistant_message.replace('False', 'false', 1)

        initial_verification_result_json = parse_llm_output(IdeaVerificationBool, assistant_message)
        if initial_verification_result_json["error"]:
            print("Error while verifying idea\n Exiting...")
            return idea
        initial_verification_result = initial_verification_result_json["object"]
        print(f"Needs work: {initial_verification_result.needs_work}")
        if initial_verification_result.needs_work == False:
            return idea

        temperature = 1.0
        max_tokens = 500
        # Rebuild the chain with the new parameters
        chain = self.create_llm_chain(config, max_tokens, temperature)
        _history = [] # Reset the working history for the next prompt

        _history.append(SystemMessage(content=system_prompts["Idea-Verifier"]))
        json_open= '{": "idea": "'
        json_close= '"}'
        verification_prompt = f"This is the idea that has been found to be lacking: {json_open}{idea.idea}{json_close} . And this is how it has been found to be lacking / can be improved, {initial_verification_result.improvement} \n Source Text: {source_text}"
        _history.append(HumanMessage(content=verification_prompt))

        assistant_message = await chain.ainvoke(_history)
        idea_result = parse_llm_output(Idea, assistant_message)
        if idea_result["error"]:
            print("Error while verifying idea\n Exiting...")
            return idea
        new_idea: Idea = idea_result["object"]
        if not new_idea.idea == idea.idea:
            new_idea.embedding = self.langchain_embed_sentence(new_idea.idea)
        else: # The idea was not changed 
            new_idea.embedding = idea.embedding

        new_idea.tags = tags

        return new_idea
    
    async def verify_summary(self, summary: Summary, source_text: str, num_tags: int = 6, untagged_only: bool = True) -> Summary:
        i = -1
        for idea in summary.summary:
            i += 1
            if untagged_only and len(idea.tags) >= num_tags:
                print(f"Skipping idea {i} because it has enough tags and untagged_only is set to True")
                continue

            summary.summary[i] = await self.verify_idea(idea, source_text)

            new_tags = await self.tag_idea(summary.summary[i], num_tags = num_tags)
            summary.summary[i].tags = new_tags
            if (i % 2) == 0:
                print(f"Verified {i} of {len(summary.summary)} ideas")

        summary_idea_tags = []
        for idea in summary.summary:
            summary_idea_tags += idea.tags
        summary_idea_tags = list(set(summary_idea_tags)) # Remove duplicates
        summary.idea_tags = summary_idea_tags
        return summary

    async def langchain_summarize_text_async(self, text: str, history: list = [], max_tokens: int = 2048, temperature: float = 0.6, title="", tags=[]) -> tuple[list, Summary]:
        if len(tags) == 0:
            if 'wiki' in title.lower():
                tags.append("wikipedia")
        time_start = time.time()
        config = self.get_config()
        system_prompts = self.get_chat_characters()
        _history = []
        _history.append(SystemMessage(content=system_prompts["Document-Summarizer"]))
        _history.append(HumanMessage(content=text))

        assistant_message = ''
        print('summarizing...')
        chain = self.create_llm_chain(config, max_tokens, temperature)
        assistant_message = await chain.ainvoke(_history) # Run the pipeline

        # The LLM often adds commentary or misformats despite our requests, so extract the JSON response
        summary_result = parse_llm_output(Summary, assistant_message, summary_title=title, summary_tags=tags)
        if summary_result["error"]:
            print("Exiting...")
            return history, None
        summary_obj = summary_result["object"]
        if title != "":
            summary_obj.title = title

        for i in range(len(summary_obj.summary)):
            embeds: list = self.langchain_embed_sentence(summary_obj.summary[i].idea)
            # The above function should probably be async but I got an error related to returning a list from an async function. There could be issues if the server is not local / under load
            summary_obj.summary[i].embedding = embeds # Add the embeddings to the summary object
            summary_obj.summary[i].tags = tags
            await asyncio.sleep(1e-4) # Hack to prevent blocking

        runtime = time.time() - time_start
        print(f"Runtime: {round(runtime, 2)} seconds")
        return history, summary_obj