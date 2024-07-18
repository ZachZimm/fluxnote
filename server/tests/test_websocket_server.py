import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch, MagicMock
import time
import json
import asyncio
from fastapi.testclient import TestClient
from api_server import app

class TestWebSocketServer(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.websocket_url = "/ws"

    def test_get_configuration(self):
        # Create an event loop for the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Define the asynchronous test function
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json() # Receive the welcome message
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "get_configuration"})
                data = websocket.receive_json() # Receive the configuration data
                self.assertEqual(data['mode'], "status")
                websocket.close() # Close the connection

        # Run the asynchronous test function
        loop.run_until_complete(async_test())
        loop.close()

    def test_get_secret_configuration(self):
        # Create an event loop for the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Define the asynchronous test function
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "get_secret_configuration"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status")
                websocket.close() 

        # Run the asynchronous test function
        loop.run_until_complete(async_test())
        loop.close()

    def test_get_available_files_default_path(self):
        # Create an event loop for the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Define the asynchronous test function
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "list"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status")
                self.assertIsInstance(data['message'], list) # Check if the message is a list
                websocket.close()

        # Run the asynchronous test function
        loop.run_until_complete(async_test())
        loop.close()
    
    def test_chat(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "chat", "message": "Hello"})
                for i in range(5): # Make sure there are a few messages
                    data = websocket.receive_json()
                    self.assertEqual(data['mode'], "chat streaming")
                    self.assertIsInstance(data['message'], str)
                websocket.close()

        loop.run_until_complete(async_test())
        loop.close()
    
    def test_get_and_clear_chat_history(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "chat", "message": "Hello"}) # Send a chat message
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "chat streaming") # Check for the 'chat streaming' confirmation
                time_start = time.time()
                streaming = True
                while streaming: # Wait for the chat message to complete
                    data = websocket.receive_json()
                    finished: bool = data['mode'] == "chat streaming finished"
                    if finished:
                        streaming = False
                    if time.time() - time_start > 45:
                        print("Chat history took too long to return")
                        self.fail("Chat history took too long to return")
                        streaming = False
                websocket.send_json({"func": "chat_history"}) # Request the chat history
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status")
                data_json = json.loads(data['message'])
                self.assertIsInstance(data_json, list)
                self.assertTrue(len(data['message']) > 0) # Check that the chat history is not empty

                websocket.send_json({"func": "clear_history"}) # Clear the chat history
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status") # Check for the 'history cleared' confirmation
                websocket.send_json({"func": "chat_history"}) # Request the chat history again
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status") # Check for the 'status' confirmation
                data_json = json.loads(data['message'])
                self.assertIsInstance(data_json, list) # Check that the message is a list
                self.assertTrue(len(data_json) == 0) # Check that the chat history is empty
                websocket.close()


        loop.run_until_complete(async_test())
        loop.close()

    def test_summarize_text_default_path(self): # Unfortunatly, this is a long running test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "summarize", "file_index": "1"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status") # Check for the 'summarizing' conffirmation
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "summary")
                summary_dict = json.loads(data['message'])
                self.assertIsInstance(summary_dict, dict)
                websocket.close()

        loop.run_until_complete(async_test())
        loop.close()

    def test_summarize_string(self): # Unfortunatly, this is a long running test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "summarize", "file_path": "sample_data/juluiscaesar.txt"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status") # Check for the 'summarizing' conffirmation
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "summary")
                summary_dict = json.loads(data['message'])
                self.assertIsInstance(summary_dict, dict)
                websocket.close()

        loop.run_until_complete(async_test())
        loop.close()
    
    def test_wiki_search(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "wiki_search", "query": "Roman Republic"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "wiki search results")
                wiki_results = json.loads(data['message'])
                self.assertIsInstance(wiki_results, list)
                # assert that list is not empty
                self.assertTrue(len(wiki_results) > 0)
                websocket.close()

        loop.run_until_complete(async_test())
        loop.close()
    
    def test_wiki_results(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "wiki_search", "query": "Roman Republic"})
                data = websocket.receive_json()
                websocket.send_json({"func": "wiki_results"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "wiki search results")
                wiki_results = json.loads(data['message'])
                self.assertIsInstance(wiki_results, list)
                websocket.close()

        loop.run_until_complete(async_test())
        loop.close()


if __name__ == "__main__":
    unittest.main()