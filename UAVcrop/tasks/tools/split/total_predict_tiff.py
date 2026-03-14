import rasterio
from PIL import Image, ImageFile, ImageDraw, ImageFont
import numpy as np
from tasks.detect.seedling import predict as predict
import os
from rasterio.enums import Resampling
import xarray as xr
import rioxarray
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


###
# input_filename：传入的tif文件地址
# output_prefix：切图存入的文件夹地址
# tile_size：切图尺寸
# predict_path：预测文件存入的文件夹地址
# predict_count：单次预测数量
# area_total：总面积
# allowed_types：允许预测的文件类型
# total_pixel：总的有效像素数
###
def get_predict_count(input_filename, output_prefix, tile_size, predict_path, predict_count,
                      area_total, allowed_types, total_pixel):
    # 打开tif文件
    with rasterio.open(input_filename) as tif_img:
        # 获取红色波段（波长：620-640nm）
        red = tif_img.read(1)  # 1代表红色波段的索引
        # 获取绿色波段（波长：545-565nm）
        green = tif_img.read(2)  # 2代表绿色波段的索引
        # 获取蓝色波段（波长：459-479nm）
        blue = tif_img.read(3)  # 3代表蓝色波段的索引
    # 将三个通道合并成一个三维数组
    image = np.stack((red, green, blue), axis=-1)
    # 使用Pillow创建图像
    img = Image.fromarray(image, 'RGB')
    draw = ImageDraw.Draw(img)
    # 声明一个用来存总数的变量
    count_total = 0
    # 打开保存的文档文件，用来获取预测信息，只读
    with open(f"{output_prefix}/position.txt", 'r') as file:
        # 获取所有行的数据
        lines = file.readlines()
        file.close()
    # 打开保存的文档文件，用来存入预测信息
    with open(f"{output_prefix}/position.txt", 'w') as file:
        predict_list = list()
        predict_name_list = list()
        file_counts = 0
        file_list = list()
        name_list = list()
        line_i_list = list()
        for f in os.listdir(output_prefix):
            if os.path.isfile(os.path.join(output_prefix, f)) and is_file_type_within_range(
                    os.path.join(output_prefix, f), allowed_types):
                for i in range(len(lines)):
                    line = lines[i]
                    if line.startswith(f):
                        line_array = line.split()
                        if line_array[5] != '0':
                            file_counts += 1
                            file_list.append(os.path.join(output_prefix, f))
                            name_list.append(f)
                            line_i_list.append(i)
                        else:
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
            list_counts = list()
            return_res_predicts = predict.get_predict_counts_total(predict_list)
            for m in range(len(return_res_predicts)):
                return_res_predict = return_res_predicts[m]
                f = predict_name_list[m]
                class_ids = return_res_predict['class_ids']
                confidencs = return_res_predict['confidencs']
                rects = return_res_predict['rects']
                print("未进行处理前长度为：", len(class_ids))
                areas = 0
                if len(class_ids) != 0:
                    for rect in rects:
                        area = (rect[2] - rect[0]) * (rect[3] - rect[1])
                        areas += area
                    areas = areas / len(class_ids)
                index = 0
                while index < len(class_ids):
                    rect = rects[index]
                    if (((rect[2] - rect[0]) * (rect[3] - rect[1]) < areas * 0.5) and (
                            rect[0] == 0 or rect[1] == 0 or rect[2] == (tile_size[0] - 1) or rect[3] == (tile_size[1] - 1))) or (
                            (rect[2] - rect[0]) * (rect[3] - rect[1]) < areas * 0.2):
                        rects.pop(index)
                        class_ids.pop(index)
                        confidencs.pop(index)
                    index += 1
                print("处理后的长度：", len(class_ids))
                index = 0
                # 遍历最后的结果集
                while index < len(confidencs):
                    # 置信取两位小数
                    rect = rects[index]
                    # 设置默认的（类型为0时）线和字体的颜色
                    line_color = 'blue'
                    # 获取两个坐标点
                    point1 = (int(rect[0]), int(rect[1]))
                    point2 = (int(rect[2]), int(rect[3]))
                    # 计算矩形的左上角和右下角
                    left, top = min(point1[0], point2[0]), min(point1[1], point2[1])
                    right, bottom = max(point1[0], point2[0]), max(point1[1], point2[1])
                    index_i = int(f.split('.')[0].split('-')[1]) * tile_size[0]
                    index_j = int(f.split('.')[0].split('-')[2]) * tile_size[1]
                    # 绘制矩形，当上方高度不够时文本框改在下方
                    # 根据坐标点画框以及文本框
                    draw.rectangle((left + index_i, top + index_j, right + index_i, bottom + index_j), None,
                                   line_color, 3)
                    index += 1
                list_counts.append(len(class_ids))
            for k in range(len(list_counts)):
                count = list_counts[k]
                index_count = i * predict_count + k
                line = lines[line_i_list[index_count]]
                line_array = line.split()
                area_percent = int(line_array[5]) / total_pixel
                count_area = count / (area_total * area_percent)
                line = line.replace("\n", " ")
                line += str(count_area) + "\n"
                count_total += count
                lines[line_i_list[index_count]] = line
        file.writelines(lines)
        file.close()
    img.save(f"{predict_path}/result.tif")
    return count_total


def add_img_color_word(cut_path, predict_path, red_warn, yellow_warn, total_count_area, cut_size, final_path):
    with open(f"{cut_path}/position.txt", 'r') as file:
        lines = file.readlines()
        # 获取该小图的经纬度等信息
        img = Image.open(f"{predict_path}/result.tif")
        # 保存修改后的图像
        img.save('modified_image.tiff')
        for line in lines:
            line_array = line.split()
            count_area = line_array[6]
            top = line_array[1]
            left = line_array[2]
            bottom = line_array[3]
            right = line_array[4]
            f_name = line_array[0]
            result = None
            # 将图片转换为RGBA模式，以便处理透明度
            x1, y1 = int(f_name.split('.')[0].split('-')[1]) * cut_size[0], int(f_name.split('.')[0].split('-')[2]) * cut_size[1]
            x2, y2 = (int(f_name.split('.')[0].split('-')[1]) + 1) * cut_size[0], (int(f_name.split('.')[0].split('-')[2]) + 1) * cut_size[1]
            color = (255, 255, 255, 0)
            if line_array[5] != '0':
                # 如果小图的苗/亩数小于等于全部的苗/亩数*红色警告值
                if float(count_area) <= total_count_area * red_warn:
                    # 创建一个纯红色图层
                    color = (255, 0, 0, 128)
                # 如果小图的苗/亩数小于等于全部的苗/亩数*黄色警告值且大于全部的苗/亩数*红色警告值
                elif total_count_area * yellow_warn >= float(count_area) > total_count_area * red_warn:
                    # 创建一个黄色图层
                    color = (255, 255, 0, 128)
                # 绘制遮罩区域，这里以矩形为例，你可以根据需要调整为任意形状
                overlay_image = Image.new('RGBA', cut_size, color)  # RGBA模式，最后一个参数是透明度（alpha）
                # 将透明黄色层粘贴到原图上
                img.paste(overlay_image, (x1, y1), overlay_image)
                # 定义字体和大小
                font = ImageFont.truetype("SimHei.ttf", 30)
                text = f"top:{top}\nleft:{left}\nbottom:{bottom}\nright:{right}\ncounts:{count_area}"
                # 创建一个可以在给定图像上绘图的对象
                draw = ImageDraw.Draw(img)
                # 写字
                draw.text((x1 + 10, y1 + 10), text, font=font, fill=(255, 255, 255))
        # 保存修改后的图像
        img.save(f"{final_path}/result.tif")


def add_img_color_word_other(cut_path, predict_path, red_warn, yellow_warn, total_count_area, cut_size, final_path):
    with open(f"{cut_path}/position.txt", 'r') as file:
        lines = file.readlines()
        # 获取该小图的经纬度等信息
        img = Image.open(f"{predict_path}/result.tif")
        yellow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))  # 初始透明度为0
        # red_layer = Image.new('RGBA', img.size, (255, 0, 0, 0))  # 初始透明度为0
        draw_yellow = ImageDraw.Draw(yellow_layer)
        yellow_pixel = 0
        red_pixel = 0
        list_text = list()
        list_draw = list()
        # draw_red = ImageDraw.Draw(red_layer)
        # 保存修改后的图像
        # img.save('modified_image.tiff')
        for line in lines:
            line_array = line.split()
            count_area = line_array[6]
            top = line_array[1]
            left = line_array[2]
            bottom = line_array[3]
            right = line_array[4]
            f_name = line_array[0]
            result = None
            # 定义字体和大小
            font = ImageFont.truetype("SimHei.ttf", 30)
            # 将图片转换为RGBA模式，以便处理透明度
            x1, y1 = int(f_name.split('.')[0].split('-')[1]) * cut_size[0], int(f_name.split('.')[0].split('-')[2]) * cut_size[1]
            x2, y2 = min(img.width, (int(f_name.split('.')[0].split('-')[1]) + 1) * cut_size[0]), min(img.height, (int(f_name.split('.')[0].split('-')[2]) + 1) * cut_size[1])
            if line_array[5] != '0':
                text = f"top:{top}\nleft:{left}\nbottom:{bottom}\nright:{right}\ncounts:{count_area}"
                # 如果小图的苗/亩数小于等于全部的苗/亩数*红色警告值
                if float(count_area) <= total_count_area * red_warn:
                    list_draw.append({'color': (255, 0, 0, 128), 'xy': (x1, y1), 'xy2': (x2, y2)})
                    red_pixel += int(line_array[5])
                    # draw_yellow.rectangle([x1, y1, x2, y2], fill=(255, 0, 0, 128))  # 填充红色
                    # draw_yellow，仅在蒙版区域显示黄色图层
                # 如果小图的苗/亩数小于等于全部的苗/亩数*黄色警告值且大于全部的苗/亩数*红色警告值
                elif total_count_area * yellow_warn >= float(count_area) > total_count_area * red_warn:
                    list_draw.append({'color': (255, 255, 0, 128), 'xy': (x1, y1), 'xy2': (x2, y2)})
                    # draw_yellow.rectangle([x1, y1, x2, y2], fill=(255, 255, 0, 128))  # 填充黄色，
                    yellow_pixel += int(line_array[5])
                list_text.append({'text': text, 'x': x1 + 10, 'y': y1 + 10})
        for draws in list_draw:
            x1, y1 = draws['xy']
            x2, y2 = draws['xy2']
            for x in range(x1, x2):
                for y in range(y1, y2):
                    if img.getpixel((x, y)) != (0, 0, 0):
                        yellow_layer.putpixel((x, y), draws['color'])  # 黄色，半透明（128为半透明度）
                    else:
                        yellow_layer.putpixel((x, y), (0, 0, 0, 0))
        # for line in list_text:
        #     # 写字
        #     draw_yellow.text((line['x'], line['y']), line['text'], font=font, fill=(255, 255, 255))
        result = Image.alpha_composite(img.convert('RGBA'), yellow_layer)
        # 保存修改后的图像
        result.save(f"{final_path}/result.tif")
        return yellow_pixel, red_pixel


def copy_geographic_info_old(src_path, dst_path, output_path):
    # 打开源文件
    with rasterio.open(src_path) as src, rasterio.open(dst_path) as dst:
        # 读取源文件的元数据和坐标转换参数
        src_profile = src.profile
        src_transform = src.transform
        src_crs = src.crs

        # 读取目标文件的元数据（不包括坐标转换参数）
        dst_profile = dst.profile.copy()
        del dst_profile['transform']  # 删除目标文件的transform，因为我们稍后将替换它
        del dst_profile['crs']  # 删除目标文件的crs，因为我们稍后将替换它

        # 使用源文件的坐标转换参数和目标文件的元数据创建新的profile
        new_profile = src_profile.copy()
        new_profile.update(dst_profile)
        new_profile['transform'] = src_transform  # 设置新的transform
        new_profile['crs'] = src_crs  # 设置新的crs

        # 读取目标文件的数据（如果需要）并写入新文件（可选）
        with rasterio.open(output_path, 'w', **new_profile) as out:
            out.write(dst.read(1), 1)  # 假设我们只处理第一个波段，可以根据需要修改波段索引或处理多个波段
            out.write(dst.read(2), 2)  # 假设我们只处理第一个波段，可以根据需要修改波段索引或处理多个波段
            out.write(dst.read(3), 3)  # 假设我们只处理第一个波段，可以根据需要修改波段索引或处理多个波段
            out.write(dst.read(4), 4)  # 假设我们只处理第一个波段，可以根据需要修改波段索引或处理多个波段
        with rasterio.open(output_path) as src_final:
            # 获取原始图像的参数
            transform = src_final.transform
            width = src_final.width
            height = src_final.height
            crs = src_final.crs

            # 计算新的分辨率（例如，原始分辨率的1/2）
            x_res = transform[0] * 2  # 水平分辨率翻倍
            y_res = transform[4] * 2  # 垂直分辨率翻倍
            new_transform = rasterio.transform.from_origin(transform.xoff, transform.yoff + height * y_res, x_res,
                                                           y_res)
            # 计算新的图像尺寸
            new_width = int(width / 2)
            new_height = int(height / 2)

            # 读取数据并重采样
            data = src_final.read(1, out_shape=(1, new_height, new_width), resampling=Resampling.bilinear)

            # 创建新的输出文件
            with rasterio.open(dst_path, 'w', driver='GTiff', height=new_height, width=new_width, count=1,
                               dtype=src_final.dtypes[0], crs=crs, transform=new_transform) as dst_final:
                dst_final.write(data, 1)
            with rasterio.open(dst_path) as src:
                # 读取原始数据和元数据
                profile = src.profile
                data = src.read(1)
                data2 = src.read(2)
                data3 = src.read(3)
                data4 = src.read(4)

                # 设置压缩选项，例如使用 DEFLATE 压缩，并设置压缩质量（对于 DEFLATE）
                profile.update(compress='DEFLATE', predictor=2)  # predictor=2 用于更好的压缩效果
                # profile.update(compress='lzw')  # 使用LZW压缩
                # profile.update(tiled=True)  # 设置为瓦片格式，有助于压缩

                # 写入新的 TIFF 文件，保持元数据不变
                with rasterio.open(dst_path, 'w', **profile) as dst:
                    dst.write(data, 1)  # 写入数据到第一个波段
                    dst.write(data2, 2)  # 写入数据到第一个波段
                    dst.write(data3, 3)  # 写入数据到第一个波段
                    dst.write(data4, 4)  # 写入数据到第一个波段

            print("TIFF 文件已成功压缩并保存。")


def load_raster(file_path, bands=3):
    """
    读取栅格文件并提取指定波段，仅在所有三个波段的像素值均为0时替换为NaN
    """
    data = rioxarray.open_rasterio(file_path, masked=True)[:bands, :, :]
    # 创建掩膜：所有波段的像素值均为0
    mask = (data == 0).all(dim='band')
    # 将符合条件的像素替换为nan
    data = data.where(~mask, np.nan)
    return data

def get_crs_and_transform(reference_file):
    """
    获取参考文件的CRS和仿射变换
    """
    with rasterio.open(reference_file) as src:
        crs = src.crs
        transform = src.transform
    return crs, transform

def create_dataarray(data, crs, transform):
    """
    创建带有坐标、CRS和仿射变换的DataArray对象
    """
    height, width = data.shape[1], data.shape[2]
    # 生成空间坐标
    x = np.arange(width) * transform.a + transform.c + transform.a / 2
    y = np.arange(height) * transform.e + transform.f + transform.e / 2
    data_array = xr.DataArray(
        data,
        coords=[["r", "g", "b"], y, x],
        dims=["band", "y", "x"]
    )
    data_array = data_array.rio.write_crs(crs)
    data_array = data_array.rio.write_transform(transform)
    return data_array

def save_raster(data_array, out_path, nodata_value=-9999):
    """
    保存DataArray为GeoTIFF，设置nodata值和压缩
    """
    # 将NaN替换为nodata值
    data_array = data_array.fillna(nodata_value)
    # 转换数据类型为float32以支持nodata值
    data_array = data_array.astype('float32')
    data_array.rio.to_raster(
        out_path,
        dtype='float32',
        driver='GTiff',
        nodata=nodata_value,
        compress='DEFLATE'
    )

def remove_black_borders(input_file, output_file, nodata_value=-9999):
    """
    移除黑色边界，通过设置nodata值
    """
    with rasterio.open(input_file) as src:
        data = src.read()
        profile = src.profile

    # 替换NaN（已填充为 nodata_value）为 nodata_value
    data = np.where(np.isnan(data), nodata_value, data)
    profile.update(
        dtype=rasterio.float32,
        nodata=nodata_value,
        compress='DEFLATE'
    )

    with rasterio.open(output_file, 'w', **profile) as dst:
        dst.write(data.astype(rasterio.float32))

def copy_geographic_info(src_path, dst_path, intermediate_path,outpath):
    # 忽略NotGeoreferencedWarning警告
    warnings.filterwarnings("ignore", message="Dataset has no geotransform, gcps, or rpcs.*", category=UserWarning)
    # 读取文件并处理
    datas1 = load_raster(dst_path)
    #datas2 = load_raster(src_path)
    # 获取参考文件的CRS和仿射变换
    crs, transform = get_crs_and_transform(src_path)
    # 创建DataArray对象
    foo = create_dataarray(datas1, crs, transform)
    # 保存为中间GeoTIFF
    save_raster(foo, intermediate_path)
    # 移除黑色边界
    remove_black_borders(intermediate_path, outpath)
    # 删除中间文件
    if os.path.exists(intermediate_path):
        os.remove(intermediate_path)


###
# task_id：任务id
# file_url：传入的tif文件地址
# cut_path：切图存入的文件夹地址
# predict_path：预测文件存入的文件夹地址
# final_path：结果文件存入的文件夹地址
# cut_size：切图尺寸
# allowed_types：允许预测的文件类型
# predict_count：单次预测数量
# area_total：总面积
# red_warn：红色提醒百分比
# yellow_warn：黄色提醒百分比
###
def get_result(task_id, file_url, cut_path, predict_path, final_path, cut_size, allowed_types, predict_count,
               area_total, red_warn, yellow_warn):
    # 切割图片，保存文本文件
    ###
    # tif_width：tif文件像素宽
    # tif_height：tif文件像素高
    # tiles_wide：tif文件横向切割的数量
    # tiles_high：tif文件纵向切割的数量
    # total_pixel：总的有效像素数
    ###
    tif_width, tif_height, tiles_wide, tiles_high, total_pixel = split_tiff(file_url, cut_path, cut_size)
    # 总的预测数量
    count_total = get_predict_count(file_url, cut_path, cut_size, predict_path, predict_count, area_total,
                                    allowed_types, total_pixel)
    # 总的苗/亩数
    total_count_area = count_total / area_total
    # 处理识别后的图片（加透明黄色、红色警告图层及添加经纬度等文字信息）
    yellow_pixel, red_pixel = add_img_color_word_other(cut_path, predict_path, red_warn, yellow_warn, total_count_area, cut_size, final_path)
    # 输入输出路径
    intermediate_path = f"{final_path}/DOM_intermediate.tif"
    output_path_tif = f"{final_path}/Seedling_Complete_{task_id}.tif"
    copy_geographic_info(file_url, f"{final_path}/result.tif", intermediate_path, output_path_tif)
    print(f"总苗数为：{total_count_area}")
    yellow_percent = yellow_pixel / total_pixel
    red_percent = red_pixel / total_pixel
    return total_count_area, red_percent, yellow_percent
