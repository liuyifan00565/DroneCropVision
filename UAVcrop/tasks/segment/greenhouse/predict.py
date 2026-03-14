from ultralytics import YOLO
import cv2
import numpy as np
import config

model = YOLO(config.MODEL_PATH)

img = cv2.imread("/Users/caiwei/Desktop/yolo_results/greenhouse/test/picture18.jpg")

yolo_classes = list(model.names.values())
classes_ids = [yolo_classes.index(clas) for clas in yolo_classes]

conf = 0.3

results = model.predict(img, conf=conf, save=True, imgsz=1024, iou=0.6)
# '大棚':0, '水印':1, '作物':2, '过道':3
colors = [(0, 0, 255),    # 红色 -> 大棚
    (255, 0, 0),    # 蓝色 -> 水印
    (0, 255, 0),      # 绿色 -> 作物
    (0, 201, 238), ]      # 黄色 -> 过道 

# 创建掩码图层，用于存储绘制的掩码
overlay = img.copy()

for result in results:
    for mask, box, class_id in zip(result.masks.xy, result.boxes, result.boxes.cls):
        points = np.int32([mask])
        # cv2.polylines(img, points, True, (255, 0, 0), 1)
        color_number = classes_ids.index(int(class_id))
        cv2.fillPoly(img, points, colors[color_number])

    alpha = 0.5  # 透明度参数，值在 0 到 1 之间，值越小颜色越淡
    # 混合原图与掩码图层
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    output_path = "segmented_image.png"
    cv2.imwrite(output_path, img)