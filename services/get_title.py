from utils.helper import clean_title

# Title
async def get_title(page):
    try:
        title_text = await page.title()
        return clean_title(title_text) if title_text else 'N/A'
    except:
        return 'Error'