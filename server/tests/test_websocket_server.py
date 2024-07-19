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
    
    def tearDown(self) -> None:
        asyncio.get_event_loop().close()
    
    def run_async_test(self, test_function):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(test_function())
        loop.close()

    def test_get_configuration(self):
        # Define the asynchronous test function
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_get_configuration")
                data = websocket.receive_json() # Receive the welcome message
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "get_configuration"})
                data = websocket.receive_json() # Receive the configuration data
                self.assertEqual(data['mode'], "status")
                websocket.close() # Close the connection

        # Run the asynchronous test function
        self.run_async_test(async_test)

    def test_get_secret_configuration(self):
        # Define the asynchronous test function
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_get_secret_configuration")
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "get_secret_configuration"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status")
                websocket.close() 

        # Run the asynchronous test function
        self.run_async_test(async_test)

    def test_get_available_files_default_path(self):
        # Define the asynchronous test function
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_get_available_files_default_path")
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "list"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "status")
                self.assertIsInstance(data['message'], list) # Check if the message is a list
                websocket.close()

        # Run the asynchronous test function
        self.run_async_test(async_test) 

    def test_chat(self):
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_chat")
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "chat", "message": "Hello"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "chat streaming")
                self.assertIsInstance(data['message'], str)
                time_start = time.time()
                while True:
                    data = websocket.receive_json()
                    if data['mode'] == "chat streaming finished":
                        break
                    if time.time() - time_start > 45:
                        print("Chat took too long to complete")
                        self.fail("Chat took too long to complete")
                        break
                websocket.close()

        self.run_async_test(async_test)
    
    def test_get_and_clear_chat_history(self):
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_get_and_clear_chat_history")
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

        self.run_async_test(async_test)
        
    def test_summarize_text_default_path(self): # Unfortunatly, this is a long running test
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_summarize_text_default_path")
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

        self.run_async_test(async_test)

    def test_summarize_by_path(self): # Unfortunatly, this is a long running test
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_summarize_by_path")
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

        self.run_async_test(async_test)

    def test_wiki_search(self):
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_wiki_search")
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

        self.run_async_test(async_test)

    def test_wiki_results(self):
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_wiki_results")
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

        self.run_async_test(async_test)
    
    def test_wiki_get_page(self):
        async def async_test():
            with self.client.websocket_connect(self.websocket_url) as websocket:
                print("test_wiki_get_page")
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "welcome")
                websocket.send_json({"func": "wiki_search", "query": "Roman Republic"})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "wiki search results")
                wiki_page = json.loads(data['message'])
                self.assertIsInstance(wiki_page, list)
                self.assertTrue(len(wiki_page) > 0)
                websocket.send_json({"func": "wiki", "query": "1", "return_full": True, "should_save": False})
                data = websocket.receive_json()
                self.assertEqual(data['mode'], "wiki")
                data_json = data['message']
                self.assertIsInstance(data_json, dict)
                self.assertTrue('title' in data_json.keys()) # Check that all of the expected keys are present
                self.assertTrue('summary' in data_json.keys())
                self.assertTrue('content' in data_json.keys())
                # Check that the data conforms to our expectations
                self.assertTrue(len(data_json['title']) < len(data_json['summary']))
                self.assertTrue(len(data_json['summary']) < len(data_json['content']))
                websocket.close()

        self.run_async_test(async_test)

if __name__ == "__main__":
    unittest.main()