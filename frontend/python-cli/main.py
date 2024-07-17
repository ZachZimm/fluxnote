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

def print_json_message(json_str):
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
    else:
        print(f"{dict_obj['mode']}: {dict_obj['message']}")
        return

async def listen_for_messages(websocket):
    while True:
        message = await websocket.recv()
        print_json_message(message)

async def send_messages(websocket):
    await asyncio.sleep(1)
    print("Enter a command: ")
    while True:
        message = await aioconsole.ainput()
        if message == "quit":
            await websocket.close()
            break
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
        message_object = {"func": "chat", "message": message}
        await websocket.send(json.dumps(message_object)) 

async def create_websocket_connection():
    uri = f"ws://{config['hostname']}:{config['port']}/ws"  
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")
        try:
            await asyncio.gather(listen_for_messages(websocket), send_messages(websocket))
        except websockets.exceptions.ConnectionClosedOK:
            print('-'*18)
            print("Connection closed.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_websocket_connection())