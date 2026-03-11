import scrapy
from monster_scraping.items import MonsterItem

class AllocineSpider(scrapy.Spider):
    
    """
    This is a scrapy spider designed to scrap monsters from the website aideddd.org
    """
    
    name = "monster_scraping_spider"
    allowed_domains = ["www.aidedd.org"]
    
    start_urls = ["https://www.aidedd.org/monster/"]
    
    base_url = "https://www.aidedd.org/monster/"

    def parse(self, response):
        
        for link in response.css("td.item a::attr(href)").getall():
            yield response.follow(f"https://www.aidedd.org/monster/{link}", callback=self.parse_monster)
        
    def parse_monster(self, response):
        
        item = MonsterItem()
        
        item["name"] = response.css("h1::text").get()
        item["armor"] = response.xpath('//strong[normalize-space()="AC"]/following-sibling::text()[1]').get().strip()
        
        hp_text = response.xpath('//strong[normalize-space()="HP"]/following-sibling::text()[1]').get()
        item["HP"] = hp_text and hp_text.strip().split()[0]  
        item["strength"] = response.css("div.car3::text").getall()[0].lstrip("+-")
        item["dexterity"] = response.css("div.car3::text").getall()[2].lstrip("+-")
        item["constitution"] = response.css("div.car3::text").getall()[4].lstrip("+-")
        item["intelligence"] = response.css("div.car6::text").getall()[4].lstrip("+-")
        item["wisdom"] = response.css("div.car6::text").getall()[4].lstrip("+-")
        item["charisma"] = response.css("div.car6::text").getall()[4].lstrip("+-")
        item["challenge_rating"] = response.xpath('//strong[normalize-space()="CR"]/following-sibling::text()[1]').get().strip().split()[0]        
        
        return item
        