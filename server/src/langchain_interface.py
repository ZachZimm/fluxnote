import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from utils import read_config, parse_llm_output
from fastapi import WebSocket
from models.Summary import Summary, Idea


# TODO create a way of keeping the secrets_config up to date with available secrets without tracking it in git
# read loaded secrets' keys -> compare those with saved key names -> if a key is missing add it to the secrets_config
# once I start using something that needs to be secret, anyways
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
    history = []
    chain = None


    def __init__(self):
        self.config_json = read_config(self.config_path)
        self.secret_config_json = read_config(self.secret_config_path)
        self.system_prompts = read_config(self.system_prompts_path)
        os.environ["OPENAI_API_KEY"] = self.secret_config_json['openai_api_key']
        self.model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'])
        self.url = f"{self.config_json['llm_base_url']}/v1/chat/completions"

    def append_history(self, message: str, history: list = [], is_human: bool = True) -> list:
        history.append(HumanMessage(content=message)) if is_human else history.append(AIMessage(content=message))
        return history

    # def stream_langchain_chat_loop(self, history: list = []) -> list:
    #     history.append(SystemMessage(content=self.system_prompts[self.chat_character]))
    #     self.model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1',
    #                             api_key=self.secret_config_json['openai_api_key'],
    #                             max_tokens=600,
    #                             temperature=0.7
    #                              )

    #     while True:
    #         message = input("\n> ")
    #         if message == "exit":
    #             return history
    #         history.append(HumanMessage(content=message))
    #         parser = StrOutputParser()
    #         chain = self.model | parser 

    #         assistant_message = ''
    #         print()
    #         for chunk in chain.stream(history):
    #             print(chunk, end="", flush=True)
    #             assistant_message += chunk
    #         print()
    #         history.append(AIMessage(content=assistant_message))

    async def stream_langchain_chat_loop_async_generator(self, history: list = []):
        history.append(SystemMessage(content=self.system_prompts[self.chat_character]))
        
        self.model = ChatOpenAI(base_url=self.config_json['llm_base_url']+'/v1',
                                api_key=self.secret_config_json['openai_api_key'],
                                max_tokens=600,
                                temperature=0.7
                                )

        parser = StrOutputParser()
        chain = self.model | parser 
        return chain.astream(history)

    
    # def langchain_summarize_text(self, text: str, history: list = []) -> tuple[list, Summary]:
    #     _history = history
    #     _history.append(SystemMessage(content=self.system_prompts["Document-Summarizer"]))
    #     _history.append(HumanMessage(content=text))
        
    #     self.model = ChatOpenAI(
    #         base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'],
    #         max_tokens=1536,
    #         temperature=0.5,
    #         )
    #     parser = StrOutputParser()
    #     chain = self.model | parser
    #     assistant_message = ''
    #     print('summarizing...')
    #     for chunk in chain.stream(_history):
    #         assistant_message += chunk

    #     # The LLM often adds commentary or misformats despite our requests, so extract the JSON response
    #     summary_result = parse_llm_output(Summary, assistant_message)
    #     if summary_result["error"]:
    #         print("Exiting...")
    #         return history, None
    #     summary_obj = summary_result["object"]
    #     # print(summary_obj.summary)
    #     # history.append(HumanMessage(content=text)) # Not sure which of these to add to the history
    #     history.append(AIMessage(content=str(summary_obj.model_dump()))) # It many not matter in the end
    #     return history, summary_obj

    async def langchain_summarize_text_async(self, text: str, history: list = []) -> tuple[list, Summary]:
        time_start = time.time()
        _history = history
        _history.append(SystemMessage(content=self.system_prompts["Document-Summarizer"]))
        _history.append(HumanMessage(content=text))
        
        self.model = ChatOpenAI(
            base_url=self.config_json['llm_base_url']+'/v1', api_key=self.secret_config_json['openai_api_key'],
            max_tokens=1536,
            temperature=0.5,
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
        history.append(AIMessage(content=str(summary_obj.model_dump()))) # It many not matter in the end
        return history, summary_obj

    def text_summary_loop(self, history: list = []) -> list: 
        # This function is essentialy deprecated
        print("1: sample_data/marcuscrassus.txt")
        print("2: sample_data/juluiscaesar.txt")
        print("3: sample_data/thaiculture.txt")
        file_path = input("Provide the path to the text file you would like to summarize:  ")
        if file_path == "exit":
            exit()
        elif file_path == "skip":
            return history
        elif file_path == "1":
            file_path = "sample_data/marcuscrassus.txt"
        elif file_path == "2":
            file_path = "sample_data/juluiscaesar.txt"
        elif file_path == "3":
            file_path = "sample_data/thaiculture.txt"
        elif file_path == "":
            file_path = "../README.md"
        print()
        text = ""
        if not os.path.exists(file_path):
            print("File not found.")
            return {"error": "File not found."}

        with open(file_path, "r") as file:
            text = file.read()
        
        history, summary = self.langchain_summarize_text(text, history)

        # once a little more infrastructure is in place, we can save the summaries to a database
        # the database entries should include the user, the topic, the original text, the summary object, and the date
        
        return history


# if __name__ == "__main__":
#     langchain_i = langchain_interface()
#     history = langchain_i.text_summary_loop()
#     langchain_i.stream_langchain_chat_loop(history)
