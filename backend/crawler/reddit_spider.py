from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.selector import Selector
from base_spider import BaseSpider

class RedditSpider(BaseSpider):
    name = "reddit"


    def crawl(self, search_query, max_mod, max_cm, crawled_mods):
        results = []
        url = 'https://www.reddit.com/r/StardewValley/search/?q=mod+'
        self.driver.get(url + "+".join(search_query.split())) # Search for the query

        mod_links = []
        try: # Wait for the page to load
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-testid="post-title"]')))
        except Exception as e:
            print(e)
            return
        # Get the mod links from the page
        sel = Selector(text=self.driver.page_source)
        mod_links = sel.css('a[data-testid="post-title"]::attr(href)').getall()

        crawled_no=0 # Number of mods crawled
        link_index = 0 # Index of the mod link to crawl
        while link_index < len(mod_links) and crawled_no < max_mod:    
            result =  self.parse_mod_page(mod_links[link_index],max_cm,crawled_mods)
            # Check if the result is valid 
            if result:
                results.append(result)
                crawled_mods.add(result["Mod title"])
                crawled_no += 1 
            link_index +=1
        return results

    def parse_mod_page(self, link, max_cm, crawled_mods):
        post_tab_url = "https://www.reddit.com" + link
        comments = []
        if "faqs" in post_tab_url:
            return  # Skip the FAQs page
        self.driver.get(post_tab_url)

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[slot='title']")))
        mod_name = self.driver.find_element(By.CSS_SELECTOR, "h1[slot='title']").text
        if mod_name in crawled_mods:
            return # Skip if the mod name is already crawled

        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#empty-comments-banner")))
            content = self.driver.find_element(By.CSS_SELECTOR, "#empty-comments-banner")
            if content.text in "Be the first to comment":
                return # Skip if there are no comments
        except:
            print("This mod has comments. Continuing to scrape comments.")

        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".text-neutral-content")))
            text_body = self.driver.find_element(By.CSS_SELECTOR, ".text-neutral-content p")
            comments.append(text_body.text) # Add the text body to the comments
        except:
            print("No text body found.")

        try:
            sel = Selector(text=self.driver.page_source)
            cms = sel.css('[slot="comment"]')
            for cm in cms[:max_cm]:
                comment_string = cm.xpath('string()').get().strip()
                comments.append(comment_string) # Add the comment to the comments list
        except:
            print("No comments found.")

        formatted_comments = ' '.join(comments)
        return {"Mod title": mod_name, "Comments": formatted_comments}

if __name__ == "__main__":
    import asyncio

    async def run_spider():
        spider = RedditSpider()
        results = await spider.crawl("sushi",1,50, set())
        print(results)
    asyncio.run(run_spider())
