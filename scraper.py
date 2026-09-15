import json
import re

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    )
}


def clean_text(text):
    """Clean unnecessary whitespace."""
    if not text:
        return ""
    return " ".join(text.split())


def normalize_image_url(url, base_url=""):
    """
    Normalize Shopify image URL.
    Removes resizing/query parameters so the same image
    is not imported multiple times.
    """
    if not url:
        return ""

    if base_url:
        url = urljoin(base_url, url)

    # Remove Shopify query parameters
    if "?" in url:
        url = url.split("?")[0]

    # Ensure HTTPS
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("http://"):
        url = url.replace("http://", "https://")

    return url


def scrape_product(url):
    print(f"Fetching: {url}")
    
    parsed_uri = urlparse(url)
    base_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}"

    # =========================================================
    # 1. TRY SHOPIFY JSON ENDPOINT (MOST RELIABLE)
    # =========================================================
    json_url = url.split("?")[0]
    if not json_url.endswith(".json"):
        json_url += ".json"
        
    try:
        j_resp = requests.get(json_url, headers=HEADERS, timeout=15)
        if j_resp.status_code == 200:
            data = j_resp.json().get("product", {})
            if data:
                product_name = clean_text(data.get("title", ""))
                scraped_description = data.get("body_html", "") or ""
                scraped_brand = clean_text(data.get("vendor", ""))
                
                regular_price = ""
                sale_price = ""
                variants = data.get("variants", [])
                if variants:
                    v = variants[0]
                    price = v.get("price")
                    compare_price = v.get("compare_at_price")
                    
                    if compare_price:
                        regular_price = str(compare_price)
                    if price:
                        sale_price = str(price)
                        if not regular_price:
                            regular_price = sale_price
                        
                images = []
                for img_obj in data.get("images", []):
                    img_src = img_obj.get("src")
                    if img_src:
                        img_src = normalize_image_url(img_src, base_url)
                        if img_src and img_src not in images:
                            images.append(img_src)
                            
                return {
                    "name": product_name,
                    "description": scraped_description.strip(),
                    "regular_price": regular_price,
                    "sale_price": sale_price,
                    "images": images,
                    "brand": scraped_brand,
                }
    except Exception as e:
        print(f"JSON endpoint fetch failed: {e}. Falling back to HTML scraping.")

    # =========================================================
    # 2. HTML FALLBACK SCRAPING
    # =========================================================
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    # PRODUCT NAME
    product_name = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        product_name = clean_text(og_title["content"])
    if not product_name:
        title_tag = soup.find("title")
        if title_tag:
            product_name = clean_text(title_tag.get_text())

    # PRICE
    regular_price = ""
    sale_price = ""
    
    # Try generic JSON-LD first for price
    scraped_brand = ""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict) or item.get("@type") != "Product":
                    continue
                    
                offers = item.get("offers")
                if isinstance(offers, list):
                    offers = offers[0] if offers else None
                if isinstance(offers, dict):
                    price = offers.get("price")
                    if price and not sale_price:
                        sale_price = str(price)
                        
                brand_info = item.get("brand")
                if isinstance(brand_info, dict):
                    name = brand_info.get("name")
                    if name:
                        scraped_brand = clean_text(name)
                elif isinstance(brand_info, str):
                    scraped_brand = clean_text(brand_info)
        except Exception:
            continue

    if not sale_price:
        # Fallback for Bagallery specifically if JSON-LD fails
        for script in soup.find_all("script"):
            text = script.string or ""
            match = re.search(r"window\.estimatedProductVariants\s*=\s*(\[.+?\]);", text, re.DOTALL)
            if match:
                try:
                    variants = json.loads(match.group(1))
                    if variants:
                        variant = variants[0]
                        price_cents = variant.get("price")
                        compare_cents = variant.get("compare_at_price")
                        if compare_cents:
                            regular_price = str(compare_cents / 100)
                        if price_cents:
                            sale_price = str(price_cents / 100)
                except Exception:
                    pass
                break

    # PRODUCT DESCRIPTION
    scraped_description = ""
    # Try some common generic HTML description classes
    for desc_class in ["t4s-rte", "product__description", "product-description", "rte", "product-single__description"]:
        html_desc_div = soup.find("div", class_=desc_class)
        if html_desc_div:
            scraped_description = html_desc_div.decode_contents().strip()
            if scraped_description:
                break

    if not scraped_description:
        og_description = soup.find("meta", property="og:description")
        if og_description and og_description.get("content"):
            scraped_description = clean_text(og_description["content"])

    if not scraped_description:
        # Fallback to json-ld
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or script.get_text())
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "Product" and item.get("description"):
                        scraped_description = clean_text(item.get("description"))
                        break
            except Exception:
                continue

    # PRODUCT IMAGES
    images = []

    def add_image(image_url):
        if not image_url:
            return
        image_url = normalize_image_url(image_url, base_url)
        if not image_url:
            return
        lower_url = image_url.lower()

        skip_words = ["logo", "banner", "popup", "icon", "payment", "instalment", "jazzcash", "yeylo", "pay_in", ".gif"]
        if any(word in lower_url for word in skip_words):
            return

        # Generic Shopify CDN check
        if not ("cdn.shopify.com" in lower_url or "/cdn/" in lower_url):
            return

        if image_url not in images:
            images.append(image_url)

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        add_image(og_image["content"])

    for img in soup.find_all("img"):
        possible_urls = [img.get("src"), img.get("data-src"), img.get("data-original")]
        for image_url in possible_urls:
            add_image(image_url)

        srcset = img.get("srcset")
        if srcset:
            for item in srcset.split(","):
                item = item.strip()
                if not item:
                    continue
                image_url = item.split(" ")[0]
                add_image(image_url)

    return {
        "name": product_name,
        "description": scraped_description,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "images": images,
        "brand": scraped_brand,
    }

if __name__ == "__main__":
    test_url = "https://bagallery.com/collections/rtw/products/rtw-black-suede-push-lock-messenger-bag"
    try:
        product = scrape_product(test_url)
        print("\n" + "=" * 60)
        print("PRODUCT")
        print("=" * 60)
        print("\nName:\n", product["name"])
        print("\nRegular Price:\n", product["regular_price"])
        print("\nSale Price:\n", product["sale_price"])
        print("\nImages:")
        for image in product["images"]:
            print("-", image)
        print("\nTotal Images:", len(product["images"]))
        print("\nBrand:\n", product.get("brand"))
        print("\nDescription:\n", product.get("description"))
        print("\n" + "=" * 60)
    except Exception as e:
        print("\nERROR:")
        print(type(e).__name__)
        print(e)