import json
import re

import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


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


def normalize_image_url(url):
    """
    Normalize Shopify image URL.

    Removes resizing/query parameters so the same image
    is not imported multiple times.
    """

    if not url:
        return ""

    url = urljoin(
        "https://bagallery.com",
        url
    )

    # Remove Shopify query parameters
    if "?" in url:
        url = url.split("?")[0]

    # Use HTTPS
    url = url.replace(
        "http://bagallery.com",
        "https://bagallery.com"
    )

    return url


def scrape_product(url):

    print(f"Fetching: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "lxml"
    )

    # =========================================================
    # PRODUCT NAME
    # =========================================================

    product_name = ""

    # Try OpenGraph title
    og_title = soup.find(
        "meta",
        property="og:title"
    )

    if og_title and og_title.get("content"):

        product_name = clean_text(
            og_title["content"]
        )

    # Fallback to page title
    if not product_name:

        title_tag = soup.find("title")

        if title_tag:

            product_name = clean_text(
                title_tag.get_text()
            )

    # =========================================================
    # PRICE
    # =========================================================

    regular_price = ""
    sale_price = ""

    # Bagallery exposes variant pricing through
    # window.estimatedProductVariants
    for script in soup.find_all("script"):

        text = script.string or ""

        match = re.search(
            r"window\.estimatedProductVariants\s*=\s*(\[.+?\]);",
            text,
            re.DOTALL
        )

        if match:

            try:

                variants = json.loads(
                    match.group(1)
                )

                if variants:

                    variant = variants[0]

                    price_cents = variant.get(
                        "price"
                    )

                    compare_cents = variant.get(
                        "compare_at_price"
                    )

                    # Compare-at price = regular price
                    if compare_cents:

                        regular_price = str(
                            compare_cents / 100
                        )

                    # Current price = sale price
                    if price_cents:

                        sale_price = str(
                            price_cents / 100
                        )

            except Exception:

                pass

            break

    # =========================================================
    # FALLBACK PRICE FROM JSON-LD
    # =========================================================

    if not sale_price:

        for script in soup.find_all(
            "script",
            type="application/ld+json"
        ):

            try:

                data = json.loads(
                    script.string
                    or script.get_text()
                )

                if isinstance(data, list):

                    items = data

                else:

                    items = [data]

                for item in items:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    if item.get("@type") != "Product":
                        continue

                    offers = item.get(
                        "offers"
                    )

                    if isinstance(
                        offers,
                        list
                    ):

                        offers = (
                            offers[0]
                            if offers
                            else None
                        )

                    if isinstance(
                        offers,
                        dict
                    ):

                        price = offers.get(
                            "price"
                        )

                        if price:

                            sale_price = str(
                                price
                            )

            except Exception:

                continue

    # =========================================================
    # PRODUCT IMAGES
    # =========================================================

    images = []

    def add_image(image_url):

        if not image_url:
            return

        image_url = normalize_image_url(
            image_url
        )

        if not image_url:
            return

        lower_url = image_url.lower()

        # Skip non-product images
        skip_words = [
            "logo",
            "banner",
            "popup",
            "icon",
            "payment",
            "instalment",
            "jazzcash",
            "yeylo",
            "pay_in",
            ".gif"
        ]

        if any(
            word in lower_url
            for word in skip_words
        ):
            return

        # Only Bagallery / Shopify CDN images
        if not (
            "cdn.shopify.com" in lower_url
            or "bagallery.com/cdn/" in lower_url
        ):
            return

        if image_url not in images:

            images.append(
                image_url
            )

    # ---------------------------------------------------------
    # OpenGraph image
    # ---------------------------------------------------------

    og_image = soup.find(
        "meta",
        property="og:image"
    )

    if og_image and og_image.get("content"):

        add_image(
            og_image["content"]
        )

    # ---------------------------------------------------------
    # Images from <img>
    # ---------------------------------------------------------

    for img in soup.find_all("img"):

        # Normal image attributes
        possible_urls = [
            img.get("src"),
            img.get("data-src"),
            img.get("data-original"),
        ]

        for image_url in possible_urls:

            add_image(image_url)

        # Shopify srcset
        srcset = img.get("srcset")

        if srcset:

            for item in srcset.split(","):

                item = item.strip()

                if not item:
                    continue

                image_url = item.split(" ")[0]

                add_image(
                    image_url
                )

    # =========================================================
    # RESULT
    # =========================================================

    return {
        "name": product_name,
        "regular_price": regular_price,
        "sale_price": sale_price,
        "images": images,
    }


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    test_url = (
        "https://bagallery.com/"
        "collections/lattafa/products/"
        "lattafa-opulent-dubai-edp-100ml"
    )

    try:

        product = scrape_product(
            test_url
        )

        print("\n" + "=" * 60)
        print("PRODUCT")
        print("=" * 60)

        print("\nName:")
        print(product["name"])

        print("\nRegular Price:")
        print(product["regular_price"])

        print("\nSale Price:")
        print(product["sale_price"])

        print("\nImages:")

        for image in product["images"]:

            print("-", image)

        print(
            "\nTotal Images:",
            len(product["images"])
        )

        print(
            "\n" + "=" * 60
        )

    except Exception as e:

        print("\nERROR:")
        print(
            type(e).__name__
        )
        print(e)