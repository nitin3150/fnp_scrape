import asyncio
import signal
import sys
import time
import random
from playwright.async_api import async_playwright
from get_urls import get_urls
from utils.helper import save_data_to_csv
from services.get_title import get_title
from services.get_price import get_price
from services.get_cat import get_cat

# Global
scraped_data = []
CONCURRENT_TASKS = 5
RESET_INTERVAL = 500  # Restart browser context every 500 URLs
semaphore = asyncio.Semaphore(CONCURRENT_TASKS)

def handle_interrupt(signal_num, frame):
    print("\n❌ Interrupted! Saving scraped data...")
    save_data_to_csv(scraped_data, "interrupted_checkpoint.csv")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_interrupt)

async def scrape_product_data(context, url, max_retries=2):
    retries = 0
    while retries < max_retries:
        page = await context.new_page()
        try:
            await page.goto(url, timeout=10000)
            await page.wait_for_load_state('domcontentloaded')

            # Title
            title = await get_title(page)
            # Price
            price = await get_price(page)
            # Category
            category = await get_cat(page)

            # print(f"✅ Scraped: {url}")
            return {'url': url, 'title': title, 'price': price, 'Category': category}

        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            retries += 1
            await asyncio.sleep(2)
            if retries == max_retries:
                return {'url': url, 'title': 'Error', 'price': 'Error', 'Category': 'Error'}
        finally:
            await page.close()


async def scrape_batch(playwright, urls_batch, batch_index):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    batch_data = []

    async def scrape_with_semaphore(url):
        async with semaphore:
            await asyncio.sleep(random.uniform(0.5, 2.0))  # Avoid detection
            return await scrape_product_data(context, url)

    tasks = [scrape_with_semaphore(url) for url in urls_batch]

    for i, task in enumerate(asyncio.as_completed(tasks), start=1):
        result = await task
        scraped_data.append(result)
        batch_data.append(result)

        elapsed = time.time() - start_time
        avg = elapsed / (batch_index * RESET_INTERVAL + i)
        remaining = avg * (total_urls - (batch_index * RESET_INTERVAL + i))
        print(f"[{batch_index * RESET_INTERVAL + i}/{total_urls}] ETA: {remaining/60:.1f} min")

    await browser.close()
    save_data_to_csv(batch_data, f"checkpoint_{batch_index * RESET_INTERVAL}.csv")


async def main():
    global start_time, total_urls
    urls = get_urls()
    total_urls = len(urls)
    start_time = time.time()

    async with async_playwright() as playwright:
        batches = [urls[i:i+RESET_INTERVAL] for i in range(0, total_urls, RESET_INTERVAL)]

        for batch_index, batch_urls in enumerate(batches):
            print(f"\n🚀 Starting batch {batch_index + 1}/{len(batches)}")
            await scrape_batch(playwright, batch_urls, batch_index)

    # Final save
    save_data_to_csv(scraped_data, "products.csv")
    print("✅ All done! Saved to products.csv")


if __name__ == "__main__":
    asyncio.run(main())