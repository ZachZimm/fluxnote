# TODO rename this file to something LLM related
import requests
import os
import json


# TODO implement a proper provider class that can handle the different providers and their respective endpoints
# alternatively, just implement Langchain
config_path = "src/config.json"
config_json  = {}
if os.path.exists(config_path):
    with open(config_path, "r") as file:
        config_json = json.load(file)
    print("Config file loaded.")
else:
    print("Config file not found. Exiting.")

url = f"{config_json['llm_base_url']}/chat/completions"

headers = {
    "Content-Type": "application/json"
}

history = []
usage = {}

def run_chat_loop():

    while True:
        user_message = input("> ")
        print()
        if user_message == "exit":
            exit()
        elif user_message == "":
            user_message = "What is the meaning of life?"
        global history
        history.append({"role": "user", "content": user_message})
        data = {
            "mode": "chat",
            "character": config_json['chat_character'],
            "messages": history
        }

        response = requests.post(url, headers=headers, json=data, verify=False)
        assistant_message = response.json()['choices'][0]['message']['content']

        history.append({"role": "assistant", "content": assistant_message})
        global usage
        usage = response.json()['usage']
        print(assistant_message)
        print(usage)
        print()

def summarize_text(text: str) -> str:
# My initial experimentation here is suggesting that the local LLM is not able to summarize text as well as I would like. Deepseek and OpenAI work well though. I'll have to experiment more with larger models.
# This is just an initial implementation. I expect a multi-pass approach will be necessary to get the best results.
    data = {
        "mode": "chat",
        "messages": [
            {"role": "system", "content": "Your job is to summarize the following text. Do not copy the text verbatim. Do not mention that you are summarizing the text. Simply provide a summary that is about 20% the length of the original without commentary."},
            {"role": "user", "content": f"Document to be summarized:\n{text}"},
        ],
        "character": "Document-Summarizer"
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    assistant_message = response.json()['choices'][0]['message']['content']
    global usage
    usage = response.json()['usage']
    global history
    history.append(data["messages"][0])
    history.append(data["messages"][1])
    history.append({"role": "assistant", "content": assistant_message})
    # save the history to a file
    with open("history.txt", "w") as file:
        file.write(str(history))

    # summary should be verified somehow, I will have to design a chain of though routine or use one from langchain
    # summary should also be saved to a file / db along with some indication of the 'resolution' of the summary
    return assistant_message 

def text_summary_loop(): 
    print("1: sample_data/marcuscrassus.txt")
    print("2: sample_data/juluiscaesar.txt")
    file_path = input("Provide the path to the text file you would like to summarize:  ")
    if file_path == "exit":
        exit()
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
    
    summary = summarize_text(text)
    print(summary)
    print(usage)
    print()
    return {"success": True}

    


if __name__ == "__main__":
    success = False
    while not success:
        status = text_summary_loop()
        if "error" not in status.keys():
            success = True
    run_chat_loop()