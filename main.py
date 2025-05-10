from get_urls import get_urls
from playwright.async_api import async_playwright
from utils.helper import clean_title, save_data_to_csv
import asyncio
import re
import time
import signal
import sys

# Global store for scraped data
scraped_data = []

# Max number of concurrent scrapes
CONCURRENT_TASKS = 5

# Semaphore to limit concurrency
semaphore = asyncio.Semaphore(CONCURRENT_TASKS)

async def scrape_product_data(context, url, max_retries=1):
    retries = 0
    while retries < max_retries:
        try:
            page = await context.new_page()

            # Block images, fonts, and stylesheets
            # await page.route("**/*", lambda route, request:
            #     route.abort() if request.resource_type in ["image", "stylesheet", "font"] else route.continue_()
            # )

            await page.goto(url, timeout=10000)
            await page.wait_for_load_state('domcontentloaded')

            # Defaults
            title = price = category = 'Error'

            try:
                title_text = await page.title()
                title = clean_title(title_text) if title_text else 'N/A'
            except:
                title = 'Error'

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

            try:
                category_element = page.locator('a[itemprop="name"]').nth(1)
                full_text = await category_element.inner_text(timeout=3000)
                category = full_text.split("/")[0].strip()
            except:
                category = 'Error'

            await page.close()
            # print(f"Scraped: {url}")
            return {'url': url, 'title': title, 'price': price, 'Category': category}

            
        except Exception as e:
            retries += 1
            if retries == max_retries:
                return {'url': url, 'title': 'Error', 'price': 'Error', 'Category': 'Error'}
            await asyncio.sleep(2)

def handle_interrupt(signal_num, frame):
    print("\n❌ Interrupted! Saving scraped data...")
    save_data_to_csv(scraped_data)
    sys.exit(0)

# Register interrupt signal handler
signal.signal(signal.SIGINT, handle_interrupt)

async def scrape_with_semaphore(context, url):
    async with semaphore:
        return await scrape_product_data(context, url)

async def main():
    global scraped_data
    urls = get_urls()
    total = len(urls)
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        tasks = [scrape_with_semaphore(context, url) for url in urls]

        for i, future in enumerate(asyncio.as_completed(tasks)):
            data = await future
            scraped_data.append(data)

            # Time & progress logging
            elapsed = time.time() - start_time
            avg_time_per_url = elapsed / (i + 1)
            remaining = avg_time_per_url * (total - (i + 1))
            print(f"[{i+1}/{total}] Elapsed: {elapsed/60:.1f} min | ETA: {remaining/60:.1f} min")

            # Optional: Save every 1000 records as a backup
            if (i + 1) % 1000 == 0:
                save_data_to_csv(scraped_data, f"checkpoint_{i+1}.csv")

        await browser.close()

    # Final save
    save_data_to_csv(scraped_data, "products.csv")

if __name__ == "__main__":
    asyncio.run(main())