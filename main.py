"""This Bot is intended to search through jobs and write all details in a CSV file."""

import csv
import json
import logging
import os
import pickle
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from constants import Constant


class LinkedInJobBot(Constant):
    """The bot class has methods which will navigate through the website and search jobs based on keywords."""

    def __init__(self, username: str, password: str, job_title: str, job_location: str, path: str):
        """Initialize the bot.

        Args:
            username (str): Username in linkedin account(Email)
            password (str): Password of linkedin account
            job_title (str): The role you want to look for. (Eg. Software Engineer)
            job_location (str): The location you want to look for. (Eg. India)
            path (str): The path where your chrome driver is.
        """
        super().__init__()
        logging.basicConfig(
            filename='log.log', format=self.LOG_FMT, level=logging.INFO)
        logging.info("Object instantiated")
        os.environ["PATH"] += r'{}'.format(path)
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.username = username
        self.password = password
        self.job_title = job_title
        self.job_location = job_location

    def login_to_linkedin(self):
        """Login to the linkedin website."""
        logging.info("Logging to LinkedIn")
        self.driver.get(self.LOGIN_LINKEDIN)
        user = self.driver.find_element(By.ID, self.FIND_USERNAME)
        user.send_keys(self.username)
        pass_ = self.driver.find_element(By.ID, self.FIND_PASSWORD)
        pass_.send_keys(self.password)
        time.sleep(1)
        pass_.send_keys(Keys.RETURN)

    def save_cookies(self):
        """Cookies saved so that login does not occur every time."""
        with open(self.PICKLE_FILE, 'wb') as f:
            pickle.dump(self.driver.get_cookies(), f)
            logging.info("Cookies saved to Local")

    def fetch_cookies(self):
        """Fetch the saved cookies."""
        with open(self.PICKLE_FILE, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            logging.info("Cookies fetched by browser")

    def search_for_jobs(self):
        """Search for jobs."""
        logging.info("Job search with title and location")
        self.driver.get(self.JOB_URL)
        self.driver.implicitly_wait(5)
        search_box = self.driver.find_elements(By.CLASS_NAME, self.FIND_SEARCH_BOX)
        try:
            search_box[0].send_keys(self.job_title)
            search_box[3].send_keys(self.job_location)
            time.sleep(2)
            search_box[3].send_keys(Keys.ENTER)
        except Exception as e:
            print(e)

    def scroll_to(self, job_list_item):
        """Scroll to the particular job item."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", job_list_item)
            job_list_item.click()

        except Exception as e:
            print(e)

    def get_particular_values(self, job):
        """Get all detail of a particular job list item."""
        logging.info("Getting particular values")
        li = job.text.split("\n")[:3]
        details = self.driver.find_element(By.ID, self.FIND_DETAILS).text.encode("utf-8")
        details = str(details, encoding="utf-8")
        li.append(details)
        return li

    def close_browser(self):
        """Close browser after execution."""
        logging.info("Closing browser")
        self.driver.close()
        self.driver.quit()

    def start_linkedin_bot(self):
        """Start the linkedin bot."""
        if (os.path.exists(self.PICKLE_FILE)):
            logging.info("Cookies exist. No need to Login")
            self.driver.get(self.LINKEDIN_URL)
            self.fetch_cookies()
            self.driver.get(self.LINKEDIN_URL)
        else:
            logging.info("Cookies do not exist. Creating...")
            self.login_to_linkedin()
            self.save_cookies()

        self.search_for_jobs()
        filename = ""
        cnt = 1
        while (True):
            if (os.path.exists("./outputs/" + "job_details_" + str(cnt) + ".csv")):
                cnt += 1
            else:
                filename = "job_details_" + str(cnt) + ".csv"
                break
        filename = os.path.join("./outputs", filename)
        job_list = []

        try:
            time.sleep(2)
            with open(filename, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.CSV_HEADER)
            for page in range(1, 5):
                time.sleep(1)
                xpath = f'//button[@aria-label="Page {page}"]'
                next_page = self.driver.find_element(By.XPATH, xpath)
                next_page.click()
                time.sleep(1)

                jobs = self.driver.find_elements(By.CLASS_NAME, self.FIND_JOBS)
                logging.info("Found all jobs")
                for job in jobs:
                    self.scroll_to(job)
                    job_list.append(self.get_particular_values(job))
                    logging.info("Added job to job list")
        except OSError as e:
            print(e)
        finally:
            with open(filename, "a", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(job_list)
            self.close_browser()


if __name__ == "__main__":

    with open("my_data.json") as f:
        data = json.load(f)
    email = data["Email"]
    password = data["Password"]
    job_title = data["Job Title"]
    job_location = data["Job Location"]
    path = data["Driver Path"]
    bot = LinkedInJobBot(email, password, job_title, job_location, path)
    bot.start_linkedin_bot()
