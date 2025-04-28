import requests
from bs4 import BeautifulSoup

url = "https://projectsekai.fandom.com/wiki/Asahina_Mafuyu/Cards"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Kiểm tra tất cả các tiêu đề để tìm phần "Card Images"
print("=== Tìm kiếm các tiêu đề ===")
for heading in soup.find_all(['h2', 'h3']):
    print(f"Tiêu đề: {heading.text.strip()}")
    if heading.find('span', class_='mw-headline'):
        print(f"  - ID: {heading.find('span', class_='mw-headline').get('id')}")
    
# Tìm kiếm thẻ span với class="mw-headline" và id="Card_Images"
print("\n=== Tìm kiếm trực tiếp ===")
card_images_span = soup.find('span', {'id': 'Card_Images'})
print(f"Kết quả tìm trực tiếp bằng ID: {card_images_span}")

card_images_span_by_class = soup.find('span', class_='mw-headline', string="Card Images")
print(f"Kết quả tìm bằng class và text: {card_images_span_by_class}")

# In ra thông tin về thẻ div chứa các thẻ gallery
print("\n=== Tìm kiếm gallery ===")
galleries = soup.find_all('div', class_='wikia-gallery')
print(f"Số lượng gallery tìm thấy: {len(galleries)}")
for i, gallery in enumerate(galleries):
    print(f"Gallery {i+1} - ID: {gallery.get('id')}") 