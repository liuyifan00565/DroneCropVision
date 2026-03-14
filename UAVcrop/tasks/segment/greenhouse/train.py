import torch
from ultralytics import YOLO
import config

print('__file__: ', __file__)

DEVICE = (config.TRAIN_DEVICE if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
print('device: ', DEVICE)

# 训练模型地址
model_path = config.TRAIN_MODEL
model = YOLO(model_path)

# 训练方法（yaml文件地址，循环次数，图片大小，设备）
train_result = model.train(data=config.TRAIN_DATA, epochs=config.TRAIN_EPOCHS, batch=config.TRAIN_BATCH,
                           imgsz=config.TRAIN_IMGSZ, save=config.TRAIN_SAVE, device=DEVICE,
                           workers=config.TRAIN_WORKERS, plots=config.TRAIN_PLOTS)
