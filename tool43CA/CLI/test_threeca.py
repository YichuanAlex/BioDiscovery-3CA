import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import threeca


HTML = """
<html><head><title>Lung | 3CA</title></head><body>
<div id="block-wis-theme-content"><h1>Lung</h1>
<table class="views-table"><tbody><tr>
<td headers="view-title-table-column"><a href="https://example.org/paper">Example et al. 2024</a></td>
<td headers="view-field-data-table-column"><a href="https://www.dropbox.com/scl/fi/a/Data_X.tar.gz?dl=1">Data</a></td>
<td headers="view-field-meta-data-table-column"><a href="https://www.dropbox.com/scl/fi/b/Meta_X.tar.gz?dl=1">Metadata</a></td>
<td headers="view-field-cell-types-table-column"><a href="study-data/cell-types/42">Cell types<span class="visually-hidden"> extra</span></a></td>
<td headers="view-field-disease-table-column">Disease X</td>
<td headers="view-field-technology-table-column">10x</td>
<td headers="view-field-samples-table-column">12</td><td headers="view-field-cells-table-column">34,567</td>
</tr></tbody></table></div></body></html>
"""


class ThreeCATest(unittest.TestCase):
    def test_parse_search_and_archive_safety(self):
        parser = threeca._PageParser(threeca.BASE_URL + "lung")
        parser.feed(HTML)
        page = parser.result()
        category = {"name": "Lung", "url": threeca.BASE_URL + "lung"}
        studies = threeca._study_rows(page, category)
        self.assertEqual(studies[0]["id"], "3ca:42")
        self.assertEqual(studies[0]["cells"], 34567)
        self.assertEqual(studies[0]["detail_pages"]["cell_types"], threeca.BASE_URL + "study-data/cell-types/42")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            threeca._write_json(root / "catalog.json", {"fetched_at": "now", "studies": studies})
            found = threeca.search_studies("example", technology="10x", cache=root)
            self.assertEqual(found["count"], 1)
            archive_path = root / "unsafe.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                data = b"bad"
                info = tarfile.TarInfo("../escape.txt")
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
            with self.assertRaises(threeca.ThreeCAError):
                threeca.inspect_dataset(archive_path)


if __name__ == "__main__":
    unittest.main()
