# # Job scraping module
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class JobScraper:
    def __init__(self, base_url, driver_path):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for better performance
        self.driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
        self.base_url = base_url

    def scrape_jobs(self):
        url = f"{self.base_url}"  # Scrape from the main page directly
        print(f"Scraping jobs from {url}...")

        self.driver.get(url)
        time.sleep(2)

        # Find all job listings (using the "listing-container" class)
        job_cards = self.driver.find_elements(By.CLASS_NAME, 'listing-container')

        # Define roles of interest
        roles_of_interest = ['Software Engineer', 'Machine Learning Engineer', 'Data Engineer', 'Data Analyst']

        jobs = []
        for job_card in job_cards:
            try:
                # Extract job title
                title_element = job_card.find_element(By.CSS_SELECTOR, '.left h2')
                title = title_element.text.strip()

                # Check if the title matches any of the roles of interest
                if any(role in title for role in roles_of_interest):
                    # Extract other job details
                    company_element = job_card.find_element(By.CSS_SELECTOR, '.left h4')
                    location_element = job_card.find_element(By.CSS_SELECTOR, '.right p')

                    company = company_element.text.strip()
                    location = location_element.text.strip()

                    # Find the "right" div where the apply button is located
                    right_div = job_card.find_element(By.CLASS_NAME, 'right')

                    # Extract the Apply button within the "right" div
                    apply_button = right_div.find_element(By.CLASS_NAME, 'apply')

                    # Scroll to the Apply button
                    self.scroll_to_element(apply_button)

                    # Use JavaScript to click the Apply button
                    self.driver.execute_script("arguments[0].click();", apply_button)

                    # Wait for the new tab to open (or window)
                    time.sleep(2)

                    # Get the current window handle (the original window)
                    main_window = self.driver.current_window_handle

                    # Switch to the newly opened tab
                    windows = self.driver.window_handles
                    for window in windows:
                        if window != main_window:
                            self.driver.switch_to.window(window)
                            break

                    # Capture the new URL after the button click redirects
                    link = self.driver.current_url

                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': link
                    })

                    # Close the new tab and switch back to the main window
                    self.driver.close()
                    self.driver.switch_to.window(main_window)

            except Exception as e:
                print(f"Error scraping job card: {e}")

        return jobs

    def scroll_to_element(self, element):
        """Scroll the page until the element is visible."""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def close_driver(self):
        self.driver.quit()


# Example Usage:
if __name__ == "__main__":
    base_url = "https://hunt.redsols.us"
    driver_path = "/Users/surya/Desktop/chromedriver-mac-arm64/chromedriver"  # Replace with the path to your ChromeDriver

    scraper = JobScraper(base_url, driver_path)
    scraped_jobs = scraper.scrape_jobs()

    # Print the scraped jobs
    for job in scraped_jobs:
        print(f"Job Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Link: {job['link']}\n")

    # Close the browser after scraping
    scraper.close_driver()
