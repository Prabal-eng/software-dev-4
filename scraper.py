import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class AmazonScraper:
    def __init__(self, search_term, num_pages):
        self.base_url = "https://www.amazon.com/s?k="
        self.search_term = search_term.replace(' ', '+')
        self.num_pages = num_pages
        self.user_agent = UserAgent()
        self.product_data = []
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def get_headers(self):
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def fetch_page(self, url):
        try:
            response = self.session.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_product(self, product):
        try:
            name_elem = product.find('span', {'class': 'a-size-medium a-color-base a-text-normal'})
            name = name_elem.text.strip() if name_elem else "N/A"

            price_elem = product.find('span', {'class': 'a-offscreen'})
            price = price_elem.text.strip() if price_elem else "N/A"

            rating_elem = product.find('span', {'class': 'a-icon-alt'})
            rating = rating_elem.text.split()[0] if rating_elem else "N/A"

            reviews_elem = product.find('span', {'class': 'a-size-base s-underline-text'})
            reviews = reviews_elem.text.strip() if reviews_elem else "N/A"

            return {
                'Name': name,
                'Price': price,
                'Rating': rating,
                'Reviews': reviews
            }
        except Exception as e:
            print(f"Error parsing product: {e}")
            return None

    def scrape_products(self):
        for page in range(1, self.num_pages + 1):
            url = f"{self.base_url}{self.search_term}&page={page}"
            print(f"Scraping page {page}...")
            html_content = self.fetch_page(url)

            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                product_list = soup.find_all('div', {'data-component-type': 's-search-result'})

                for product in product_list:
                    product_info = self.parse_product(product)
                    if product_info:
                        self.product_data.append(product_info)

            delay = random.uniform(10, 15)
            print(f"Waiting for {delay:.2f} seconds before the next request...")
            time.sleep(delay)

    def save_to_csv(self, filename):
        if not self.product_data:
            print("No data to save.")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Price', 'Rating', 'Reviews']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for product in self.product_data:
                writer.writerow(product)

        print(f"Data saved to {filename}")

def main():
    search_term = input("Enter the product you want to search for: ")
    num_pages = int(input("Enter the number of pages to scrape (1-5): "))
    num_pages = min(max(num_pages, 1), 5)  # Limit to 1-5 pages

    scraper = AmazonScraper(search_term, num_pages)
    scraper.scrape_products()

    filename = f"{search_term.replace(' ', '_')}_products.csv"
    scraper.save_to_csv(filename)

if __name__ == "__main__":
    main()
