from playwright.sync_api import sync_playwright
import rdflib
import time
import re
from datetime import datetime

START_URL = "https://www.delamar.nl/voorstellingen/"
OUTPUT_FILE = "scraped_delamar_events.ttl"

def extract_show_links(page):
    print("🔍 Extracting show links...")
    elements = page.query_selector_all("a[href^='/voorstellingen/']")
    links = set()
    for el in elements:
        href = el.get_attribute("href")
        if href and href.startswith("/voorstellingen/") and "#" not in href and href != "/voorstellingen/":
            links.add("https://delamar.nl" + href.rstrip("/"))
    return list(links)

def extract_duration_from_show_page(page):
    try:
        dropdown = page.query_selector("button:has-text('Praktische informatie')")
        if dropdown:
            dropdown.click()
            time.sleep(0.5)

        rows = page.query_selector_all("table tr")
        for row in rows:
            th = row.query_selector("th")
            td = row.query_selector("td")
            if th and td and "duur" in th.inner_text().strip().lower():
                return td.inner_text().strip()
    except Exception as e:
        print(f"⚠️ Failed to extract duration: {e}")
    return None

def extract_performance_dates(page):
    try:
        # Wait for production date blocks to be visible
        page.wait_for_selector(".production__date", timeout=10000)
        time.sleep(1)  # Allow JS rendering

        date_blocks = page.query_selector_all(".production__date")
        print(f"🔎 Found {len(date_blocks)} performance blocks.")

        dates = []
        for block in date_blocks:
            date_attr = block.get_attribute("data-date")
            time_text = block.inner_text().strip()

            # Extract the HH:MM time portion using regex
            match = re.search(r"\b\d{2}:\d{2}\b", time_text)
            if date_attr and match:
                datetime_str = f"{date_attr}T{match.group()}"
                dates.append(datetime_str)

        return dates

    except Exception as e:
        print(f"⚠️ Error extracting performance dates: {e}")
        return [] 

def run_scraper():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        print("🎭 Starting DelaMar show scraper.")
        print("🌐 Navigating to show list...")
        page.goto(START_URL, timeout=60000)
        page.wait_for_timeout(3000)

        show_urls = extract_show_links(page)
        print(f"🔗 Found {len(show_urls)} valid show pages.")

        g = rdflib.Graph()
        show_count = 0

        for idx, url in enumerate(show_urls, start=1):
            print(f"\n[{idx}/{len(show_urls)}] 📄 Visiting {url}")
            try:
                show_page = browser.new_page()
                show_page.goto(url, timeout=60000)
                show_page.wait_for_timeout(3000)

                title = show_page.title().replace(" - DeLaMar", "").strip()
                duration = extract_duration_from_show_page(show_page)
                dates = extract_performance_dates(show_page)

                subject = rdflib.URIRef(url)
                g.add((subject, rdflib.RDFS.label, rdflib.Literal(title)))

                if duration and "niet bekend" not in duration.lower():
                    g.add((subject, rdflib.URIRef("http://schema.org/duration"), rdflib.Literal(duration)))
                    print(f"⏱️ Duration found: {duration}")
                else:
                    print("❓ No duration found or not available yet.")

                for dt in dates:
                    g.add((subject, rdflib.URIRef("http://schema.org/startDate"), rdflib.Literal(dt)))
                print(f"📅 Found {len(dates)} performance date(s).")

                show_count += 1
            except Exception as e:
                print(f"❌ Error visiting {url}: {e}")
            finally:
                show_page.close()

        print(f"\n💾 Writing RDF with {show_count} shows to {OUTPUT_FILE}")
        g.serialize(destination=OUTPUT_FILE, format="turtle")
        print("✅ Done!")
        browser.close()

if __name__ == "__main__":
    run_scraper()