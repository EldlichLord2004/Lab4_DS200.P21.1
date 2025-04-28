import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin

def scrape_character_images(url):
    # Lấy tên nhân vật từ URL
    character_name = url.split('/')[-2]
    
    # Tạo thư mục Ảnh và thư mục con cho nhân vật
    save_dir = os.path.join("Ảnh", character_name)
    os.makedirs(save_dir, exist_ok=True)
    
    # Gửi yêu cầu HTTP và lấy nội dung trang
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Lỗi: Không thể truy cập URL. Mã lỗi: {response.status_code}")
        return
    
    # Phân tích HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Tìm phần Card Images bằng ID chính xác
    card_images_span = soup.find('span', {'id': 'Card_Images'})
    card_images_section = None
    
    if card_images_span:
        # Nếu tìm thấy span, lấy phần tử cha (h2 hoặc h3)
        card_images_section = card_images_span.parent
    else:
        # Thử tìm kiếm theo cả tiêu đề nếu không tìm thấy bằng ID
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.text.strip()
            if "Card Images" in heading_text or "Card  Images" in heading_text:
                card_images_section = heading
                break
    
    if not card_images_section:
        print("Không tìm thấy phần Card Images trên trang")
        return
    
    # Tìm tất cả các gallery trên trang
    galleries = soup.find_all('div', class_='wikia-gallery')
    image_container = None
    
    # Phương pháp 1: Tìm gallery ngay sau tiêu đề Card Images
    current = card_images_section
    while current and not image_container:
        current = current.next_sibling
        if current and current.name == 'div' and 'wikia-gallery' in current.get('class', []):
            image_container = current
            break
    
    # Phương pháp 2: Nếu không tìm thấy, lấy gallery thứ hai nếu có
    if not image_container and len(galleries) > 1:
        # Thường gallery đầu tiên là danh sách card, gallery thứ hai là card images
        image_container = galleries[1]
    elif not image_container and galleries:
        # Nếu chỉ có một gallery, dùng gallery đó
        image_container = galleries[0]
    
    # Phương pháp 3: Tìm tất cả các ảnh ở giữa tiêu đề này và tiêu đề tiếp theo
    if not image_container:
        next_heading = None
        all_headings = soup.find_all(['h2', 'h3'])
        
        for i, heading in enumerate(all_headings):
            if heading == card_images_section and i < len(all_headings) - 1:
                next_heading = all_headings[i + 1]
                break
        
        images = []
        current = card_images_section
        
        while current and current != next_heading:
            current = current.next_element
            if current and current.name == 'img':
                images.append(current)
            elif current and hasattr(current, 'find_all'):
                images.extend(current.find_all('img'))
                
        if not images:
            print("Không tìm thấy ảnh nào trong phần Card Images")
            return
    else:
        images = image_container.find_all('img')
    
    # Tải và lưu các ảnh
    count = 0
    for img in images:
        # Lấy URL của ảnh gốc (có độ phân giải cao)
        img_url = img.get('src') or img.get('data-src')
        if img_url:
            # Bỏ qua các ảnh base64 hoặc ảnh placeholder
            if img_url.startswith('data:image/gif;base64'):
                continue
                
            # Chuyển sang URL có độ phân giải cao nếu có thể
            img_url = re.sub(r'/scale-to-width-down/\d+', '', img_url)
            img_url = urljoin(url, img_url)
            
            # Lấy tên file
            filename = os.path.join(save_dir, f"{character_name}_card_{count}.jpg")
            
            try:
                # Tải ảnh
                img_data = requests.get(img_url).content
                
                # Lưu ảnh
                with open(filename, 'wb') as file:
                    file.write(img_data)
                
                print(f"Đã tải: {filename}")
                count += 1
            except Exception as e:
                print(f"Lỗi khi tải ảnh {img_url}: {str(e)}")
    
    print(f"Đã tải tổng cộng {count} ảnh cho nhân vật {character_name}")

# Thử nghiệm với URL Asahina Mafuyu
if __name__ == "__main__":
    url = "https://projectsekai.fandom.com/wiki/Asahina_Mafuyu/Cards"
    scrape_character_images(url) 