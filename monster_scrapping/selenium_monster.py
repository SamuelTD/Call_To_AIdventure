#!/usr/bin/env python3
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_monster_urls(driver, base_url):
    driver.get(base_url)
    # wait until the links are present
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td.item a"))
    )
    return [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "td.item a")]

def scrape_monster(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    data = {}
    # Name
    data["name"] = driver.find_element(By.TAG_NAME, "h1").text.strip()

    # AC, HP, CR
    for label, key in [("AC","armor"), ("HP","HP"), ("CR","challenge_rating")]:
        strong = driver.find_element(
            By.XPATH,
            f'//strong[normalize-space()="{label}"]'
        )
        raw = driver.execute_script("""
            // start at the node immediately after the <strong>
            let n = arguments[0].nextSibling;
            // skip over any empty / “=” / punctuation nodes
            while(n && (!n.nodeValue || !n.nodeValue.match(/\d/))) {
            n = n.nextSibling;
            }
            return n ? n.nodeValue.trim() : "";
        """, strong)
        # e.g. raw == "16"  or  "66 (12d8+12)"  or  "5/2" (for CR 2.5)
        data[key] = raw.split()[0]

    # Strength, Dexterity, Constitution are in div.car3
    car3 = [
        el.text
        for el in driver.find_elements(By.CSS_SELECTOR, "div.car3")
        if el.text.strip()
    ]
    if len(car3) >= 3:
        data["strength"], data["dexterity"], data["constitution"] = car3[:3]

    # Intelligence, Wisdom, Charisma are in div.car6
    car6 = [
        el.text
        for el in driver.find_elements(By.CSS_SELECTOR, "div.car6")
        if el.text.strip()
    ]
    if len(car6) >= 3:
        data["intelligence"], data["wisdom"], data["charisma"] = car6[:3]
    
    el = data["description"] = driver.find_element(By.CSS_SELECTOR, "div.description")
    data["description"] = el.text

    return data

def main():
    # --- set up headless Chrome with webdriver-manager ---
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)

    base_url = "https://www.aidedd.org/monster/"
    print("Fetching monster list…")
    monster_urls = scrape_monster_urls(driver, base_url)
    print(f"Found {len(monster_urls)} monsters.")

    results = []
    for url in monster_urls:
        try:
            m = scrape_monster(driver, url)
            results.append(m)
            print(f" • scraped {m['name']}")
        except Exception as e:
            print(f" ! error at {url}: {e}")

    driver.quit()

    # dump to JSON
    with open("monsters.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} monsters to monsters.json")

if __name__ == "__main__":
    main()
