import requests
import config

# OLLAMA_URL = "http://192.168.1.50:11434"
# MODEL = "qwen3:4b"

product_name = "Lattafa Yara EDP 100ML"

prompt = f"""
You are an ecommerce product copywriter.

Product name:
{product_name}

Write a short product description.

Requirements:
- 40 to 60 words
- Professional ecommerce tone
- Suitable for a beauty and fragrance store
- Natural and attractive
- Do not invent fragrance notes
- Do not invent ingredients
- Do not invent specifications
- Do not make unsupported claims
- Do not mention Bagallery
- Do not mention AI
- No markdown
- No heading
- Return only the description
"""

response = requests.post(
    f"{config.OLLAMA_URL}/api/generate",
    json={
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    },
    timeout=120
)

response.raise_for_status()

data = response.json()

print("\nGenerated description:\n")
print(data["response"])