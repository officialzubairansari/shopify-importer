import requests, re
url = 'https://bagallery.com/collections/lattafa/products/lattafa-opulent-dubai-edp-100ml'
text = requests.get(url).text
vendors = set(re.findall(r'"vendor"\s*:\s*"([^"]+)"', text, flags=re.IGNORECASE))
brands = set(re.findall(r'"brand"\s*:\s*"([^"]+)"', text, flags=re.IGNORECASE))
print("Vendors found:", vendors)
print("Brands found:", brands)
