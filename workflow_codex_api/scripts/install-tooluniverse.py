#!/usr/bin/env python3
"""Safely unpack the vendored ToolUniverse MCPB into the workflow."""

import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


WORKFLOW_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = WORKFLOW_ROOT.parent
ARCHIVE = REPOSITORY_ROOT / "anthropics-life-sciences" / "tooluniverse" / "tooluniverse.mcpb"
DESTINATION = WORKFLOW_ROOT / "components" / "tooluniverse"
EXPECTED_SHA256 = "b8ab7b8a9475fed5362271f5c6b3dd1a04bc466840433d28876dd7bd02298f77"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    if not ARCHIVE.is_file():
        raise SystemExit(f"Missing vendored MCPB: {ARCHIVE}")
    actual_hash = digest(ARCHIVE)
    if actual_hash != EXPECTED_SHA256:
        raise SystemExit(f"Refusing changed MCPB: expected {EXPECTED_SHA256}, got {actual_hash}")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tooluniverse-", dir=DESTINATION.parent) as temporary:
        staging = Path(temporary)
        with zipfile.ZipFile(ARCHIVE) as bundle:
            for record in bundle.infolist():
                name = PurePosixPath(record.filename)
                if name.is_absolute() or ".." in name.parts or "\\" in record.filename:
                    raise SystemExit(f"Unsafe MCPB member: {record.filename}")
                # ZIP external attributes identify Unix symlinks with file type 0120000.
                if (record.external_attr >> 16) & 0o170000 == 0o120000:
                    raise SystemExit(f"Refusing MCPB symlink: {record.filename}")
                target = staging.joinpath(*name.parts)
                if record.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with bundle.open(record) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)

        manifest = json.loads((staging / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("name") != "tooluniverse" or manifest.get("version") != "1.0.15":
            raise SystemExit("Unexpected ToolUniverse bundle identity.")
        if manifest.get("server", {}).get("entry_point") != "src/run_stdio.py":
            raise SystemExit("Unexpected ToolUniverse MCP entry point.")

        pyproject_path = staging / "pyproject.toml"
        pyproject = pyproject_path.read_text(encoding="utf-8")
        broken_requirement = '    "fitz>=0.0.1.dev2",'
        if pyproject.count(broken_requirement) != 1:
            raise SystemExit("Expected the known MCPB fitz dependency exactly once.")
        pyproject_path.write_text(
            pyproject.replace(broken_requirement, '    "PyMuPDF>=1.24.0",'),
            encoding="utf-8",
        )

        install_record = {
            "schema_version": 1,
            "source": "anthropics-life-sciences/tooluniverse/tooluniverse.mcpb",
            "source_sha256": actual_hash,
            "bundle_version": manifest["version"],
            "mode": "local-stdio-compact",
            "authenticated_mcp_installed": False,
            "local_compatibility_patch": "replace unavailable fitz distribution with PyMuPDF provider",
            "schema_cache": "workflow-tool-schema.json",
            "schema_cache_generation": "post-install live stdio tools/list with SHA-256",
            "exposed_tools": [
                "tooluniverse__list_tools",
                "tooluniverse__grep_tools",
                "tooluniverse__get_tool_info",
                "tooluniverse__execute_tool",
                "tooluniverse__find_tools",
            ],
        }
        (staging / "workflow-install.json").write_text(
            json.dumps(install_record, indent=2) + "\n", encoding="utf-8"
        )
        backup = DESTINATION.with_name(f"{DESTINATION.name}.old")
        shutil.rmtree(backup, ignore_errors=True)
        if DESTINATION.exists():
            DESTINATION.rename(backup)
        try:
            staging.rename(DESTINATION)
        except BaseException:
            if backup.exists() and not DESTINATION.exists():
                backup.rename(DESTINATION)
            raise
        shutil.rmtree(backup, ignore_errors=True)

    print(f"Unpacked ToolUniverse {manifest['version']} into {DESTINATION}")


if __name__ == "__main__":
    sys.exit(main())
