# # Job scraping module
import openai
import psycopg2
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class JobScraper:
    def __init__(self, base_url, driver_path, gpt_api_key, db_credentials):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode for better performance
        self.driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
        self.base_url = base_url
        self.gpt_api_key = gpt_api_key
        openai.ai_key = self.gpt_api_key

        # PostgreSQL setup
        self.conn = psycopg2.connect(**db_credentials)
        self.create_table()

        # Define a list of job titless that match your profile
        self.roles_of_interest = ['Software Engineer','Full Stack Engineer','Backend Engineer', 'Machine Learning Engineer', 'Data Engineer', 'Data Analyst']

    def create_table(self):
        """Create table to store application data."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_applications(
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(255),
                            company VARCHAR(255),
                            location VARCHAR(255),
                            link TEXT,
                            resume_used VARCHAR(50),
                            application_status VARCHAR(50)
                            );
        """)
        self.conn.commit()

    def scrape_jobs(self, job_title, Keys):
        url = f"{self.base_url}"  # Scrape from the main page directly
        print(f"Scraping jobs from {url}...")

        self.driver.get(url)
        time.sleep(2)

        # Search for the desired job title (e.g., Software Engineer)
        search_box = self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Search for a job"]')
        search_box.clear()
        search_box.send_keys(job_title)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        # Apply filters
        self.apply_filters()

        # Find all job listings (using the "listing-container" class)
        job_cards = self.driver.find_elements(By.CLASS_NAME, 'listing-container')

        for job_card in job_cards:
            try:
                # Skip jobs with "APPLIED"
                if "APPLIED" in job_card.text:
                    continue

                # Extract job title
                title_element = job_card.find_element(By.CSS_SELECTOR, '.left h2')
                title = title_element.text.strip()

                # Check if the title matches any of the roles of interest
                if any(role in title for role in self.roles_of_interest):
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

                    # Extract Job Description if available
                    description = ""
                    try:
                        description = self.driver.find_element(By.CLASS_NAME, 'job-description').text
                    except:
                        pass
                    
                    # Use GPT-4 to analyze the job description
                    is_relevant, resume_type = self.is_job_relevant(description)
                    if not is_relevant:
                        continue # Skip irrelevant jobs

                    # Save job to database
                    self.save_to_db(title, company, location, link, resume_type, "Applied")

                    # Close the new tab and switch back to the main window
                    self.driver.close()
                    self.driver.switch_to.window(main_window)

            except Exception as e:
                print(f"Error scraping job card: {e}")

        return True
    def apply_filters(self):
        """Apply Entry Level, Mid Level, and Remote filters."""
        try:
            entry_level_filter = self.driver.find_element(By.XPATH, "//button(text()='Entry Level']")
            entry_level_filter.click()
            mid_level_filter = self.driver.find_element(By.XPATH, "//button[text()='Mid Level']")
            mid_level_filter.click()
            remote_filter = self.driver.find_element(By.XPATH, "//button[text()='Remote']")
            remote_filter.click()
            time.sleep(2)
        except Exception as e:
            print(f"Error applying filters: {e}")
    
    def is_job_relevant(self, description):
        """Use GPT-4 to check if the job desciption matches visa, experience, and resume criteria."""
        if description == "":
            return False, None # No description, skip the job
        
        prompt = f"""
        Job Description: {description}

        Please check if:
        1. The job offers visa sponsorship or mentions restrictions for U.S. citizens.
        2. The job is suitable for someone with less than 3 years of experience, like a new grad.
        3. Based on the description, should I use my Software Engineer resume or Machine Learning Engineer resume?

        Respond with a Yes/No answer for points 1 and 2. For point 3, respond with either "SDE resume" or "ML resume."
        """
        try:
            response = openai.Completion.create(
                engine="gpt-4",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            result = response['choices'][0]['text'].strip().lower()

            # Process GPT-4 response to determine relevance and resume choice
            if "yes" in result:
                if "sde resume" in result:
                    return True, "SDE"
                elif "ml resume" in result:
                    return True, "ML"
                else:
                    return False, None # No clear resume recommendation
            else:
                return False, None # Job is not relevant

        except Exception as e:
            print(f"Error with GPT-4 API: {e}")
            return False, None 


    def scroll_to_element(self, element):
        """Scroll the page until the element is visible."""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def save_to_db(self, title, company, location, link, resume, status):
        """Save the job details into PostgresSQL."""
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO job_applications (title, company, location, link, resume_used, application_status)
                VALUES (%s, %s, %s, %s, %s, %s)       
                """, (title, company, location, link, resume, status))
            self.conn.commit()

    def close_driver(self):
        self.driver.quit()


# Example Usage:
if __name__ == "__main__":
    base_url = "https://hunt.redsols.us"
    driver_path = "/Users/surya/Desktop/chromedriver-mac-arm64/chromedriver"  # Replace with the path to your ChromeDriver
    gpt_api_key = ""  # Replace with your OpenAI API key

    db_credentials = {
        'dbname': 'your_db_name',
        'user': 'your_db_user',
        'password': 'your_db_password',
        'host': 'localhost',
        'port': 5432
    }

    scraper = JobScraper(base_url, driver_path, gpt_api_key, db_credentials)
    scraper.scrape_jobs()
    scraper.close_driver()

# # Example Usage:
# if __name__ == "__main__":
#     base_url = "https://hunt.redsols.us"
#     driver_path = "/Users/surya/Desktop/chromedriver-mac-arm64/chromedriver"  # Replace with the path to your ChromeDriver

#     scraper = JobScraper(base_url, driver_path)
#     scraped_jobs = scraper.scrape_jobs()

#     # Print the scraped jobs
#     for job in scraped_jobs:
#         print(f"Job Title: {job['title']}")
#         print(f"Company: {job['company']}")
#         print(f"Location: {job['location']}")
#         print(f"Link: {job['link']}\n")

#     # Close the browser after scraping
#     scraper.close_driver()
