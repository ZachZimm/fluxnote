import json
import os
import time
from langchain_openai import ChatOpenAI
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

def serialize_history(history: list) -> str:
    _history = []
    for message in history:
        history_message = {}
        history_message['role'] = message.type
        history_message['content'] = message.content
        _history.append(history_message)
    return json.dumps(_history)

def deserialize_history(history_str: str) -> list:
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
    headers = { "Content-Type": "application/json" }
    url = ""
    history = []
    permanent_characters = []
    chain = None
    mongo_client = None
    db = None

    def __init__(self, userid: str = ""):
        self.userid = userid
        self.config_json = read_config(self.config_path)
        self.secret_config_json = read_config(self.secret_config_path)
        self.system_prompts = read_config(self.system_prompts_path)
        self.permanent_characters = self.system_prompts.keys()
        os.environ["OPENAI_API_KEY"] = self.secret_config_json['openai_api_key']
        if self.config_json['use_openai']:
            self.model = ChatOpenAI(api_key=self.secret_config_json['openai_api_key'])
        else:
            self.model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'])
        self.url = f"{self.config_json['llm_base_url']}/v1/chat/completions"
        self.config_json["notes_directory"] = self.notes_dir
        self.chat_character = self.config_json['chat_character'].replace(" ", "-")

        self.mongo_uri = self.secret_config_json['mongo_uri']
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client["fluxnote"]
        # insert these only if they don't exist
        document = {
            self.userid: 
                {
                "userid": self.userid,
                "config": self.config_json,
                "secret_config": self.secret_config_json,
                "system_prompts": self.system_prompts
                }
            }
        filter = {self.userid: {"$exists": True}}
        update = {"$setOnInsert": document} # This will only insert the document if it doesn't exist
        # update = {"$set": document} # This will update the document if it exists
        result = self.db["config"].update_one(filter, update, upsert=True)

        self.notes_dir = self.config_json['notes_directory']
        if self.notes_dir[-1] != "/":
            self.notes_dir += "/"
        
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
        result = self.db["config"].update_one({"userid": self.userid}, update)
        self.system_prompts = self.get_chat_characters()
    
    def get_chat_characters(self) -> dict:
        print(self.userid)
        result = self.db["config"].find_one({"userid": self.userid})
        return result["system_prompts"]

    def get_chat_characters_str(self) -> str:
        return json.dumps(self.get_chat_characters(), indent=4)
    
    def remove_chat_character(self, character_name: str) -> bool:
        if character_name not in self.permanent_characters:
            if character_name in self.system_prompts.keys():
                self.system_prompts.pop(character_name)
                update = {"$unset": {f"system_prompts.{character_name}": ""}}
                result = self.db["config"].update_one({"userid": self.userid}, update) 

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
        # update the history in the database
        update = {"$set": {"history": serialize_history(history)}}
        result = self.db["history"].update_one({"userid": self.userid}, update)
        return history
    
    def clear_history(self) -> None:
        self.db["history"].update_one({"userid": self.userid}, {"$set": {"history": "[]"}})
        self.history = []
    
    def get_history(self, userid: str = "") -> list:
        result = self.get_history_str()
        return deserialize_history(result)
    
    def get_history_str(self, _indent: int = 4) -> str:
        # _history = []
        # for message in self.history:
        #     history_message = {}
        #     history_message['role'] = message.type
        #     history_message['content'] = message.content
        #     _history.append(history_message)
        # return json.dumps(_history, indent=_indent)
        result = self.db["history"].find_one({"userid": self.userid})
        return result["history"]
 
    def get_config_str(self, _indent: int = 4) -> str:
        return json.dumps(self.get_config(), indent=_indent)
    
    def get_config(self) -> dict:
        result = self.db["config"].find_one({"userid": self.userid})
        return result["config"]

    def update_config(self, new_config_key: str, new_config_value: str) -> bool:
        self.config_json[new_config_key] = new_config_value
        update = {"$set": {f"config.{new_config_key}": new_config_value}}
        result = self.db["config"].update_one({"userid": self.userid}, update)
        return True
    
    def get_secret_config_str(self, _indent: int = 4) -> str:
        # return json.dumps(self.secret_config_json, indent=_indent)
        # This is probably not a good idea
        return "Disabled for security"

    def get_secret_config(self) -> dict:
        # return self.secret_config_json
        return "Disabled for security"

    async def stream_langchain_chat_loop_async_generator(self, history: list = [], max_tokens: int = 600, temperature: float = 0.7) -> StreamingStdOutCallbackHandler:
        self.append_history(self.system_prompts[self.chat_character], history, is_human=False)

        if self.config_json['use_openai']:
            self.model = ChatOpenAI(api_key=self.secret_config_json['openai_api_key'], max_tokens=600, temperature=0.7)
        else: 
            self.model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1',
                                api_key=self.secret_config_json['openai_api_key'],
                                max_tokens=max_tokens,
                                temperature=temperature
                                )

        parser = StrOutputParser()
        chain = self.model | parser 
        return chain.astream(history)

    async def langchain_summarize_text_async(self, text: str, history: list = [], max_tokens: int = 1536, temperature: float = 0.6) -> tuple[list, Summary]:
        time_start = time.time()
        _history = [] 
        _history.append(SystemMessage(content=self.system_prompts["Document-Summarizer"]))
        _history.append(HumanMessage(content=text))
        if self.config_json['use_openai']:
            self.model = ChatOpenAI(api_key=self.secret_config_json['openai_api_key'], max_tokens=max_tokens, temperature=temperature)
        else: 
            self.model = ChatOpenAI(
                base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'],
                max_tokens=max_tokens,
                temperature=temperature,
                )
        parser = StrOutputParser()
        chain = self.model | parser
        assistant_message = ''
        print('summarizing...')
        assistant_message = await chain.ainvoke(_history)

        # The LLM often adds commentary or misformats despite our requests, so extract the JSON response
        summary_result = parse_llm_output(Summary, assistant_message)
        if summary_result["error"]:
            print("Exiting...")
            return history, None
        summary_obj = summary_result["object"]
        runtime = time.time() - time_start
        print(f"Runtime: {round(runtime, 2)} seconds")
        # history.append(HumanMessage(content=text)) # Not sure which of these to add to the history
        # history.append(AIMessage(content=str(summary_obj.model_dump()))) # It many not matter in the end
        self.append_history(str(summary_obj.model_dump()), history)
        return history, summary_obj