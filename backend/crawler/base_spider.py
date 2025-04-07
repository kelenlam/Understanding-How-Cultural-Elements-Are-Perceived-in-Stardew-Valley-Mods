from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from scrapy.spiders import CrawlSpider
import os

class BaseSpider(CrawlSpider):

    name = "basespider"
    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors') 
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--enable-unsafe-swiftshader')
        chrome_options.add_argument("--disable-extensions")
        prefs = {"profile.managed_default_content_settings.images": 2}  # 2 means do not load images
        chrome_options.add_experimental_option("prefs", prefs) # Disable images

        # Path to ChromeDriver
        chromedriver = Service('chromedriver.exe')
        # Initialize the driver
        self.driver = webdriver.Chrome(service=chromedriver, options=chrome_options)
        self.driver.maximize_window() # Maximize the window to avoid issues with elements being off-screen

    def close(self):
        self.driver.quit()