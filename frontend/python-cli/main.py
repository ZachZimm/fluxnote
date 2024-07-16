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
    elif 'streaming' in dict_obj["mode"]:
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

async def websocket_client():
    uri = f"ws://{config['hostname']}:{config['port']}/ws"  # Adjust the URI as needed
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        
        while True:
            message = await websocket.recv()
            message_dict = json.loads(message)

            if ('streaming' not in message_dict["mode"]) or ('finished' in message_dict["mode"]):
                if 'finished' in message_dict["mode"]:
                    print()
                else: print_json_message(message)
                user_input = input("> ")
                await websocket.send(user_input)
                print()

            else:
                print_json_message(message)

asyncio.get_event_loop().run_until_complete(websocket_client())