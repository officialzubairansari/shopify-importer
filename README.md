# Shopify to WooCommerce Importer

This Python script automates the process of importing products from a Shopify store into a target WooCommerce site. It reads product URLs from an Excel file, scrapes the product details, generates a high-quality AI product description using Ollama or Google Gemini API, and publishes the product to WooCommerce.

> **Note**: Currently, this script only supports cloning **Simple Products**. Variable products are not supported yet.

## Features

- **Automated Scraping**: Fetches product details (name, prices, images) directly from a provided Shopify product URL.
- **AI Description Generation**: Uses either a local Ollama instance or the Google Gemini API to generate engaging, professional product descriptions tailored for e-commerce. You can switch between them in the `.env` file.
- **Category & Brand Management**: Automatically creates new categories and brands in WooCommerce if they don't exist.
- **Batch Processing**: Reads products from an Excel file (`Products.xlsx`) and keeps track of upload status, skipping already uploaded items so you can safely pause and resume.

## Prerequisites

Before running the script, ensure you have the following:

- **Python 3.7+**
- **WooCommerce Store**: With REST API enabled (Consumer Key and Consumer Secret).
- **Ollama or Gemini API**: Either Ollama running locally/via network, or a Google Gemini API Key.

## Installation

1. **Clone or Download the Repository**
2. **Create a Virtual Environment (Optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. **Install Dependencies**
   Install the required Python packages (e.g., `requests`, `openpyxl`, `python-dotenv`, `beautifulsoup4`, etc.). If you have a `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure you have installed packages like `requests`, `openpyxl`, `python-dotenv`, and any scraping libraries used in `scraper.py`)*

## Configuration

1. Create a `.env` file in the root directory of the project.
2. Add your configuration details as follows:

```env
WOOCOMMERCE_URL=https://your-woocommerce-site.com
WOOCOMMERCE_KEY=your_consumer_key_here
WOOCOMMERCE_SECRET=your_consumer_secret_here

OLLAMA_URL=http://localhost:11434  # Or your Ollama server IP
OLLAMA_MODEL=qwen3:4b              # Or any other model you have pulled

# AI Provider Settings
AI_PROVIDER=ollama                 # Options: ollama, gemini
GEMINI_API_KEY=your_gemini_key     # Required if AI_PROVIDER is set to gemini
```

## How to Use

1. **Prepare the Excel File**: 
   Ensure there is a file named `Products.xlsx` in the root directory. The file must have the following columns in the **first row**:
   - Column A: `URL` (Shopify product URL)
   - Column B: `Category` (Target WooCommerce category)
   - Column C: `Brand` (Target WooCommerce brand)
   - Column D: `Status` (Leave blank; the script updates this to "Uploaded" upon success)

2. **Run the Importer**:
   Execute the `importer.py` script:
   ```bash
   python importer.py
   ```

3. **Monitor Progress**:
   The script will log its progress in the terminal. It will skip any rows where the status is already marked as `Uploaded` in the Excel file.

## Known Limitations

- **Simple Products Only**: The script currently does not scrape or upload variations (sizes, colors, etc.). It uploads everything as a "simple" product type.
- **AI Generation Time**: Depending on your hardware and the Ollama model used (or Gemini API rate limits), generating descriptions may take some time. The script has a built-in 120-second timeout for AI requests.
