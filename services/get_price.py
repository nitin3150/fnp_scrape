import re

async def get_price(page):
    try:
        price_element = await page.query_selector('#odometer')
        if price_element:
            price_text = await price_element.inner_text()
            return int(re.sub(r"[^\d]", "", price_text))
        else:
            return 'N/A'
    except:
        return 'Error'