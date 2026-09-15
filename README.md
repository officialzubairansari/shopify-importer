# Shopify to WooCommerce Importer

A fast, automated script to clone products from any Shopify store directly into your WooCommerce site.

## What it does
- **Scrapes Shopify**: Pulls the product name, price, brand, and images directly from a Shopify link.
- **AI Descriptions**: Uses Google Gemini (or Ollama) to automatically write a professional, engaging product description.
- **Uploads to WooCommerce**: Creates the product, creates missing categories/brands, and uploads the images automatically.
- **Smart Resuming**: Automatically skips products that are already uploaded.

### Data Mapping
Here is exactly what gets inserted into your WooCommerce site and where it comes from:

| WooCommerce Field | Source | Details |
| :--- | :--- | :--- |
| **Product Name** | Scraped (Shopify) | Extracted from the Shopify page title or metadata. |
| **Regular Price** | Scraped (Shopify) | Extracted from Shopify's variant data or JSON-LD. |
| **Sale Price** | Scraped (Shopify) | Extracted from Shopify's variant data or JSON-LD. |
| **Images** | Scraped (Shopify) | Pulls the main image and gallery images directly from Shopify's CDN. |
| **Brand** | Configurable | Set in `Products.xlsx`. Can be scraped, omitted, or custom text. |
| **Description** | Configurable | Set in `Products.xlsx`. Can be AI Generated, scraped, or omitted. |
| **Category** | Excel File | Read from Column B in your `Products.xlsx` file. |
| **Product Type** | Hardcoded | Always set to `simple` product. |
| **Status** | Hardcoded | Always set to `publish` (live on your store). |

> **Note:** Currently supports **Simple Products** only (no variations).

---

## 1. Setup

1. Make sure you have **Python 3.7+** installed.
2. Install the required libraries:
   ```bash
   pip install requests openpyxl python-dotenv beautifulsoup4 lxml
   ```
3. Create a `.env` file in this folder and add your API keys:
   ```env
   WOOCOMMERCE_URL=https://your-woocommerce-site.com
   WOOCOMMERCE_KEY=your_consumer_key
   WOOCOMMERCE_SECRET=your_consumer_secret

   # Choose 'gemini' or 'ollama'
   AI_PROVIDER=gemini                 
   GEMINI_API_KEY=your_gemini_api_key

   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=qwen3:4b
   ```

## 2. Prepare your Excel File
Create a `Products.xlsx` file in the same folder with **exactly 5 columns** in the first row:
- **Column A:** `URL` (The Shopify product link)
- **Column B:** `Category` (The WooCommerce category you want it in)
- **Column C:** `Brand` (`Default` to scrape it, leave blank for none, or type a custom brand name).
- **Column D:** `Product Description` (`AI` to write an AI description, `Default` to use the original scraped text, leave blank for none).
- **Column E:** `Status` (Leave this blank. The script will write "Uploaded" here when done).

## 3. Run the Importer
Run the script from your terminal:
```bash
python importer.py
```

The script will handle the rest! If it gets interrupted, just run it again—it will safely skip any products marked as "Uploaded" in your Excel file.
