# Monster extraction

This isolated Scrapy project extracts monster statistics into the raw source
used by the Block 1 data pipeline. The main pipeline can always be demonstrated
with the committed source snapshot and HTML fixture; a live crawl is optional.

Run the offline parser test from the repository root:

```bash
cd monster_scrapping/monster_scraping
../.venv/bin/python -m unittest discover -s tests -v
```

Before a live crawl, verify the website terms, data licence, and robots policy.
The spider obeys `robots.txt`, identifies itself, limits concurrency, waits
between requests, retries transient failures, and uses a 20-second timeout.

To produce deterministic JSON Lines output:

```bash
cd monster_scrapping/monster_scraping
../.venv/bin/scrapy crawl monster_scraping_spider \
  -O ../../staging/scraped-monsters.jsonl:jsonlines
```

Do not make a certification demonstration depend on live website availability.
