import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("OpenAlexTool")
class OpenAlexTool(BaseTool):
    """
    Tool to retrieve literature from OpenAlex based on search keywords.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.base_url = "https://api.openalex.org/works"

    def run(self, arguments):
        """Main entry point for the tool."""
        search_keywords = arguments.get("search_keywords")
        max_results = arguments.get("max_results", 10)
        year_from = arguments.get("year_from", None)
        year_to = arguments.get("year_to", None)
        open_access = arguments.get("open_access", None)

        return self.search_literature(
            search_keywords, max_results, year_from, year_to, open_access
        )

    def search_literature(
        self,
        search_keywords,
        max_results=10,
        year_from=None,
        year_to=None,
        open_access=None,
    ):
        """
        Search for literature using OpenAlex API.

        Parameters
            search_keywords (str): Keywords to search for in title, abstract, and content.
            max_results (int): Maximum number of results to return (default: 10).
            year_from (int): Start year for publication date filter (optional).
            year_to (int): End year for publication date filter (optional).
            open_access (bool): Filter for open access papers only (optional).

        Returns
            list: List of dictionaries containing paper information.
        """
        # Build query parameters
        params = {
            "search": search_keywords,
            "per-page": min(max_results, 200),  # OpenAlex allows max 200 per page
            "sort": "cited_by_count:desc",  # Sort by citation count (most cited first)
            "mailto": "support@openalex.org",  # Polite pool access
        }

        # Add year filters if provided
        filters = []
        if year_from is not None and year_to is not None:
            filters.append(f"publication_year:{year_from}-{year_to}")
        elif year_from is not None:
            filters.append(f"from_publication_date:{year_from}-01-01")
        elif year_to is not None:
            filters.append(f"to_publication_date:{year_to}-12-31")

        # Add open access filter if specified
        if open_access is True:
            filters.append("is_oa:true")
        elif open_access is False:
            filters.append("is_oa:false")

        if filters:
            params["filter"] = ",".join(filters)

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for work in data.get("results", []):
                try:
                    paper_info = self._extract_paper_info(work)
                    papers.append(paper_info)
                except Exception:
                    # Skip papers with missing data rather than failing completely
                    continue

            print(
                f"[OpenAlex] Retrieved {len(papers)} papers for keywords: '{search_keywords}'"
            )
            return papers

        except requests.exceptions.RequestException as e:
            return f"Error retrieving data from OpenAlex: {e}"

    def _extract_paper_info(self, work):
        """
        Extract relevant information from a work object returned by OpenAlex API.

        Parameters
            work (dict): Work object from OpenAlex API response.

        Returns
            dict: Formatted paper information.
        """
        # Extract title
        title = work.get("title", "No title available")

        # Extract abstract (display_name from abstract_inverted_index if available)
        abstract = None
        if work.get("abstract_inverted_index"):
            # Reconstruct abstract from inverted index
            abstract_dict = work["abstract_inverted_index"]
            abstract_words = [""] * 500  # Assume max 500 words
            for word, positions in abstract_dict.items():
                for pos in positions:
                    if pos < len(abstract_words):
                        abstract_words[pos] = word
            abstract = " ".join([word for word in abstract_words if word]).strip()

        if not abstract:
            abstract = "Abstract not available"

        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            author_name = author.get("display_name", "Unknown Author")
            authors.append(author_name)

        # Extract publication year
        publication_year = work.get("publication_year", "Year not available")

        # Extract organizations/affiliations
        organizations = set()
        for authorship in work.get("authorships", []):
            for institution in authorship.get("institutions", []):
                org_name = institution.get("display_name")
                if org_name:
                    organizations.add(org_name)

        # Extract additional useful information
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        venue = source.get("display_name", "Unknown venue")
        doi = work.get("doi", "No DOI")
        citation_count = work.get("cited_by_count", 0)
        open_access_info = work.get("open_access") or {}
        open_access = open_access_info.get("is_oa", False)
        pdf_url = open_access_info.get("oa_url")

        # Extract keywords/concepts
        keywords = []
        concepts = work.get("concepts", [])
        if isinstance(concepts, list):
            for concept in concepts:
                if isinstance(concept, dict):
                    concept_name = concept.get("display_name", "")
                    if concept_name:
                        keywords.append(concept_name)

        # Extract article type
        article_type = work.get("type", "Unknown")

        # Extract publisher
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        publisher = source.get("publisher", "Unknown")

        return {
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": publication_year,
            "organizations": list(organizations),
            "venue": venue,
            "doi": doi,
            "citation_count": citation_count,
            "open_access": open_access,
            "pdf_url": pdf_url,
            "keywords": keywords if keywords else "Keywords not available",
            "article_type": article_type,
            "publisher": publisher,
            "openalex_id": work.get("id", ""),
            "url": work.get("doi") if work.get("doi") else work.get("id", ""),
            "data_quality": {
                "has_abstract": bool(abstract and abstract != "Abstract not available"),
                "has_authors": bool(authors),
                "has_venue": bool(venue and venue != "Unknown venue"),
                "has_year": bool(
                    publication_year and publication_year != "Year not available"
                ),
                "has_doi": bool(doi and doi != "No DOI"),
                "has_citation_count": bool(citation_count and citation_count > 0),
                "has_keywords": bool(keywords),
            },
        }

    def get_paper_by_doi(self, doi):
        """
        Retrieve a specific paper by its DOI.

        Parameters
            doi (str): DOI of the paper to retrieve.

        Returns
            dict: Paper information or None if not found.
        """
        try:
            # OpenAlex supports DOI lookup directly
            url = f"https://api.openalex.org/works/https://doi.org/{doi}"
            params = {"mailto": "support@openalex.org"}

            response = requests.get(url, params=params)
            response.raise_for_status()
            work = response.json()

            return self._extract_paper_info(work)

        except requests.exceptions.RequestException as e:
            print(f"Error retrieving paper by DOI {doi}: {e}")
            return None

    def get_papers_by_author(self, author_name, max_results=10):
        """
        Retrieve papers by a specific author.

        Parameters
            author_name (str): Name of the author to search for.
            max_results (int): Maximum number of results to return.

        Returns
            list: List of papers by the author.
        """
        try:
            params = {
                "filter": f"author.display_name.search:{author_name}",
                "per-page": min(max_results, 200),
                "sort": "cited_by_count:desc",
                "mailto": "support@openalex.org",
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            papers = []
            for work in data.get("results", []):
                paper_info = self._extract_paper_info(work)
                papers.append(paper_info)

            print(
                f"[OpenAlex] Retrieved {len(papers)} papers by author: '{author_name}'"
            )
            return papers

        except requests.exceptions.RequestException as e:
            return f"Error retrieving papers by author {author_name}: {e}"
