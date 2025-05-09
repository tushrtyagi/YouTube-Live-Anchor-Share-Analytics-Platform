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

def get_reaction_count(post):
    try:
        # First try the standard text post reaction button
        reaction_elements = post.find_elements(By.XPATH, './/button[contains(@aria-label, "in total")]')
        
        # If no standard reaction button, try video/GIF specific reaction elements
        if not reaction_elements:
            reaction_elements = post.find_elements(By.XPATH, './/span[contains(@aria-label, "in total")]')
            
        # If still no reactions found, try alternative formats
        if not reaction_elements:
            reaction_elements = post.find_elements(By.XPATH, './/*[contains(@aria-label, "reactions")]')

        for element in reaction_elements:
            aria_label = element.get_attribute('aria-label')
            if aria_label:
                # Try different regex patterns to match various formats
                patterns = [
                    r'([\d,]+)\s+in total',
                    r'([\d,]+)\s+reactions',
                    r'([\d,]+)\s+reaction',
                    r'([\d,.]+)K?\s+in total',  # Handle K format (thousands)
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, aria_label)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        if 'K' in count_str:
                            # Convert K format to actual number
                            return int(float(count_str.replace('K', '')) * 1000)
                        return int(count_str)
                        
        return 0
    except Exception as e:
        print(f"Error getting reaction count: {e}")
        return 0

def scrape_whatsapp_channels(driver):
    channels = ['CNBC-TV18']  # Add other channels as needed
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
        search_term = channel_name
        search_box.send_keys(search_term)
        print(f"Entered '{search_term}' in search box")
        time.sleep(6)
    except TimeoutException:
        print(f"Search box not found for channel {channel_name}")
        return []
    except Exception as e:
        print(f"Unexpected error with search box: {e}")
        return []

    try:
        channel_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, f'//span[contains(@title, "{search_term}")]'))
        )
        print(f"Found {len(channel_elements)} potential matches for '{search_term}'")
        
        if len(channel_elements) > 0:
            for element in channel_elements:
                if channel_name.lower() in element.get_attribute('title').lower():
                    element.click()
                    print(f"Clicked on the match for '{channel_name}'")
                    break
            else:
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
    for i in range(120):
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
    
    for index, post in enumerate(posts):
        try:
            # Get content and timestamp
            content = ''
            try:
                content_element = WebDriverWait(post, 5).until(
                    EC.presence_of_element_located((By.XPATH, './/div[contains(@class, "copyable-text")]'))
                )
                content = content_element.text
            except:
                # Check for video/GIF caption
                try:
                    content_element = post.find_element(By.XPATH, './/div[contains(@class, "video-caption")]')
                    content = content_element.text
                except:
                    content = "[Media Content]"

            timestamp = WebDriverWait(post, 5).until(
                EC.presence_of_element_located((By.XPATH, './/div[contains(@data-pre-plain-text, "[")]'))
            ).get_attribute('data-pre-plain-text')

            # Get reaction count using the new function
            reaction_count = get_reaction_count(post)

            # Determine post type
            post_type = "Text"
            if post.find_elements(By.XPATH, './/video'):
                post_type = "Video"
            elif post.find_elements(By.XPATH, './/img[contains(@src, "blob")]'):
                post_type = "GIF/Image"

            links = extract_links(content)

            if timestamp:
                channel_data.append({
                    'Channel_Name': channel_name,
                    'Channel_Language': 'Business',
                    'Post_Content': content,
                    'Post_Type': post_type,
                    'Timestamp': timestamp,
                    'Post_Reaction': reaction_count,
                    'Links': links,
                    'Poll': 'No'
                })
                print(f"Processed {post_type} post {index+1} for '{channel_name}' with {reaction_count} reactions")
            
        except Exception as e:
            print(f"Error processing post {index+1} for '{channel_name}': {e}")
            continue

    print(f"Finished processing {len(channel_data)} posts for '{channel_name}'")
    return channel_data

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