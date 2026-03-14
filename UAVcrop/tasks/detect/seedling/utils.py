from PIL import Image, ImageDraw, ImageFont
from sortedcontainers import SortedSet
import math
import os
from tasks.detect.seedling import config
from tasks.detect.seedling import predict
import imagesize
import numpy as np
from PIL.ExifTags import TAGS, GPSTAGS


def split_image(name, image_path, output_dir, cut_size):
    """
    切图方法（切图文件保存命名格式为：{源文件名}_-_{切图在原图中左上角像素x}_-_{切图在原图中左上角像素y}.{原图格式后缀}）
    Args:
        name: 文件名
        image_path: 文件路径
        output_dir: 切图保存路径
        cut_size: 切图尺寸

    Returns:
        w: 原图像素宽
        h: 原图像素高
        size_list: 切图中包含的不同尺寸集合
    """
    img = Image.open(image_path)
    size_list = SortedSet()
    w, h = img.size
    # 循环宽高
    for x in range(0, w, cut_size[0]):
        for y in range(0, h, cut_size[1]):
            # 切分的大小左上右下
            box = (x, y, min(x + cut_size[0], w), min(y + cut_size[1], h))
            size_list.add((min(x + cut_size[0], w) - x, min(y + cut_size[1], h) - y))
            img.crop(box).save(f"{output_dir}/{name.split('.')[0]}_-_{x}_-_{y}.{name.split('.')[1]}")
    return w, h, size_list


def is_file_type_size_within_range(file_path, allowed_types=config.ALLOWED_TYPES, size=None):
    """
    判断图片文件类型、文件尺寸是否符合要求
    Args:
        file_path: 图片文件路径
        allowed_types: 允许的图片类型
        size: 要求的图片尺寸

    Returns:
        res： True or False（是否符合要求）
    """
    res = False
    file_extension = os.path.splitext(file_path)[1].lower()[1:]  # 获取文件扩展名
    if size is not None:
        width, height = imagesize.get(file_path)
        if (width, height) == size and file_extension in allowed_types:
            res = True
    else:
        if file_extension in allowed_types:
            res = True
    return res


def reduce_quantity(class_ids, confidences, rects, cut_size):
    """
    对图片预测的结果进行减少处理（去掉边缘面积过小的框）
    Args:
        class_ids: 类别id列表
        confidences: 置信度列表
        rects: 标框像素坐标列表
        cut_size: 切图尺寸

    Returns:
        class_ids：处理后的类别id列表
        confidences：处理后的置信度列表
        rects：处理后的标框像素坐标列表
    """
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
                rect[0] == 0 or rect[1] == 0 or rect[2] == (cut_size[0] - 1) or rect[3] == (
                cut_size[1] - 1))) or (
                (rect[2] - rect[0]) * (rect[3] - rect[1]) < areas * 0.2):
            rects.pop(index)
            class_ids.pop(index)
            confidences.pop(index)
        index += 1
    print("处理后的长度：", len(class_ids))
    return class_ids, confidences, rects


def draw_boxes(rects, f, if_save_rect_txt, cut_path, if_draw_boxes, boxes_color, f_path=None, predict_path=None):
    """
    画框方法（适用于在切图上画框）
    Args:
        rects: 画框信息
        f: 文件名（切图的文件名）
        if_save_rect_txt: 是否在切图文件夹保存一份画框信息的txt文件
        cut_path: 切图路径
        if_draw_boxes: 是否画框
        f_path: 需要画框的图片路径
        draw: 需要画框的图片画笔
        boxes_color: 框的颜色
        predict_path: 保存的路径

    Returns:

    """
    global img, draw
    draw_list = list()
    if if_draw_boxes:
        img = Image.open(f_path)
        draw = ImageDraw.Draw(img)
    index = 0
    # 遍历最后的结果集
    while index < len(rects):
        # 置信取两位小数
        rect = rects[index]
        # 获取两个坐标点
        point1 = (int(rect[0]), int(rect[1]))
        point2 = (int(rect[2]), int(rect[3]))
        # 计算矩形的左上角和右下角
        left, top = point1[0], point1[1]
        right, bottom = point2[0], point2[1]
        index_i = int(f.split('.')[0].split('_-_')[1])
        index_j = int(f.split('.')[0].split('_-_')[2])
        if if_save_rect_txt:
            with open(f"{cut_path}/position-rect.txt", "a") as file_rect:
                file_rect.write(
                    f"({left + index_i}, {top + index_j}, {right + index_i}, {bottom + index_j})\n")
        if if_draw_boxes:
            draw_list.append((left + index_i, top + index_j, right + index_i, bottom + index_j))
            # 根据坐标点画框以及文本框
            draw.rectangle((left, top, right, bottom), None, boxes_color, 3)
        index += 1
    if if_draw_boxes:
        # 保存图片
        img.save(os.path.join(predict_path, f))
        print("保存识别后的结果图片")
    return draw_list


def get_predict_result(cut_path, size, predict_count, file_list, name_list, cut_size, predict_path, if_draw_boxes=config.PLOT,
                       if_reduce_quantity=config.IF_REDUCE_QUANTITY, boxes_color=config.SINGLE_COLOR, if_save_rect_txt=config.IF_SAVE_RECT_TXT_TOTAL):
    """
    获取预测结果
    Args:
        cut_path: 切图保存位置
        size: 预测的批量图片的尺寸
        predict_count: 单次批量预测图片数量
        file_list: 需要预测的文件全路径地址列表
        name_list: 需要预测的文件名列表（带后缀）
        cut_size: 切图尺寸
        predict_path: 预测结果图片保存位置
        if_draw_boxes: 是否对结果图片进行画框处理
        if_reduce_quantity: 是否对预测结果进行去边等减小数量的处理
        boxes_color: 画框颜色
        if_save_rect_txt: 是否将识别结果的框像素信息保存到cut文件夹下的position-rect.txt文件中

    Returns:
        list_counts: 本次识别到的的总苗数
    """
    for_counts = math.ceil(len(file_list) / predict_count)
    draw_list = list()
    list_counts = list()
    for i in range(for_counts):
        # 声明一个预测列表，之后用来存放预测的图片
        predict_list = list()
        # 声明一个预测文件名列表，之后用来存放预测的图片名
        predict_name_list = list()
        final_count = min((i + 1) * predict_count, len(file_list))
        for j in range(i * predict_count, final_count):
            predict_list.append(file_list[j])
            predict_name_list.append(name_list[j])
        print(f"需要进行预测的图片文件列表predict_list: {predict_list}")
        return_res_predicts = predict.get_predict_counts_total(predict_list, size)
        for m in range(len(return_res_predicts)):
            return_res_predict = return_res_predicts[m]
            f = predict_name_list[m]
            f_path = file_list[m]
            class_ids = return_res_predict['class_ids']
            confidences = return_res_predict['confidencs']
            rects = return_res_predict['rects']
            print(f"{f}文件识别出来的未处理数量为：{len(class_ids)}")
            if if_reduce_quantity:
                class_ids, confidences, rects = reduce_quantity(class_ids, confidences, rects, cut_size)
            draw_boxes(rects=rects, f=f, if_save_rect_txt=if_save_rect_txt, cut_path=cut_path, if_draw_boxes=if_draw_boxes
                       , f_path=f_path, boxes_color=boxes_color, predict_path=predict_path)
            list_counts.append(len(class_ids))
    return list_counts


def composite_image(file_url, predict_path, final_path, text, file_name):
    print(f"开始合成结果图片，参数为：\nfile_url:{file_url}\npredict_path:{predict_path}\nfinal_path:{final_path}\ntext:{text}")
    """
    识别后的结果图合成原图
    Args:
        file_url: 原图路径
        predict_path: 预测结果图保存路径
        final_path: 结果图保存路径
        text: 原图上写字内容
        file_name: 原图名

    """
    # 1. 将预测结果图合成大图
    # 创建一个新的图像来容纳所有小图像
    original_image = Image.open(file_url)
    new_image = Image.new('RGB', original_image.size, (255, 255, 255))
    for f in os.listdir(predict_path):
        if f.split('_-_')[0] == file_name.split('.')[0]:
            path = predict_path + '/' + f
            f_name = f.split('.')[0]
            image = Image.open(path)
            new_image.paste(image, (int(f_name.split('_-_')[1]), int(f_name.split('_-_')[2])))
            image.close()
    # 保存合并后的图像
    draw = ImageDraw.Draw(new_image)
    font = ImageFont.truetype(config.FONT_URL, 100)
    # 写字
    draw.text((10, 10), text, font=font, fill=(255, 255, 255))

    # 保存新图片（这里保存为JPG格式，你可以根据需要选择其他格式）
    new_image_path = final_path + "/" + file_name
    new_image.save(new_image_path)


def generate_array_no_loop(start, step, end):
    """
    跳跃固定步长，生成数组，以start开头，end结尾
    Args:
        start: 数组起始值
        step: 步长
        end: 数组结束值

    Returns:
        生成的数组
    """
    # 计算需要多少步才能达到或超过end
    n = (end + step - 1) // step  # 向上取整
    # 生成等差数列
    array = np.arange(start, n * step, step)
    # 检查最后一个元素是否超过end
    if array[-1] > end:
        # 如果超过，则替换最后一个元素为end
        array[-1] = end
    # 如果最后一个元素仍然小于end（理论上不应该发生），则添加end到数组
    elif array[-1] < end:
        array = np.append(array, end)
    return array.tolist()


def get_exif_data(image):
    """
    获取图片的EXIF数据，并尝试解析GPS信息
    """
    exif_data = {}
    try:
        if hasattr(image, '_getexif') and callable(image._getexif):
            info = image._getexif()
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        gps_data = {}
                        for t in value:
                            sub_decoded = GPSTAGS.get(t, t)
                            gps_data[sub_decoded] = value[t]
                        exif_data[decoded] = gps_data
                    else:
                        exif_data[decoded] = value
        else:
            print("警告：无法从Image对象中获取EXIF数据。")
    except Exception as e:
        print(e)
    finally:
        return exif_data


def set_exif_data(image, exif_data):
    """
    将EXIF数据设置回图片
    """
    exif_ifd = {
        TAGS[k]: v for k, v in exif_data.items()
        if k in TAGS and k not in [0x0000, 0x0001, 0x0002]  # 排除一些不需要的标签
    }
    image.info["exif"] = exif_ifd
    return image


def get_gps_info_save(file_url, file_name, final_path):
    """
    保存gps信息
    Args:
        file_url: 源文件路径
        file_name: 文件名
        final_path: 最终保存路径

    Returns:

    """
    original_image = Image.open(file_url)
    new_image = Image.open(os.path.join(final_path, file_name))
    exif_data = get_exif_data(original_image)
    new_image_path = final_path + "/" + file_name
    try:
        if "GPSInfo" in exif_data:
            gps_info = exif_data["GPSInfo"]
            print("GPS信息:")
            for key, value in gps_info.items():
                print(f"  {key}: {value}")
            # 将原始EXIF数据设置到新图片中
            set_exif_data(new_image, exif_data)
            # 保存新图片（这里保存为JPG格式，你可以根据需要选择其他格式）
            new_image.save(new_image_path, exif=original_image.info.get("exif"))
            print(f"图片已保存至 {new_image_path}，并尝试保留GPS信息。")
        else:
            print("图片中不包含GPS信息。")
    except KeyError:
        print("发生KeyError，图片中不包含GPSInfo键，因此不包含GPS信息。")
    finally:
            print(f"图片已保存至 {new_image_path}，并尝试保留GPS信息。")





