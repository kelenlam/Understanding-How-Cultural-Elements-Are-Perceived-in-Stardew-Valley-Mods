import time
from selenium.webdriver.common.by import By
from scrapy.selector import Selector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from base_spider import BaseSpider

class NexusSpider(BaseSpider):
    name = "nexus"

    def crawl(self, search_query, max_mod, max_cm, crawled_mods):
        results = []
        url = 'https://www.nexusmods.com/games/stardewvalley/mods?keyword='
        full_url=url+search_query+"&sort=endorsements" # Search for the query
        self.driver.get(full_url)

        page_number = 1
        mod_links = []
        intercepted=False
        while True:
            if not intercepted:
                try:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'a[data-e2eid="mod-tile-title"]')))
                except Exception as e:
                    print(e)
                    return
                # Get the mod links from the page
                sel = Selector(text=self.driver.page_source)
                mod_links = sel.css('a[data-e2eid="mod-tile-title"]::attr(href)').getall()
                page_number+=1
            else:
                intercepted=False

            try:
                if len(mod_links) >= self.max_mod*2 or page_number>=5:
                    break
                self.driver.get(full_url + f"&page={page_number}") # Navigate to the next page

            
            except ElementClickInterceptedException: 
                print(f"Click intercepted for page {page_number}. Trying to scroll or wait...")
                self.driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
                intercepted=True
                continue

            except Exception as e:
                print(f"No next page button found for page {page_number}. Ending pagination.")
                break

        crawled_no=0       
        link_index = 0
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
        post_tab_url = link + "?tab=posts"
        self.driver.get(post_tab_url)

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#pagetitle h1")))
        mod_name  = self.driver.find_element(By.CSS_SELECTOR, "#pagetitle h1").text
        if mod_name in crawled_mods: # Skip if the mod name is already crawled
            return


        sel = Selector(text=self.driver.page_source)
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".comment:not(.comment-sticky) .comment-content-text")))
        except:
            print("No comments found for this mod.")
            return # Skip if there are no comments
        
        page_number = 1
        comments = []
        intercepted=False
        while True:
            if not intercepted:
                sel = Selector(text=self.driver.page_source)
                for comment_div in sel.css(".comment:not(.comment-sticky) .comment-content-text"):
                    if len(comments) >= max_cm:
                        break # Stop if we reach the max comments
                    comment_texts = comment_div.xpath('.//text()').getall()
                    full_comment = ' '.join(text.strip() for text in comment_texts if text.strip())
                    comments.append(full_comment) # Add the comment to the comments list
                    page_number += 1
            else:
                intercepted=False
            try:       
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//a[contains(@onclick, \"window.RH_CommentContainer.Send('page', '{page_number}')\")]")))
                next_page = self.driver.find_element(By.XPATH, f"//a[contains(@onclick, \"window.RH_CommentContainer.Send('page', '{page_number}')\")]")
                next_page.click() # Click the next page button
                print(f"Navigated to page {page_number}")
                time.sleep(1)

            except ElementClickInterceptedException:
                print(f"Click intercepted for page {page_number}. Trying to scroll or wait...")
                self.driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
                intercepted=True
                continue

            except Exception as e:
                print(f"No next page button found for page {page_number}. Ending pagination.")
                break
        
        formatted_comments = ' '.join(comments)
        return {"Mod title": mod_name, "Comments": formatted_comments}

if __name__ == "__main__":
    import asyncio

    async def run_spider():
        spider = NexusSpider()
        results = await spider.crawl("sushi",1,50, set())
        print(results)

    asyncio.run(run_spider())