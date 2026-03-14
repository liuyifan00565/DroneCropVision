from ultralytics import YOLO
from PIL import Image
import cv2
import os
from pathlib import Path

# im1 = Image.open(r"E:\yolotrain\yolobiaoji\riceinput\compress\rice2\rice2_1_compress.jpg")
# # Load a COCO-pretrained YOLOv8n model
# model_path = "volov8n_best_50.pt"
# model = YOLO(model_path)
#
# results = model.predict(source=im1, save=True)
#
# result = results[0]
# coord = []
# for box in result.boxes:
#     xyxy = box.xyxy[0]
#     xyxy_cpu = xyxy.cpu().tolist()
#     coord.append({'x_min': xyxy_cpu[0], 'y_min': xyxy_cpu[1], 'x_max': xyxy_cpu[2], 'y_max': xyxy_cpu[3]})


def drawdot_img(coordinates, input_img_path, write_img_path):
    # 读取了一张图像到 img 中
    img = cv2.imread(input_img_path,cv2.IMREAD_COLOR +cv2.IMREAD_IGNORE_ORIENTATION)

    color = (256, 0, 0)  # 使用蓝色
    thickness = -1  # 框的厚度，-1为填充
    # 逐个绘制
    for coord in coordinates:
        x, y, x2, y2 = int(coord["x_min"]), int(coord["y_min"]), int(coord["x_max"]), int(coord["y_max"])

        # 圆心坐标
        cx, cy = (x + x2) // 2, (y + y2) // 2

        # 绘制实心圆
        cv2.circle(img, center=(cx, cy), radius=5, color=color, thickness=thickness)
    # 显示图像
    # output_path = 'riceoutput_v8n_2_1.jpg'
    cv2.imwrite(write_img_path, img)


if __name__ == "__main__":
    test_dir = "/home/bdhapp/shuli_01/test_img/img/test_multis"
    write_dir = "/home/bdhapp/shuli_01/test_img/output/11s_multi_test1"
    write_dir_path = Path(write_dir)
    if not write_dir_path.is_dir():
        write_dir_path.mkdir()
    # Load a COCO-pretrained YOLOv8n model
    model_type = "yolov11s"
    model_path = "/home/bdhapp/shuli_01/test_img/img/best.pt"
    model = YOLO(model_path)
    for img_name in os.listdir(test_dir):
        img_path = os.path.join(test_dir, img_name)
        write_path = os.path.join(write_dir, f"{model_type}_{img_name}")
        img = Image.open(img_path)

        results = model.predict(source=img, device=2,save=False, conf=0.3, iou=0.4, imgsz=1024, max_det=1000)
        result = results[0]
        # result.save_txt("/home/bdhapp/shuli/saved_txt/test1/test1.txt")
        print(len(results))
        coord = []

        for box in result.boxes:
            xyxy = box.xyxy[0]
            xyxy_cpu = xyxy.cpu().tolist()
            coord.append({'x_min': xyxy_cpu[0], 'y_min': xyxy_cpu[1], 'x_max': xyxy_cpu[2], 'y_max': xyxy_cpu[3]})
            drawdot_img(coord, img_path, write_path)
