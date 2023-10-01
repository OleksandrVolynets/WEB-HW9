import json
import scrapy
from itemadapter import ItemAdapter
from scrapy.item import Item, Field
from scrapy.crawler import CrawlerProcess


class Quote(Item):
    author = Field()
    quote = Field()
    tags = Field()


class Author(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    bio = Field()


class SpiderPipline(object):
    quotes = list()
    authors = list()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'author' in adapter.keys():
            self.quotes.append({
                'author': adapter['author'],
                'quote': adapter['quote'],
                'tags': adapter['tags']
            })
        if 'fullname' in adapter.keys():
            self.authors.append({
                'fullname': adapter['fullname'],
                'born_date': adapter['born_date'],
                'born_location': adapter['born_location'],
                'bio': adapter['bio']
            })
        return item
    
    def close_spider(self, spider):
        with open('quotes.json', 'w', encoding='utf-8') as fd:
            json.dump(self.quotes, fd, ensure_ascii=False)

        with open('authors.json', 'w', encoding='utf-8') as fd:
            json.dump(self.authors, fd, ensure_ascii=False)


class Spider(scrapy.Spider):
    name = "my_spider"
    allowed_domains = ['quotes.toscrape.com'] 
    start_urls = ['http://quotes.toscrape.com/'] 
    custom_settings = {
        "ITEM_PIPELINES": {
            SpiderPipline: 300,            
        }
    }


    def parse(self, response):
        for q in response.xpath('/html//div[@class="quote"]'):
            quote = q.xpath('span[@class="text"]/text()').get().strip()
            author = q.xpath('span/small[@class="author"]/text()').get().strip()  # get if 1 value
            tags = q.xpath('div[@class="tags"]/a[@class="tag"]/text()').extract()  # extract if many values
            yield Quote(author=author, quote=quote, tags=tags)
            yield response.follow(url=self.start_urls[0] + q.xpath('span/a/@href').get(), callback=self.parse_author)  # переходить по посиланню та запускаэ додатковий парсер який прописаний у (callback)

        next_link = response.xpath('/html//li[@class="next"]/a/@href').get()  # next page
        
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    def parse_author(self, response):
        body = response.xpath('/html//div[@class="author-details"]')
        fullname = body.xpath('h3[@class="author-title"]/text()').get().strip()
        born_date = body.xpath('p/span[@class="author-born-date"]/text()').get().strip()
        born_location = body.xpath('p/span[@class="author-born-location"]/text()').get().strip()
        bio = body.xpath('div[@class="author-description"]/text()').get().strip()
        yield Author(fullname=fullname, born_date=born_date, born_location=born_location, bio=bio)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(Spider)
    process.start()