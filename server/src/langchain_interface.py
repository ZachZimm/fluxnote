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
from models.Summary import Summary, Idea
from pymongo import MongoClient

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
    embed_model = None
    headers = { "Content-Type": "application/json" }
    url = ""
    history = []
    permanent_characters = []
    chain = None
    mongo_client = None
    db = None

    def __init__(self, userid: str = ""):
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
        update = {"$setOnInsert": document} # This will only insert the document if it doesn't exist
        result = self.db["config"].update_one(filter, update, upsert=True)

        # if there is no history in the database, create it
        if not self.db["history"].find_one({"userid": self.userid}): 
            history = {
                "userid": self.userid,
                "history": serialize_history(self.history)
            }
            self.db["history"].insert_one(history)
        

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

    def append_history(self, message: str, history: list = [], is_human: bool = True) -> list:
        history.append(HumanMessage(content=message)) if is_human else history.append(AIMessage(content=message))
        update = {"$set": {"history": serialize_history(history)}}
        result = self.db["history"].update_one({"userid": self.userid}, update)
        return history
    
    def clear_history(self) -> None:
        self.db["history"].update_one({"userid": self.userid}, {"$set": {"history": "[]"}})
        self.history = []
    
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
    
    def get_secret_config_str(self, _indent: int = ) -> str:
        # return json.dumps(self.secret_config_json, indent=_indent)
        # This is probably not a good idea
        return "Disabled for security"

    def get_secret_config(self) -> dict:
        # return self.secret_config_json
        return "Disabled for security"

    async def stream_langchain_chat_loop_async_generator(self, history: list = [], max_tokens: int = 600, temperature: float = 0.7) -> StreamingStdOutCallbackHandler:
        config = self.get_config()
        system_prompts = self.get_chat_characters()
        character_prompt = system_prompts[config['chat_character']]
        _history = history
        history.append(SystemMessage(content=character_prompt))

        if config['use_openai']:
            self.model = ChatOpenAI(api_key=self.secret_config_json['openai_api_key'], max_tokens=600, temperature=0.7)
        else: 
            self.model = ChatOpenAI(base_url=config['llm_base_url']+'/v1',
                                api_key=self.secret_config_json['openai_api_key'],
                                max_tokens=max_tokens,
                                temperature=temperature
                                )

        parser = StrOutputParser()
        chain = self.model | parser 
        return chain.astream(history)

    def langchain_embed_sentence(self, sentence: str, config: dict = None) -> list[float]:
        if config is None: config = self.get_config()
        embeds = []
        try:
            if config['use_openai']:
                self.embed_model = OpenAIEmbeddings(api_key=self.secret_config_json['openai_api_key'])
            else:
                self.embed_model = OpenAIEmbeddings(base_url=config['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key']) # Assuming your OpenAI compatible api has an endpoint for embeddings
            embeds = self.embed_model.embed_query(sentence)
        except Exception as e:
            print("Exception in langchain_embed_sentence")
            print(f"Error: {e}")
            
        return embeds 

    async def langchain_summarize_text_async(self, text: str, history: list = [], max_tokens: int = 1536, temperature: float = 0.5) -> tuple[list, Summary]:
        time_start = time.time()
        config = self.get_config()
        system_prompts = self.get_chat_characters()
        _history = [] 
        _history.append(SystemMessage(content=system_prompts["Document-Summarizer"]))
        _history.append(HumanMessage(content=text))
        if config['use_openai']:
            self.model = ChatOpenAI(api_key=self.secret_config_json['openai_api_key'], max_tokens=max_tokens, temperature=temperature)
        else: 
            self.model = ChatOpenAI(
                base_url=config['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'],
                max_tokens=max_tokens,
                temperature=temperature,
                )
        parser = StrOutputParser()
        chain = self.model | parser # Build the pipeline
        assistant_message = ''
        print('summarizing...')
        assistant_message = await chain.ainvoke(_history) # Run the pipeline

        # The LLM often adds commentary or misformats despite our requests, so extract the JSON response
        summary_result = parse_llm_output(Summary, assistant_message)
        if summary_result["error"]:
            print("Exiting...")
            return history, None
        summary_obj = summary_result["object"]

        self.append_history(str(summary_obj.model_dump()), history) # do this before we add the embeddings
        for i in range(len(summary_obj.summary)): 
            embeds: list[float] = self.langchain_embed_sentence(summary_obj.summary[i].idea, config=config)
            # The above function should probably be async but I got an error related to returning a list from an async function. There could be issues if the server is not local / under load
            summary_obj.summary[i].embedding = embeds # Add the embeddings to the summary object
            await asyncio.sleep(1e-4) # Hack to prevent blocking 

        runtime = time.time() - time_start
        print(f"Runtime: {round(runtime, 2)} seconds")
        # history.append(HumanMessage(content=text)) # Not sure which of these to add to the history
        # history.append(AIMessage(content=str(summary_obj.model_dump()))) # It many not matter in the end
        
        return history, summary_obj