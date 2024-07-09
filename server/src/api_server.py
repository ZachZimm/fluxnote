from langchain_interface import langchain_interface

if __name__ == "__main__":
    langchain_i = langchain_interface()
    history = langchain_i.text_summary_loop()
    langchain_i.stream_langchain_chat_loop(history)