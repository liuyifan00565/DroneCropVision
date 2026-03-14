from ultralytics import YOLO
import config

model = YOLO(config.MODEL_PATH)

metrics = model.val(data=config.TRAIN_DATA, imgsz=config.TRAIN_IMGSZ, batch=config.TRAIN_BATCH, save_json=True,
                    conf=config.PREDICT_CONF, iou=config.PREDICT_IOU, max_det=config.PREDICT_MAX_DET,
                    device=config.TRAIN_DEVICE, plots=True)

print(metrics)
