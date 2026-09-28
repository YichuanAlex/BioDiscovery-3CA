"""
ToolMetadataStandardizer

Standardizes and groups semantically equivalent metadata strings (e.g., sources, tags) into canon...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ToolMetadataStandardizer(
    metadata_list: list[Any],
    limit: Optional[int] = None,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> Any:
    """
    Standardizes and groups semantically equivalent metadata strings (e.g., sources, tags) into canon...

    Parameters
    ----------
    metadata_list : list[Any]
        List of raw metadata strings (e.g., sources, tags) to standardize and group.
    limit : int
        If provided, the maximum number of canonical strings to return. The LLM will ...
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
        {
            "name": "ToolMetadataStandardizer",
            "arguments": {"metadata_list": metadata_list, "limit": limit},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ToolMetadataStandardizer"]
