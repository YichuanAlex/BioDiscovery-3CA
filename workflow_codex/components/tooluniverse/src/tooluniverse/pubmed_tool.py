import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("PubMedTool")
class PubMedTool(BaseTool):
    """
    Search PubMed using NCBI E-utilities (esearch + esummary) and return
    articles.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.esummary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        )

    def run(self, arguments):
        query = arguments.get("query")
        limit = int(arguments.get("limit", 10))
        api_key = arguments.get("api_key")  # optional NCBI API key
        if not query:
            return {"error": "`query` parameter is required."}
        return self._search(query, limit, api_key)

    def _search(self, query, limit, api_key=None):
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max(1, min(limit, 200)),
            "retmode": "json",
        }
        if api_key:
            params["api_key"] = api_key

        try:
            r = requests.get(self.esearch_url, params=params, timeout=20)
        except requests.RequestException as e:
            return {
                "error": "Network error calling PubMed esearch",
                "reason": str(e),
            }
        if r.status_code != 200:
            return {
                "error": f"PubMed esearch error {r.status_code}",
                "reason": r.reason,
            }

        data = r.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
        }
        if api_key:
            summary_params["api_key"] = api_key

        try:
            s = requests.get(
                self.esummary_url,
                params=summary_params,
                timeout=20,
            )
        except requests.RequestException as e:
            return {
                "error": "Network error calling PubMed esummary",
                "reason": str(e),
            }
        if s.status_code != 200:
            return {
                "error": f"PubMed esummary error {s.status_code}",
                "reason": s.reason,
            }

        result = s.json().get("result", {})
        uids = result.get("uids", [])
        articles = []
        for uid in uids:
            rec = result.get(uid, {})
            title = rec.get("title")
            journal = rec.get("fulljournalname") or rec.get("source")

            # Extract author information
            authors = []
            author_list = rec.get("authors", [])
            if isinstance(author_list, list):
                for author in author_list:
                    if isinstance(author, dict):
                        name = author.get("name", "")
                        if name:
                            authors.append(name)

            # Extract year
            year = None
            pubdate = rec.get("pubdate")
            if pubdate and len(pubdate) >= 4 and pubdate[:4].isdigit():
                year = int(pubdate[:4])

            # Extract DOI
            doi = None
            for id_obj in rec.get("articleids", []):
                if id_obj.get("idtype") == "doi":
                    doi = id_obj.get("value")
                    break

            # Extract citation count (PubMed doesn't provide this directly)
            citations = 0
            # PubMed API itself doesn't provide citation count, keeping it as 0

            # Extract open access status
            open_access = False
            # PubMed API itself doesn't directly provide open access status

            # Extract keywords
            keywords = []
            mesh_terms = rec.get("meshterms", [])
            if isinstance(mesh_terms, list):
                for term in mesh_terms:
                    if isinstance(term, dict):
                        keyword = term.get("term", "")
                        if keyword:
                            keywords.append(keyword)

            # Extract article type
            article_type = rec.get("pubtype", [])
            if isinstance(article_type, list) and article_type:
                article_type = (
                    article_type[0]
                    if isinstance(article_type[0], str)
                    else str(article_type[0])
                )
            else:
                article_type = "Unknown"

            # Build URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"

            articles.append(
                {
                    "title": title or "Title not available",
                    "abstract": "Abstract not available",  # PubMed API itself doesn't provide abstracts
                    "authors": (
                        authors if authors else "Author information not available"
                    ),
                    "journal": journal or "Journal information not available",
                    "year": year,
                    "doi": doi or "DOI not available",
                    "url": url,
                    "citations": citations,
                    "open_access": open_access,
                    "keywords": keywords if keywords else "Keywords not available",
                    "article_type": article_type,
                    "source": "PubMed",
                    "data_quality": {
                        "has_abstract": False,  # PubMed API itself doesn't provide abstracts
                        "has_authors": bool(authors),
                        "has_journal": bool(journal),
                        "has_year": bool(year),
                        "has_doi": bool(doi),
                        "has_citations": False,  # PubMed API itself doesn't provide citation count
                        "has_keywords": bool(keywords),
                        "has_url": bool(url),
                    },
                }
            )

        return articles
