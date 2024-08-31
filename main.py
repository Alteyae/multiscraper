from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str

@app.post("/scrape/")
async def scrape(request: ScrapeRequest):
    url = request.url
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if "hdsupplysolutions.com" in domain:
        return scrape_hdsupplysolutions(url)
    elif "bestbuy.com" in domain:
        return scrape_bestbuy(url)
    elif "alibaba.com" in domain:
        return scrape_alibaba(url)
    elif "staples.com" in domain:
        return scrape_staples(url)
    elif "officesupply.com" in domain:
        return scrape_officesupply(url)
    elif "www.menards.com" in domain:
        return scrape_menards(url)
    elif "www.wayfair.com" in domain:
        return scrape_wayfair(url)
    else:
        raise HTTPException(status_code=400, detail="No scraper available for this domain.")

def scrape_officesupply(url: str) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        price_tag = soup.find("span", class_="jx-price price")
        price = price_tag.text.strip() if price_tag else "Not found"

        script_tag = soup.find("script", type="text/javascript", string=re.compile("br_data"))
        if script_tag:
            script_content = script_tag.string
            product_data_match = re.search(r'br_data\s*=\s*({.*?});', script_content)
            if product_data_match:
                product_data = json.loads(product_data_match.group(1))
                product_name = product_data.get("prod_name", "Not found")
                sku = product_data.get("sku", "Not found")
            else:
                product_name = "Not found"
                sku = "Not found"
        else:
            product_name = "Not found"
            sku = "Not found"

        img_tag = soup.find("img", class_="jx-main-img")
        image_url = img_tag["src"] if img_tag else "Image URL not found"

        data = {
            "price": price,
            "product_name": product_name,
            "sku": sku,
            "image_url": image_url
        }

        return data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve the page.")

def scrape_hdsupplysolutions(url: str) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Referer': 'https://hdsupplysolutions.com/',  
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        json_ld_script = soup.find('script', type='application/ld+json')
        if json_ld_script:
            product_data = json.loads(json_ld_script.string)

            extracted_data = {
                'name': product_data.get('name', 'N/A'),
                'description': product_data.get('description', 'N/A'),
                'sku': product_data.get('sku', 'N/A'),
                'price': product_data.get('offers', {}).get('price', 'N/A')
            }

            img_tag = soup.find("img", {"id": "productMainImage"})
            image_url = img_tag["src"] if img_tag else "Not found"
            extracted_data['image_url'] = image_url

            return extracted_data
        else:
            raise HTTPException(status_code=404, detail="JSON-LD script not found.")
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve content.")

def scrape_bestbuy(url: str) -> dict:
    if not url.endswith("&intl=nosplash"):
        url += "&intl=nosplash"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        product_name = soup.title.string.strip()

        price_tag = soup.find('div', class_='priceView-hero-price priceView-customer-price')
        if price_tag:
            price_span = price_tag.find('span', {'aria-hidden': 'true'})
            if price_span:
                product_price = price_span.text.strip()
            else:
                product_price = "Price not found"
        else:
            product_price = "Price container not found"

        meta_tag = soup.find("meta", property="twitter:image")
        image_src = meta_tag['content'] if meta_tag else "Not found"

        extracted_data = {
            'url': url,
            'product_name': product_name,
            'price': product_price,
            'image': image_src
        }

        return extracted_data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve the page.")

def scrape_alibaba(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        item_name = None
        h1_tag = soup.find("h1")
        if h1_tag:
            item_name = h1_tag.text.strip()

        price = None
        price_div = soup.find("div", class_="price")
        if price_div:
            strong_tag = price_div.find("strong")
            if strong_tag:
                price = strong_tag.text.strip()

        if not price:
            price_item_div = soup.find("div", class_="price-item")
            if price_item_div:
                span_tag = price_item_div.find("span")
                if span_tag:
                    price = span_tag.text.strip()

        image_link_tag = soup.find("link", {"rel": "preload", "as": "image"})
        image_url = image_link_tag["href"] if image_link_tag else "Not found"

        data = {
            "item_name": item_name if item_name else "Not found",
            "price": price if price else "Not found",
            "image_url": image_url if image_url else "Not found"
        }

        return data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve the page.")

def scrape_staples(url: str) -> dict:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        product_name = soup.find("div", class_="sticky-CTA-UX2__prod_title")
        product_name = product_name.text.strip() if product_name else "Not found"

        product_price = soup.find("div", class_="sticky-CTA-UX2__prod_price")
        product_price = product_price.text.strip() if product_price else "Not found"
        img_tag = soup.find("div", class_="sticky-CTA-UX2__product_image").find("img")
        image_url = img_tag['alt'] if img_tag else "Image URL not found"

        data = {
            "product_name": product_name,
            "product_price": product_price,
            "image_url": image_url
        }

        return data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve content.")

def scrape_menards(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title").text if soup.find("title") else "Not found"

        price = soup.find("span", class_="price")
        price = price.text.strip() if price else "Not found"

        img_tag = soup.find("img", class_="primary-image")
        image_url = img_tag["src"] if img_tag else "Not found"

        data = {
            "title": title,
            "price": price,
            "image_url": image_url
        }

        return data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve content.")

def scrape_wayfair(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("h1", class_="product-title")
        title = title_tag.text.strip() if title_tag else "Not found"

        price_tag = soup.find("span", class_="price")
        price = price_tag.text.strip() if price_tag else "Not found"

        image_tag = soup.find("img", class_="product-image")
        image_url = image_tag["src"] if image_tag else "Not found"

        data = {
            "title": title,
            "price": price,
            "image_url": image_url
        }

        return data
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve content.")
