from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
import numpy as np
from PIL import Image
import os
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

app = Flask(__name__)

# Cấu hình đường dẫn Python cho PySpark
os.environ['PYSPARK_PYTHON'] = r"C:/Users/TRIS/AppData/Local/Programs/Python/Python310/python.exe"
os.environ['PYSPARK_DRIVER_PYTHON'] = r"C:/Users/TRIS/AppData/Local/Programs/Python/Python310/python.exe"

# Khởi tạo SparkSession với cấu hình tăng giới hạn task size
spark = SparkSession.builder \
    .appName("ImageBatchProcessor") \
    .config("spark.driver.memory", "16g") \
    .config("spark.executor.memory", "16g") \
    .config("spark.task.maxBytes", "2000000") \
    .getOrCreate()

# Tiền xử lý ảnh
def preprocess_image(image_path):
    try:
        image = Image.open(image_path)
        # Chuyển đổi sang định dạng RGB nếu cần
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image = image.resize((32, 32))  # Resize ảnh về kích thước cố định
        image_array = np.array(image) / 255.0  # Chuẩn hóa giá trị pixel
        return image_array
    except Exception as e:
        print(f"Error preprocessing {image_path}: {e}")
        return None

# Debugging: Kiểm tra kích thước ảnh
def check_image_shapes(image_label_pairs):
    for label, image in image_label_pairs:
        if image is not None:
            print(f"Image shape for {label}: {image.shape}")
        else:
            print(f"Invalid image for {label}")

# Endpoint để nhận batch từ client
@app.route('/receive_batch', methods=['POST'])
def receive_batch():
    try:
        # Lấy dữ liệu từ request
        data = request.json
        batch = data.get('batch', [])
        print(f"Received raw batch: {batch}")  # In ra dữ liệu nhận được

        # Kiểm tra và lọc dữ liệu hợp lệ
        valid_batch = []
        for item in batch:
            if isinstance(item, dict) and 'path' in item and 'label' in item:
                valid_batch.append(item)
            else:
                print(f"Invalid item in batch: {item}")

        if not valid_batch:
            return jsonify({"status": "error", "message": "No valid items in batch"}), 400

        print(f"Valid batch after filtering: {valid_batch}")  # In ra dữ liệu hợp lệ

        # Chuyển batch thành RDD
        rdd_images = spark.sparkContext.parallelize(valid_batch)

        # Tiền xử lý ảnh và trích xuất label
        preprocessed_rdd = rdd_images.map(lambda item: (item['label'], preprocess_image(item['path']))).filter(lambda x: x[1] is not None)

        # Kiểm tra kích thước ảnh
        preprocessed_data = preprocessed_rdd.collect()
        check_image_shapes(preprocessed_data)

        # Loại bỏ ảnh có kích thước không đồng nhất
        valid_preprocessed_rdd = spark.sparkContext.parallelize([
            (label, img) for label, img in preprocessed_data
            if img is not None and img.shape == (32, 32, 3)
        ])

        if valid_preprocessed_rdd.isEmpty():
            return jsonify({"status": "error", "message": "No valid images after preprocessing"}), 400

        # Chia tập dữ liệu thành train/test
        train_rdd, test_rdd = valid_preprocessed_rdd.randomSplit([0.8, 0.2], seed=42)

        # Chuyển RDD thành numpy array
        X_train = np.array([img for _, img in train_rdd.collect()])
        y_train = np.array([label for label, _ in train_rdd.collect()])

        X_test = np.array([img for _, img in test_rdd.collect()])
        y_test = np.array([label for label, _ in test_rdd.collect()])

        # Huấn luyện mô hình Logistic Regression
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train.reshape(X_train.shape[0], -1), y_train)

        # Đánh giá mô hình
        accuracy = model.score(X_test.reshape(X_test.shape[0], -1), y_test)
        print(f"Model accuracy: {accuracy}")

        # Lưu mô hình
        joblib.dump(model, 'best_model.pkl')

        # Trả về phản hồi thành công
        return jsonify({"status": "success", "message": "Model trained and saved", "accuracy": accuracy}), 200
    except Exception as e:
        print(f"Error processing batch: {e}")  # In lỗi để debug
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)