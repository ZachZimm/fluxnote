import starlette.websockets
import uvicorn
from fastapi import FastAPI, WebSocket
from langchain_interface import langchain_interface
from wiki_interface import WikiInterface
import sys
import json
import asyncio
import interactions

app = FastAPI()
loop = asyncio.new_event_loop()
welcome_message = "Enter 'options' to see available text files to summarize or 'exit' to quit."
wiki_results = {}
_debug = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None: 
    """
    This function is called when a websocket connection is established. Within the loop, the value of the 'func' key in the JSON object is used to determine which function to call. The function is then called with the arguments provided in the JSON object. The function returns a message and a mode. The message is sent back to the client as a JSON object and the mode is used to determine how the message is displayed on the client side.
    """
    try:
        await websocket.accept()
        await interactions.send_ws_message(websocket, welcome_message, mode="welcome")
        lc_interface = langchain_interface()
        wiki = WikiInterface()
        while True:
            data = await websocket.receive_json()
            """
            {"func": "chat", "message": "Hello"}
            {"func": "get_current_configuration"}
            {"func": "get_configuration_options", "field": "character"}
            {"func": "configure", "selected_character": "Sherlock-Holmes"}
            {"func": "summmarize", "file_path": "path/to/file"}
            {"func": "summmarize", "file_index": "1"}
            {"func": "options", "message": "options"}
            """
            lc_interface.append_user_history(json.dumps(data))
            if _debug:
                print(data)
            if data["func"] == "quit":
                # I don't think I need to do this if the client closes the connection
                await websocket.close()
                break

            func_name = data.get("func")
            if func_name not in interactions.available_request_functions:
                await interactions.send_ws_message(websocket, f"Invalid function request: {func_name}", mode="error")
                continue

            # Call the function with the provided arguments
            func = interactions.available_request_functions[func_name]
            kwargs = {k: v for k, v in data.items() if k != "func"}
            async_functions = ["chat", "summarize", "summarize_article", "summarize_file"] # Unfortunately some of the functions need to be handled differently. This is a temporary solution and will be refactored.
            wiki_functions = ["wiki_search", "wiki_results", "wiki"]
            if func_name in async_functions:
                response_message, response_mode = await func(websocket, lc_interface, **kwargs)
            elif func_name in wiki_functions:
                response_message, response_mode = await func(websocket, lc_interface, wiki, **kwargs)
            else:
                response_message, response_mode = func(websocket, lc_interface, **kwargs)

            await interactions.send_ws_message(websocket, response_message, mode=response_mode)
    except starlette.websockets.WebSocketDisconnect:
        print("Websocket client disconnected.")
        pass


if __name__ == "__main__":
    print(json.dumps(sys.argv))
    if '--debug' in json.dumps(sys.argv):
        print("Debug mode enabled.")
        _debug = True

    uvicorn.run(app, host="0.0.0.0", port=8090)

# TODO
# things to think about:
# Users (authentication?)
# Topics
