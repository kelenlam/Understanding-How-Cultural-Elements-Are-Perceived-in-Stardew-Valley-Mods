from selenium.webdriver.common.by import By
from scrapy.selector import Selector
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from base_spider import BaseSpider

class ModDropSpider(BaseSpider):
    name = "moddrop"

    def crawl(self, search_query, max_mod, max_cm, crawled_mods):
        results = []
        url= 'https://www.moddrop.com/stardew-valley/mods?order=updated&content='
        self.driver.get(url+search_query) # Search for the query

        try:
            # Locate the "Accept Cookies" button
            accept_cookies_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Accept Cookies')]")  
            # Click the button if it exists
            accept_cookies_button.click()
            print("Clicked the 'Accept Cookies' button.")

        except NoSuchElementException:
            print("The 'Accept Cookies' button was not found.")

      
        
        try: 
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn.btn-default.btn-wide")))
            last_page_element = self.driver.find_element(By.CSS_SELECTOR, ".btn.btn-default.btn-wide")
            last_page = list(last_page_element.text)[-1] # Get the last page number
        except Exception as e:
            print("Error getting last page number. Defaulting to 0 page.")
            return # Return if there's an error getting the last page number
        temp = []
        mod_links = []
        page_number = 1
        intercepted=False
        while True:
            if page_number > int(last_page) or len(mod_links)>max_mod*2:
                break
            if not intercepted:
                # Get mod links in that page
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a")))
                sel = Selector(text=self.driver.page_source)
                temp=sel.css("a::attr(href)").getall()
                for i in temp:
                    if '/stardew-valley/mods/' in i:
                        mod_links.append(i)
                page_number += 1
            else:
                intercepted=False

            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.btn-default > i.fa.fa-chevron-right")))
                next_page = self.driver.find_element(By.CSS_SELECTOR, "span.btn.btn-default > i.fa.fa-chevron-right")
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
            # Check if the result is valid
            if result:
                results.append(result)
                crawled_mods.add(result["Mod title"])
                crawled_no += 1
            link_index +=1
        return results


    def parse_mod_page(self,link,max_cm, crawled_mods):
        post_tab_url = "https://www.moddrop.com"+link+"/comments"
        comments = []
        self.driver.get(post_tab_url)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "cm-mb-8")))
        mod_name = self.driver.find_element(By.CSS_SELECTOR, "cm-mb-8").text 
        if mod_name in crawled_mods: # Skip if the mod name is already crawled
            return
        
        current_url = self.driver.current_url
        if current_url != post_tab_url:
            print(f"Redirect detected! Original URL: {post_tab_url}, Redirected to: {current_url}")
            return  # Return from the function if redirected i.e. no comments page
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.page-content > i")))
            content = self.driver.find_element(By.CSS_SELECTOR, "div.page-content > i")
            if content.text=="No comments found.": # Skip if there are no comments
                print("No comments found for this mod.")
                return
        except Exception as e:
            print("This mod has comments. Continuing to scrape comments.")

        
        page_number = 2
        for i in range(5): # Try to click the "View More" button up to 5 times
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'View More')]")))
                span_button=self.driver.find_element(By.XPATH,"//span[contains(text(), 'View More')]")
                actions = ActionChains(self.driver)
                actions.move_to_element(span_button).perform() # Scroll to the button at the bottom to make it clickable
                span_button.click() # Click the "View More" button to load more comments
                print(f"Navigated to page {page_number}")
                time.sleep(1)
                break # Break the loop if the button is clicked successfully

            # Scroll down if the ads are blocking the next page button
            except ElementClickInterceptedException:
                print(f"Click intercepted for page {page_number}. Trying to scroll or wait...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")                
            
            except Exception as e:
                print(e)
                print(f"No next page button found for page {page_number}. Ending pagination.")

        # Get the comments after scrolled to the bottom
        sel = Selector(text=self.driver.page_source)
        cms = sel.css(".cm-mark > p")
        for comment in cms[:max_cm]:
            comment_string = comment.xpath('string()').get().strip()
            comments.append(comment_string)

        formatted_comments = ' '.join(comments)
        return {"Mod title": mod_name, "Comments": formatted_comments}


if __name__ == "__main__":
    import asyncio

    async def run_spider():
        spider = ModDropSpider()
        results = await spider.crawl("sushi",1,50, set())
        print(results)

    asyncio.run(run_spider())