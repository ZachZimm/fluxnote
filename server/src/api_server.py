from fastapi import FastAPI, WebSocket
from langchain_interface import langchain_interface
import os
import json
import asyncio

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Enter 'options' to see available text files to summarize or 'exit' to quit.")
    lc_interface = langchain_interface()
    history = []

    # this will be replaced with a database query
    # or just a filesystem lookup depending on the implementation
    # or user preferences
    available_files = ["sample_data/marcuscrassus.txt", "sample_data/juluiscaesar.txt", "sample_data/thaiculture.txt"]

    while True:

        data = await websocket.receive_text()
        data = data.strip()
        print(data)
        if data == "exit":
            print("User requested exit")
            break
        elif data == "options":
            print("User requested options")
            options_message = []
            for i, file in enumerate(available_files):
                options_message.append(f"{i + 1}: {file}")
            options_message.append("Provide the number corresponding with text file you would like to summarize:")

            for message in options_message:
                await websocket.send_text(message)
        elif data.isdigit():
            file_path = data
            file_path = available_files[int(file_path) - 1]

            if not os.path.exists(file_path):
                await websocket.send_text("File not found.")
                continue

            with open(file_path, "r") as file:
                text = file.read()

            history, summary = await lc_interface.langchain_summarize_text_async(text, history)
            if summary:
                await websocket.send_text(json.dumps(summary.model_dump()))
            else:
                await websocket.send_text("Error summarizing text.")
        else:
            await websocket.send_text("Invalid input. Enter 'options' to see available text files to summarize or 'exit' to quit.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
# TODO
# implement a fastapi server that can be used to interact with the langchain_interface
# things to think about:
# Websockets
# Users (authentication?)
# Topics

# Probably for a different part of the code: a resolution aware conversation
# ex: "I want to know more about X" -> Finds ideas closely related to X -> Searches the database for detailed information (high resolution summaries) on X related ideas -> Generates a response with the most relevant information

# if __name__ == "__main__":
#     langchain_i = langchain_interface()
#     history = langchain_i.text_summary_loop()
#     langchain_i.stream_langchain_chat_loop(history)