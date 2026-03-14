'''
时间: 2025-04-26
版本: 1.0.0
作者: luogy
'''

from ultralytics import YOLO

# Load a COCO-pretrained YOLOv8n model
model_path = "/home/bdhapp/lgy/yolo/model/yolo11s.pt"
model = YOLO(model_path)

# Train the model on the COCO8 example dataset for 100 epochs
model.train(data="/home/bdhapp/lgy/yolo/data.yaml", epochs=200, \
            imgsz=1024,                 # 提高图像分辨率以检测小物体
            batch=16,                   # 批次大小
            device=4,                   # 使用GPU设备pyth
            rect=True,                  # 启用矩形训练，减少图像填充损失
            mosaic=1.0,                 # 启用马赛克数据增强，增加复杂场景
            mixup=0.5,                  # 启用混合数据增强，处理物体遮挡
            scale=0.5,                  # 启用缩放，模拟不同距离的小物体
            translate=0.1,              # 启用平移增强，模拟部分可见物体
            copy_paste=0.3)             # 启用复制粘贴，处理重叠小物体imgsz=640,device=0)
