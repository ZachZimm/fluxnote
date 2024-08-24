from models.WikiData import WikiData
from mediawiki import MediaWiki, exceptions

class WikiInterface:
    wiki = None
    wiki_results = []
    # data: Wiki = None
    def __init__(self, wiki_url: str = ""):
        if wiki_url == "":
            self.wiki = MediaWiki()
        else:
            self.wiki = MediaWiki(wiki_url)

    def search(self, query: str) -> list[str]:
        return self.wiki.search(query)

    def get_data(self, query: str) -> WikiData:
        try:
            page = self.wiki.page(query)
            data: WikiData = WikiData(
                title=page.title + " wiki", # this naming scheme is going to need some thought
                summary=page.summary,
                content=page.content,
                links=page.links
            )
            return data
        except exceptions.DisambiguationError as e:
            return WikiData(
                title=e.title,
                summary="error: Disambiguation Error",
                content="error: Disambiguation Error",
                links=[]
            )
