from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
from datetime import datetime
import re

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_whatsapp_channels(driver):
    channels = ['News - Dainik Bhaskar Hindi - India, Rajasthan, Madhya Pradesh, MP, CG, UP, Bihar, Delhi']  # Add other channels as needed
    all_channel_data = []

    driver.get("https://web.whatsapp.com/")
    
    print("Please scan the QR code to log in to WhatsApp Web.")
    
    WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Channels"]'))
    )

    for channel in channels:
        channel_data = scrape_channel(driver, channel)
        all_channel_data.extend(channel_data)

    return all_channel_data, channels[0]

def scrape_channel(driver, channel_name):
    print(f"Scraping channel: {channel_name}")
    
    try:
        channels_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[title="Channels"]'))
        )
        channels_button.click()
        print("Clicked on Channels button successfully")
    except TimeoutException:
        print("Channels button not clickable. Trying to proceed anyway.")
    except Exception as e:
        print(f"Unexpected error clicking Channels button: {e}")
    
    try:
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
        )
        search_box.clear()
        # Search for the first word of the channel name
        search_term = channel_name.split()[0]
        search_box.send_keys(search_term)
        print(f"Entered '{search_term}' in search box")
        time.sleep(6)  # Increased wait time
    except TimeoutException:
        print(f"Search box not found for channel {channel_name}")
        return []
    except Exception as e:
        print(f"Unexpected error with search box: {e}")
        return []

    try:
        # Look for partial matches in the search results
        channel_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, f'//span[contains(@title, "{search_term}")]'))
        )
        print(f"Found {len(channel_elements)} potential matches for '{search_term}'")
        
        if len(channel_elements) > 0:
            # Check if any of the found elements contain the full channel name
            for element in channel_elements:
                if channel_name.lower() in element.get_attribute('title').lower():
                    element.click()
                    print(f"Clicked on the match for '{channel_name}'")
                    break
            else:
                # If no exact match, click the first result
                channel_elements[0].click()
                print(f"Clicked on the first partial match for '{channel_name}'")
        else:
            print(f"No matches found for '{channel_name}'")
            return []
    except TimeoutException:
        print(f"Channel {channel_name} not found in search results")
        return []
    except Exception as e:
        print(f"Unexpected error finding or clicking channel: {e}")
        return []

    time.sleep(5)
    print(f"Waiting completed after clicking '{channel_name}'")


    channel_data = []
    for i in range(30):
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_UP)
        time.sleep(2)
        print(f"Scrolled up {i+1} times")

    try:
        posts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "message-in")]'))
        )
        print(f"Found {len(posts)} posts for '{channel_name}'")
    except TimeoutException:
        print(f"No posts found for '{channel_name}'")
        return []
    except Exception as e:
        print(f"Unexpected error finding posts: {e}")
        return []
    
    for index, post in enumerate(posts):
        try:
            content = WebDriverWait(post, 10).until(
                EC.presence_of_element_located((By.XPATH, './/div[contains(@class, "copyable-text")]'))
            ).text
            timestamp = WebDriverWait(post, 10).until(
                EC.presence_of_element_located((By.XPATH, './/div[contains(@data-pre-plain-text, "[")]'))
            ).get_attribute('data-pre-plain-text')
         
            try:
                reaction_button = WebDriverWait(post, 10).until(
                    EC.presence_of_element_located((By.XPATH, './/button'))
                )
                reaction_count_str = reaction_button.get_attribute('aria-label')
                if reaction_count_str:
                    reaction_count_match = re.search(r'(\d+)\s+in total', reaction_count_str)
                    reaction_count = int(reaction_count_match.group(1)) if reaction_count_match else 0
                else:
                    reaction_count = 0
            except (TimeoutException, NoSuchElementException):
                reaction_count = 0

            links = extract_links(content)

            if content and timestamp:
                channel_data.append({
                    'channel': channel_name,
                    'content': content,
                    'timestamp': timestamp,
                    'reaction_count': reaction_count,
                    'links': links
                })
                print(f"Processed post {index+1} for '{channel_name}'")
            else:
                print(f"Skipped post {index+1} for '{channel_name}' due to missing content or timestamp")
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error processing post {index+1} for '{channel_name}': {e}")
            continue

    print(f"Finished processing {len(channel_data)} posts for '{channel_name}'")
    return channel_data

# Function to extract links from the 'content' column
def extract_links(text):
    return ', '.join(re.findall(r'(https?://\S+)', str(text)))

def main():
    driver = setup_driver()
    try:
        all_data, first_channel = scrape_whatsapp_channels(driver)
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Save the data into an Excel file
            df.to_excel(f'Whatsapp_Final_Data_{first_channel}_{datetime.now().date()}.xlsx', index=False)
            print("Data saved to Excel file.")
        else:
            print("No data to save.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()






# ### without scrolling 


# from webdriver_manager.chrome import ChromeDriverManager
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# import time
# import pandas as pd
# from datetime import datetime, timedelta
# import re

# def setup_driver():
#     chrome_options = Options()
#     # chrome_options.add_argument("--start-maximized")
#     # chrome_options.add_argument('--ignore-certificate-errors')
#     # chrome_options.add_argument('--ignore-ssl-errors')
    
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#     return driver

# def scrape_whatsapp_channels(driver, start_date):
#     channels = ['Business Today']  # Add other channels as needed
#     all_channel_data = []

#     driver.get("https://web.whatsapp.com/")
    
#     print("Please scan the QR code to log in to WhatsApp Web.")
    
#     WebDriverWait(driver, 300).until(
#         EC.presence_of_element_located((By.CSS_SELECTOR, 'div[title="Channels"]'))
#     )

#     for channel in channels:
#         channel_data = scrape_channel(driver, channel, start_date)
#         all_channel_data.extend(channel_data)

#     return all_channel_data, channels[0]

# def scrape_channel(driver, channel_name, start_date):
#     print(f"Scraping channel: {channel_name} from {start_date}")
    
#     try:
#         channels_button = WebDriverWait(driver, 10).until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[title="Channels"]'))
#         )
#         channels_button.click()
#         print("Clicked on Channels button successfully")
#     except TimeoutException:
#         print("Channels button not clickable. Trying to proceed anyway.")
#     except Exception as e:
#         print(f"Unexpected error clicking Channels button: {e}")
    
#     try:
#         search_box = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
#         )
#         search_box.clear()
#         search_term = channel_name.split()[0]
#         search_box.send_keys(search_term)
#         print(f"Entered '{search_term}' in search box")
#         time.sleep(6)  # Increased wait time
#     except TimeoutException:
#         print(f"Search box not found for channel {channel_name}")
#         return []
#     except Exception as e:
#         print(f"Unexpected error with search box: {e}")
#         return []

#     try:
#         channel_elements = WebDriverWait(driver, 15).until(
#             EC.presence_of_all_elements_located((By.XPATH, f'//span[contains(@title, "{search_term}")]'))
#         )
#         print(f"Found {len(channel_elements)} potential matches for '{search_term}'")
        
#         if len(channel_elements) > 0:
#             for element in channel_elements:
#                 if channel_name.lower() in element.get_attribute('title').lower():
#                     element.click()
#                     print(f"Clicked on the match for '{channel_name}'")
#                     break
#             else:
#                 channel_elements[0].click()
#                 print(f"Clicked on the first partial match for '{channel_name}'")
#         else:
#             print(f"No matches found for '{channel_name}'")
#             return []
#     except TimeoutException:
#         print(f"Channel {channel_name} not found in search results")
#         return []
#     except Exception as e:
#         print(f"Unexpected error finding or clicking channel: {e}")
#         return []

#     time.sleep(5)
#     print(f"Waiting completed after clicking '{channel_name}'")

#     channel_data = []
#     last_date = None
#     continue_scraping = True

#     while continue_scraping:
#         try:
#             posts = WebDriverWait(driver, 10).until(
#                 EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "message-in")]'))
#             )
#             print(f"Found {len(posts)} posts for '{channel_name}'")
#         except TimeoutException:
#             print(f"No posts found for '{channel_name}'")
#             break
#         except Exception as e:
#             print(f"Unexpected error finding posts: {e}")
#             break
        
#         for index, post in enumerate(posts):
#             try:
#                 content = WebDriverWait(post, 10).until(
#                     EC.presence_of_element_located((By.XPATH, './/div[contains(@class, "copyable-text")]'))
#                 ).text
#                 timestamp_str = WebDriverWait(post, 10).until(
#                     EC.presence_of_element_located((By.XPATH, './/div[contains(@data-pre-plain-text, "[")]'))
#                 ).get_attribute('data-pre-plain-text')
                
#                 date_match = re.search(r'\[(.*?)\]', timestamp_str)
#                 if date_match:
#                     post_date = datetime.strptime(date_match.group(1), '%d/%m/%Y %I:%M:%S %p')
#                     if post_date.date() < start_date:
#                         continue_scraping = False
#                         break
                    
#                     try:
#                         reaction_button = WebDriverWait(post, 10).until(
#                             EC.presence_of_element_located((By.XPATH, './/button'))
#                         )
#                         reaction_count_str = reaction_button.get_attribute('aria-label')
#                         if reaction_count_str:
#                             reaction_count_match = re.search(r'(\d+)\s+in total', reaction_count_str)
#                             reaction_count = int(reaction_count_match.group(1)) if reaction_count_match else 0
#                         else:
#                             reaction_count = 0
#                     except (TimeoutException, NoSuchElementException):
#                         reaction_count = 0

#                     links = extract_links(content)

#                     channel_data.append({
#                         'channel': channel_name,
#                         'content': content,
#                         'timestamp': timestamp_str,
#                         'reaction_count': reaction_count,
#                         'links': links
#                     })
#                     print(f"Processed post {index+1} for '{channel_name}' from {post_date.date()}")
                    
#                     last_date = post_date.date()
#                 else:
#                     print(f"Skipped post {index+1} for '{channel_name}' due to missing or invalid timestamp")
                    
#             except (TimeoutException, NoSuchElementException) as e:
#                 print(f"Error processing post {index+1} for '{channel_name}': {e}")
#                 continue

#         if continue_scraping:
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             time.sleep(2)  # Wait for new posts to load
            
#             if last_date and (datetime.now().date() - last_date) > timedelta(days=30):
#                 print(f"Reached posts older than 30 days, stopping scraping for '{channel_name}'")
#                 break

#     print(f"Finished processing {len(channel_data)} posts for '{channel_name}'")
#     return channel_data

# def extract_links(text):
#     return ', '.join(re.findall(r'(https?://\S+)', str(text)))

# def main():
#     driver = setup_driver()
#     try:
#         start_date = (datetime.now() - timedelta(days=30)).date()  # Scrape last 7 days
#         all_data, first_channel = scrape_whatsapp_channels(driver, start_date)
#         if all_data:
#             df = pd.DataFrame(all_data)
#             df.to_excel(f'Whatsapp_Data_{first_channel}_{datetime.now().date()}.xlsx', index=False)
#             print("Data saved to Excel file.")
#         else:
#             print("No data to save.")
#     finally:
#         driver.quit()
