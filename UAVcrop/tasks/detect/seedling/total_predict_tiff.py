import math
import time
import rasterio
from PIL import Image, ImageFile
import numpy as np
import tasks.detect.seedling.predict as predict
import tasks.detect.seedling.utils as utils
import tasks.detect.seedling.config as config
import os
import cv2
from sortedcontainers import SortedSet
import bisect

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


def count_non_empty(arr):
    count = 0
    for item in arr:
        if item is not None and item != '':  # 根据需要，你可以调整条件
            count += 1
    return count


def split_tiff(input_filename, output_prefix, tile_size):
    """

    Args:
        input_filename: tif文件地址
        output_prefix: 切图保存路径
        tile_size: 切图尺寸

    Returns:
        tif_width: tif文件像素宽
        tif_height: tif文件像素高
        tiles_wide: 横向切割图片数
        tiles_high: 纵向切割图片数
        total_pixel: tif文件总有效像素数
    """
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
        tif_width = img.width
        tif_height = img.height
        # 计算分割后的图片数量
        tiles_wide = math.ceil(img.width / tile_size[0])
        tiles_high = math.ceil(img.height / tile_size[1])
        size_list = SortedSet()
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
                # 将切割后的图片保存为jpg
                if len(data.shape) == 3:
                    r = red[start_h:end_h, start_w:end_w]
                    g = green[start_h:end_h, start_w:end_w]
                    b = blue[start_h:end_h, start_w:end_w]
                    # 将几何区域转换为窗口
                    # 计算所有不为0的像素数量，并打印
                    # 合并为 (高度, 宽度, 3) 的数组
                    img_rgb = np.dstack((r, g, b))
                    # 检查任一通道非零（注意数据类型可能为 uint8）
                    nonzero_mask = np.any(img_rgb != 0, axis=-1)
                    non_zero_count = np.sum(nonzero_mask)
                    print(f"output_image-{i}-{j}---Pixel values: {non_zero_count}")
                    # 在总的有效像素上加上当前栅格的有效像素数
                    total_pixel += non_zero_count
                    # 将RGB图像转换为Pillow图像并保存为JPG格式，命名格式为output_image-横向序列号-纵向序列号.jpg
                    jpg_image = f'{output_prefix}/output_image_-_{i * tile_size[0]}_-_{j * tile_size[1]}.jpg'
                    pil_image = Image.fromarray(img_rgb.astype('uint8'), 'RGB')
                    size_list.add(pil_image.size)
                    """
                    JPEG格式
                        参数名: quality
                        默认值: 75（范围1-95，值越高质量越好，文件越大）
                        示例: img.save("output.jpg", quality=75)  # 高质量保存
                    PNG格式
                        参数名: compress_level（压缩级别，非直接质量参数）
                        默认值: 6（范围0-9，0表示不压缩，9表示最大压缩但最慢）
                        注意: PNG是无损格式，compress_level影响文件大小和保存速度，不直接影响视觉质量。
                        示例: img.save("output.png", compress_level=9)  # 最小文件体积
                    其他格式
                        WEBP: 支持quality参数（默认80）和lossless（无损模式）。
                        TIFF: 支持compression参数（如"tiff_lzw"）。
                        GIF: 无质量参数，但支持dither（抖动）控制。
                    """
                    pil_image.save(jpg_image, 'JPEG')
                    # 位置信息保存在文档中
                    with open(f"{output_prefix}/position.txt", "a") as file:
                        file.write(
                            f"output_image_-_{i * tile_size[0]}_-_{j * tile_size[1]}.jpg {top} {left} {bottom} {right} {non_zero_count}\n")
                        print("File has been created successfully.")
                else:
                    print("图像output_prefix不是彩色图像，无需处理。")
        print(f"有图的总像素数：{total_pixel}")
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
                    if line_array[5] != '0':
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
            # with open(f"{output_prefix}/position-rect.txt", "a") as file_rect:
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
                    area_percent = int(line_array[5]) / total_pixel
                    count_area = count / (area_total * area_percent)
                    line = line.replace("\n", " ")
                    line += str(count_area) + " " + str(count) + "\n"
                    count_total += count
                    lines[line_i_list[index_count]] = line
        file.writelines(lines)
    return count_total


def draw_box_color(file_url, lines, lines_all, cut_size, red_warn, yellow_warn, output_path_tif, total_count_area, total_plot, total_coloring, total_box_color):
    """
        画框和渲染
    Args:
        lines: 画框信息
        lines_all: 图片信息

    """
    with rasterio.open(file_url) as img:
        profile = img.profile
        red = img.read(1)  # 1代表红色波段的索引
        # 获取绿色波段（波长：545-565nm）
        green = img.read(2)  # 2代表绿色波段的索引
        # 获取蓝色波段（波长：459-479nm）
        blue = img.read(3)  # 3代表蓝色波段的索引
        band4 = img.read(4)  # 4代表alpha波段的索引
        data = img.read()  # c,h,w
        whole_pic = np.transpose(data, (1, 2, 0))  # h,w,c
        yellow_pixel = 0
        red_pixel = 0

        # 画框
        if total_plot:
            for line in lines:
                elements = list(eval(line))
                x, y, x2, y2 = int(elements[0]), int(elements[1]), int(elements[2]), int(elements[3])
                # 绘制彩色框（所有RGB波段）
                channel_list = [red, green, blue]
                for index in range(len(channel_list)):
                    cv2.rectangle(channel_list[index], (x, y), (x2, y2), total_box_color[index], 2)

        # 图层
        start_time = time.time()
        if total_coloring:
            # 创建透明遮罩
            for line in lines_all:
                line_array = line.split()
                count_area = line_array[6]
                f_name = line_array[0]
                # 将图片转换为RGBA模式，以便处理透明度
                x1, y1 = int(f_name.split('.')[0].split('_-_')[1]), int(f_name.split('.')[0].split('_-_')[2])
                x2, y2 = min(img.width, (int(f_name.split('.')[0].split('_-_')[1]) + 1) * cut_size[0]), min(img.height, (
                        int(f_name.split('.')[0].split('_-_')[2]) + 1) * cut_size[1])
                r = red[y1:y2, x1:x2]
                g = green[y1:y2, x1:x2]
                b = blue[y1:y2, x1:x2]
                img_rgb = np.dstack((r, g, b))
                # 将RGB图像转换为Pillow图像并保存为JPG格式，命名格式为output_image-横向序列号-纵向序列号.jpg
                pil_image = Image.fromarray(img_rgb.astype('uint8'), 'RGB')
                if line_array[5] != '0':
                    # 如果小图的苗/亩数小于等于全部的苗/亩数*红色警告值
                    # if float(count_area) <= total_count_area * red_warn:
                    count_per_slice = int(line_array[7]) # todo 临时赋色方案，便于根据效果调整阈值，后续孙静改造
                    if count_per_slice < red_warn:  # todo 临时赋色方案，后续孙静续改造float(count_area) <= total_count_area * red_warn
                        red_pixel += int(line_array[5])
                        red_layer = Image.new('RGBA', pil_image.size, (255, 0, 0, 100))
                        result = Image.alpha_composite(pil_image.convert('RGBA'), red_layer)
                    # 如果小图的苗/亩数小于等于全部的苗/亩数*黄色警告值且大于全部的苗/亩数*红色警告值
                    # elif total_count_area * yellow_warn >= float(count_area) > total_count_area * red_warn:
                    elif red_warn < count_per_slice < yellow_warn:  # todo 临时赋色方案，后续孙静续改造float(count_area) < = total_count_area * yellow_warn
                        yellow_pixel += int(line_array[5])
                        yellow_layer = Image.new('RGBA', pil_image.size, (255, 255, 0, 100))  # 初始透明度为0
                        result = Image.alpha_composite(pil_image.convert('RGBA'), yellow_layer)
                    else:
                        # 无需着色
                        continue

                    # 获取着色后的小图
                    pic_slice = np.array(result)  # h,w,c
                    slice_height, slice_width, channel_count = pic_slice.shape
                    # 获取待覆盖像素
                    indexes_to_replace = ~np.all(whole_pic[:, :, :3] == 0, axis=2)
                    # 找到小图要替换的掩码区域
                    replace_mask = indexes_to_replace[y1:y1 + slice_height, x1:x1 + slice_width]

                    # 用广播方式替换指定区域的像素
                    # 只替换掩码为 True 的像素
                    for channel, index in zip([red, green, blue, band4], range(channel_count)):  # 对每个通道单独处理
                        channel[y1:y1 + slice_height, x1:x1 + slice_width][replace_mask] = pic_slice[..., index][replace_mask]

        with rasterio.open(output_path_tif, 'w', **profile) as dst:
            dst.write(red, 1)  # 写入数据到第一个波段
            dst.write(green, 2)  # 写入数据到第一个波段
            dst.write(blue, 3)  # 写入数据到第一个波段
            dst.write(band4, 4)  # 写入数据到第一个波段

        end_time = time.time()
        print('cost %.2fs  to render' % (end_time - start_time))
    return red_pixel, yellow_pixel


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
    # 总的预测数量
    # total_pixel = 287848
    print(f"total_pixel: {total_pixel}")
    count_total = get_predict_count(cut_path, predict_count, area_total, allowed_types, total_pixel, size_list)
    # count_total = 287848
    print(f"count_total:{count_total}")
    total_count_area = count_total / area_total
    # total_count_area = 20
    output_path_tif = f"{final_path}/Seedling_Complete_{task_id}.tif"
    with open(f"{cut_path}/position-rect.txt", 'r') as file:
        # 获取所有行的数据
        lines = file.readlines()
    with open(f"{cut_path}/position-1.txt", 'r') as file:
        # 获取所有行的数据
        lines_all = file.readlines()
    red_pixel, yellow_pixel = draw_box_color(file_url, lines, lines_all, cut_size, red_warn, yellow_warn, output_path_tif, total_count_area, total_plot, total_coloring, total_box_color)
    yellow_percent = yellow_pixel / total_pixel
    red_percent = red_pixel / total_pixel
    print(f"处理完成，结果已保存至 {output_path_tif}")
    return total_count_area, red_percent, yellow_percent
    # return 0, 0, 0

