from wiki_interface import WikiInterface

if __name__ == "__main__":
    wiki = WikiInterface()
    query = input("Enter a search term: ")
    query_results = wiki.search(query)
    max_results = 10
    print(f'First {max_results} search results:')
    for i, result in enumerate(wiki.search(query)):
        if i >= max_results:
            break
        print(f"{i + 1}. {result}") # Print the first 10 search results
    p_query = input("Enter a result number: ")
    print('user query:  ', )
    data = wiki.get_data(query_results[int(p_query) - 1])
    print("\nContent:")
    print(data.content)
    print(len(data.content), 'characters')
