
# browserStackAssignment

## Selenium Web Scraping and Cross-Browser Testing Project

This repository contains a Selenium-based project demonstrating:

1. **Web Scraping** (El País Opinion articles)
2. **API Integration** (Rapid Translate Multi Traduction API)
3. **Text Processing** (Identify repeated words in translated titles)
4. **Cross-Browser Testing** (BrowserStack in parallel)

---

### Key Steps

1. **Scrape El País**  
   - Ensure text is in Spanish  
   - Go to Opinion section  
   - Get first five articles: print title, content  
   - Download cover images if available  

2. **Translate Titles** (Spanish → English)  
   - Rapid Translate Multi Traduction API  

3. **Find Repeated Words** in all translated titles  
   - Print any words appearing **more than twice**  

4. **Run Locally or on BrowserStack**  
   - By default, this script runs on BrowserStack with 5 parallel threads (desktop + mobile).

---

### Files

- **Test.py**: Main test script  
- **capabilities.json**: Contains 5 sets of BrowserStack capabilities  
- **README.md**: Project instructions  

---

### Important Notes

1. **BrowserStack Credentials** and **Rapid API Key** are **hardcoded** in `Test.py` for demonstration. In production, use environment variables or a secure store.  
2. **Mobile Capabilities** cannot maximize the browser window. The code now **skips** `driver.maximize_window()` if it detects a mobile device.  
3. **Daily Quota Exceeded**: If you exceed the Rapid Translate daily quota, the code logs an error and **keeps the original Spanish** as the “translation.”  
4. **Repeated Words**: The script prints repeated words from whatever is in `translated_title`. If the API fails, the Spanish text remains, but repeated words are still counted.

---

### How to Run
1. Enter your BrowserStack credentials and Rapid Translate API key in `Test.py`.
2. **Install Dependencies**  
   ```bash
   pip install selenium requests
