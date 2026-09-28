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
    def test_migrated_partial_extraction_is_preserved_and_rebuilt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "data.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                contents = b"matrix contents"
                info = tarfile.TarInfo("counts.mtx")
                info.size = len(contents)
                archive.addfile(info, io.BytesIO(contents))
            partial = root / "data.extracted"
            partial.mkdir()
            (partial / "old.txt").write_text("preserve")
            result = threeca.extract_archive(archive_path)
            rebuilt = Path(result["path"])
            self.assertNotEqual(rebuilt, partial)
            self.assertEqual((partial / "old.txt").read_text(), "preserve")
            self.assertEqual((rebuilt / "counts.mtx").read_bytes(), contents)
            self.assertTrue((rebuilt / ".threeca-extraction.json").is_file())

    def test_parse_search_and_archive_safety(self):
        self.assertEqual(threeca.DEFAULT_MAX_BYTES, 0)
        self.assertEqual(threeca.DEFAULT_MAX_EXTRACT_BYTES, 0)
        self.assertEqual(threeca._parser().parse_args(["crawl"]).max_pages, 0)
        self.assertEqual(threeca.publication_doi_candidate("https://www.nature.com/articles/s41588-022-01061-8"), "10.1038/s41588-022-01061-8")
        self.assertEqual(threeca.publication_doi_candidate("https://doi.org/10.1038/s41586-020-2649-2"), "10.1038/s41586-020-2649-2")
        self.assertIsNone(threeca.publication_doi_candidate("https://example.org/no-doi"))
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
            self.assertEqual(threeca.get_study("3ca:42", root)["publication_verification_call"]["arguments"], {"doi": "3ca:42"})
            (root / "actual.csv").write_text("cell,value\nc1,2\n", encoding="utf-8")
            (root / "subdirectory").mkdir()
            listing = threeca.inspect_dataset(root)
            self.assertEqual(listing["format"], "directory")
            self.assertIn({"name": "actual.csv", "type": "file"}, listing["entries"])
            self.assertIn({"name": "subdirectory", "type": "directory"}, listing["entries"])
            self.assertEqual(listing["previews"], [])
            self.assertTrue(threeca.inspect_dataset(root, max_members=1)["entries_truncated"])
            self.assertEqual(threeca.inspect_dataset(root / "actual.csv")["previews"][0]["columns"], ["cell", "value"])
            with self.assertRaises(threeca.ThreeCAError):
                threeca.inspect_dataset(root / "invented.csv")
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
