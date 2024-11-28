# detect.py
import os
from ultralytics import YOLO
import cv2
import numpy as np

def run_detection(input_image_path, output_dir):
    # Load model
    model = YOLO("model/weights/best.pt")
    results = model(input_image_path)

    # Extract the image name from the input image path
    name = os.path.basename(input_image_path)
    image_name = f"masks-{name}"
    
    # Kiểm tra nếu kết quả không có masks
    masks = results[0].masks
    if masks is None:
        print("No masks detected")
        return "", False, [], [], 0, 0, 0
    
    save_dir = os.path.join(output_dir, os.path.splitext(name)[0]).replace('\\', '/')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Lưu ảnh gốc với mask
    full_image_save_path = os.path.join(save_dir, image_name).replace('\\', '/')
    result_image = results[0].plot(labels=False, boxes=False, masks=True)
    cv2.imwrite(full_image_save_path, result_image)
    
    # Đọc ảnh gốc và tính diện tích ảnh gốc
    original_image = cv2.imread(input_image_path)
    original_area = original_image.shape[0] * original_image.shape[1]

    percentages = []
    areas = []
    total_area = 0
    total_percentage = 0

    # Lặp qua từng mask và lưu chúng riêng biệt
    for idx, mask in enumerate(masks.xy): # masks.xy là list của các polygons

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
        
        # Tính tỷ lệ phần trăm diện tích
        mask_area = cv2.countNonZero(mask_image)
        percentage = (mask_area / original_area) * 100
        percentages.append(round(percentage, 2))
        areas.append(mask_area)

        # Tính tổng diện tích và tổng tỷ lệ phần trăm
        total_area += mask_area
        total_percentage += percentage
    
    total_percentage = round(total_percentage, 2)
    return save_dir, True, percentages, areas, total_area, total_percentage, original_area
