"""
list_tools

Unified tool listing with multiple modes for different use cases. Supports listing tool names, ba...
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def list_tools(
    mode: str,
    categories: Optional[list[Any]] = None,
    fields: Optional[list[Any]] = None,
    group_by_category: Optional[bool] = False,
    brief: Optional[bool] = False,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Unified tool listing with multiple modes for different use cases. Supports listing tool names, ba...

    Parameters
    ----------
    mode : str
        Output mode: 'names' (tool names only), 'basic' (name+description), 'categori...
    categories : list[Any]
        Optional list of tool categories to filter by (applies to all modes except 'c...
    fields : list[Any]
        Required for mode='custom'. List of fields to include (e.g., ["name", "type",...
    group_by_category : bool
        Whether to group results by category (only for mode='names', 'basic', or 'sum...
    brief : bool
        Whether to truncate description to brief (only for mode='basic' or 'summary')
    limit : int
        Maximum number of tools to return (optional, for pagination)
    offset : int
        Number of tools to skip (optional, for pagination, default: 0)
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
            "name": "list_tools",
            "arguments": {
                "mode": mode,
                "categories": categories,
                "fields": fields,
                "group_by_category": group_by_category,
                "brief": brief,
                "limit": limit,
                "offset": offset,
            },
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["list_tools"]
