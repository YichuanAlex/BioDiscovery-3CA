"""
gnomad_get_gene_constraints

Get gene constraint metrics from gnomAD. Returns pLI, LOEUF, and other constraint scores for genes.
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def gnomad_get_gene_constraints(
    gene_symbol: str,
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Get gene constraint metrics from gnomAD. Returns pLI, LOEUF, and other constraint scores for genes.

    Parameters
    ----------
    gene_symbol : str
        Gene symbol (e.g., 'BRCA1', 'TP53')
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
            "name": "gnomad_get_gene_constraints",
            "arguments": {"gene_symbol": gene_symbol},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["gnomad_get_gene_constraints"]
