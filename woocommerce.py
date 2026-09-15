"""WooCommerce REST API client for creating and managing products."""

from woocommerce import API
import config


class WooCommerceClient:
    def __init__(self):
        self.api = API(
            url=config.WOO_URL,
            consumer_key=config.WOO_CONSUMER_KEY,
            consumer_secret=config.WOO_CONSUMER_SECRET,
            version="wc/v3",
            timeout=30,
        )

    def get_products(self, per_page: int = 10) -> list:
        """Fetch existing products from WooCommerce."""
        response = self.api.get("products", params={"per_page": per_page})
        response.raise_for_status()
        return response.json()

    def create_product(self, product_data: dict) -> dict:
        """Create a new product in WooCommerce."""
        response = self.api.post("products", product_data)
        response.raise_for_status()
        return response.json()

    def build_product_payload(self, product: dict, description: str, short_description: str) -> dict:
        """Build a WooCommerce product payload from scraped + AI-enhanced data."""
        images = [{"src": url} for url in product.get("images", [])]

        return {
            "name": product.get("title", ""),
            "type": "simple",
            "status": "draft",
            "description": description,
            "short_description": short_description,
            "regular_price": self._clean_price(product.get("price", "")),
            "images": images,
            "categories": self._resolve_categories(product.get("category", "")),
        }

    def _clean_price(self, price_str: str) -> str:
        """Extract numeric price from string like 'PKR 5,999'."""
        import re
        numbers = re.sub(r"[^\d.]", "", price_str)
        return numbers

    def _resolve_categories(self, category_name: str) -> list:
        """Find or create a category by name and return list for payload."""
        if not category_name:
            return []

        # Search for existing category
        response = self.api.get("products/categories", params={"search": category_name})
        categories = response.json()

        if categories:
            return [{"id": categories[0]["id"]}]

        # Create new category
        new_cat = self.api.post("products/categories", {"name": category_name}).json()
        return [{"id": new_cat["id"]}]


if __name__ == "__main__":
    client = WooCommerceClient()
    products = client.get_products(per_page=3)
    print(f"Fetched {len(products)} products from WooCommerce.")
