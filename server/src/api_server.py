import starlette.websockets
import uvicorn
from fastapi import FastAPI, WebSocket
from langchain_interface import langchain_interface
from wiki_interface import WikiInterface
import os
import json
import asyncio

app = FastAPI()
loop = asyncio.new_event_loop()
welcome_message = "Enter 'options' to see available text files to summarize or 'exit' to quit."
wiki_results = {}

# TODO break these all out into a separate file

async def chat(websocket, lc_interface, message, help=False):
    if help == True:
        return "Chat with the LLM, using your configured character. Information from summaries can be loaded into history for the LLM's reference but the way of doing that is in development. Currently it involves creating a summary then initiating a chat session. Chat history is currently deleted on disconnection, though that is likely to change.", "help"
    user_message = message.strip()
    history = lc_interface.get_history()
    history = lc_interface.append_history(user_message, history, is_human = True) 
    print("User message:", user_message)
    generator = await lc_interface.stream_langchain_chat_loop_async_generator(history)
    assistant_message = ""
    async for chunk in generator:
        assistant_message += chunk
        await send_ws_message(websocket, chunk, mode="chat streaming")
    # await send_ws_message(websocket, "<stream_finished>", mode="chat streaming finished")

    history = lc_interface.append_history(assistant_message, history, is_human = False)
    print(assistant_message)
    return "<stream_finished>", "chat streaming finished"

def get_chat_history(websocket, lc_interface, help=False):
    if help == True:
        return "Get the chat history.", "help"
    history = lc_interface.get_history_str()
    return history, "status"

def clear_chat_history(websocket, lc_interface, help=False):
    if help == True:
        return "Clear the chat history.", "help"
    lc_interface.clear_history()
    return "Chat history cleared.", "status"

def get_configuration(websocket, lc_interface, help=False):
    if help == True:
        return "Get the configuration options.", "help"
    config_str = lc_interface.get_config_str()
    return config_str, "status"

def get_secret_configuration(websocket, lc_interface, help=False):
    if help == True:
        return "Get the secret configuration options.", "help"
    secret_config_str = lc_interface.get_secret_config_str()
    return secret_config_str, "status"

def set_secret_configuration(websocket, lc_interface, help=False):
    if help == True:
        return "Set the secret configuration options based on arguments passed in.", "help"
    # This function will be used to set secret config options that are passed in
    return f"Secret configuration set"

def get_configuration_options(websocket, lc_interface, field, help=False):
    if help == True:
        return "Get all possible configuration fields.", "help"
    # Implement your get_configuration_options logic here
    return f"Configuration options for field: {field}"

def set_configuration(websocket, lc_interface, select_character=None, help=False):
    if help == True:
        return "Set the configuration options based on arguments passed in. Use get_configuration_options to see the availible configuration fields.", "help"
    # This function will be used to set config options that are passed in
    return f"Configured character: {select_character}"

async def summarize(websocket, lc_interface, file_path: str="sample_data/", file_index:str=None, help:bool=False):
    if help == True:
        return "Summarize text from a specified file. Either a directory with an index or a full file path can be passed in. Relative paths are not allowed.", "help"
    available_files = []
    file_path = file_path.strip().replace("..", "")
    path_is_file: bool = os.path.isfile(file_path)

    # Build a file path for the file to be summarized
    if path_is_file: 
        file_index = None
    elif file_index is not None and file_index.isdigit():
        available_files, _ = get_available_files(websocket, lc_interface, file_path)
        file_path = available_files[int(file_index) - 1]
    if file_index and not file_index.isdigit():
        return "File index must be a digit.", "summary error"

    if not os.path.exists(file_path):
        return "File not found.", "summary error"

    with open(file_path, "r") as file:
        text = file.read()
    
    await send_ws_message(websocket, "Summarizing text from " + file_path.split('\\')[-1], mode="status")

    history = lc_interface.get_history()
    history, summary = await lc_interface.langchain_summarize_text_async(text, history)
    summary_string = ""
    try:
        summary_string = json.dumps(summary.model_dump())
    except:
        # Try again
        print("Error summarizing text, trying again.")
        history, summary = await lc_interface.langchain_summarize_text_async(text, history)
        try:
            summary_string = json.dumps(summary.model_dump())
        except:
            print("Failed to summarize text.")
            return "Error summarizing text.", "summary error"
    summary_string = json.dumps(summary.model_dump())
    history = lc_interface.append_history(summary_string, history, is_human = False)
    if summary:
        return summary_string, "summary"
    else:
        return "Error summarizing text.", "summary error"
    
async def wiki_search(websocket, lc_interface, wiki, query, help=False):
    if help == True:
        return "Search the configured wiki for a query.", "help"
    query_results = wiki.search(query)
    max_results = 10
    wiki_results[lc_interface.userid] = []
    for i, result in enumerate(query_results):
        if i >= max_results:
            break
        wiki_results[lc_interface.userid].append(result)
    return json.dumps(wiki_results[lc_interface.userid]), "wiki search results"

async def get_wiki_results(websocket, lc_interface, wiki, help=False):
    if help == True:
        return "Get the results of the last wiki search.", "help"
    return json.dumps(wiki_results[lc_interface.userid]), "wiki search results"

async def wiki(websocket, lc_interface, wiki, query, should_save=False, help=False):
    if help == True:
        return "Get the content of a wiki page.", "help"
    if len(wiki_results[lc_interface.userid]) == 0:
        return "No search results. Enter 'wiki search' to search for a topic.", "wiki error"
    if not query.isdigit():
        return "Invalid input. Enter a number corresponding to a search result.", "wiki error"
    data = wiki.get_data(wiki_results[lc_interface.userid][int(query) - 1])
    return_object = {}
    return_object = {
        "title": data.title,
        "summary": data.summary,
    }

    if should_save: # This should probably also save the summary in a separate file
        # This will also save to a database as soon as I integrate that 
        filepath = f"sample_data/{data.title.replace(' ', '_')}_wikidownload.txt"
        with open(filepath, "w") as file:
            file.write(data.content)
        await send_ws_message(websocket, f"Content downloaded to {filepath}", mode="wiki")
    return return_object, "wiki"

def get_available_files(websocket, lc_interface, help = False):
    # This will not be a list of files in a path in the future, but a database query that returns a list of files associated with a user and their ids
    # probably filterable as well
    if help == True:
        return "Get a list of available text files in the path passed in.", "help"
    path = lc_interface.get_notes_dir()
    path = path.strip().replace("..", "") # Shouldn't be needed anymore
    files_in_dir = os.listdir(path)
    available_files = [f"{path}/{file}" for file in files_in_dir if file.endswith(".txt")]
    return available_files, "status"

def get_functions(websocket, lc_interface, help=False):
    if help == True:
        return "Get a list of available backend functions.", "help"
    return json.dumps(list(available_request_functions.keys())), "status"

def end_session(websocket, lc_interface, help=False):
    if help == True:
        return "End the current session.", "help"
    # await websocket.close()
    return "Ending session.", "status"

def get_help(websocket, lc_interface, help=False):
    help_message = "Available functions:\n"
    help_message += "use any command followed by 'help' to get more information on that command.\n"
    help_message += json.dumps(get_functions(websocket, lc_interface, help=True)[0])
    return help_message, "help"

# Dictionary to map function names to functions
available_request_functions = {
    "chat": chat,
    "get_configuration": get_configuration,
    "get_configuration_options": get_configuration_options,
    "get_secret_configuration": get_secret_configuration,
    "set_secret_configuration": set_secret_configuration,
    "configure": set_configuration,
    "summarize": summarize,
    "wiki_search": wiki_search,
    "wiki": wiki,
    "wiki_results": get_wiki_results,
    "options": get_functions,
    "help": get_help,
    "list": get_available_files,
    "chat_history": get_chat_history,
    "clear_history": clear_chat_history,
    "quit": end_session,
}
# End that seperate file

# This could go in the utils file as well
async def send_ws_message(websocket: WebSocket, message: str, mode: str = "default"):
    await websocket.send_json({"message": message, "mode": mode})
# End that seperate file

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket): 
    try:
        await websocket.accept()
        await send_ws_message(websocket, welcome_message, mode="welcome")
        userid = "test_user"
        lc_interface = langchain_interface(userid)
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
            if data["func"] == "quit":
                # I don't think I need to do this if the client closes the connection
                websocket.close()
                break

            func_name = data.get("func")
            if func_name not in available_request_functions:
                await send_ws_message(websocket, f"Invalid function request: {func_name}", mode="status")
                continue

            # Call the function with the provided arguments
            func = available_request_functions[func_name]
            kwargs = {k: v for k, v in data.items() if k != "func"}
            async_functions = ["chat", "summarize"]
            wiki_functions = ["wiki_search", "wiki_results", "wiki"]
            if func_name in async_functions:
                response_message, response_mode = await func(websocket, lc_interface, **kwargs)
            elif func_name in wiki_functions:
                response_message, response_mode = await func(websocket, lc_interface, wiki, **kwargs)
            else:
                response_message, response_mode = func(websocket, lc_interface, **kwargs)

            await send_ws_message(websocket, response_message, mode=response_mode)
    except starlette.websockets.WebSocketDisconnect:
        print("Websocket client disconnected.")
        pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)

# TODO
# things to think about:
# Users (authentication?)
# Topics