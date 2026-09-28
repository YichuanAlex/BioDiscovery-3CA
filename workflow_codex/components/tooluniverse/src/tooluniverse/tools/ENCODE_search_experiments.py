"""
ENCODE_search_experiments

Search ENCODE functional genomics experiments (e.g., ChIP-seq, ATAC-seq) by assay/target/organism...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ENCODE_search_experiments(
    assay_title: Optional[str] = None,
    target: Optional[str] = None,
    organism: Optional[str] = None,
    status: Optional[str] = "released",
    limit: Optional[int] = 10,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Search ENCODE functional genomics experiments (e.g., ChIP-seq, ATAC-seq) by assay/target/organism...

    Parameters
    ----------
    assay_title : str
        Assay name filter (e.g., 'ChIP-seq', 'ATAC-seq').
    target : str
        Target filter (e.g., 'CTCF').
    organism : str
        Organism filter (e.g., 'Homo sapiens', 'Mus musculus').
    status : str
        Record status filter (default 'released').
    limit : int
        Max number of results (1–100).
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    dict[str, Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "ENCODE_search_experiments",
            "arguments": {
                "assay_title": assay_title,
                "target": target,
                "organism": organism,
                "status": status,
                "limit": limit,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ENCODE_search_experiments"]
