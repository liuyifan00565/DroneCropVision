import math
import time
from PIL import Image, ImageFile
import numpy as np
import tasks.detect.seedling.predict as predict
import tasks.detect.seedling.utils as utils
import tasks.detect.seedling.config as config
import os
from sortedcontainers import SortedSet
from osgeo import gdal

# 避免tif文件过大读取会报错, 设置值
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None  # 或者设置一个更大的值，如1000000000


def split_tiff(tif_path, output_dir, tile_size=(1024, 1024)):
    global dataset
    tif_width, tif_height, tiles_wide, tiles_high, total_pixel = 0, 0, 0, 0, 0
    size_list = SortedSet()
    try:
        # 注册GDAL驱动
        gdal.AllRegister()
        # 打开输入文件
        dataset = gdal.Open(tif_path)
        if dataset is None:
            raise FileNotFoundError(f"无法打开文件：{tif_path}")
        # 获取地理信息
        geotransform = dataset.GetGeoTransform()
        projection = dataset.GetProjection()
        # 获取图像尺寸
        bands = dataset.RasterCount
        tif_width = dataset.RasterXSize
        tif_height = dataset.RasterYSize
        # 计算需要的切片数量
        tiles_wide = math.ceil(tif_width / tile_size[0])
        tiles_high = math.ceil(tif_height / tile_size[1])
        # 遍历所有切片并保存为JPG
        for i in range(tiles_wide):
            for j in range(tiles_high):
                # 计算当前切片的起始和结束位置
                x1 = i * tile_size[0]
                y1 = j * tile_size[1]
                x2 = min((i + 1) * tile_size[0], tif_width)
                y2 = min((j + 1) * tile_size[1], tif_height)

                # 读取4波段数据
                data = []

                for b in range(1, bands + 1):  # GDAL波段从1开始
                    band = dataset.GetRasterBand(b)
                    arr = band.ReadAsArray(x1, y1, x2-x1, y2-y1)
                    # 数据类型转换（假设原始数据为浮点型）
                    if arr.dtype == np.float32:
                        # 根据实际数据范围调整缩放参数
                        arr = np.clip((arr * 255).astype(np.uint8), 0, 255)
                    else:
                        # 其他类型直接转换
                        arr = arr.astype(np.uint8)
                    data.append(arr)

                # 合并波段（假设波段顺序为RGBAlpha）
                rgb_alpha = np.dstack(data)
                nonzero_mask = np.any(rgb_alpha != 0, axis=-1)
                non_zero_count = np.sum(nonzero_mask)
                print(f"output_image-{i}-{j}---Pixel values: {non_zero_count}")
                # 在总的有效像素上加上当前栅格的有效像素数
                total_pixel += non_zero_count
                # 创建JPG文件
                output_path = os.path.join(
                    output_dir,
                    f"output_image_-_{x1}_-_{y1}.jpg"
                )
                # 使用PIL保存为JPG（自动处理Alpha通道）
                img = Image.fromarray(rgb_alpha, 'RGBA')
                img.convert('RGB').save(output_path, quality=85)
                size_list.add(img.size)
                with open(f"{output_dir}/position.txt", "a") as file:
                    file.write(
                        f"output_image_-_{i * tile_size[0]}_-_{j * tile_size[1]}.jpg {non_zero_count}\n")
                    print("File has been created successfully.")
    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")
    finally:
        if 'dataset' in locals() and dataset is not None:
            dataset = None  # 关闭数据集
    return tif_width, tif_height, tiles_wide, tiles_high, total_pixel, size_list


def get_predict_count(output_prefix, predict_count, area_total, allowed_types, total_pixel, size_list):
    """
        获取预测结果
    Args:
        input_filename: 传入的tif文件地址
        output_prefix: 切图存入的文件夹地址
        tile_size: 切图尺寸
        predict_path: 预测文件存入的文件夹地址
        predict_count: 单次预测数量
        area_total: 总面积
        allowed_types: 允许预测的文件类型
        total_pixel: 总的有效像素数

    Returns:
        count_total: 总苗数
    """
    # 声明一个用来存总数的变量
    count_total = 0
    with open(f"{output_prefix}/position-rect.txt", "w") as file_rect:
        pass
    # 打开保存的文档文件，用来获取预测信息，只读
    with open(f"{output_prefix}/position.txt", 'r') as file:
        # 获取所有行的数据
        lines = file.readlines()
    # 打开保存的文档文件，用来存入预测信息
    with open(f"{output_prefix}/position-1.txt", 'w') as file:
        # 遍历切图文件夹的图片文件
        for size in size_list:
            # 需要预测的图片文件数量
            file_counts = 0
            # 声明一个文件列表
            file_list = list()
            # 声明一个文件名列表
            name_list = list()
            # 行号列表
            line_i_list = list()
            for i in range(len(lines)):
                # 获取每行信息
                line = lines[i]
                f = line.split(' ')[0]
                # 找到当前文件对应行
                if os.path.isfile(os.path.join(output_prefix, f)) and utils.is_file_type_size_within_range(
                        os.path.join(output_prefix, f), allowed_types, size):
                    line_array = line.split()
                    # 判断当前图片中，需要有内容的彩色像素不为0
                    if line_array[1] != '0':
                        # 文件数量+1
                        file_counts += 1
                        # 文件列表全路径+1
                        file_list.append(os.path.join(output_prefix, f))
                        # 文件名列表+1
                        name_list.append(f)
                        # 记录在lines中的行号
                        line_i_list.append(i)
                    # 图片中没有需要预测的像素，在末尾追加一个预测的数量为0
                    else:
                        line = line.replace("\n", " ")
                        line += str(0) + " " + str(0) + "\n"
                    # 修改后的行信息重新赋值
                    lines[i] = line
            # 根据单次预测图片数量与总图片数量，计算需要循环的次数
            for_counts = math.ceil(file_counts / predict_count)
            # 循环开始预测
            for i in range(for_counts):
                final_count = min((i + 1) * predict_count, file_counts)
                # 声明一个预测列表，之后用来存放预测的图片
                predict_list = list()
                # 声明一个预测文件名列表，之后用来存放预测的图片名
                predict_name_list = list()
                for j in range(i * predict_count, final_count):
                    predict_list.append(file_list[j])
                    predict_name_list.append(name_list[j])
                list_counts = list()
                print(f"predict_list: {predict_list}")
                return_res_predicts = predict.get_predict_counts_total(predict_list, size)
                # print(f"return_res_predicts: {return_res_predicts}")
                for m in range(len(return_res_predicts)):
                    return_res_predict = return_res_predicts[m]
                    f = predict_name_list[m]
                    class_ids = return_res_predict['class_ids']
                    confidencs = return_res_predict['confidencs']
                    rects = return_res_predict['rects']
                    print(f"{f}文件识别出来的未处理数量为：{len(class_ids)}")
                    # class_ids, confidences, rects = utils.reduce_quantity(class_ids, confidencs, rects, tile_size)
                    utils.draw_boxes(rects=rects, f=f, if_save_rect_txt=config.IF_SAVE_RECT_TXT_TOTAL, cut_path=output_prefix,
                                     if_draw_boxes=False, boxes_color=config.TOTAL_COLOR)
                    list_counts.append(len(class_ids))
                for k in range(len(list_counts)):
                    count = list_counts[k]
                    index_count = i * predict_count + k
                    line = lines[line_i_list[index_count]]
                    line_array = line.split()
                    area_percent = int(line_array[1]) / total_pixel
                    count_area = count / (area_total * area_percent)
                    line = line.replace("\n", " ")
                    line += str(count_area) + " " + str(count) + "\n"
                    count_total += count
                    lines[line_i_list[index_count]] = line
        file.writelines(lines)
    return count_total


class AdvancedTifProcessor:
    def __init__(self, input_path, output_path):
        # 打开输入文件
        self.src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
        if self.src_ds is None:
            raise FileNotFoundError(f"无法打开文件：{input_path}")

        # 创建输出文件（带RGBA四波段）
        driver = gdal.GetDriverByName('GTiff')
        self.dst_ds = driver.CreateCopy(
            output_path,
            self.src_ds,
            0,
            options=['COMPRESS=DEFLATE', 'PHOTOMETRIC=RGB']
        )
        self.dst_ds.SetGeoTransform(self.src_ds.GetGeoTransform())
        self.dst_ds.SetProjection(self.src_ds.GetProjection())

        # 预加载数据到内存
        self.band_count = self.dst_ds.RasterCount
        self.raster_size = (self.dst_ds.RasterXSize, self.dst_ds.RasterYSize)
        self.bands = self.dst_ds.GetRasterBand
        self.band_data = []
        for b in range(1, 5):  # 读取RGBA四波段
            band = self.dst_ds.GetRasterBand(b)
            self.band_data.append(band.ReadAsArray().astype(np.float32))

        # 颜色配置（RGBA格式）
        self.colors = {
            'red': (255, 1, 1, 255),  # 半透明红色
            'yellow': (255, 255, 1, 255)  # 半透明黄色
        }

    def batch_draw_rectangles(self, rectangles, color):
        """批量绘制矩形框"""
        # 获取颜色值
        if self.band_count == 4:
            color = color + (255,)
        # 批量处理
        for rect in rectangles:
            elements = list(eval(rect))
            x1, y1, x2, y2 = int(elements[0]), int(elements[1]), int(elements[2]), int(elements[3])
            # 生成边框掩膜
            xx, yy = np.meshgrid(np.arange(x1, x2 + 1), np.arange(y1, y2 + 1))
            is_border = (
                    (xx >= x1) & (xx <= x2) &
                    (yy >= y1) & (yy <= y2) &
                    (
                            (xx == x1) | (xx == x2) |
                            (yy == y1) | (yy == y2)
                    )
            )
            # 应用颜色到RGBA波段
            for b in range(self.band_count):  # RGB通道
                valid_mask = (xx >= 0) & (xx < self.raster_size[0]) & (yy >= 0) & (yy < self.raster_size[1])
                self.band_data[b][yy[valid_mask], xx[valid_mask]] = np.where(
                    is_border[valid_mask],
                    color[b],
                    self.band_data[b][yy[valid_mask], xx[valid_mask]]
                )

    def batch_add_masks(self, masks):
        """批量添加透明遮罩"""
        # 预处理遮罩参数
        # 获取颜色值
        for m in masks:
            x1, y1, x2, y2 = int(m['center'][0]), int(m['center'][1]), int(m['center'][2]), int(m['center'][3])
            r, g, b, a = self.colors[m['color']]
            alpha = 0.3  # 转换为0-1范围
            # 提取区域数据
            region_r = self.band_data[0][y1:y2, x1:x2]
            region_g = self.band_data[1][y1:y2, x1:x2]
            region_b = self.band_data[2][y1:y2, x1:x2]
            region_a = self.band_data[3][y1:y2, x1:x2]

            content_mask = (region_r != 0) | (region_g != 0) | (region_b != 0)

            # 仅处理非纯黑区域
            if np.any(content_mask):
                # # 颜色混合计算
                blended_r = np.where(
                    content_mask,
                    (region_r * (1 - alpha)) + (r * alpha),
                    region_r
                )
                blended_g = np.where(
                    content_mask,
                    (region_g * (1 - alpha)) + (g * alpha),
                    region_g
                )
                blended_b = np.where(
                    content_mask,
                    (region_b * (1 - alpha)) + (b * alpha),
                    region_b
                )
                blended_a = np.where(
                    content_mask,
                    (region_a * (1 - alpha)) + (a * alpha),
                    region_a
                )
                # 写回数据
                self.band_data[0][y1:y2, x1:x2] = blended_r
                self.band_data[1][y1:y2, x1:x2] = blended_g
                self.band_data[2][y1:y2, x1:x2] = blended_b
                self.band_data[3][y1:y2, x1:x2] = blended_a

    def flush(self):
        """写回所有修改"""
        for b in range(self.band_count):
            self.dst_ds.GetRasterBand(b + 1).WriteArray(self.band_data[b].astype(np.uint8))
            self.dst_ds.GetRasterBand(b + 1).FlushCache()

    def close(self):
        self.src_ds = None
        self.dst_ds = None


def get_masks(lines_all, tif_width, tif_height, cut_size, red_warn, yellow_warn):
    red_pixel, yellow_pixel = 0, 0
    mask_list = list()
    for line in lines_all:
        line_array = line.split()
        count_area = line_array[2]
        f_name = line_array[0]
        # 将图片转换为RGBA模式，以便处理透明度
        x1, y1 = int(f_name.split('.')[0].split('_-_')[1]), int(f_name.split('.')[0].split('_-_')[2])
        x2, y2 = min(tif_width, int(f_name.split('.')[0].split('_-_')[1]) + (1 * cut_size[0])), min(tif_height,
                int(f_name.split('.')[0].split('_-_')[2]) + (1 * cut_size[1]))
        if line_array[1] != '0':
            # 如果小图的苗/亩数小于等于全部的苗/亩数*红色警告值
            # if float(count_area) <= total_count_area * red_warn:
            count_per_slice = int(line_array[3])  # todo 临时赋色方案，便于根据效果调整阈值，后续孙静改造
            if count_per_slice < red_warn:  # todo 临时赋色方案，后续孙静续改造float(count_area) <= total_count_area * red_warn
                red_pixel += int(line_array[1])
                mask_dict = dict()
                mask_dict['center'] = (x1, y1, x2, y2)
                mask_dict['color'] = 'red'
                mask_list.append(mask_dict)
            # 如果小图的苗/亩数小于等于全部的苗/亩数*黄色警告值且大于全部的苗/亩数*红色警告值
            # elif total_count_area * yellow_warn >= float(count_area) > total_count_area * red_warn:
            elif red_warn < count_per_slice < yellow_warn:  # todo 临时赋色方案，后续孙静续改造float(count_area) < = total_count_area * yellow_warn
                yellow_pixel += int(line_array[1])
                mask_dict = dict()
                mask_dict['center'] = (x1, y1, x2, y2)
                mask_dict['color'] = 'yellow'
                mask_list.append(mask_dict)
            else:
                # 无需着色
                continue
    return red_pixel, yellow_pixel, mask_list

def get_result(task_id, file_url, cut_path, predict_path, final_path, cut_size, allowed_types, predict_count,
               area_total, red_warn, yellow_warn, total_plot, total_coloring, total_box_color):
    """
        全量识别总方法
    Args:
        task_id: 任务id
        file_url: 传入的tif文件地址
        cut_path: 切图存入的文件夹地址
        predict_path: 预测文件存入的文件夹地址
        final_path: 结果文件存入的文件夹地址
        cut_size: 切图尺寸
        allowed_types: 允许预测的文件类型
        predict_count: 单次预测数量
        area_total: 总面积
        red_warn: 红色提醒百分比
        yellow_warn: 黄色提醒百分比

    Returns:
        count_area: 总的单位面积苗数
        red_percent: 红色占比
        yellow_percent: 黄色占比
    """
    # 切割图片，保存文本文件
    tif_width, tif_height, tiles_wide, tiles_high, total_pixel, size_list = split_tiff(file_url, cut_path, cut_size)
    # total_pixel = 287848
    print(f"total_pixel: {total_pixel}")
    count_total = get_predict_count(cut_path, predict_count, area_total, allowed_types, total_pixel, size_list)
    # count_total = 287848
    print(f"count_total:{count_total}")
    total_count_area = count_total / area_total
    yellow_percent, red_percent = 0, 0

    # output_path_tif = f"/home/ubuntu/Desktop/seed-tif/heshan/114-121/res/{file_name}.tif"
    output_path_tif = f"{final_path}/Seedling_Complete_{task_id}.tif"
    if total_plot or total_coloring:
        with open(f"{cut_path}/position-rect.txt", 'r') as file:
            # 获取所有行的数据
            lines = file.readlines()
        with open(f"{cut_path}/position-1.txt", 'r') as file:
            # 获取所有行的数据
            lines_all = file.readlines()
        # lines = list()
        # lines_all = list()
        renderer = AdvancedTifProcessor(file_url, output_path_tif)
        if total_plot:
            start = time.time()
            renderer.batch_draw_rectangles(lines, total_box_color)
            print(f"矩形绘制完成！耗时：{time.time() - start:.2f}秒")
        if total_coloring:
            red_pixel, yellow_pixel, mask_list = get_masks(lines_all, tif_width, tif_height, cut_size, red_warn, yellow_warn)
            start = time.time()
            renderer.batch_add_masks(mask_list)
            print(f"遮罩添加完成！耗时：{time.time() - start:.2f}秒")
            yellow_percent = yellow_pixel / total_pixel
            red_percent = red_pixel / total_pixel
        renderer.flush()
        renderer.close()
    print(f"处理完成，结果已保存至 {output_path_tif}")
    return total_count_area, red_percent, yellow_percent

