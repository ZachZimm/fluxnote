# TODO rename this file to something LLM related
import sys
import requests
import os
import json
import langchain
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import TextGen
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from utils import read_config

# TODO create a way of keeping the secrets_config up to date with available secrets without tracking it in git
# read loaded secrets' keys -> compare those with saved key names -> if a key is missing add it to the secrets_config

class langchain_interface():
    chat_character = "Sherlock-Holmes"
    config_path = "src/config.json"
    secret_config_path = "src/secret_config.json"
    system_prompts_path = "src/system_prompts.json"
    config_json = {}
    secret_config_json = {}
    system_prompts = {}
    model = None
    headers = { "Content-Type": "application/json" }
    url = ""

    def __init__(self):
        self.config_json = read_config(self.config_path)
        self.secret_config_json = read_config(self.secret_config_path)
        self.system_prompts = read_config(self.system_prompts_path)
        os.environ["OPENAI_API_KEY"] = self.secret_config_json['openai_api_key']
        self.model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'])
        self.url = f"{self.config_json['llm_base_url']}/v1/chat/completions"

    def stream_langchain_chat_loop(self, history: list = []) -> list:
        history.append(SystemMessage(content=self.system_prompts[self.chat_character]))
        model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'])

        while True:
            message = input("\n> ")
            if message == "exit":
                return history
            history.append(HumanMessage(content=message))
            parser = StrOutputParser()
            chain = model | parser 

            assistant_message = ''
            for chunk in chain.stream(history):
                print(chunk, end="", flush=True)
                assistant_message += chunk

            history.append(AIMessage(content=assistant_message))


    def langchain_summarize_text(self, text: str, history: list = []) -> list:
        _history = history
        _history.append(SystemMessage(content=self.system_prompts["Document-Summarizer"]))
        _history.append(HumanMessage(content=text))
        history.append(HumanMessage(content=text))
        model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'])
        
        parser = StrOutputParser()
        chain = model | parser
        assistant_message = ''
        for chunk in chain.stream(_history):
            print(chunk, end="", flush=True)
            assistant_message += chunk
        history.append(AIMessage(content=assistant_message))
        print()
        return  history 

    def text_summary_loop(self, history: list = []) -> list: 
        print("1: sample_data/marcuscrassus.txt")
        print("2: sample_data/juluiscaesar.txt")
        file_path = input("Provide the path to the text file you would like to summarize:  ")
        if file_path == "exit":
            exit()
        elif file_path == "skip":
            return history
        elif file_path == "1":
            file_path = "sample_data/marcuscrassus.txt"
        elif file_path == "2":
            file_path = "sample_data/juluiscaesar.txt"
        elif file_path == "":
            file_path = "../README.md"
        print()
        text = ""
        if not os.path.exists(file_path):
            print("File not found.")
            return {"error": "File not found."}

        with open(file_path, "r") as file:
            text = file.read()
        
        history = self.langchain_summarize_text(text, history)

        return history


if __name__ == "__main__":
    langchain_i = langchain_interface()
    history = langchain_i.text_summary_loop()
    langchain_i.stream_langchain_chat_loop(history)