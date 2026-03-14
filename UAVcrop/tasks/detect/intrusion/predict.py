## python版本：Python 3.10.14 (main, May  6 2024, 19:42:50) [GCC 11.2.0] on linux
from ultralytics import YOLO
from PIL import Image
import json
from io import BytesIO

model_path = "../../../models/yolo11s.pt"  # 模型地址
model = YOLO(model_path) # 加载模型
# [0, 1, 2, 3, 5, 6, 7] 0是人，1~7都是车，字典将车归为一类用1来标识
person_car_dict = {0:0, 1:1, 2:1, 3:1, 5:1, 6:1, 7:1} # 人车映射
res = [] # save

def yolo_detect(img_byte : bytes) -> str:
    img = Image.open(BytesIO(img_byte)) # 读取图片字节流
    res = []
    results = model.predict(source = img, save=False, conf=0.1) # 使用模型做推理
    for result in results:
        boxes = result.boxes
        confidences, class_ids = boxes.conf.tolist(), boxes.cls.int().tolist()
        rects = boxes.xyxy.int().tolist()
        res.append({'confidencs': confidences, 'class_ids': class_ids,'rects': rects})
    return json.dumps(res)

## 该函数输出
"""
[{"confidencs": [0.6119052767753601, 0.2301657497882843, 0.22618919610977173], 
"class_ids": [7, 0, 7], 
"rects": [[68, 53, 617, 237], [152, 88, 177, 116], [68, 53, 256, 237]]}]
confidencs代表置信度，class_ids为类别，rects为在图片绘制矩形的x1,y1,x2,y2坐标
数组中的一个json对象为一张图片
"""

## 该函数使用方式
with open('/home/bdhapp/shuli/runs/detect/predict16/car7.jpg', 'rb') as f:
    return_res = yolo_detect(f.read())
    print(return_res)

