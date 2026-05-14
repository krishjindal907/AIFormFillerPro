import requests
from bs4 import BeautifulSoup
import json

url = 'https://docs.google.com/forms/d/e/1FAIpQLSecRuuaZY0HP8eD0o7tafp4Pr1S2Mrq2_BwrTf-Nn4XW2MsoA/viewform?usp=header'
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(res.text, 'html.parser')

forms = soup.find_all('form')
print("Forms:", len(forms))

if forms:
    target = forms[0]
    els = target.find_all(['input', 'select', 'textarea'])
    print("Total els:", len(els))
    results = []
    
    for el in els:
        el_type = el.name if el.name != 'input' else el.get('type', 'text')
        name = el.get('name', '')
        
        is_google_form = True
        is_google_entry = is_google_form and el_type == 'hidden' and name.startswith('entry.')
        
        if el_type in ['hidden', 'submit', 'button', 'reset', 'file'] and not is_google_entry:
            continue
        
        heading = el.find_previous(attrs={"role": "heading"})
        lbl = heading.get_text(strip=True) if heading else ''
        
        # also test picking up ANY div with class holding text
        parent_item = el.find_parent(attrs={"role": "listitem"})
        item_text = parent_item.get_text(separator=' | ', strip=True) if parent_item else ''
        
        results.append({
            "tag": el.name,
            "type": el_type,
            "name": name,
            "role_lbl": lbl,
            "item_text": item_text[:100] # truncate
        })
        
    print(json.dumps(results, indent=2))
