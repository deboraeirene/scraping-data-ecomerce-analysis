
import json
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime
import unicodedata

general_pattern = r'\b(\d+(?:\.\d+)?)\s*?([a-zA-Z]+)\b'

def extract_units_as_string_original_case(text: str) -> str:
    supported_units = [
        'ml', 'l', 'oz', 'cl', 'cc', 'gal', 'qt', 'pt',
        'kg', 'g', 'mg', 'lb',
        'km', 'm', 'cm', 'mm'
    ]
    
    units_pattern_part = '|'.join(supported_units)
    
    pattern = re.compile(
        r'\b'
        r'(?:\d+[xX])?'
        r'(?:\d+(?:\.\d+)?)'
        r'\s*'
        r'(?:' + units_pattern_part + ')'
        r'\b',
        re.IGNORECASE
    )
    
    matches = pattern.findall(text)
    
    cleaned_matches = [''.join(m.split()) for m in matches]
    
    return " ".join(cleaned_matches)


def parse_tokopedia(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    product_cards = soup.find_all('a', class_='Ui5-B4CDAk4Cv-cjLm4o0g==')

    for card in product_cards:
        product = {}
        product['id'] = None
        
        name_tag = card.find('span', class_='+tnoqZhn89+NHUA43BpiJg==')
        product['name'] = ' '.join(name_tag.text.strip().split()) if name_tag else None
        product['name'] = unicodedata.normalize('NFKC', product['name'])

        price_tag = card.find('div', class_='urMOIDHH7I0Iy1Dv2oFaNw==') or card.find('span', class_='YZHqvX+8TVU2YltRC9S+oA==')
        if price_tag:
            try:
                product['price'] = int(price_tag.text.strip().replace('Rp', '').replace('.', ''))
            except (ValueError, AttributeError):
                product['price'] = None
        else:
            product['price'] = None
            
        original_price_tag = card.find('span', class_='hC1B8wTAoPszbEZj80w6Qw==')
        if original_price_tag:
            try:
                product['originalprice'] = int(original_price_tag.text.strip().replace('Rp', '').replace('.', ''))
            except (ValueError, AttributeError):
                product['originalprice'] = None
        else:
            product['originalprice'] = product['price']
        
        product['discountpercentage'] = ((product['originalprice'] - product['price']) / product['originalprice']) * 100
        product['discountpercentage'] = round(product['discountpercentage'], 2)

        rating_tag = card.find('span', class_='_2NfJxPu4JC-55aCJ8bEsyw==')
        product['rating'] = float(rating_tag.text.strip()) if rating_tag else 0.00
        
        
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        matches = extract_units_as_string_original_case(product['name'])
        
        product_slug = None

        image_tag = card.find('img', alt='product-image')

        if image_tag:
            anchor_tag = image_tag.find_parent('a')
            
            if anchor_tag and anchor_tag.has_attr('href'):
                href = anchor_tag['href']
                
                parsed_url = urlparse(href)
                path = parsed_url.path
                
                product_slug = path.split('/')[-1]
                
            else:
                print("Could not find a parent <a> tag with an href.")
        else:
            print("Could not find the anchor image with alt='product-image'.")
        
        product['detail'] = matches or ""
        product['platform'] = "www.tokopedia.com"
        product['productmasterid'] = product_slug
        product['createdat'] = today

        products.append(product)
        
    return products

def parse_blibli(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    product_cards = soup.find_all('div', class_='product-list__card')

    for card in product_cards:
        product = {}
        product['id'] = None
        
        name_tag = card.find('span', class_='els-product__title')
        product['name'] = ' '.join(name_tag.text.strip().split()) if name_tag else None
        product['name'] = unicodedata.normalize('NFKC', product['name'])
        product['name'] = product['name'].replace('\u200b', '')

        price_tag = card.find('div', class_='els-product__fixed-price')
        if price_tag:
            try:
                product['price'] = int(price_tag.text.strip().replace('Rp', '').replace('.', ''))
            except (ValueError, AttributeError):
                product['price'] = None
        else:
            product['price'] = 0
            
        original_price_tag = card.find('span', class_='els-product__discount-price')
        if original_price_tag:
            try:
                product['originalprice'] = int(original_price_tag.text.strip().replace('.', ''))
            except (ValueError, AttributeError):
                product['originalprice'] = None
        else:
            product['originalprice'] = product['price']
            
        discount_tag = card.find('div', class_='els-promo-label__text')
        if discount_tag:
            try:
                product['discountpercentage'] = float(re.search(r'(\d+)', discount_tag.text).group(1))
            except (ValueError, AttributeError):
                product['discountpercentage'] = None
        else:
            product['discountpercentage'] = 0

        rating_tag = card.find('div', class_='els-product__rating-wrapper')
        if rating_tag:
            rating_text = rating_tag.text.strip().replace(',', '.')
            try:
                product['rating'] = float(rating_text)
            except (ValueError, AttributeError):
                product['rating'] = 0.00
        else:
            product['rating'] = 0.00
            
        product_anchor_tag = card.select_one('a[id^="product-card__"]')
        product_id = None
        if product_anchor_tag:
            full_id = product_anchor_tag.get('id')
            
            try:
                product_id = full_id.split('__')[1]
            except IndexError:
                product_id = None
        
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        matches = extract_units_as_string_original_case(product['name'])
        
        product['detail'] = matches or ""
        product['platform'] = "www.blibli.com"
        product['productmasterid'] = product_id
        product['createdat'] = today

        products.append(product)
        
    return products

def parse_klikindomaret(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []
    product_cards = soup.find_all('div', class_='card-product')

    for card in product_cards:
        product = {}
        product['id'] = None
        
        name_tag = card.find('h2', class_='md-0 line-clamp-2 text-b1 text-neutral-70 des:mb-2')
        product['name'] = ' '.join(name_tag.text.strip().split()) if name_tag else None
        product['name'] = unicodedata.normalize('NFKC', product['name'])

        price_tag = card.find('div', class_='price')
        if price_tag:
            try:
                product['price'] = int(price_tag.text.strip().replace('&nbsp;','').replace('Rp', '').replace('.', ''))
            except (ValueError, AttributeError):
                product['price'] = None
        else:
            product['price'] = None
        
        product['originalprice'] = product['price']
        product['discountpercentage'] = 0.00
        product['rating'] = 0.00
        
        today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        matches = extract_units_as_string_original_case(product['name'])
        
        product_link_tag = card.select_one('a[href*="/xpress/"]')
        if product_link_tag:
            href = product_link_tag.get('href')
            
            try:
                slug = href.split('/')[-1]

            except (IndexError, AttributeError):
                print("Could not parse the product ID from the href.")
        else:
            print("Could not find the product link tag.")
        
        product['detail'] = matches or ""
        product['platform'] = "www.klikindomaret.com"
        product['productmasterid'] = slug
        product['createdat'] = today

        products.append(product)
        
    return products

all_products = []

print("Processing 'tokopedia' directory...")
tokopedia_dir = Path('tokopedia/')
if tokopedia_dir.is_dir():
    for html_file in tokopedia_dir.glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        all_products.extend(parse_tokopedia(html_content))

print("Processing 'blibli' directory...")
blibli_dir = Path('blibli/')
if blibli_dir.is_dir():
    for html_file in blibli_dir.glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        all_products.extend(parse_blibli(html_content))

print("Processing 'klikindomaret' directory...")
klikindomaret_dir = Path('klikindomaret/')
if klikindomaret_dir.is_dir():
    for html_file in klikindomaret_dir.glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        all_products.extend(parse_klikindomaret(html_content))


for i, product in enumerate(all_products):
    product['id'] = i + 1

output = {"products": all_products}
output_filename = 'products.json'

with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nProcessing complete. Data saved to '{output_filename}'.")
