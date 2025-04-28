# import os
# import json
# import requests
# import random
# from pyspark.sql import SparkSession

# # Cấu hình đường dẫn Python cho PySpark
# os.environ['PYSPARK_PYTHON'] = r"C:/Users/TRIS/AppData/Local/Programs/Python/Python310/python.exe"
# os.environ['PYSPARK_DRIVER_PYTHON'] = r"C:/Users/TRIS/AppData/Local/Programs/Python/Python310/python.exe"

# # Khởi tạo SparkSession
# spark = SparkSession.builder.appName("ImageBatchSender") \
#     .config("spark.ui.port", "4050") \
#     .getOrCreate()

# # Đường dẫn đến thư mục chứa ảnh
# image_folder = "Anh/train"  # Thay đổi đường dẫn nếu cần

# # Đọc tất cả các file trong thư mục train và thêm label
# def read_images_with_labels(directory):
#     image_label_pairs = []
#     for root, dirs, files in os.walk(directory):
#         for file in files:
#             if file.endswith(".jpg") or file.endswith(".png"):  # Chỉ lấy file ảnh
#                 image_path = os.path.join(root, file)
#                 # Lấy label từ tên thư mục cha
#                 label = os.path.basename(os.path.dirname(image_path))
#                 image_label_pairs.append({"path": image_path, "label": label})
#     # Shuffle dữ liệu
#     random.shuffle(image_label_pairs)
#     if not image_label_pairs:
#         print("No images found in the directory.")  # Thông báo nếu không tìm thấy ảnh
#     else:
#         unique_labels = set(item['label'] for item in image_label_pairs)
#         print(f"Unique labels: {unique_labels}")  # In ra các lớp duy nhất
#     return image_label_pairs

# # Chia danh sách đường dẫn thành các batch với label
# def create_batches_with_labels(image_label_pairs, batch_size=20):  # Giảm batch_size xuống 20
#     return [image_label_pairs[i:i + batch_size] for i in range(0, len(image_label_pairs), batch_size)]

# # Gửi batch đến server
# def send_batch_to_server(batch, server_url):
#     print(f"Batch to send: {batch}")  # In ra batch trước khi gửi
#     data = {"batch": batch}
#     response = requests.post(server_url, json=data)
#     if response.status_code == 200:
#         print(f"Sent batch of size {len(batch)} successfully")
#     else:
#         print(f"Failed to send batch. Status code: {response.status_code}")
#         print(f"Response from server: {response.text}")  # In ra phản hồi từ server

# # Main function
# if __name__ == "__main__":
#     # Đọc tất cả các file trong thư mục train và thêm label
#     image_label_pairs = read_images_with_labels(image_folder)

#     # Chia thành các batch với label
#     batches = create_batches_with_labels(image_label_pairs, batch_size=200)

#     # Địa chỉ server
#     server_url = "http://localhost:5000/receive_batch"

#     # Gửi từng batch đến server
#     for batch in batches:
#         send_batch_to_server(batch, server_url)

import os
import json
import requests
from pyspark.sql import SparkSession

# Cấu hình đường dẫn Python cho PySpark
os.environ['PYSPARK_PYTHON'] = r"C:/Users/TRIS/AppData/Local/Programs/Python/Python310/python.exe"
os.environ['PYSPARK_DRIVER_PYTHON'] = r"C:/Users/TRIS/AppData/Local/Programs/Python/Python310/python.exe"

# Khởi tạo SparkSession
spark = SparkSession.builder \
    .appName("ImageBatchSender") \
    .config("spark.ui.port", "4050") \
    .getOrCreate()

# Đường dẫn đến thư mục chứa ảnh
image_folder = "Anh/train"  # Thay đổi đường dẫn nếu cần

# Đọc tất cả các file trong thư mục train và thêm label
def read_images_with_labels(directory):
    image_label_pairs = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".jpg") or file.endswith(".png"):  # Chỉ lấy file ảnh
                image_path = os.path.join(root, file)
                # Lấy label từ tên thư mục cha
                label = os.path.basename(os.path.dirname(image_path))
                image_label_pairs.append({"path": image_path, "label": label})
    return image_label_pairs

# Chuyển danh sách ảnh thành DataFrame PySpark
def create_spark_dataframe(image_label_pairs):
    # Tạo DataFrame từ danh sách ảnh
    df = spark.createDataFrame(image_label_pairs)
    return df

# Gửi batch đến server
def send_batch_to_server(batch, server_url):
    print(f"Batch to send: {batch}")  # In ra batch trước khi gửi
    data = {"batch": batch}
    response = requests.post(server_url, json=data)
    if response.status_code == 200:
        print(f"Sent batch of size {len(batch)} successfully")
    else:
        print(f"Failed to send batch. Status code: {response.status_code}")
        print(f"Response from server: {response.text}")  # In ra phản hồi từ server

# Main function
if __name__ == "__main__":
    # Đọc tất cả các file trong thư mục train và thêm label
    image_label_pairs = read_images_with_labels(image_folder)

    # Tạo DataFrame PySpark
    df = create_spark_dataframe(image_label_pairs)

    # Chia DataFrame thành các batch với label
    batch_size = 200  # Kích thước batch
    batches = [df.limit(batch_size).collect() for _ in range(0, df.count(), batch_size)]

    # Địa chỉ server
    server_url = "http://localhost:5000/receive_batch"

    # Gửi từng batch đến server
    for batch in batches:
        # Chuyển batch thành list dictionary
        batch_dict = [{"path": item["path"], "label": item["label"]} for item in batch]
        send_batch_to_server(batch_dict, server_url)