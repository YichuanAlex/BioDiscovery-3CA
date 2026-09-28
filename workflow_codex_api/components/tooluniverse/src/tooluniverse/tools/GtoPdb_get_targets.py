"""
GtoPdb_get_targets

Get pharmacological targets from Guide to Pharmacology database
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def GtoPdb_get_targets(
    target_type: Optional[str] = "protein",
    limit: Optional[int] = 20,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> list[Any]:
    """
    Get pharmacological targets from Guide to Pharmacology database

    Parameters
    ----------
    target_type : str
        Target type
    limit : int
        Number of results
    stream_callback : Callable, optional
        Callback for streaming output
    use_cache : bool, default False
        Enable caching
    validate : bool, default True
        Validate parameters

    Returns
    -------
    list[Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "GtoPdb_get_targets",
            "arguments": {"target_type": target_type, "limit": limit},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["GtoPdb_get_targets"]
