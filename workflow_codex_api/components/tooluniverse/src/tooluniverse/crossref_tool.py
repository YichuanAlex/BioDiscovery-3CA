import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("CrossrefTool")
class CrossrefTool(BaseTool):
    """
    Search Crossref Works API for articles by keyword.
    """

    def __init__(
        self,
        tool_config,
        base_url="https://api.crossref.org/works",
    ):
        super().__init__(tool_config)
        self.base_url = base_url

    def run(self, arguments):
        query = arguments.get("query")
        rows = int(arguments.get("limit", 10))
        # e.g., 'type:journal-article,from-pub-date:2020-01-01'
        filter_str = arguments.get("filter")
        if not query:
            return {"error": "`query` parameter is required."}
        return self._search(query, rows, filter_str)

    def _search(self, query, rows, filter_str):
        params = {"query": query, "rows": max(1, min(rows, 100))}
        if filter_str:
            params["filter"] = filter_str

        try:
            response = requests.get(self.base_url, params=params, timeout=20)
        except requests.RequestException as e:
            return {
                "error": "Network error calling Crossref API",
                "reason": str(e),
            }

        if response.status_code != 200:
            return {
                "error": f"Crossref API error {response.status_code}",
                "reason": response.reason,
            }

        data = response.json().get("message", {}).get("items", [])
        results = []
        for item in data:
            # Extract title
            title_list = item.get("title") or []
            title = title_list[0] if title_list else None

            # Extract abstract
            abstract = item.get("abstract")
            if abstract and isinstance(abstract, str):
                # Clean HTML tags
                import re

                abstract = re.sub(r"<[^>]+>", "", abstract)
                abstract = abstract.strip()

            # Extract author information
            authors = []
            author_list = item.get("author", [])
            if isinstance(author_list, list):
                for author in author_list:
                    if isinstance(author, dict):
                        given = author.get("given", "")
                        family = author.get("family", "")
                        if given and family:
                            authors.append(f"{given} {family}")
                        elif family:
                            authors.append(family)

            # Extract year
            year = None
            issued = item.get("issued", {}).get("date-parts") or []
            if issued and issued[0]:
                year = issued[0][0]

            # Extract URL and DOI
            url = item.get("URL")
            doi = item.get("DOI")

            # Extract journal information
            container_title = item.get("container-title") or []
            journal = container_title[0] if container_title else None

            # Extract citation count
            citations = item.get("is-referenced-by-count", 0)
            if citations:
                try:
                    citations = int(citations)
                except (ValueError, TypeError):
                    citations = 0

            # Extract open access status
            open_access = item.get(
                "is-referenced-by-count", 0
            )  # This field might not be accurate
            # Try to get open access status from license information
            license_info = item.get("license", [])
            if isinstance(license_info, list) and license_info:
                open_access = (
                    True  # If there's license information, it might be open access
                )

            # Extract keywords
            keywords = []
            subject_list = item.get("subject", [])
            if isinstance(subject_list, list):
                keywords.extend(subject_list)

            # Extract article type
            article_type = item.get("type", "Unknown")

            # Extract publisher
            publisher = item.get("publisher", "Unknown")

            # Handle missing abstract
            if not abstract:
                abstract = "Abstract not available"

            results.append(
                {
                    "title": title or "Title not available",
                    "abstract": abstract,
                    "authors": (
                        authors if authors else "Author information not available"
                    ),
                    "journal": journal or "Journal information not available",
                    "year": year,
                    "doi": doi or "DOI not available",
                    "url": url or "URL not available",
                    "citations": citations,
                    "open_access": open_access,
                    "keywords": keywords if keywords else "Keywords not available",
                    "article_type": article_type,
                    "publisher": publisher,
                    "source": "Crossref",
                    "data_quality": {
                        "has_abstract": bool(
                            abstract and abstract != "Abstract not available"
                        ),
                        "has_authors": bool(authors),
                        "has_journal": bool(journal),
                        "has_year": bool(year),
                        "has_doi": bool(doi),
                        "has_citations": bool(citations and citations > 0),
                        "has_keywords": bool(keywords),
                        "has_url": bool(url),
                    },
                }
            )

        return results
