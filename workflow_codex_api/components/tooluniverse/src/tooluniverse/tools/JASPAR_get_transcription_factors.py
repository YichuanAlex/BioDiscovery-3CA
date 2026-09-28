"""
JASPAR_get_transcription_factors

Get transcription factor binding site matrices from JASPAR
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def JASPAR_get_transcription_factors(
    collection: Optional[str] = "CORE",
    limit: Optional[int] = 20,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Get transcription factor binding site matrices from JASPAR

    Parameters
    ----------
    collection : str
        JASPAR collection
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
    dict[str, Any]
    """
    # Handle mutable defaults to avoid B006 linting error

    return get_shared_client().run_one_function(
        {
            "name": "JASPAR_get_transcription_factors",
            "arguments": {"collection": collection, "limit": limit},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["JASPAR_get_transcription_factors"]
