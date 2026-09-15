"""Ollama client for generating/enhancing product descriptions via local LLM."""

import requests
import config


class OllamaClient:
    def __init__(self):
        self.host = config.OLLAMA_HOST
        self.model = config.OLLAMA_MODEL

    def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated text."""
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json().get("response", "")

    def enhance_product_description(self, product: dict) -> str:
        """Generate an enhanced WooCommerce product description from scraped data."""
        prompt = f"""You are an e-commerce copywriter. Rewrite the following product information 
into a compelling WooCommerce product description in HTML format.

Product Title: {product.get('title', '')}
Original Description: {product.get('description', '')}
Category: {product.get('category', '')}
Price: {product.get('price', '')}

Requirements:
- Write a professional, SEO-friendly description
- Use HTML formatting (paragraphs, bullet points)
- Highlight key features and benefits
- Keep it concise but persuasive
- Do NOT include the price in the description
"""
        return self.generate(prompt)

    def generate_short_description(self, product: dict) -> str:
        """Generate a short product summary for WooCommerce."""
        prompt = f"""Write a 1-2 sentence product summary for:
Title: {product.get('title', '')}
Description: {product.get('description', '')}

Keep it concise and compelling. No HTML."""
        return self.generate(prompt)


if __name__ == "__main__":
    client = OllamaClient()
    sample = {
        "title": "Leather Crossbody Bag",
        "description": "Premium leather bag with adjustable strap",
        "category": "Bags",
        "price": "PKR 5,999",
    }
    print("Enhanced Description:")
    print(client.enhance_product_description(sample))
