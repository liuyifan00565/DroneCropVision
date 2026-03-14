import os
from tasks.detect.seedling import utils
from tasks.detect.seedling import config
import math
from PIL import Image, ImageDraw
import random


def get_predict_result(cut_path, predict_path, predict_count, size_list, cut_size, single_box_color):
    """
    获取切图识别结果，将识别的rect结果保存到txt中，获得原图中识别到的总苗数
    Args:
        cut_path: 切图文件保存路径
        predict_path: 预测图片文件保存路径
        predict_count: 单次批量预测的图片数量
        size_list: 切图中包含的不同尺寸集合
        cut_size: 切图尺寸

    Returns:

    """
    total_counts = 0
    # 每个尺寸分别识别
    for size in size_list:
        name_list = list()
        file_list = list()
        for f in os.listdir(cut_path):
            # 声明需要预测的文件名与文件路径列表
            cut_pic_path = os.path.join(cut_path, f)
            # 判断是符合格式与尺寸要求的文件
            res = utils.is_file_type_size_within_range(file_path=cut_pic_path, size=size)
            if os.path.isfile(os.path.join(cut_path, f)) and res:
                file_list.append(os.path.join(cut_path, f))
                name_list.append(f)
        # 本轮尺寸下预测的苗数
        list_counts = utils.get_predict_result(cut_path=cut_path, size=size, predict_count=predict_count, file_list=file_list, name_list=name_list,
                                               cut_size=cut_size, predict_path=predict_path, if_draw_boxes=True, if_reduce_quantity=False,
                                               boxes_color=single_box_color, if_save_rect_txt=config.IF_SAVE_RECT_TXT_SINGLE)
        # 总苗数相加
        total_counts += sum(list_counts)
    return total_counts


def count_boxes_in_regions_color(lines, little_size, area_measure, final_path, file_name, red_warn, yellow_warn):
    print(f"开始添加框和颜色，参数为：lines:{lines}, area_measure:{area_measure}, final_path:{final_path}, file_name:{file_name}")
    """
    获取每块小区域中包含的框的数量
    Args:
        lines(list of tuple): 框的坐标列表，每个框由(左上x, 左上y, 右下x, 右下y)表示。
        little_size: 小区域的大小
        area_measure: 每个像素代表的厘米
        final_path: 最终图片宝轮路径
        red_warn: 补苗临界值（苗/亩）
        yellow_warn: 警告临界值（苗/亩）

    Returns:
    """
    img = Image.open(os.path.join(final_path, file_name)).convert("RGBA")
    width, height = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for_x_count = math.ceil(width / little_size[0])
    for_y_count = math.ceil(height / little_size[1])
    for i in range(for_x_count):
        for j in range(for_y_count):
            left, top = i * little_size[0], j * little_size[1]
            right, bottom = min((i + 1) * little_size[0], width), min((j + 1) * little_size[1], height)
            # 当前区域内的框总数
            box_counts = 0
            for line in lines:
                elements = list(eval(line))
                x1, y1, x2, y2 = int(elements[0]), int(elements[1]), int(elements[2]), int(elements[3])
                # 左上、右下任意一个点在box内就算数
                if (left <= x1 <= right and top <= y1 <= bottom) or (left <= x2 <= right and top <= y2 <= bottom):
                    box_counts += 1
            # 当前区域内的实际面积
            area_box = ((right - left) * area_measure) * ((bottom - top) * area_measure) / (10000 * 666.6666666666666)
            box = (left, top, right, bottom)
            red_count = red_warn * area_box
            yellow_count = yellow_warn * area_box
            # 判断是否需要给颜色渲染
            if box_counts < red_count:
                # 绘制红色半透明矩形
                draw.rectangle(box, fill=(255, 0, 0, 100))
            elif red_count < box_counts < yellow_count:
                # 绘制黄色半透明矩形
                draw.rectangle(box, fill=(255, 255, 0, 100))
            else:
                continue
    # 合并图层
    combined = Image.alpha_composite(img, overlay)
    # 保存图片为JPEG格式（注意：JPEG不支持透明度，因此需要先转换为RGB模式）
    combined.convert("RGB").save(os.path.join(final_path, file_name), "JPEG")
    return


def render_colors(file_url, file_name, area_measure, red_warn, yellow_warn, final_path,
                  little_size, predict_path, count_area, res_test, total_counts, cut_path):
    print("-----------------开始渲染图片-----------------")
    # 原图写字内容
    # count_area = random.uniform(5800, 6100)
    text = f"苗数: {total_counts}\n亩苗数: {math.ceil(count_area)}\n状态：{res_test}"
    # text = f"苗数: {total_counts}\n亩苗数: {math.ceil(count_area)}\n状态：正常"
    # 预测结果图合成图片
    utils.composite_image(file_url, predict_path, final_path, text, file_name)
    with open(f"{cut_path}/position-rect.txt", 'r') as file:
        # 获取所有行的数据
        lines = file.readlines()
    print("获取lines成功")
    count_boxes_in_regions_color(lines, little_size, area_measure, final_path, file_name, red_warn, yellow_warn)


def get_result(area_measure, file_url, file_name, red_warn_single, yellow_warn_single, expect_counts, cut_path,
               predict_path, final_path, cut_size, predict_count, single_box_color, little_size):
    """
    单张识别入口方法
    Args:
        area_measure: 每像素代表的厘米数
        file_url: 文件路径
        file_name: 文件名称
        red_warn_single: 单张识别的红色警戒值（补苗阈值）
        yellow_warn_single: 单张识别的黄色警戒值（观察阈值）
        expect_counts: 标准苗（穴）数（单位/亩）
        cut_path: 切图保存路径
        predict_path: 预测结果图保存路径
        final_path: 最终结果保存路径
        cut_size:切图尺寸
        predict_count: 单次批量预测的图片数量
        single_box_color: 单张识别画框的颜色

    Returns:

    """
    print('-----------------进入单张识别-----------------')
    # 1. 切图，返回全图的长宽像素数及尺寸集，计算总面积
    with open(f"{cut_path}/position-rect.txt", "w") as file:
        pass
    # 1.1 获取原图像素宽、高、切图的不同尺寸集合
    pic_width, pic_height, size_list = utils.split_image(file_name, file_url, cut_path, cut_size)
    # 1.2 计算原图实际占地面积
    total_area_act = (pic_width * area_measure) * (pic_height * area_measure) / (10000 * 666.6666666666666)
    print(f"原图所代表的实际面积为：{total_area_act}亩")
    # 2. 获取切图识别结果，将识别的rect结果保存到txt中，保存切图识别结果带框图并合成，获得原图中识别到的总苗数
    total_counts = get_predict_result(cut_path, predict_path, predict_count, size_list, cut_size, single_box_color)
    print(f"识别到的总苗数为：{total_counts}")
    # 3. 单位面积个数（穴/亩）,取两位小数
    count_area = round(total_counts/total_area_act, 2)
    print(f"平均每亩的苗数为：{count_area}")
    # 4. 计算照片识别的单位面积个数在什么区间内（需补苗、需观察、正常）
    # 需补苗的阈值为：
    red_warn = int(expect_counts) * float(red_warn_single)
    # 需观察的阈值为：
    yellow_warn = int(expect_counts) * float(yellow_warn_single)
    if count_area < red_warn:
        res_test = "需补苗"
    elif red_warn < count_area < yellow_warn:
        res_test = "需观察"
    else:
        res_test = "正常"
    print(f"图片识别后给出的建议为：{res_test}，红色警告值为{red_warn}苗/亩，黄色警告值为{yellow_warn}苗/亩")
    # 5. 打开大图，切小块判断亩苗数的比例区间，渲染颜色，保存最终结果图片
    render_colors(file_url, file_name, area_measure, red_warn, yellow_warn, final_path, little_size, predict_path, count_area, res_test, total_counts, cut_path)
    # 6. 判断是否有gps信息，有就给最终图片加上
    utils.get_gps_info_save(file_url, file_name, final_path)
    return res_test, total_counts, count_area, os.path.join(final_path, file_name)



