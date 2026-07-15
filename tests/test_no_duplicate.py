import json
import os
import tempfile
import unittest
from unittest.mock import patch

import app as module


class DuplicateGalleryTest(unittest.TestCase):
    def test_existing_gallery_id_is_not_downloaded_again(self):
        original_out_dir = module.OUT_DIR
        try:
            with tempfile.TemporaryDirectory() as root:
                module.OUT_DIR = root
                old_folder = os.path.join(root, "101_Old_Title")
                os.makedirs(old_folder)
                with open(os.path.join(old_folder, "0001.jpg"), "wb") as handle:
                    handle.write(b"already-here")

                image_calls = []

                def fake_http(url, ua):
                    if "/galleries/" in url:
                        return json.dumps({"pages": [{"number": 1, "path": "1.jpg"}]}).encode()
                    image_calls.append(url)
                    return b"duplicate"

                result = {"id": 101, "media_id": 9, "english_title": "New Title"}
                with patch.object(module.scraper, "search", return_value=iter([result])), patch.object(
                    module.scraper, "http", side_effect=fake_http
                ):
                    module.run_scrape("test", 1, 0, 1, "ua")

                folders = [name for name in os.listdir(root) if os.path.isdir(os.path.join(root, name))]
                self.assertEqual(image_calls, [])
                self.assertEqual(folders, ["101_Old_Title"])
        finally:
            module.OUT_DIR = original_out_dir


if __name__ == "__main__":
    unittest.main()
