import requests
import gzip
import io
from bs4 import BeautifulSoup

def get_urls():
    #products
    sitemap_url = "https://www.fnp.com/zip/products__Sitemap_1.xml.gz"
    #countries
    # sitemap_url = "https://www.fnp.com/zip/InternationalCat__Sitemap_1.xml.gz"
    #blogs
    # sitemap_url = "https://www.fnp.com/zip/Static__Sitemap_1.xml.gz" 
    #not working
    # sitemap_url = "https://www.fnp.com/zip/Category__Sitemap_1.xml.gz"

    # Download the .gz file
    response = requests.get(sitemap_url)
    compressed_data = io.BytesIO(response.content)

    # Decompress it
    with gzip.GzipFile(fileobj=compressed_data) as f:
        xml_data = f.read()

    soup = BeautifulSoup(xml_data, 'lxml-xml')

    urls = [loc.text for loc in soup.find_all('loc')]
    
    # print(len(urls))
    return urls

if __name__ == "__main__":
    get_urls()