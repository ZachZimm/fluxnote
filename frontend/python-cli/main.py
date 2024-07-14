import asyncio
import websockets
import json

config_dir = "config.json"
config = json.load(open(config_dir))

def print_summary(summary):
    i = 0
    num_ideas = len(summary)
    print(f"Summary has {num_ideas} ideas.")

    for idea in range(num_ideas):
        print(f"{idea}: {summary[idea]['idea']}")
        i += 1

def print_json_message(json_str):
    dict_obj = json.loads(json_str)
    if dict_obj["mode"] == "chat":
        print(f"Chat: {dict_obj['message']}")
        return
    elif dict_obj["mode"] == "chat_streaming":
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
    else:
        print(f"{dict_obj['mode']}: {dict_obj['message']}")
        return
    # for key in dict_obj.keys():
    #     if dict_obj[key] == "summary":
    #         print(f"{type(dict_obj[key])}: key")
    #     if key == "message":
    #         print(f"{key}: {dict_obj[key]}")
    #     else:
    #         print(f"{key}: {dict_obj[key]}")

async def websocket_client():
    uri = f"ws://{config['hostname']}:{config['port']}/ws"  # Adjust the URI as needed
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        
        while True:
            message = await websocket.recv()
            print_json_message(message)
            message_dict = json.loads(message)
            if message_dict["mode"] == "summary":
                print("summary mode")
                user_input = input("Enter your command: ")
                await websocket.send(user_input)
                continue

            
            if "Enter 'options' to see available text files to summarize or 'exit' to quit." in message:
                user_input = input("Enter your command: ")
                await websocket.send(user_input)
            elif "Provide the number corresponding with text file you would like to summarize:" in message:
                user_input = input("Enter the file number: ")
                await websocket.send(user_input)
            elif "Chat:" in message:
                while True:
                    user_input = input("> ")
                    await websocket.send(user_input)
                    while True:
                        message = await websocket.recv()
                        if "<stream_finished>" in message:
                            break
                        print_json_message(message)
                    if user_input == "exit":
                        break
                    print("\n")
            elif "Enter a search term:" in message:
                user_input = input("Enter search term: ")
                await websocket.send(user_input)
            elif "Enter a number corresponding to a search result:" in message:
                user_input = input("Enter result number: ")
                await websocket.send(user_input)
            elif "Enter the name of a wikipedia page:" in message:
                user_input = input("Enter page name: ")
                await websocket.send(user_input)
            elif "Download content? (y/n)" in message:
                user_input = input("Download content? (y/n): ")
                await websocket.send(user_input)
            elif "History cleared." in message:
                user_input = input("Enter your command: ")
                await websocket.send(user_input)
            elif "Invalid input." in message:
                user_input = input("Enter your command: ")
                await websocket.send(user_input)

asyncio.get_event_loop().run_until_complete(websocket_client())