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
welcome_message = "Enter 'options' to see available text files to summarize or 'exit' to quit."


async def send_ws_message(websocket: WebSocket, message: str, mode: str = "default"):
    await websocket.send_json({"message": message, "mode": mode})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket): # In order to scale, I imagine this all should be within a class that can be instantiated on connection
    await websocket.accept()
    await send_ws_message(websocket, welcome_message, mode="welcome")
    lc_interface = langchain_interface()
    wiki_results = []
    history = []
    wiki = WikiInterface()

    # this will be replaced with a database query
    # or just a filesystem lookup depending on the implementation
    # or user preferences
    files_in_dir = os.listdir("sample_data")
    available_files = [f"sample_data/{file}" for file in files_in_dir if file.endswith(".txt")]

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

            await send_ws_message(websocket, json.dumps(options_message), mode="options")
        elif data.isdigit():
            file_path = data
            file_path = available_files[int(file_path) - 1]

            if not os.path.exists(file_path):
                await send_ws_message(websocket, "File not found.")
                continue

            with open(file_path, "r") as file:
                text = file.read()

            history, summary = await lc_interface.langchain_summarize_text_async(text, history)
            summary_string = json.dumps(summary.model_dump())
            history = lc_interface.append_history(summary_string, history, is_human = False)
            if summary:
                await send_ws_message(websocket, summary_string, mode="summary")
            else:
                await send_ws_message(websocket, "Error summarizing text.", mode="summary error")

        elif data == "chat":
            await send_ws_message(websocket, "Enter 'exit' to quit chat.", mode="chat")
            while True:
                chat_data = await websocket.receive_text() # TODO This should be recveive_json
                user_message = chat_data.strip()
                if user_message == "exit":
                    await send_ws_message(websocket, "Exiting chat.", mode="chat exit")
                    break

                history = lc_interface.append_history(user_message, history, is_human = True)
                generator = await lc_interface.stream_langchain_chat_loop_async_generator(history)
                assistant_message = ""
                async for chunk in generator:
                    assistant_message += chunk
                    await send_ws_message(websocket, chunk, mode="chat streaming")
                await send_ws_message(websocket, "<stream_finished>", mode="chat streaming finished")

                history = lc_interface.append_history(assistant_message, history, is_human = False)
                print(assistant_message)
        elif data == "wiki search":
            await send_ws_message(websocket, "Enter a search term:")
            query = await websocket.receive_text() # TODO This should be recveive_json
            query_results = wiki.search(query)
            max_results = 10
            wiki_results = []
            for i, result in enumerate(query_results):
                if i >= max_results:
                    break
                # await send_ws_message(websocket, f"{i + 1}. {result}", mode="wiki search results")
                wiki_results.append(result)
            await send_ws_message(websocket, json.dumps(wiki_results), mode="wiki search results")
        elif data == "wiki results":
            await send_ws_message(websocket, json.dumps(wiki_results), mode="wiki search results")
            # for i, result in enumerate(wiki_results):
                # await send_ws_message(websocket, f"{i + 1}. {result}")
        elif data == "wiki" or data == "wikid":
            if len(wiki_results) == 0 and data == "wiki":
                await send_ws_message(websocket, "No search results. Enter 'wiki search' to search for a topic.", mode="wiki error")
            if data == "wiki":
                await send_ws_message(websocket, "Enter a number corresponding to a search result:", mode="wiki")
            else:
                await send_ws_message(websocket, "Enter the name of a wikipedia page:", mode="wiki")
            query = await websocket.receive_text() # TODO This should be recveive_json
            query = query.strip()
            if not query.isdigit() and data != "wikid":
                await send_ws_message(websocket, "Invalid input. Enter a number corresponding to a search result.", mode="wiki error")
                await send_ws_message(websocket, "Enter 'wiki search' to search for a topic.\nOr 'wiki results' to see the search results.", mode="wiki error")

            else:
                if data == "wikid":
                    data = wiki.get_data(query.strip())
                else:
                    data = wiki.get_data(wiki_results[int(query) - 1])

                await send_ws_message(websocket, f"Wiki info for {data.title} downloaded.", mode="wiki")
                await send_ws_message(websocket, f"Summary: {data.summary}", mode="wiki")
                await send_ws_message(websocket, f"Download content? (y/n)", mode="wiki")
                download_content = await websocket.receive_text()
                if 'y' in download_content:
                    filepath = f"sample_data/{data.title.replace(' ', '_')}_wikidownload.txt"
                    with open(filepath, "w") as file:
                        file.write(data.content)
                    await send_ws_message(websocket, f"Content downloaded to {filepath}", mode="wiki")
                    available_files.append(filepath)
                        
        elif data == "clear":
            history = []
            await send_ws_message(websocket, "History cleared.", mode="status")
        else:
            await send_ws_message(websocket, "Invalid input. Enter 'options' to see available text files to summarize or 'exit' to quit.", mode="status")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)

# TODO
# things to think about:
# Users (authentication?)
# Topics