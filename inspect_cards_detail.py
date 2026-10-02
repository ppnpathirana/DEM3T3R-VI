from bs4 import BeautifulSoup

with open('dist/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

left_col = soup.find('aside') or soup.find('div', class_=lambda c: c and 'w-80' in c) or soup.find('main')
print("Left column / cards found:")
for div in soup.find_all('div', class_=lambda c: c and ('frost-card' in c or 'card-bg' in c)):
    txt = div.get_text(" ", strip=True)[:100]
    print(" -", txt)
