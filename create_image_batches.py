import os
import shutil
import numpy as np
import pickle
from PIL import Image
import io

def create_batches(source_dir, output_dir, num_batches=5, test_batch=True):
    """
    Create batches from image folders
    
    Args:
        source_dir: Directory containing 'train' and 'val' folders
        output_dir: Directory to save batches
        num_batches: Number of training batches to create
        test_batch: Whether to create a test batch from validation data
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all classes from train directory
    train_dir = os.path.join(source_dir, 'train')
    classes = sorted([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))])
    
    # Create a mapping from class name to index
    class_to_idx = {classes[i]: i for i in range(len(classes))}
    
    # Create metadata file
    metadata = {
        'num_cases_per_batch': 0,  # Will be updated later
        'label_names': classes
    }
    
    # Collect all training images and their labels
    train_images = []
    train_labels = []
    
    for class_name in classes:
        class_dir = os.path.join(train_dir, class_name)
        class_idx = class_to_idx[class_name]
        
        for img_name in os.listdir(class_dir):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(class_dir, img_name)
                try:
                    # Load and convert image to bytes
                    with Image.open(img_path) as img:
                        img = img.convert('RGB')  # Ensure RGB format
                        img_data = img.resize((32, 32))  # Resize to a standard size
                        
                        # Convert image to numpy array
                        img_array = np.array(img_data)
                        
                        train_images.append(img_array)
                        train_labels.append(class_idx)
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
    
    # Convert to numpy arrays
    train_images = np.array(train_images)
    train_labels = np.array(train_labels)
    
    # Shuffle the data
    indices = np.arange(len(train_images))
    np.random.shuffle(indices)
    train_images = train_images[indices]
    train_labels = train_labels[indices]
    
    # Calculate images per batch
    images_per_batch = len(train_images) // num_batches
    metadata['num_cases_per_batch'] = images_per_batch
    
    # Save metadata
    with open(os.path.join(output_dir, 'batches.meta'), 'wb') as f:
        pickle.dump(metadata, f)
    
    # Create and save training batches
    for i in range(num_batches):
        start_idx = i * images_per_batch
        end_idx = (i + 1) * images_per_batch if i < num_batches - 1 else len(train_images)
        
        batch_data = {
            'data': train_images[start_idx:end_idx],
            'labels': train_labels[start_idx:end_idx].tolist()
        }
        
        with open(os.path.join(output_dir, f'data_batch_{i+1}'), 'wb') as f:
            pickle.dump(batch_data, f)
        
        print(f"Created data_batch_{i+1} with {end_idx - start_idx} images")
    
    # Create test batch from validation data if requested
    if test_batch:
        val_dir = os.path.join(source_dir, 'val')
        test_images = []
        test_labels = []
        
        for class_name in classes:
            class_dir = os.path.join(val_dir, class_name)
            if not os.path.exists(class_dir):
                continue
                
            class_idx = class_to_idx[class_name]
            
            for img_name in os.listdir(class_dir):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(class_dir, img_name)
                    try:
                        with Image.open(img_path) as img:
                            img = img.convert('RGB')
                            img_data = img.resize((32, 32))
                            img_array = np.array(img_data)
                            
                            test_images.append(img_array)
                            test_labels.append(class_idx)
                    except Exception as e:
                        print(f"Error processing {img_path}: {e}")
        
        # Convert to numpy arrays
        test_images = np.array(test_images)
        test_labels = np.array(test_labels)
        
        # Save test batch
        test_batch_data = {
            'data': test_images,
            'labels': test_labels.tolist()
        }
        
        with open(os.path.join(output_dir, 'test_batch'), 'wb') as f:
            pickle.dump(test_batch_data, f)
        
        print(f"Created test_batch with {len(test_images)} images")

    # Create a simple readme file
    with open(os.path.join(output_dir, 'readme.html'), 'w') as f:
        f.write(f"""
        <html>
        <head><title>Image Batches</title></head>
        <body>
        <h1>Image Batches</h1>
        <p>This dataset contains {len(classes)} classes:</p>
        <ul>
        {"".join(f"<li>{cls}</li>" for cls in classes)}
        </ul>
        <p>Number of training batches: {num_batches}</p>
        <p>Images per batch: {images_per_batch}</p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    # Update these paths to match your directory structure
    source_directory = "D:\\file ht\\PTDLL\\Tài liệu thực hành-22521522\\Lab 4\\Ảnh"
    output_directory = "D:\\file ht\\PTDLL\\Tài liệu thực hành-22521522\\Lab 4\\Anh_batchbatch"
    
    create_batches(source_directory, output_directory, num_batches=5, test_batch=True)
    print("Batch creation completed!")