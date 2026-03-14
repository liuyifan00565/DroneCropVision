import rasterio
from PIL import Image, ImageFile, ImageDraw, ImageFont
import numpy as np
# from tasks.detect.seedling import predict as predict
import os
# from rasterio.enums import Resampling
# import xarray as xr
# import rioxarray
import warnings

# 避免tif文件过大读取会报错, 设置值
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None  # 或者设置一个更大的值，如1000000000


# # tif文件路径
# url = 'E:/Wechat/WeChat Files/wxid_7575955759622/FileStorage/File/2024-11/result.tif'
# # 总占地面积（单位亩）
# area_total = 1
# # 获取当前时间戳
# timestamp = int(time())
# # jpg图片及文本文件输出路径
# out_put_path = f'E:/pyProject/output_image/{timestamp}'
# os.makedirs(out_put_path, exist_ok=True)
# # 黄标（低于总的苗/亩数90%）
# yellow_warn = 0.9
# # 红标（低于总的苗/亩数50%）
# red_warn = 0.5
# # 预测结果图片输出地址
# predict_output_path = out_put_path + "/predict"
# os.makedirs(predict_output_path, exist_ok=True)
# # 一次预测图片个数
# predict_count = 10
# # 预测的图片类型
# allowed_types = {'jpg', 'png', 'jpeg'}


# 检查文件扩展名是否在指定的文件类型列表内
def is_file_type_within_range(file_path, allowed_types):
    file_extension = os.path.splitext(file_path)[1].lower()[1:]  # 获取文件扩展名
    return file_extension in allowed_types


def count_non_empty(arr):
    count = 0
    for item in arr:
        if item is not None and item != '':  # 根据需要，你可以调整条件
            count += 1
    return count


###
# input_filename：tif文件地址
# output_prefix：切图保存路径
# tile_size：切图尺寸
###
def split_tiff(input_filename, output_prefix, tile_size):
    # 打开tif文件
    with rasterio.open(input_filename) as img:
        # 总的有图案的像素面积
        total_pixel = 0
        # 获取数据
        data = img.read()
        # 波段数据为二维数组，是对应像素位置的值
        # 获取红色波段（波长：620-640nm）
        red = img.read(1)  # 1代表红色波段的索引
        # 获取绿色波段（波长：545-565nm）
        green = img.read(2)  # 2代表绿色波段的索引
        # 获取蓝色波段（波长：459-479nm）
        blue = img.read(3)  # 3代表蓝色波段的索引
        if img.count == 4:
            # 获取第四个波段
            band_four = img.read(4)
        tif_width = img.width
        tif_height = img.height
        # 计算分割后的图片数量
        tiles_wide = (img.width // tile_size[0]) + (1 if img.width % tile_size[0] > 0 else 0)
        tiles_high = (img.height // tile_size[1]) + (1 if img.height % tile_size[1] > 0 else 0)
        # 开始切割tif
        for i in range(tiles_wide):
            for j in range(tiles_high):
                # 计算当前块的索引：纵向的开始结束、横向的开始结束
                start_h = j * tile_size[1]
                end_h = min((j + 1) * tile_size[1], img.height)
                start_w = i * tile_size[0]
                end_w = min((i + 1) * tile_size[0], img.width)
                # 可以用此方法获取总体所有波段在上述区域范围的栅格信息  block = data[:, start_w:end_w, start_h:end_h, ]
                # 获取当前块的经纬度范围：左上&右下
                top, left = img.xy(start_w, start_h)
                bottom, right = img.xy(end_w, end_h)
                # 打印当前块的经纬度范围
                print(f"Block {i}_{j}: top={top}, left={left}, bottom={bottom}, right={right}")
                if img.count == 4:
                    # 将几何区域转换为窗口
                    four = band_four[start_h:end_h, start_w:end_w]
                else:
                    four = red[start_h:end_h, start_w:end_w]
                # 计算所有不为0的像素数量，并打印
                non_zero_count = np.count_nonzero(four)
                print(f"output_image-{i}-{j}---Pixel values: {non_zero_count}")
                # 在总的有效像素上加上当前栅格的有效像素数
                total_pixel += non_zero_count
                # 将切割后的图片保存为jpg
                if len(data.shape) == 3:
                    # 假设我们需要获取第一行第一列的像素值
                    r = red[start_h:end_h, start_w:end_w]
                    g = green[start_h:end_h, start_w:end_w]
                    b = blue[start_h:end_h, start_w:end_w]
                    img_rgb = np.dstack((r, g, b))
                    # 将RGB图像转换为Pillow图像并保存为JPG格式，命名格式为output_image-横向序列号-纵向序列号.jpg
                    jpg_image = f'{output_prefix}/output_image-{i}-{j}.jpg'
                    pil_image = Image.fromarray(img_rgb.astype('uint8'), 'RGB')
                    pil_image.save(jpg_image, 'JPEG')
                else:
                    print("图像output_prefix不是彩色图像，无需处理。")
                # 位置信息保存在文档中
                with open(f"{output_prefix}/position.txt", "a") as file:
                    file.write(
                        f"output_image-{i}-{j}.jpg {top} {left} {bottom} {right} {non_zero_count}\n")
                    print("File has been created successfully.")
        print(f"有图的总像素数：{total_pixel}")
    return tif_width, tif_height, tiles_wide, tiles_high, total_pixel
