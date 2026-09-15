import requests

from config import (
    WOOCOMMERCE_URL,
    WOOCOMMERCE_KEY,
    WOOCOMMERCE_SECRET,
)

url = f"{WOOCOMMERCE_URL}/wp-json/wc/v3/products"

response = requests.get(
    url,
    auth=(WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET),
    params={
        "per_page": 5
    },
    timeout=30
)

print("Status:", response.status_code)
print(response.text[:3000])