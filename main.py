from get_urls import get_urls
import asyncio
from playwright.async_api import async_playwright
import csv
import re

def clean_title(title):
    title = re.sub(r"^(Buy/Send|Buy|Send)\s+", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*FNP.*$", "", title, flags=re.I)
    title = re.sub(r"\s*Online\s*", "", title, flags=re.I)

    return title.strip()

async def scrape_product_data(page, url, max_retries=1):
    retries = 0
    while retries < max_retries:
        try:
            await page.goto(url, timeout=10000)
            await page.wait_for_load_state('domcontentloaded')
            
            # Initialize defaults
            title = price = category = 'Error'

            # Try getting title
            try:
                title_text = await page.title()
                title = clean_title(title_text) if title_text else 'N/A'
            except Exception as e:
                print(f"Title error: {e}")

            # Try getting price
            try:
                price_element = await page.query_selector('#odometer')
                if price_element:
                    price_text = await price_element.inner_text()
                    price = int(re.sub(r"[^\d]", "", price_text))
                else:
                    price = 'N/A'
            except Exception as e:
                print(f"Price error: {e}")
                price = 'Error'

            # Try getting category
            try:
                category_element = page.locator('a[itemprop="name"]').nth(1)
                full_text = await category_element.inner_text(timeout=3000)
                category = full_text.split("/")[0].strip()
            except Exception as e:
                # print(f"Category error (skipped): {e}")
                category = 'Error'

            print(f"Scraped: {url}")
            return {'url': url, 'title': title, 'price': price, 'Category': category}

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            retries += 1
            if retries == max_retries:
                print(f"Failed after {max_retries} retries: {url}")
                return {'url': url, 'title': 'Error', 'price': 'Error', 'Category': 'Error'}
            await asyncio.sleep(2)

async def main():
    urls = get_urls()
    urls = urls[:100]
    scraped_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in urls:
            data = await scrape_product_data(page, url)
            scraped_data.append(data)

        await browser.close()

    # Save to CSV
    keys = scraped_data[0].keys()
    with open('products.csv', 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(scraped_data)

if __name__ == "__main__":
    asyncio.run(main())