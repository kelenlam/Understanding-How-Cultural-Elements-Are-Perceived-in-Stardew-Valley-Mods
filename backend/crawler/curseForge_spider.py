from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from scrapy.selector import Selector
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from base_spider import BaseSpider

class CurseForgeSpider(BaseSpider):
    name = "curseforge"

    def crawl(self, search_query, max_mod, max_cm, crawled_mods):
        results=[]
        url= 'https://www.curseforge.com/stardewvalley'
        self.driver.get(url) # Search for the query

        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "search-input-field")))
        search_input = self.driver.find_element(By.CLASS_NAME, "search-input-field")
        search_input.send_keys(search_query) # Enter the search query
        # Press Enter to perform the search
        search_input.send_keys(Keys.RETURN) 

        page_number = 1
        mod_links = []
        intercepted=False
        while True:
            if not intercepted:
                # Get mod links in that page
                try:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".results-container .name")))
                except Exception as e:
                    return
                sel = Selector(text=self.driver.page_source)
                mod_links= mod_links+sel.css("div.results-container div.project-card a.name::attr(href)").getall()
                page_number += 1
            else:
                intercepted=False

            try:
                if len(mod_links) >= max_mod*2:
                    break         
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//div[contains(@class, 'pagination')]//button[text()='{page_number}']")))
                next_page = self.driver.find_element(By.XPATH, f"//div[contains(@class, 'pagination')]//button[text()='{page_number}']")
                next_page.click() # Click the next page button
                print(f"Navigated to page {page_number}")

            # Scroll down if the ads are blocking the next page button
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
            if result:
                results.append(result)
                crawled_mods.add(result["Mod title"])
                crawled_no += 1
            link_index +=1
        return results


    def parse_mod_page(self,link,max_cm,  crawled_mods):
        post_tab_url = "https://www.curseforge.com"+link +"/comments"
        self.driver.get(post_tab_url)
        comments=[]
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".name-container>h1")))
        mod_name = self.driver.find_element(By.CSS_SELECTOR, ".name-container>h1").text
        if mod_name in  crawled_mods: # Skip if the mod name is already crawled
            return
        
        current_url = self.driver.current_url
        if current_url != post_tab_url:
            print(f"Redirect detected! Original URL: {post_tab_url}, Redirected to: {current_url}")
            return  # Return from the function if redirected
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".empty-content-placeholder.undefined")))
            no_comments_elements = self.driver.find_element(By.CSS_SELECTOR, ".empty-content-placeholder.undefined")
            if no_comments_elements: # Skip if there are no comments
                print("No comments found for this mod.")
                return
        except:
            print("This mod has comments. Continuing to scrape comments.")


        page_number = 1
        intercepted=False
        while True:
            if not intercepted:
                sel = Selector(text=self.driver.page_source)
                cms = sel.css(".comments-list .comment .text > div> p")
                for comment in cms:
                    if len(comments) >= max_cm:
                        break # Stop if we reach the max comments
                    comment_string= comment.xpath('string()').get().strip()
                    comments.append(comment_string)
                page_number += 1
            else:
                intercepted=False

            try:
                if len(comments) >= max_cm:
                    break
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//div[contains(@class, 'pagination')]//button[text()='{page_number}']")))
                next_page = self.driver.find_element(By.XPATH, f"//div[contains(@class, 'pagination')]//button[text()='{page_number}']")
                next_page.click() # Click the next page button
                print(f"Navigated to page {page_number}")
                time.sleep(1)

            # Scroll down if the ads are blocking the next page button
            except ElementClickInterceptedException:
                print(f"Click intercepted for page {page_number}. Trying to scroll or wait...")
                self.driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
                intercepted=True
                continue
            
            except Exception as e:
                print(f"No next page button found for page {page_number}. Ending pagination.")
                break  # Exit the loop if an error occurs
            
        formatted_comments = ' '.join(comments)
        return {"Mod title": mod_name, "Comments": formatted_comments}

if __name__ == "__main__":
    import asyncio

    async def run_spider():
        spider = CurseForgeSpider()
        results = await spider.crawl("sushi",1,50, set())
        print(results)

    asyncio.run(run_spider())