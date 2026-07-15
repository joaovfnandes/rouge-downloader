import os
import tempfile
import unittest
from unittest.mock import patch

import app


class TagHistoryTest(unittest.TestCase):
    def test_saves_only_tags_counts_galleries_once_and_sorts_by_frequency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            history_file = os.path.join(temp_dir, "tag_history.json")
            with patch.object(app, "TAG_HISTORY_FILE", history_file):
                first = {
                    "tags": [
                        {"type": "tag", "name": "Feet"},
                        {"type": "tag", "name": "Group"},
                        {"type": "language", "name": "English"},
                    ]
                }
                second = {
                    "tags": [
                        {"type": "tag", "name": "feet"},
                        {"type": "tag", "name": "Catgirl"},
                    ]
                }

                self.assertTrue(app.record_gallery_tags(101, first))
                self.assertFalse(app.record_gallery_tags(101, first))
                self.assertTrue(app.record_gallery_tags(102, second))

                suggestions = app.get_tag_suggestions()
                self.assertEqual(suggestions[0]["name"], "feet")
                self.assertEqual(suggestions[0]["count"], 2)
                self.assertEqual({item["name"] for item in suggestions}, {"feet", "group", "catgirl"})
                self.assertEqual(app.get_gallery_tag_map()[101], ["feet", "group"])
                self.assertEqual(app.get_gallery_tag_map()[102], ["catgirl", "feet"])

                response = app.app.test_client().get("/")
                self.assertEqual(response.status_code, 200)
                self.assertIn('data-tag="feet"', response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
