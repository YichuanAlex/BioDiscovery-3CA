"""
ensembl_get_sequence

Get DNA sequence for a gene, transcript, or genomic region. Returns sequence in FASTA format.
"""

from typing import Any, Optional, Callable
from ._shared_client import get_shared_client


def ensembl_get_sequence(
    sequence_id: str,
    type: Optional[str] = "genomic",
    *,
    stream_callback: Optional[Callable[[str], None]] = None,
    use_cache: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    """
    Get DNA sequence for a gene, transcript, or genomic region. Returns sequence in FASTA format.

    Parameters
    ----------
    sequence_id : str
        Ensembl gene/transcript ID or genomic region (e.g., 'ENSG00000139618' or '1:1...
    type : str
        Sequence type: 'genomic', 'cds', 'cdna', 'peptide'
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
            "name": "ensembl_get_sequence",
            "arguments": {"sequence_id": sequence_id, "type": type},
        },
        stream_callback=stream_callback,
        use_cache=use_cache,
        validate=validate,
    )


__all__ = ["ensembl_get_sequence"]
