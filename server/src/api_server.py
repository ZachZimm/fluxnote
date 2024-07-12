import uvicorn
from fastapi import FastAPI, WebSocket
from langchain_interface import langchain_interface
from wiki_interface import WikiInterface
import os
import json
import threading
import asyncio

app = FastAPI()
loop = asyncio.new_event_loop()

async def send_ws_message(websocket: WebSocket, message: str):
    await websocket.send_json({"message": message})

def streaming_callback(websocket: WebSocket, message: str):
    # asyncio.run(send_ws_message(websocket, message))    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_ws_message(websocket, message))
    loop.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket): # In order to scale, I imagine this all should be within a class that can be instantiated on connection
    await websocket.accept()
    await websocket.send_text("Enter 'options' to see available text files to summarize or 'exit' to quit.")
    lc_interface = langchain_interface()
    wiki_results = []
    history = []

    # this will be replaced with a database query
    # or just a filesystem lookup depending on the implementation
    # or user preferences
    available_files = ["sample_data/marcuscrassus.txt", "sample_data/juluiscaesar.txt", "sample_data/thaiculture.txt"]

    while True: # This seems like a really poor way to handle this
                # surely the different cases can at least be split into functions / files

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
                await send_ws_message(websocket, message)
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
                await send_ws_message(websocket, json.dumps(summary.model_dump()))
            else:
                await send_ws_message(websocket, "Error summarizing text.")
        elif data == "chat":
            await websocket.send_text("Chat:")
            while True:
                chat_data = await websocket.receive_text() # TODO This should be recveive_json
                user_message = chat_data.strip()
                if user_message == "exit":
                    break

                history = lc_interface.append_history(user_message, history, is_human = True)
                generator = await lc_interface.stream_langchain_chat_loop_async_generator(history)
                assistant_message = ""
                async for chunk in generator:
                    assistant_message += chunk
                    await send_ws_message(websocket, chunk)

                history = lc_interface.append_history(assistant_message, history, is_human = False)
                print(assistant_message)
        elif data == "wiki search":
            await send_ws_message(websocket, "Enter a search term:")
            wiki = WikiInterface()
            query = await websocket.receive_text() # TODO This should be recveive_json
            query_results = wiki.search(query)
            max_results = 10
            wiki_results = []
            for i, result in enumerate(query_results):
                if i >= max_results:
                    break
                await send_ws_message(websocket, f"{i + 1}. {result}")
                wiki_results.append(result)
        elif data == "wiki results":
            for i, result in enumerate(wiki_results):
                await send_ws_message(websocket, f"{i + 1}. {result}")
        elif data == "wiki" or data == "wikid":
            if len(wiki_results) == 0 and data == "wiki":
                await send_ws_message(websocket, "No search results. Enter 'wiki search' to search for a topic.")
            if data == "wiki":
                await send_ws_message(websocket, "Enter a number corresponding to a search result:")
            else:
                await send_ws_message(websocket, "Enter the name of a wikipedia page:")
            query = await websocket.receive_text() # TODO This should be recveive_json
            query = query.strip()
            if not query.isdigit() and query != "wikid":
                await send_ws_message(websocket, "Invalid input. Enter a number corresponding to a search result.")
                await send_ws_message(websocket, "Enter 'wiki search' to search for a topic.\nOr 'wiki results' to see the search results.")

            else:
                if data == "wikid":
                    data = wiki.get_data(query.strip())
                else:
                    data = wiki.get_data(wiki_results[int(query) - 1])
                await send_ws_message(websocket, f"Wiki info for {data.title} downloaded.")
                await send_ws_message(websocket, f"Summary: {data.summary}")
                        
        elif data == "clear":
            history = []
            await send_ws_message(websocket, "History cleared.")
        else:
            await send_ws_message(websocket, "Invalid input. Enter 'options' to see available text files to summarize or 'exit' to quit.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)

# TODO
# things to think about:
# Users (authentication?)
# Topics