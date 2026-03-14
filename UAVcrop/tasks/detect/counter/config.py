# https://docs.ultralytics.com/modes/

# Train
TRAIN_MODEL = "../../../models/yolo11x.pt"  # 预训练模型地址

# Train Settings
TRAIN_DATA = "data.yaml"
TRAIN_EPOCHS = 150
TRAIN_BATCH = 16
TRAIN_IMGSZ = 1024
TRAIN_SAVE = True
TRAIN_DEVICE = 2, 3
TRAIN_WORKERS = 8
TRAIN_SINGLE_CLS = False
TRAIN_PLOTS = True

# Predict

# 模型地址
MODEL_PATH = "models/yolo11x.pt"

# 测试图像
PREDICT_SOURCE = ""

# Inference arguments
PREDICT_CONF = 0.3
PREDICT_IOU = 0.4
PREDICT_MAX_DET = 1200

# Visualization arguments
PREDICT_SAVE = False
PREDICT_SHOW_LABELS = False
