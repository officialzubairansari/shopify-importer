import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import openpyxl
from scraper import scrape_product
from config import (
    WOOCOMMERCE_URL,
    WOOCOMMERCE_KEY,
    WOOCOMMERCE_SECRET,
    OLLAMA_URL,
    OLLAMA_MODEL,
    AI_PROVIDER,
    GEMINI_API_KEY
)

# Setup requests session with retries for robust API calls
session = requests.Session()
retries = Retry(
    total=3, 
    backoff_factor=2, 
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(['GET', 'POST'])
)
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

def generate_description(product_name):
    """Generate product description using Ollama or Gemini."""
    print(f"Generating description for: {product_name} using {AI_PROVIDER.upper()}")
    
    prompt = f"""
You are an expert ecommerce product copywriter.

Product name:
{product_name}

Write a detailed, captivating product description.

Requirements:
- Write 3 to 4 well-structured paragraphs
- The tone must be professional, engaging, and persuasive
- It must sound like it was written by a human professional content writer, NOT an AI or bot
- Suitable for a high-end beauty and fragrance store
- Do not invent fragrance notes, ingredients, or specifications
- Do not make unsupported claims
- Do not mention Bagallery or AI
- Format the response using HTML <p> tags for paragraphs
- Return ONLY the HTML description, nothing else
"""
    
    if AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing in .env")
        # Using gemini-flash-lite-latest as it is the fastest, most lightweight model available
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        response = session.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=45)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        # Default to Ollama
        response = session.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=45
        )
        response.raise_for_status()
        return response.json()["response"]

def resolve_category(category_name):
    """Find or create a WooCommerce category."""
    if not category_name:
        return []
        
    url = f"{WOOCOMMERCE_URL}/wp-json/wc/v3/products/categories"
    auth = (WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET)
    
    # Search
    resp = requests.get(url, auth=auth, params={"search": category_name})
    resp.raise_for_status()
    categories = resp.json()
    
    if categories:
        for cat in categories:
            if cat["name"].lower() == category_name.lower():
                return [{"id": cat["id"]}]
        return [{"id": categories[0]["id"]}]
        
    # Create new
    print(f"Creating new category: {category_name}")
    resp = requests.post(url, auth=auth, json={"name": category_name})
    resp.raise_for_status()
    return [{"id": resp.json()["id"]}]

def resolve_brand(brand_name):
    """Find or create a WooCommerce brand."""
    if not brand_name:
        return []
        
    url = f"{WOOCOMMERCE_URL}/wp-json/wc/v3/products/brands"
    auth = (WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET)
    
    # Search
    resp = requests.get(url, auth=auth, params={"search": brand_name})
    resp.raise_for_status()
    brands = resp.json()
    
    if brands:
        for b in brands:
            if b["name"].lower() == brand_name.lower():
                return [{"id": b["id"]}]
        return [{"id": brands[0]["id"]}]
        
    # Create new
    print(f"Creating new brand: {brand_name}")
    resp = requests.post(url, auth=auth, json={"name": brand_name})
    resp.raise_for_status()
    return [{"id": resp.json()["id"]}]

def import_products():
    excel_file = "Products.xlsx"
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    print("=" * 60)
    print(f"STEP 1: Reading {excel_file}")
    print("=" * 60)
    
    # Load workbook and active sheet
    wb = openpyxl.load_workbook(excel_file)
    ws = wb.active
    
    # We assume headers are in row 1: URL, Category, Brand, Status
    # Iterating through rows starting from row 2
    for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        url = row[0].value
        category_name = row[1].value
        brand = row[2].value
        status = row[3].value
        
        if not url:
            continue
            
        if status == "Uploaded":
            print(f"Skipping {url} (already Uploaded)")
            continue
            
        print("\n" + "=" * 60)
        print(f"Processing row {row_idx}: {url}")
        
        try:
            # Scrape
            product_data = scrape_product(url)
            
            # Generate description
            ai_description = generate_description(product_data["name"])
            
            print("Uploading to WooCommerce...")
            
            woo_payload = {
                "name": product_data["name"],
                "type": "simple",
                "status": "publish",
                "description": ai_description,
                "regular_price": product_data["regular_price"],
                "sale_price": product_data["sale_price"],
                "images": [{"src": img} for img in product_data["images"]]
            }
            
            # Resolve category
            if category_name:
                category_info = resolve_category(category_name)
                if category_info:
                    woo_payload["categories"] = [{"id": category_info[0]["id"]}]
                    
            # Resolve brand
            if brand:
                brand_info = resolve_brand(brand)
                if brand_info:
                    woo_payload["brands"] = [{"id": brand_info[0]["id"]}]
                
            woo_url = f"{WOOCOMMERCE_URL}/wp-json/wc/v3/products"
            resp = requests.post(
                woo_url, 
                auth=(WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET),
                json=woo_payload
            )
            
            if resp.status_code in (200, 201):
                created_product = resp.json()
                print(f"[OK] Success! Product created with ID: {created_product['id']}")
                
                # Update status in Excel and save immediately
                row[3].value = "Uploaded"
                wb.save(excel_file)
                print(f"Updated status for row {row_idx} to Uploaded in {excel_file}")
            else:
                print(f"[ERROR] Failed to create product. Status: {resp.status_code}")
                print(resp.text)
                
        except Exception as e:
            print(f"[ERROR] Error processing {url}: {e}")

if __name__ == "__main__":
    import_products()
