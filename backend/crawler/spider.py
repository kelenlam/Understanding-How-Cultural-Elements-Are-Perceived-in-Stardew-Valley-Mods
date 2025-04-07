# backend/crawler/spider.py
import asyncio
import logging
from typing import List
from nexus_spider import NexusSpider
from modDrop_spider import ModDropSpider
from curseForge_spider import CurseForgeSpider
from reddit_spider import RedditSpider

# Set logging level for Selenium
selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
selenium_logger.setLevel(logging.WARNING)


class WebCrawler:
    def __init__(self):
        pass

    async def crawl(self, query: str, max_mod: int, max_cm: int, crawled_mods:set) -> List[dict]:
        self.spiders = [
            NexusSpider(),
            ModDropSpider(),
            CurseForgeSpider(),
            RedditSpider()
        ]
        loop = asyncio.get_event_loop() # Get the current event loop for managing asynchronous tasks in this application
        tasks = []

        # Create a list of tasks for each spider to crawl the query
        for spider in self.spiders:
            task = loop.run_in_executor(None, spider.crawl, query,max_mod,max_cm,crawled_mods)
            tasks.append(task)

        results = await asyncio.gather(*tasks) # Gather the results from all tasks
        # Close all spiders after crawling
        for spider in self.spiders:
            spider.close()
        
        # Convert results to a list of dictionaries
        converted_results = []
        for result in results:
            if result is None:
                converted_results.append([])
            elif isinstance(result, list):
                converted_results.append([item for item in result if isinstance(item, dict)])
            else:
                if isinstance(result, dict):
                    converted_results.append([result])
                else:
                    converted_results.append([])

        # Flatten the list of lists into a single list
        flattened_results = [item for sublist in converted_results for item in sublist]

        return flattened_results