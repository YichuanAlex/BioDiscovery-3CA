"""
Reactome_get_pathway_reactions

Query all Reactions contained under a Pathway using Pathway Stable ID. This is currently the only...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def Reactome_get_pathway_reactions(
    stId: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Query all Reactions contained under a Pathway using Pathway Stable ID. This is currently the only...

    Parameters
    ----------
    stId : str
        Pathway Stable ID, e.g., 'R-HSA-73817' (verified valid).
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    Any
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {"name": "Reactome_get_pathway_reactions", "arguments": {"stId": stId}},
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["Reactome_get_pathway_reactions"]
