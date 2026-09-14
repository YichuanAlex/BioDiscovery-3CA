"""Exercise the workflow-produced archive guard without touching task data."""
import importlib.util
import io
import tarfile
import tempfile
from pathlib import Path

source = Path(r"C:\Users\User\Desktop\agentic\3CA\Q1\download_data.py")
spec = importlib.util.spec_from_file_location("q1_download", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix="q1-tar-audit-") as temporary:
    root = Path(temporary)
    for name, kind in (("../escape.txt", tarfile.REGTYPE), ("link", tarfile.SYMTYPE), ("device", tarfile.CHRTYPE)):
        archive = root / "malicious.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.linkname = "../escape.txt"
            stream.addfile(member)
        try:
            module.safe_extract_tar_gz(archive, root / "out")
        except tarfile.TarError:
            pass
        else:
            raise AssertionError("Archive guard accepted " + name)
    archive = root / "valid.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        member = tarfile.TarInfo("data.txt")
        member.size = 2
        stream.addfile(member, io.BytesIO(b"OK"))
    module.safe_extract_tar_gz(archive, root / "out")
    assert (root / "out/data.txt").read_text() == "OK"
print("PASS: traversal/link/device rejection and valid file extraction.")
