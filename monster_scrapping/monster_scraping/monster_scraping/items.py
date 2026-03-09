# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MonsterItem(scrapy.Item):
    
    name = scrapy.Field()
    armor = scrapy.Field()
    HP = scrapy.Field()
    strength = scrapy.Field()
    dexterity = scrapy.Field()
    constitution = scrapy.Field()
    intelligence = scrapy.Field()
    wisdom = scrapy.Field()
    charisma = scrapy.Field()
    challenge_rating = scrapy.Field()
