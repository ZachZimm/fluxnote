import asyncio
import websockets
import json
import aioconsole

config_dir = "config.json"
config = json.load(open(config_dir))

def print_summary(summary):
    i = 0
    num_ideas = len(summary)
    print(f"Summary has {num_ideas} ideas.")

    for idea in range(num_ideas):
        print(f"{idea}: {summary[idea]['idea']}")
        i += 1

def print_json_message(json_str) -> None:
    dict_obj = json.loads(json_str)
    if dict_obj["mode"] == "chat":
        print(f"Chat: {dict_obj['message']}")
        return
    elif 'streaming' in dict_obj["mode"]:
        if 'finished' in dict_obj["mode"]:
            print("\n\n> ", end="")
            return
        print(dict_obj["message"], end="", flush=True)
        return
    elif "summary" in dict_obj["mode"]:
        if "error" in dict_obj["mode"]:
            print(f"Error: {dict_obj['message']}")
            return
        if '{' == dict_obj["message"][0]:
            dict_obj = json.loads(dict_obj["message"])
            print_summary(dict_obj["summary"])
            return
    elif "wiki search results" in dict_obj["mode"]:
        list_obj = json.loads(dict_obj["message"])
        for i in range(len(list_obj)):
            print(f"{i+1}: {list_obj[i]}")
    else:
        print(f"Mode: {dict_obj['mode']}")
        try:
            print(json.dumps(dict_obj["message"], indent=4).replace("\\"*3, "\\"))
        except:
            print("Error: Could not parse json.")
            print(dict_obj["message"])
    
        return

async def listen_for_messages(websocket) -> None:
    while True:
        message = await websocket.recv()
        print_json_message(message)

async def close_and_exit(websocket) -> None:
    # await websocket.send(json.dumps({"func": "quit"}))
    await websocket.close()
    # await websocket.close()

# This function is used to send messages to the server
# I think it should be in a seperate file and further refactored
async def send_messages(websocket) -> None: # consider checking for success and returning a boolean
    while True:
        message_object = {}
        should_continue = False
        print("Enter a command: ")
        user_command = await aioconsole.ainput()
        print()
        user_command = user_command.lower().strip()
        if user_command == "quit":
            await close_and_exit(websocket)
        elif user_command == "chat":
            # Streaming chat loop
            while True:
                message = await aioconsole.ainput()
                if message == "exit":
                    should_continue = True
                    break
                elif message == "quit":
                    await close_and_exit(websocket)
                print()
                # Message needs to be formatted as JSON
                # some examples:
                """
                {"func": "chat", "message": "Hello"}
                {"func": "get_current_configuration"}
                {"func": "get_configuration_options", "field": "character"}
                {"func": "configure", "selected_character": "Sherlock-Holmes"}
                {"func": "summmarize", "file_path": "path/to/file"}
                {"func": "summmarize", "file_index": "1"}
                {"func": "options", "message": "options"}
                {"func": "quit"}
                """
                message_object['func'] = "chat"
                message_object['message'] = message
                await websocket.send(json.dumps(message_object))

        elif 'help' == user_command:
            message_object['func'] = "help"

        elif 'summarize' in user_command:
            command_list = user_command.split(" ")
            if len(command_list) == 1:
                file_index = await aioconsole.ainput("Enter the file index: ")
                file_index = file_index.strip()
                if file_index == "quit": close_and_exit(websocket)
                if file_index == "exit": break
                if not file_index.isdigit():
                    print("File index must be a digit.")
                    continue
                else:
                    command_list.append(file_index)

            message_object['func'] = "summarize"
            message_object['file_index'] = str(command_list[1])
        elif 'wiki s' in user_command:
            message_object['func'] = "wiki_search"
            user_command_list = user_command.split(" ")
            if len(user_command_list) == 2:
                message_object['query'] = await aioconsole.ainput("Enter your search query: ")
            else:
                message_object['query'] = user_command_list[2]
        elif 'wiki r' in user_command:
            message_object['func'] = "wiki_results"
        elif 'wiki' in user_command:
            should_save_string = await aioconsole.ainput("Save this wiki page? (y/n): ")
            should_save = True if 'y' in should_save_string else False
            message_object['func'] = "wiki"
            message_object['query'] = user_command.split("wiki ")[1]
            message_object['should_save'] = should_save
        else:
            message_object = {"func": user_command}
        
        if 'help' in user_command:
            message_object['help'] = True
        
        if should_continue: continue
        else: await websocket.send(json.dumps(message_object))

async def create_websocket_connection() -> None:
    uri = f"ws://{config['hostname']}:{config['port']}/ws"  
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        try:
            await asyncio.gather(listen_for_messages(websocket), send_messages(websocket))
        except websockets.exceptions.ConnectionClosedOK:
            print('-'*18)
            print("Connection closed.")
            print()
        except websockets.exceptions.ConnectionClosedError:
            print('-'*18)
            print("Connection closed.")
            print()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_websocket_connection())