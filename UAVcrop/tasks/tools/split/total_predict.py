import rasterio
from PIL import Image, ImageFile, ImageDraw, ImageFont
import numpy as np
from tasks.detect.seedling import predict as predict
import os
from time import time
import random

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


def split_tiff(input_filename, output_prefix, tile_size):
    with rasterio.open(input_filename) as img:
        # 总的有图案的像素面积
        total_pixel = 0
        # 获取数据
        data = img.read()
        # profile = img.profile
        # 获取红色波段（波长：620-640nm）
        red = img.read(1)  # 1代表红色波段的索引
        # 获取绿色波段（波长：545-565nm）
        green = img.read(2)  # 2代表绿色波段的索引
        # 获取蓝色波段（波长：459-479nm）
        blue = img.read(3)  # 3代表蓝色波段的索引
        # 获取第四个波段
        band_four = img.read(4)
        band_four_size = band_four.size
        tif_width = img.width
        tif_height = img.height
        # position_dict = dict()
        # 计算分割后的图片数量
        tiles_wide = (img.width // tile_size[0]) + (1 if img.width % tile_size[0] > 0 else 0)
        tiles_high = (img.height // tile_size[1]) + (1 if img.height % tile_size[1] > 0 else 0)
        for i in range(tiles_wide):
            for j in range(tiles_high):
                # 计算当前块的索引
                start_h = j * tile_size[1]
                end_h = min((j + 1) * tile_size[1], img.height)
                start_w = i * tile_size[0]
                end_w = min((i + 1) * tile_size[0], img.width)
                # 提取当前块的数据
                block = data[:, start_w:end_w, start_h:end_h, ]
                # 获取当前块的经纬度范围
                top, left = img.xy(start_w, start_h)
                bottom, right = img.xy(end_w, end_h)
                # 打印当前块的经纬度范围
                print(f"Block {i}_{j}: top={top}, left={left}, bottom={bottom}, right={right}")
                # 截取图片的宽高
                width = min(img.width - i * tile_size[0], tile_size[0])
                height = min(img.height - j * tile_size[1], tile_size[1])
                # 这里可以将block保存为新的TIF文件，或者进行其他处理
                # with rasterio.open(f'{output_prefix}/output_image-{i}-{j}.tif', "w", **profile) as dest:
                #     transform = from_bounds(left, bottom, right, top, width, height)
                #     # 更新变换矩阵和投影信息
                #     dest.transform = transform
                #     dest.crs = {'init': 'epsg:4326'}  # 设置为WGS 84
                #     dest.write(block)
                # 将当前地块的经纬度信息存在一个字典中
                # key = f"{i}-{j}"
                # position_dict[key] = (top, left, bottom, right)
                # 将几何区域转换为栅格窗口
                four = band_four[start_h:end_h, start_w:end_w]
                # 计算非0像素数
                non_zero_count = np.count_nonzero(four)
                print(f"output_image-{i}-{j}---Pixel values: {non_zero_count}")
                total_pixel += non_zero_count
                # 将切割后的图片保存为jpg
                if len(data.shape) == 3:
                    # 假设我们需要获取第一行第一列的像素值
                    r = red[start_h:end_h, start_w:end_w]
                    g = green[start_h:end_h, start_w:end_w]
                    b = blue[start_h:end_h, start_w:end_w]
                    img_rgb = np.dstack((r, g, b))
                    # 将RGB图像转换为Pillow图像并保存为JPG格式
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
        return tif_width, tif_height, tiles_wide, tiles_high, total_pixel


def predict_counts(total_pixel, cut_path, predict_path, predict_count, area_total, allowed_types):
    count_total = 0
    with open(f"{cut_path}/position.txt", 'r') as file:
        lines = file.readlines()
        file.close()
    with open(f"{cut_path}/position.txt", 'w') as file:
        predict_list = list()
        predict_name_list = list()
        file_counts = 0
        file_list = list()
        name_list = list()
        line_i_list = list()
        for f in os.listdir(cut_path):
            if os.path.isfile(os.path.join(cut_path, f)) and is_file_type_within_range(os.path.join(cut_path, f), allowed_types):
                for i in range(len(lines)):
                    line = lines[i]
                    if line.startswith(f):
                        line_array = line.split()
                        if line_array[5] != '0':
                            file_counts += 1
                            file_list.append(os.path.join(cut_path, f))
                            name_list.append(f)
                            line_i_list.append(i)
                        else:
                            source_path = os.path.join(cut_path, f)
                            destination_path = os.path.join(predict_path, f)
                            image = Image.open(source_path)
                            image.save(destination_path)
                            line = line.replace("\n", " ")
                            line += str(0) + "\n"
                        lines[i] = line
        for_counts = (file_counts // predict_count) + (1 if file_counts % predict_count > 0 else 0)
        for i in range(for_counts):
            final_count = min((i + 1) * predict_count, file_counts)
            predict_list.clear()
            predict_name_list.clear()
            for j in range(i * predict_count, final_count):
                predict_list.append(file_list[j])
                predict_name_list.append(name_list[j])
            list_counts, count_areas = predict.get_predict_counts(predict_list, predict_name_list, predict_path, False, None)
            for k in range(len(list_counts)):
                count = list_counts[k]
                index_count = i * predict_count + k
                line = lines[line_i_list[index_count]]
                line_array = line.split()
                area_percent = int(line_array[5]) / total_pixel
                count_area = count / (area_total * area_percent)
                line = line.replace("\n", " ")
                line += str(count_area) + "\n"
                count_total += predict_count
                lines[line_i_list[index_count]] = line
        file.writelines(lines)
        file.close()
        return count_total


def add_img_color_word(cut_path, allowed_types, predict_path, red_warn, yellow_warn, total_count_area):
    with open(f"{cut_path}/position.txt", 'r') as file:
        lines = file.readlines()
        for f in os.listdir(predict_path):
            if os.path.isfile(os.path.join(predict_path, f)) and is_file_type_within_range(os.path.join(predict_path, f), allowed_types):
                # 打开图片
                image = Image.open(os.path.join(predict_path, f))
                for line in lines:
                    if line.startswith(f):
                        # 获取该小图的经纬度等信息
                        line_array = line.split()
                        count_area = line_array[6]
                        top = line_array[1]
                        left = line_array[2]
                        bottom = line_array[3]
                        right = line_array[4]
                        result = None
                        # 将图片转换为RGBA模式，以便处理透明度
                        image_rgba = image.convert("RGBA")
                        # 分离通道
                        red, green, blue, alpha = image_rgba.split()
                        if line_array[5] != '0':
                            # 如果小图的苗/亩数小于等于全部的苗/亩数*红色警告值
                            if float(count_area) <= total_count_area * red_warn:
                                # 创建一个纯红色图层
                                red_color = Image.new("RGBA", image_rgba.size, (255, 0, 0, 128))
                            # 如果小图的苗/亩数小于等于全部的苗/亩数*黄色警告值且大于全部的苗/亩数*红色警告值
                            elif total_count_area * yellow_warn >= float(count_area) > total_count_area * red_warn:
                                # 创建一个黄色图层
                                red_color = Image.new("RGBA", image_rgba.size, (255, 255, 0, 128))
                            else:
                                # 创建一个纯透色图层
                                red_color = Image.new("RGBA", image_rgba.size, (255, 255, 255, 0))
                            # 使用红色图层覆盖原始图片
                            result = Image.composite(red_color, image_rgba, red_color)
                            # 创建一个可以在给定图片上绘图的对象
                            draw = ImageDraw.Draw(result)
                            # 定义字体和大小
                            font = ImageFont.truetype("SimHei.ttf", 30)
                            text = f"top:{top}\nleft:{left}\nbottom:{bottom}\nright:{right}\ncounts:{count_area}"
                            # 写字
                            draw.text((10, 10), text, font=font, fill=(255, 255, 255))
                            # 保存新图片为png
                            result.save(predict_path + "/" + f.split(".")[0] + ".png")
                        else:
                            image.save(predict_path + "/" + f.split(".")[0] + ".png")


def img_stitching(width, height, tiles_wide, tiles_high, final_path, predict_path):
    # 创建一个新的图像来容纳所有小图像
    total_image = Image.new('RGB', (width, height))
    for i in range(tiles_wide):
        for j in range(tiles_high):
            f = f"output_image-{i}-{j}.png"
            if os.path.isfile(os.path.join(predict_path, f)) and f.endswith('.png'):
                image = Image.open(os.path.join(predict_path, f))
                total_image.paste(image, (1024 * i, 1024 * j))
                image.close()
    # 保存合并后的图像
    total_image.save(final_path + "/" + "final_img.png")


def get_result(file_url, cut_path, predict_path, final_path, cut_size, allowed_types, predict_count, area_total,
               red_warn, yellow_warn):
    # 使用示例
    # 切割图片，保存文本文件
    tif_width, tif_height, tiles_wide, tiles_high, total_pixel = split_tiff(file_url, cut_path, cut_size)
    print(f"有图的总像素数：{total_pixel}")
    # 所有苗的总数量, 图片预测，更新文档
    count_total = predict_counts(total_pixel, cut_path, predict_path, predict_count, area_total, allowed_types)
    # 总的苗/亩数
    total_count_area = count_total / area_total
    print(f"总苗数为：{total_count_area}")
    # 处理识别后的图片（加透明黄色、红色警告图层及添加经纬度等文字信息）
    add_img_color_word(cut_path, allowed_types, predict_path, red_warn, yellow_warn, total_count_area)
    # 拼图
    img_stitching(tif_width, tif_height, tiles_wide, tiles_high, final_path, predict_path)
    return total_count_area
