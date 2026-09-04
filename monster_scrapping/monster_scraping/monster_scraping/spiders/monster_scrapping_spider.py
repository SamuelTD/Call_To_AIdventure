import scrapy
from datetime import datetime, timezone
from monster_scraping.items import MonsterItem

class MonsterSpider(scrapy.Spider):
    
    """
    This is a scrapy spider designed to scrap monsters from the website aideddd.org
    """
    
    name = "monster_scraping_spider"
    allowed_domains = ["www.aidedd.org"]
    
    base_url = "https://www.aidedd.org/monster/"

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url or self.base_url]

    def parse(self, response):
        
        for link in response.css("td.item a::attr(href)").getall():
            yield response.follow(link, callback=self.parse_monster)

    @staticmethod
    def _text_after_label(response, label):
        value = response.xpath(
            f'//strong[normalize-space()="{label}"]/following-sibling::text()[1]'
        ).get()
        return value.strip() if value else None

    @staticmethod
    def _ability_modifiers(response):
        values = response.css("div.car3::text, div.car6::text").getall()
        modifiers = []
        for value in values:
            value = value.strip()
            if value.startswith(("+", "-")) and value[1:].isdigit():
                modifiers.append(value)
        return modifiers[:6]
        
    def parse_monster(self, response):
        
        item = MonsterItem()
        
        name = response.css("h1::text").get()
        item["source"] = "scraped_monsters"
        item["source_url"] = response.url
        item["source_record_id"] = (name or response.url).strip()
        item["collected_at"] = datetime.now(timezone.utc).isoformat()
        item["name"] = name.strip() if name else None
        armor = self._text_after_label(response, "AC")
        item["armor"] = armor.split()[0] if armor else None
        hp_text = self._text_after_label(response, "HP")
        item["HP"] = hp_text.split()[0] if hp_text else None
        modifiers = self._ability_modifiers(response)
        for index, field in enumerate(
            ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
        ):
            item[field] = modifiers[index] if index < len(modifiers) else None
        challenge = self._text_after_label(response, "CR")
        item["challenge_rating"] = challenge.split()[0] if challenge else None

        return item
