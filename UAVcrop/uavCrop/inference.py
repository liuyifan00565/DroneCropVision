from ultralytics import YOLO
from PIL import Image
import cv2
import os

# 定义绘图函数：在图像上标记检测到的目标（画出边界框）
def draw_boxes_img(coordinates, input_img_path, write_img_path):
    """
    在输入图像上绘制检测到的目标边界框

    参数:
    coordinates: 包含边界框坐标的列表，每个元素是一个字典，包含 x_min、y_min、x_max、y_max
    input_img_path: 输入图像的路径
    write_img_path: 保存图像的路径
    """
    # 读取图像，同时处理色彩和方向信息
    img = cv2.imread(input_img_path, cv2.IMREAD_COLOR + cv2.IMREAD_IGNORE_ORIENTATION)

    color = (255, 0, 0)   # BGR：蓝色
    thickness = 2         # 线宽为2像素

    # 遍历所有边界框
    for coord in coordinates:
        x1 = int(coord["x_min"])
        y1 = int(coord["y_min"])
        x2 = int(coord["x_max"])
        y2 = int(coord["y_max"])

        # 画矩形框：左上角 (x1,y1)，右下角 (x2,y2)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

    # 保存处理后的图像
    cv2.imwrite(write_img_path, img)


# 定义绘图函数：在图像上标记检测到的目标（在中心画点）
def drawdot_img(coordinates, input_img_path, write_img_path):
    """
    在输入图像上绘制检测到的目标中心点
    
    参数:
    coordinates: 包含边界框坐标的列表，每个元素是一个字典，包含x_min、y_min、x_max、y_max
    input_img_path: 输入图像的路径
    write_img_path: 保存图像的路径
    """
    # 读取图像，同时处理色彩和方向信息
    img = cv2.imread(input_img_path, cv2.IMREAD_COLOR + cv2.IMREAD_IGNORE_ORIENTATION)
    
    color = (255, 0, 0)  # 蓝色BGR
    thickness = -1  # 负值表示填充，绘制实心圆
    
    # 遍历所有边界框
    for coord in coordinates:
        # 提取边界框坐标并转换为整数
        x, y, x2, y2 = int(coord["x_min"]), int(coord["y_min"]), int(coord["x_max"]), int(coord["y_max"])
        
        # 计算边界框中心点
        cx, cy = (x + x2) // 2, (y + y2) // 2
        
        # 在中心点位置绘制实心圆标记
        cv2.circle(img, center=(cx, cy), radius=5, color=color, thickness=thickness)
    
    # 保存处理后的图像
    cv2.imwrite(write_img_path, img)

if __name__ == "__main__":
    # 配置测试图像目录和输出目录
    test_dir = "D:/StudyData/Projects/UAV/UAVcrop-master-66183173d0d5be1f00538b21082dd2a57ead245b/datasets/soybean/test/images"
    write_dir = "./SoybeanTest"
    
    # 模型配置
    model_type = "yolov11s"  # 模型类型标识
    model_path = "D:\crop_UAV\UAVcrop\uavCrop\runs\detect\trainSeabean\best.pt"  # 自定义训练的模型路径
    model = YOLO(model_path)  # 加载YOLO模型
    
    # 创建输出目录(如果不存在)
    os.makedirs(write_dir, exist_ok=True)
    
    # 遍历测试目录中的所有图像文件
    for img_name in os.listdir(test_dir):
        img_path = os.path.join(test_dir, img_name)
        
        # 跳过非图像文件
        if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
            
        # 构建输出路径，添加模型类型前缀
        write_path = os.path.join(write_dir, f"{model_type}_{img_name}")
        
        # 打开图像
        img = Image.open(img_path)
        
        # 使用模型进行目标检测
        # 参数说明:
        # save=False: 不保存模型自带的结果
        # conf=0.3: 置信度阈值为0.3
        # iou=0.3: NMS的IOU阈值为0.3
        # imgsz=1024: 输入图像尺寸为1024x1024
        # max_det=1000: 最大检测目标数为1000
        results = model.predict(source=img, save=False, conf=0.3, iou=0.3, imgsz=1024, max_det=1000)
        
        # 获取第一张图像的检测结果(批量处理中的第一张)
        result = results[0]
        
        # 打印检测到的目标数量
        print(f"在图像 {img_name} 中检测到 {len(result.boxes)} 个目标")
        
        # 提取边界框坐标
        coord = []
        for box in result.boxes:
            # 获取边界框坐标 [x1, y1, x2, y2]
            xyxy = box.xyxy[0]
            # 将tensor转换为CPU上的列表
            xyxy_cpu = xyxy.cpu().tolist()
            # 存储坐标信息
            coord.append({
                'x_min': xyxy_cpu[0], 
                'y_min': xyxy_cpu[1], 
                'x_max': xyxy_cpu[2], 
                'y_max': xyxy_cpu[3]
            })
        
        # 在原图上绘制检测点并保存结果
        draw_boxes_img(coord, img_path, write_path)