import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import re
from urllib.parse import urljoin

class EvaPharmaJobScraper:
    def __init__(self, headless=True):
        self.base_url = "https://apply.workable.com/eva-pharma/"
        self.jobs_data = []
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15) 
    
    def remove_location_filter(self):
        """Remove the default Egypt location filter"""
        try:
            print("Checking for location filters to remove...")
            time.sleep(3)  # Wait for filters to load
            
            # Look for filter tags or chips that might contain "Egypt"
            filter_selectors = [
                '[data-ui="filter-chip"]',
                '.filter-chip',
                '.filter-tag',
                '[class*="filter"]',
                '[class*="chip"]',
                '[class*="tag"]'
            ]
            
            for selector in filter_selectors:
                try:
                    filter_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in filter_elements:
                        if "egypt" in element.text.lower():
                            # Look for close button within the filter
                            close_button = None
                            try:
                                close_button = element.find_element(By.CSS_SELECTOR, '[data-ui="close"], .close, [aria-label*="remove"], [aria-label*="close"]')
                            except NoSuchElementException:
                                # Try clicking the element itself if it's clickable
                                close_button = element
                            
                            if close_button:
                                self.driver.execute_script("arguments[0].click();", close_button)
                                print("✓ Removed Egypt location filter")
                                time.sleep(2)
                                return True
                except NoSuchElementException:
                    continue
            
            # Alternative approach: look for clear filters button
            clear_selectors = [
                '[data-ui="clear-filters"]',
                '.clear-filters',
                'button[class*="clear"]',
                'a[class*="clear"]'
            ]
            
            for selector in clear_selectors:
                try:
                    clear_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if clear_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", clear_button)
                        print("✓ Cleared all filters")
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
            
            print("No location filter found to remove")
            return False
            
        except Exception as e:
            print(f"Error removing location filter: {e}")
            return False
    
    def get_job_listings(self):
        print("Loading job listings page...")
        self.driver.get(self.base_url)
        
        # Remove location filter before proceeding
        self.remove_location_filter()
        
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-ui='job']")))
            
            while True:
                try:
                    show_more_button = self.driver.find_element(By.CSS_SELECTOR, "[data-ui='load-more-button']")
                    if show_more_button.is_displayed() and show_more_button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", show_more_button)
                        time.sleep(3) 
                    else:
                        break
                except NoSuchElementException:
                    break
            
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-ui='job']")
            print(f"Found {len(job_elements)} job listings")
            
            jobs = []
            for job_element in job_elements:
                try:
                    job_data = self.extract_job_basic_info(job_element)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job basic info: {e}")
                    continue
            
            return jobs
            
        except TimeoutException:
            print("Timeout waiting for job listings to load")
            return []
    
    def extract_job_basic_info(self, job_element):
        try:
            job_id = job_element.get_attribute('data-id')
            link_element = job_element.find_element(By.CSS_SELECTOR, 'a')
            job_url = urljoin(self.base_url, link_element.get_attribute('href'))
            
            title_element = job_element.find_element(By.CSS_SELECTOR, '[data-ui="job-title"] span')
            title = title_element.text.strip()
            
            try:
                workplace_element = job_element.find_element(By.CSS_SELECTOR, '[data-ui="job-workplace"] strong')
                workplace_type = workplace_element.text.strip()
            except NoSuchElementException:
                workplace_type = "Not specified"
            
            try:
                location_elements = job_element.find_elements(By.CSS_SELECTOR, '[data-ui="job-location"] span span')
                location_parts = [elem.text.strip().rstrip(',') for elem in location_elements if elem.text.strip()]
                location = ', '.join(location_parts)
            except NoSuchElementException:
                location = "Not specified"
            
            try:
                dept_element = job_element.find_element(By.CSS_SELECTOR, '[data-ui="job-department"]')
                department = dept_element.text.strip()
            except NoSuchElementException:
                department = "Not specified"
            
            try:
                type_element = job_element.find_element(By.CSS_SELECTOR, '[data-ui="job-type"]')
                job_type = type_element.text.strip()
            except NoSuchElementException:
                job_type = "Not specified"
            
            try:
                posted_element = job_element.find_element(By.CSS_SELECTOR, '[data-ui="job-posted"]')
                posted_date = posted_element.text.strip()
            except NoSuchElementException:
                posted_date = "Not specified"
            
            return {
                'job_id': job_id,
                'job_url': job_url,
                'title': title,
                'workplace_type': workplace_type,
                'location': location,
                'department': department,
                'job_type': job_type,
                'posted_date': posted_date
            }
            
        except Exception as e:
            print(f"Error extracting basic job info: {e}")
            return None
    
    def get_job_details(self, job_url):
        print(f"Fetching details for: {job_url}")
        
        try:
            self.driver.get(job_url)
            
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  
            
            job_details = self.extract_job_content_advanced()
            
            return job_details
            
        except Exception as e:
            print(f"Error loading job details page: {e}")
    def parse_line_by_line(self, lines):
        sections = {
            'company_overview': '',
            'job_summary': '',
            'key_responsibilities': '',
            'requirements': ''
        }
        
        current_section = None
        content_buffer = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if not line_lower:
                continue
            
            if line_lower == 'company overview' or line_lower.startswith('company overview'):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                current_section = 'company_overview'
                content_buffer = []
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            elif line_lower == 'job summary' or line_lower.startswith('job summary'):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                current_section = 'job_summary'
                content_buffer = []
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            elif line_lower == 'key responsibilities' or line_lower.startswith('key responsibilities') or \
                 line_lower == 'responsibilities' or line_lower.startswith('responsibilities'):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                current_section = 'key_responsibilities'
                content_buffer = []
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            elif line_lower == 'requirements' or line_lower.startswith('requirements') or \
                 line_lower == 'qualifications' or line_lower.startswith('qualifications'):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                current_section = 'requirements'
                content_buffer = []
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            else:
                if current_section and line and len(line.strip()) > 2:
                    if not any(skip in line_lower for skip in [
                        'view website', 'view all jobs', 'help', 'accessibility', 
                        'powered by', 'workable', 'apply now', 'share', 'save'
                    ]):
                        content_buffer.append(line.strip())
        
        if current_section and content_buffer:
            sections[current_section] = '\n'.join(content_buffer).strip()
        
        return sections
    
    def extract_job_content_advanced(self):
        job_details = {
            'company_overview': '',
            'job_summary': '',
            'key_responsibilities': '',
            'requirements': ''
        }
        
        try:
            specific_details = self.extract_from_data_ui_elements()
            job_details.update(specific_details)
            
            if not any(job_details.values()):
                content_selectors = [
                    '[data-ui="job-description"]',
                    '.job-description',
                    '[role="main"]',
                    'main',
                    '.content',
                    '.job-post-content'
                ]
                
                main_content = None
                for selector in content_selectors:
                    try:
                        main_content = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if main_content:
                    full_text = main_content.text
                else:
                    try:
                        nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "nav, header, footer, .navigation, .nav")
                        for elem in nav_elements:
                            self.driver.execute_script("arguments[0].style.display = 'none';", elem)
                        
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        full_text = body.text
                    except:
                        full_text = self.driver.page_source
                
                parsed_details = self.parse_structured_content(full_text)
                for key, value in parsed_details.items():
                    if value and not job_details[key]:
                        job_details[key] = value
                
                html_details = self.extract_from_html_structure()
                for key, value in html_details.items():
                    if value and not job_details[key]:
                        job_details[key] = value
            
        except Exception as e:
            print(f"Error in advanced content extraction: {e}")
        
        return job_details
    
    def extract_from_data_ui_elements(self):
        details = {
            'company_overview': '',
            'job_summary': '',
            'key_responsibilities': '',
            'requirements': ''
        }
        
        try:
            try:
                requirements_element = self.driver.find_element(By.CSS_SELECTOR, '[data-ui="job-requirements"]')
                req_items = requirements_element.find_elements(By.TAG_NAME, 'li')
                if req_items:
                    req_list = [item.text.strip() for item in req_items if item.text.strip()]
                    details['requirements'] = '\n'.join([f"• {req}" for req in req_list])
                else:
                    details['requirements'] = requirements_element.text.strip()
                    if details['requirements'].startswith('Requirements'):
                        details['requirements'] = details['requirements'].replace('Requirements', '', 1).strip()
                
                print("✓ Successfully extracted requirements from data-ui element")
            except NoSuchElementException:
                print("⚠ Requirements data-ui element not found")
            
            try:
                description_element = self.driver.find_element(By.CSS_SELECTOR, '[data-ui="job-description"]')
                desc_text = description_element.text
                
                sections = self.parse_description_sections(desc_text)
                for key, value in sections.items():
                    if value and not details[key]:
                        details[key] = value
                
                print("✓ Successfully extracted description sections")
            except NoSuchElementException:
                print("⚠ Description data-ui element not found")
            
            if not details['key_responsibilities']:
                try:
                    resp_element = self.driver.find_element(By.CSS_SELECTOR, '[data-ui="job-responsibilities"]')
                    resp_items = resp_element.find_elements(By.TAG_NAME, 'li')
                    if resp_items:
                        resp_list = [item.text.strip() for item in resp_items if item.text.strip()]
                        details['key_responsibilities'] = '\n'.join([f"• {resp}" for resp in resp_list])
                    else:
                        details['key_responsibilities'] = resp_element.text.strip()
                    print("✓ Successfully extracted responsibilities from data-ui element")
                except NoSuchElementException:
                    pass
            
        except Exception as e:
            print(f"Error extracting from data-ui elements: {e}")
        
        return details
    
    def parse_description_sections(self, text):
        sections = {
            'company_overview': '',
            'job_summary': '',
            'key_responsibilities': ''
        }
        
        if not text:
            return sections
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_section = None
        content_buffer = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            line_lower = line.lower()
            
            if line_lower == 'company overview' or line_lower.startswith('company overview'):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                
                current_section = 'company_overview'
                content_buffer = []
                
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            elif line_lower == 'job summary' or line_lower.startswith('job summary'):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                
                current_section = 'job_summary'
                content_buffer = []
                
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            elif any(keyword in line_lower for keyword in ['key responsibilities', 'responsibilities']):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                
                current_section = 'key_responsibilities'
                content_buffer = []
                
                if ':' in line:
                    after_colon = line.split(':', 1)[1].strip()
                    if after_colon:
                        content_buffer.append(after_colon)
            
            elif any(keyword in line_lower for keyword in ['requirements', 'qualifications']):
                if current_section and content_buffer:
                    sections[current_section] = '\n'.join(content_buffer).strip()
                break
            
            else:
                if current_section and line:
                    if not any(skip in line_lower for skip in [
                        'view website', 'view all jobs', 'help', 'accessibility', 'powered by', 
                        'workable', 'apply', 'share', 'save'
                    ]):
                        content_buffer.append(line)
            
            i += 1
        
        if current_section and content_buffer:
            sections[current_section] = '\n'.join(content_buffer).strip()
        
        return sections
    
    def extract_from_html_structure(self):
        details = {
            'company_overview': '',
            'job_summary': '',
            'key_responsibilities': '',
            'requirements': ''
        }
        
        try:
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, strong, b")
            
            for heading in headings:
                heading_text = heading.text.lower().strip()
                
                if len(heading_text) < 3:
                    continue
                
                if heading_text == 'company overview' or 'company overview' in heading_text:
                    details['company_overview'] = self.get_content_after_element(heading)
                elif heading_text == 'job summary' or heading_text == 'summary':
                    details['job_summary'] = self.get_content_after_element(heading)
                elif 'key responsibilities' in heading_text or heading_text == 'responsibilities':
                    details['key_responsibilities'] = self.get_content_after_element(heading)
                elif heading_text == 'requirements' or heading_text == 'qualifications':
                    details['requirements'] = self.get_content_after_element(heading)
        
        except Exception as e:
            print(f"Error in HTML structure extraction: {e}")
        
        return details
    
    def get_content_after_element(self, element):
        try:
            content_parts = []
            
            current = element
            while True:
                try:
                    next_sibling = current.find_element(By.XPATH, "following-sibling::*[1]")
                    next_text = next_sibling.text.strip()
                    
                    if any(keyword in next_text.lower() for keyword in [
                        'company overview', 'job summary', 'key responsibilities', 'requirements',
                        'qualifications', 'view website', 'view all jobs'
                    ]):
                        break
                    
                    if next_text and len(next_text) > 3:
                        content_parts.append(next_text)
                    
                    current = next_sibling
                    
                    if len(content_parts) > 20:
                        break
                        
                except NoSuchElementException:
                    break
            
            return '\n'.join(content_parts)
        
        except Exception as e:
            print(f"Error getting content after element: {e}")
            return ""
    
    def parse_structured_content(self, text):
        sections = {
            'company_overview': '',
            'job_summary': '',
            'key_responsibilities': '',
            'requirements': ''
        }
        
        if not text:
            return sections
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        filtered_lines = []
        for line in lines:
            line_lower = line.lower()
            if not any(skip_phrase in line_lower for skip_phrase in [
                'view website', 'view all jobs', 'help', 'accessibility', 'powered by workable',
                'apply', 'share', 'save', 'back to', 'jobs', 'workable'
            ]):
                filtered_lines.append(line)
        
        sections = self.parse_line_by_line(filtered_lines)
        
        return sections
    
    def scrape_all_jobs(self):
        try:
            jobs = self.get_job_listings()
            
            if not jobs:
                print("No jobs found!")
                return []
            
            for i, job in enumerate(jobs, 1):
                print(f"Processing job {i}/{len(jobs)}: {job['title']}")
                
                try:
                    job_details = self.get_job_details(job['job_url'])
                    
                    complete_job_data = {**job, **job_details}
                    self.jobs_data.append(complete_job_data)
                    
                    print(f"Successfully processed: {job['title']}")
                    
                except Exception as e:
                    print(f"Error processing job {job['title']}: {e}")
                    self.jobs_data.append(job)
                
                time.sleep(2)
            
            return self.jobs_data
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            return self.jobs_data
    
    def save_to_json(self, filename='eva_pharma_jobs.json'):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    def print_job_summary(self):
        if not self.jobs_data:
            print("No jobs data available")
            return
        
        print(f"\n=== JOB SCRAPING SUMMARY ===")
        print(f"Total jobs scraped: {len(self.jobs_data)}")
        
        complete_jobs = 0
        for job in self.jobs_data:
            if any(job.get(field, '').strip() for field in ['job_summary', 'key_responsibilities', 'requirements']):
                complete_jobs += 1
        
        print(f"Jobs with detailed information: {complete_jobs}")
        print(f"Jobs with basic information only: {len(self.jobs_data) - complete_jobs}")
        
        return {
            'company_overview': 'Error loading details',
            'job_summary': 'Error loading details',
            'key_responsibilities': 'Error loading details',
            'requirements': 'Error loading details'
        }
    
    def close(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    scraper = EvaPharmaJobScraper(headless=True)
    try:
        print("Starting Eva Pharma job scraping...")
        jobs_data = scraper.scrape_all_jobs()
        print(f"\nScraping completed!")
        scraper.print_job_summary()
        scraper.save_to_json()
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        scraper.close()