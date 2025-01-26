


import os
import re
import json
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------------------------------------------------
# Inline Credentials (Replace these with your own if needed)
# -------------------------------------------------------------------
BROWSERSTACK_USERNAME = ""
BROWSERSTACK_ACCESS_KEY = ""# Enter Your BrowserStack Username and Access Key here
RAPID_API = "e342cb78bemsh40670d834afe738p1305b8jsn57b7ef6b08cf"#Enter Your Rapid Translate Multi Traduction API KEY
# -------------------------------------------------------------------

def click_element_by_xpath(wait, xpath, optional=False):
    """
    Click an element by XPath if present.
    If optional=True and element not found, it will skip without raising error.
    """
    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.click()
    except Exception as e:
        if optional:
            # Just log and skip
            print(f"Optional element {xpath} not found or not clickable. Skipping.")
        else:
            print(f"Error clicking element {xpath}: {e}")

def get_element_text_by_xpath(wait, xpath):
    """
    Retrieve text of an element using its XPath.
    Returns None if element is not found or there's an error.
    """
    try:
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return element.text
    except Exception as e:
        print(f"Error retrieving text from element {xpath}: {e}")
        return None

def translate_text(text, from_lang="es", to_lang="en"):
    """
    Translate text using the Rapid Translate Multi Traduction API.
    If daily quota or any error occurs, we log and return the original text.
    """
    if not text:
        return ""

    try:
        url = "https://rapid-translate-multi-traduction.p.rapidapi.com/t"
        payload = {"from": from_lang, "to": to_lang, "q": text}
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": "rapid-translate-multi-traduction.p.rapidapi.com",
            "x-rapidapi-key": RAPID_API,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            resp_json = response.json()
            # The success response might be a list of strings, e.g. ["Translated text"]
            # or an object with "result". Let's handle both.
            if isinstance(resp_json, list):
                # e.g. ["Sánchez reinforces his power..."]
                if len(resp_json) > 0:
                    return resp_json[0]
                else:
                    print(f"Empty list response for translation of '{text}'")
                    return text
            elif isinstance(resp_json, dict) and "result" in resp_json:
                # e.g. {"result": "Translated text"}
                return resp_json["result"]
            else:
                print(f"Unexpected translation response format: {resp_json}")
                return text
        else:
            # Possibly daily quota exceeded or some other error
            print(f"Translation failed for '{text}': {response.text}")
            return text

    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return text

def count_words(text):
    """
    Count word occurrences in a text (case-insensitive).
    """
    words = text.lower().split()
    word_count = defaultdict(int)
    for word in words:
        word_count[word] += 1
    return word_count

def save_image(image_url, title):
    """
    Download the image from the given URL and save it locally
    using a sanitized version of the article title as the filename.
    """
    if not image_url:
        return
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            # Remove characters that are invalid in filenames
            safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
            if not safe_title:
                safe_title = "article_image"
            filename = f"article_images/{safe_title}.jpg"
            with open(filename, "wb") as f:
                f.write(response.content)
        else:
            print(f"Failed to download image from {image_url} (status: {response.status_code})")
    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")

def preprocess_capabilities(capabilities):
    """
    Insert BrowserStack credentials and ensure default browserName if missing.
    """
    for cap in capabilities:
        if "desired_capabilities" in cap:
            if "bstack:options" in cap["desired_capabilities"]:
                cap["desired_capabilities"]["bstack:options"]["userName"] = BROWSERSTACK_USERNAME
                cap["desired_capabilities"]["bstack:options"]["accessKey"] = BROWSERSTACK_ACCESS_KEY
            if "browserName" not in cap["desired_capabilities"]:
                cap["desired_capabilities"]["browserName"] = "Chrome"
    return capabilities

# Read and preprocess capabilities from JSON
with open("capabilities.json", "r") as f:
    raw_capabilities = json.load(f)
processed_capabilities = preprocess_capabilities(raw_capabilities)

def execute_session(session_index, session_capabilities):
    driver = None
    try:
        options = webdriver.ChromeOptions()
        for key, value in session_capabilities.items():
            options.set_capability(key, value)

        # Connect to BrowserStack
        driver = webdriver.Remote(
            command_executor=f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub",
            options=options,
        )

        wait = WebDriverWait(driver, 15)

        # Try to maximize window only if not a mobile device
        bstack_options = session_capabilities.get("bstack:options", {})
        is_mobile = bstack_options.get("deviceName")  # If deviceName is set, it's mobile
        if not is_mobile:
            try:
                driver.maximize_window()
            except Exception as e:
                print(f"[Session {session_index}] Could not maximize window: {e}")

        # Open El Pais
        driver.get("https://elpais.com/")
        print(f"[Session {session_index}] Successfully opened El País website.")

        # Consent / cookie banners
        click_element_by_xpath(wait, '//*[@id="didomi-notice-agree-button"]', optional=True)
        click_element_by_xpath(wait, '//*[@id="pmConsentWall"]/div/div/div[2]/div[1]/a', optional=True)

        # Check language
        page_language = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
        if page_language and page_language.startswith("es"):
            print(f"[Session {session_index}] Page is in Spanish (lang={page_language}).")
        else:
            print(f"[Session {session_index}] Warning: The page language is '{page_language}'")

        # Navigate to Opinion section
        try:
            click_element_by_xpath(wait, '//*[@id="csw"]/div[1]/nav/div/a[3]', optional=False)
        except Exception:
            # If the above fails, fallback to direct URL
            driver.get("https://elpais.com/opinion/")

        # Get first 5 articles
        articles = driver.find_elements(By.TAG_NAME, "article")[:5]
        article_links = []
        for article in articles:
            anchors = article.find_elements(By.TAG_NAME, "a")
            if anchors:
                link = anchors[0].get_attribute("href")
                if link:
                    article_links.append(link)

        # Prepare folder for images
        if not os.path.exists("article_images"):
            os.makedirs("article_images")

        articles_data = {}
        for idx, link in enumerate(article_links, start=1):
            driver.execute_script("window.open(arguments[0], '_blank');", link)
            driver.switch_to.window(driver.window_handles[-1])

            try:
                title_xpath = "//header//h1"
                content_xpath = "//header//h2"

                title = get_element_text_by_xpath(wait, title_xpath) or ""
                content = get_element_text_by_xpath(wait, content_xpath) or ""

                # Attempt to find the first <img> in the article
                image_url = ""
                try:
                    img_element = driver.find_element(By.TAG_NAME, "img")
                    image_url = img_element.get_attribute("src")
                except Exception:
                    pass

                if title:
                    print(f"[Session {session_index}] Article {idx} Title (ES): {title}")
                if content:
                    print(f"[Session {session_index}] Article {idx} Content (ES): {content}")

                articles_data[idx] = {
                    "title": title,
                    "content": content,
                    "image": image_url
                }

                # Download cover image if available
                if image_url:
                    save_image(image_url, title if title else f"article_{idx}")
            except Exception as e:
                print(f"[Session {session_index}] Error processing article {idx}: {e}")
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        # Translate titles and print them
        for idx, article in articles_data.items():
            original_title = article["title"]
            translated_title = translate_text(original_title, "es", "en")
            article["translated_title"] = translated_title
            print(f"[Session {session_index}] Article {idx} - Translated Title (EN): {translated_title}")

        # Count repeated words across all translated titles
        word_counts = defaultdict(int)
        for _, article_info in articles_data.items():
            word_count = count_words(article_info["translated_title"])
            for w, c in word_count.items():
                word_counts[w] += c

        # Print words with occurrence > 2
        repeated_words = {w: c for w, c in word_counts.items() if c > 2}
        if repeated_words:
            print(f"[Session {session_index}] Words repeated more than twice in translated titles:")
            for w, c in repeated_words.items():
                print(f"[Session {session_index}] '{w}': {c}")

    except Exception as e:
        print(f"[Session {session_index}] Error in session: {e}")
    finally:
        if driver:
            driver.quit()

def run_sessions():
    with ThreadPoolExecutor(max_workers=5) as executor:
        for index, capability in enumerate(processed_capabilities, start=1):
            executor.submit(execute_session, index, capability["desired_capabilities"])

if __name__ == "__main__":
    run_sessions()
