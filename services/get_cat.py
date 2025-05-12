async def get_cat(page):
    try:
        category_element = page.locator('a[itemprop="name"]').nth(1)
        full_text = await category_element.inner_text(timeout=3000)
        return full_text.split("/")[0].strip()
    except:
        return'Error'