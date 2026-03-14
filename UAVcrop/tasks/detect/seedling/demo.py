from ultralytics import YOLO

"""
最新测试代码
"""

# model = YOLO(
#     '/Users/caiwei/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/jonathanc_c3dc/msg/file/2025-06/train5/weights/best.pt')
model = YOLO(
    '/Users/caiwei/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/jonathanc_c3dc/msg/file/2025-06/train5/weights/best.pt')
results = model([
    '/Users/caiwei/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/jonathanc_c3dc/msg/file/2025-06/尾山玉米标注250619/output_image_-_0_-_0.jpg',
    '/Users/caiwei/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/jonathanc_c3dc/msg/file/2025-06/尾山玉米标注250619/output_image_3_2_-_2048_-_8192.jpg'
],
    save=True, batch=8, imgsz=(2048, 2048), save_json=True, conf=0.25, iou=0.7, max_det=1000, plots=True,
    project='/Users/caiwei/Desktop/temp'
)
print(results)
