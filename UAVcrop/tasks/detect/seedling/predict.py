## python版本：Python 3.10.14 (main, May  6 2024, 19:42:50) [GCC 11.2.0] on linux
# from ultralytics import YOLO
import json
import tasks.detect.seedling.config as con
import tasks.detect.seedling.utils as utils
from PIL import Image, ImageDraw, ImageFont
import requests
from tasks.service.http.utils import upload_file
from tasks.service.http import config

# 加载模型
# model = YOLO(config.MODEL_PATH)
# url = config.PREDICT_SOURCE

# 图像检测
## 该函数输出
"""
[{"confidencs": [0.6119052767753601, 0.2301657497882843, 0.22618919610977173], 
"class_ids": [7, 0, 7], 
"rects": [[68, 53, 617, 237], [152, 88, 177, 116], [68, 53, 256, 237]]}]
confidencs代表置信度，class_ids为类别，rects为在图片绘制矩形的x1,y1,x2,y2坐标
数组中的一个json对象为一张图片
"""


def yolo_detect(source, size):
    # 读取图片字节流
    # img = Image.open(BytesIO(img_byte))
    res = []
    # response_post = requests.post(con.PREDICT_URL, data=json.dumps({'urls': source}))
    files = list()
    for file in source:
        file_name = file.split('/')[-1]
        files.append(('files', (file_name, open(file, 'rb'), 'image/jpeg')))
    url = con.BATCH_FILE_URL
    param_dict = dict()
    param_dict['imgsz'] = size
    param_dict['max_det'] = con.MAX_DET
    param_dict['conf'] = con.PREDICT_CONF
    headers = {}
    response_post = requests.request("POST", url, headers=headers, data=param_dict, files=files)
    if response_post.status_code == 200:
        results = response_post.json()
        if results['success'] == True:
            resu = results['data']['detail']
            resu = eval(resu)
            # 使用模型做推理
            # results = model.predict(source=source, conf=config.PREDICT_CONF, iou=config.PREDICT_IOU,
            #                         max_det=config.PREDICT_MAX_DET,
            #                         save=config.PREDICT_SAVE, show_labels=config.PREDICT_SHOW_LABELS)
            for result in resu:
                confidences, class_ids, rects = result['confidencs'], result['class_ids'], result['rects']
                res.append({'confidencs': confidences, 'class_ids': class_ids, 'rects': rects})
    return res


def draw_bboxes(if_text: bool, class_ids: list, rects: list, confidencs: list, areas: float,
                file_path_predict: str, output_path: str, if_write: bool, area: float):
    img = Image.open(file_path_predict)
    width, height = img.size
    i = 0
    while i < len(class_ids):
        rect = rects[i]
        if (((rect[2] - rect[0]) * (rect[3] - rect[1]) < areas * 0.5) and (
                rect[0] == 0 or rect[1] == 0 or rect[2] == (width - 1) or rect[3] == (height - 1))) or (
                (rect[2] - rect[0]) * (rect[3] - rect[1]) < areas * 0.2):
            rects.pop(i)
            class_ids.pop(i)
            confidencs.pop(i)
        i += 1

    print("处理后的长度：", len(class_ids))
    i = 0
    count_area = 0
    # 遍历最后的结果集
    while i < len(confidencs):
        # 置信取两位小数
        confidence = round(confidencs[i], 2)
        class_id = class_ids[i]
        rect = rects[i]
        # 设置默认的（类型为0时）线和字体的颜色
        line_color = 'red'
        font_color = 'black'
        # 设置文本，文本框长度
        text = 'dadou ' + str(confidence)
        length_text = 95
        # 更改当类型为其他时的文本/颜色/字体颜色
        if class_id == 1:
            line_color = 'red'
            font_color = 'white'
            text = 'shuidao ' + str(confidence)
            length_text = 105
        if class_id == 2:
            line_color = 'red'
            font_color = 'white'
            text = 'yumi ' + str(confidence)
        # 获取两个坐标点
        point1 = (int(rect[0]), int(rect[1]))
        point2 = (int(rect[2]), int(rect[3]))
        # 计算矩形的左上角和右下角
        left, top = min(point1[0], point2[0]), min(point1[1], point2[1])
        right, bottom = max(point1[0], point2[0]), max(point1[1], point2[1])
        # 绘制矩形，当上方高度不够时文本框改在下方
        x1, y1 = left, top - 20
        x2, y2 = left + length_text, top
        if y1 < 0:
            y1 = top
            y2 = top + 20
        # 根据坐标点画框以及文本框
        draw = ImageDraw.Draw(img)
        draw.rectangle((left, top, right, bottom), None, line_color, 3)
        if if_text:
            draw.rectangle((x1, y1, x2, y2), line_color, line_color, 1)
            # 设置字体和大小
            font = ImageFont.truetype("SimHei.ttf", 20)
            # 写字
            draw.text((x1, y1), text, font=font, fill=font_color)
        if if_write:
            font = ImageFont.truetype("SimHei.ttf", 20)
            # 写字
            text = f"counts: {len(class_ids)}\ncounts/area: {len(class_ids) / area}"
            count_area = len(class_ids) / area
            # 写字
            draw.text((10, 10), text, font=font, fill=(255, 255, 255))
        i += 1
    # 保存图片
    img.save(output_path)
    return len(class_ids), count_area


def draw_bboxes_for_sampling(if_text: bool, class_ids: list, rects: list, confidencs: list, file_path_predict: str,
                             output_path: str, if_write: bool, area: float, cut_size, sampling_box_color, f, cut_path,
                             predict_path):
    if con.IF_REDUCE_QUANTITY:
        utils.reduce_quantity(class_ids, confidencs, rects, cut_size)
    utils.draw_boxes(rects=rects, f=f, if_save_rect_txt=con.IF_SAVE_RECT_TXT_SAMPLING, cut_path=cut_path, if_draw_boxes=True, f_path=file_path_predict, boxes_color=sampling_box_color, predict_path=predict_path)
    count_area = len(class_ids) / area
    return len(class_ids), count_area, class_ids, confidencs, rects


def get_predict_counts(file_path_predict, predict_name_list, output_path, if_write, area_list):
    list_url = list()
    for e in file_path_predict:
        list_url.append(upload_file(config.upload_url, e))
    return_res_predicts = yolo_detect(list_url)
    return_res_predicts = json.loads(return_res_predicts)
    counts = list()
    count_areas = list()
    for i in range(len(return_res_predicts)):
        import_path = file_path_predict[i]
        return_res_predict = return_res_predicts[i]
        f = predict_name_list[i]
        if if_write:
            area_pic = area_list[i]
        else:
            area_pic = 0
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
        count, count_area = draw_bboxes(False, class_ids, rects, confidencs, areas, import_path, output_path + "/" + f,
                                        if_write, area_pic)
        counts.append(count)
        count_areas.append(count_area)
    return counts, count_areas


def get_predict_counts_for_sampling(size, file_path_predict, predict_name_list, output_path, if_write, area_list,
                                    import_img_sampling_exit, cut_size, sampling_box_color, cut_path):
    # list_url = list()
    # for e in file_path_predict:
    #     list_url.append(upload_file(config.upload_url, e))
    return_res_predicts = yolo_detect(file_path_predict, size)
    # return_res_predicts = json.loads(return_res_predicts)
    counts = list()
    count_areas = list()
    class_ids_list = list()
    rects_list = list()
    confidence_list = list()
    for i in range(len(return_res_predicts)):
        import_path = file_path_predict[i]
        return_res_predict = return_res_predicts[i]
        f = predict_name_list[i]
        area_pic = area_list[i]
        class_ids = return_res_predict['class_ids']
        confidencs = return_res_predict['confidencs']
        rects = return_res_predict['rects']
        print("未进行处理前长度为：", len(class_ids))
        count, count_area, class_ids_res, confidencs_res, rects_res = draw_bboxes_for_sampling(False, class_ids,
                                                                                               rects, confidencs,
                                                                                               import_path,
                                                                                               output_path + "/" + f,
                                                                                               if_write, area_pic,
                                                                                               cut_size,
                                                                                               sampling_box_color, f,
                                                                                               cut_path, output_path)
        for j in range(len(class_ids_res)):
            rect = rects_res[j]
            confidencs = confidencs_res[j]
            class_ids = class_ids_res[j]
            point1 = (int(rect[0]), int(rect[1]))
            point2 = (int(rect[2]), int(rect[3]))
            left, top = min(point1[0], point2[0]), min(point1[1], point2[1])
            right, bottom = max(point1[0], point2[0]), max(point1[1], point2[1])
            i, j = int(import_path.split('_-_')[1]), int(import_path.split('_-_')[2].split('.')[0])
            rect_new = list()
            rect_new.append(left + i)
            rect_new.append(top + j)
            rect_new.append(right + i)
            rect_new.append(bottom + j)
            import_img_sampling_exit[f.split('_-_')[0] + '.' + f.split('.')[1]][7].append(rect_new)
            import_img_sampling_exit[f.split('_-_')[0] + '.' + f.split('.')[1]][6].append(class_ids)
            import_img_sampling_exit[f.split('_-_')[0] + '.' + f.split('.')[1]][8].append(confidencs)
        import_img_sampling_exit[f.split('_-_')[0] + '.' + f.split('.')[1]][5] += count
        counts.append(count)
        count_areas.append(count_area)
        class_ids_list.append(class_ids_res)
        rects_list.append(rects_res)
        confidence_list.append(confidencs_res)
    return counts, count_areas, class_ids_list, confidence_list, rects_list, import_img_sampling_exit


def get_predict_counts_total(file_path_predict, size):
    # list_url = list()
    # for e in file_path_predict:
    #     list_url.append(upload_file(config.upload_url, e))
    return_res_predicts = yolo_detect(file_path_predict, size)
    return return_res_predicts
