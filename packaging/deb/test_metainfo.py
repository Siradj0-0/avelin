"""Check the source metadata and its desktop entry agree."""
import configparser
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP_ID = "io.github.siradj00.avelin"


class MetainfoTests(unittest.TestCase):
    def setUp(self):
        self.metadata = ET.parse(HERE / f"{APP_ID}.metainfo.xml").getroot()
        self.desktop = configparser.ConfigParser(interpolation=None)
        self.desktop.read(HERE / f"{APP_ID}.desktop", encoding="utf-8")

    def test_required_application_fields_and_licenses(self):
        self.assertEqual(self.metadata.tag, "component")
        self.assertEqual(self.metadata.get("type"), "desktop-application")
        self.assertEqual(self.metadata.findtext("id"), APP_ID)
        self.assertEqual(self.metadata.findtext("metadata_license"), "MIT")
        self.assertEqual(self.metadata.findtext("project_license"), "MIT")
        self.assertEqual(self.metadata.findtext("name"), self.desktop["Desktop Entry"]["Name"])
        self.assertTrue(self.metadata.findtext("summary"))
        self.assertTrue(self.metadata.find("description/p").text.strip())

    def test_launchable_matches_desktop_and_icon(self):
        launchable = self.metadata.find("launchable")
        self.assertEqual(launchable.get("type"), "desktop-id")
        self.assertEqual(launchable.text, f"{APP_ID}.desktop")
        self.assertEqual(self.desktop["Desktop Entry"]["Icon"], APP_ID)
        self.assertEqual(self.desktop["Desktop Entry"]["Exec"], "avelin")


if __name__ == "__main__":
    unittest.main()
