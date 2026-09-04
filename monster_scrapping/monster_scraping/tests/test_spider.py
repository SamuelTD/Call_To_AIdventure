import unittest
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from monster_scraping.spiders.monster_scrapping_spider import MonsterSpider


class MonsterSpiderTests(unittest.TestCase):
    def test_fixture_is_parsed_without_network_access(self):
        fixture = Path(__file__).parent / "fixtures" / "monster.html"
        url = "https://www.aidedd.org/monster/fixture-goblin"
        response = HtmlResponse(
            url=url,
            request=Request(url=url),
            body=fixture.read_bytes(),
            encoding="utf-8",
        )
        item = dict(MonsterSpider().parse_monster(response))
        self.assertEqual(item["name"], "Fixture Goblin")
        self.assertEqual(item["armor"], "15")
        self.assertEqual(item["HP"], "22")
        self.assertEqual(item["challenge_rating"], "1/4")
        fields = (
            "strength", "dexterity", "constitution",
            "intelligence", "wisdom", "charisma",
        )
        self.assertEqual([item[field] for field in fields], ["+0", "+2", "+1", "-1", "+0", "-1"])


if __name__ == "__main__":
    unittest.main()
