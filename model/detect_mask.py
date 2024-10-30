# detect.py
import os
from ultralytics import YOLO
import cv2
import numpy as np

def run_detection(input_image_path, output_dir):
    # Load model
    model = YOLO("model/weights/best.pt")
    # Run inference
    results = model(input_image_path)
    # Extract the image name from the input image path
    name = os.path.basename(input_image_path)
    image_name = f"masks-{name}"
    
    # Kiểm tra nếu kết quả không có masks
    masks = results[0].masks  # Đây là object masks
    if masks is None:
        print("No masks detected")
        return "", False
    
    # Đường dẫn để lưu ảnh có mask
    save_dir = os.path.join(output_dir, os.path.splitext(name)[0]).replace('\\', '/')
    # Kiểm tra nếu thư mục không tồn tại thì tạo
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Đường dẫn để lưu ảnh full với mask
    full_image_save_path = os.path.join(save_dir, image_name).replace('\\', '/')
    # Vẽ mask và lưu vào file
    result_image = results[0].plot(labels=False, boxes=False, masks=True)
    # Lưu ảnh với mask
    cv2.imwrite(full_image_save_path, result_image)
    print(f"Full image saved at {full_image_save_path}")
    
    # Get the original image (for cropping purposes)
    original_image = cv2.imread(input_image_path)
    
    # Lặp qua từng mask và lưu chúng riêng biệt
    for idx, mask in enumerate(masks.xy):  # masks.xy là list của các polygons
        # Tạo ảnh mask trống (cùng kích thước với ảnh gốc)
        mask_image = np.zeros((original_image.shape[0], original_image.shape[1]), dtype=np.uint8)
        # Vẽ polygon lên ảnh trống
        cv2.fillPoly(mask_image, [mask.astype(np.int32)], 255)
        # Tạo ảnh đã được mask từ ảnh gốc
        masked_image = cv2.bitwise_and(original_image, original_image, mask=mask_image)
        # Lấy bounding box của polygon để crop ảnh cho khít
        x, y, w, h = cv2.boundingRect(mask.astype(np.int32))
        # Giới hạn tọa độ trong kích thước ảnh
        x_end = min(x + w, masked_image.shape[1])
        y_end = min(y + h, masked_image.shape[0])
        # Crop ảnh từ bounding box
        cropped_image = masked_image[y:y_end, x:x_end]
        # Lưu ảnh polygon
        cropped_image_path = os.path.join(save_dir, f"polygon_{idx}.png")
        cv2.imwrite(cropped_image_path, cropped_image)
        print(f"Polygon saved at {cropped_image_path}")
    
    return save_dir, True
