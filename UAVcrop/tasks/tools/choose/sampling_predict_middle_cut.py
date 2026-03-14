import os
import random
import scipy.stats as stats
import math
from tasks.detect.seedling import predict as predict
from PIL import Image
import requests
import re


def download_image(url, save_directory='.'):
    """
    下载URL中的图像并保存到指定目录。
    参数:
    url (str): 图像的URL。
    save_directory (str): 保存图像的目录，默认为当前目录。如果目录不存在，则创建该目录。
    返回:
    str: 保存的文件路径。
    """
    # 从URL中提取文件名
    file_name = url.split('/')[-1]
    # 如果 save_directory 不存在，则创建它
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        print(f"目录 {save_directory} 已创建。")
    # 创建保存路径
    file_path = os.path.join(save_directory, file_name)
    # 发送HTTP请求获取图像内容
    response = requests.get(url)
    # 检查请求是否成功
    if response.status_code == 200:
        # 将图像内容写入到本地文件
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"图像已保存为 {file_path}")
        return file_path, file_name
    else:
        print(f"无法下载图像，HTTP状态码: {response.status_code}")
        return None


# 检查文件扩展名是否在指定的文件类型列表内
def is_file_type_within_range(file_path, allowed_types):
    file_extension = os.path.splitext(file_path)[1].lower()[1:]  # 获取文件扩展名
    return file_extension in allowed_types


# 获取文件夹中的文件数量
def count_files_in_directory(import_img_sampling_exit, import_file_list, allowed_types):
    print("count_files_in_directory()")
    count = 0
    for file_dict in import_file_list:
        url = file_dict['url']
        width = file_dict['width']
        height = file_dict['height']
        area = file_dict['area']
        if is_file_type_within_range(url, allowed_types):
            list_info = list()
            list_info.append(True)
            list_info.append(url)
            list_info.append(width)
            list_info.append(height)
            list_info.append(area)
            file_name = url.split('/')[-1]
            import_img_sampling_exit[file_name] = list_info
            count += 1
    return count, import_img_sampling_exit


# 获取标准正太分布值
def get_z_value_from_percentile(p):
    # 获取标准正态分布的Z值
    z_value = stats.norm.interval(p, loc=0, scale=1)
    return z_value


# t 分布
def get_t_value_from_percentile(df, confidence):
    alpha = 1 - confidence
    t_dist = stats.t(df)
    q = t_dist.ppf(1 - alpha / 2)
    return q


# 切分图片
def split_image(name, image_path, output_dir, cut_size, import_img_sampling_exit):
    print("split_image()", image_path)
    img = Image.open(image_path)
    list_info = import_img_sampling_exit[name]
    width = list_info[2]
    height = list_info[3]
    left = int((width - cut_size[0]) // 2)
    top = int((height - cut_size[1]) // 2)
    right = left + cut_size[0]
    bottom = top + cut_size[1]
    box = (left, top, right, bottom)
    img.crop(box).save(f"{output_dir}/{name.split('.')[0]}_-_{left}_-_{top}.{name.split('.')[1]}")
    img.close()


# 获取图片宽高
def get_image_dimensions_pil(image_path):
    with Image.open(image_path) as image:
        width, height = image.size
    return width, height


# 获取图片预测结果
def get_first_sampling_result(import_file_choose_list, sampling_count, import_img_sampling_exit, download_path,
                              cut_path, predict_count,
                              predict_path, allowed_types, cut_size):
    print("get_first_sampling_result()", sampling_count)
    list_sampling = list()
    class_ids_list = list()
    confidence_list = list()
    rects_list = list()
    # 抽取的样品图片列表和切图的列表
    list_sampling_total = list()
    # 在字典中找到没有被抽样过的文件放入集合
    for key in import_img_sampling_exit:
        if import_img_sampling_exit[key][0]:
            list_sampling_total.append(key)
    if len(list_sampling_total) >= sampling_count:
        # 选出30张样本图片进行切图
        random_subset = random.sample(list_sampling_total, sampling_count)
    else:
        random_subset = list_sampling_total
    print("抽取的大图为：", random_subset)
    # 遍历抽样列表
    for import_img in random_subset:
        import_file_choose_list.append(import_img_sampling_exit[import_img][1])
        # 更改图片抽取状态
        import_img_sampling_exit[import_img][0] = False
        # 下载图片
        file_path, file_name = download_image(import_img_sampling_exit[import_img][1], download_path)
        # 切图
        split_image(import_img, file_path, cut_path, cut_size, import_img_sampling_exit)
    # 获取预测样本总数
    random_subset_cut = list()
    for f in os.listdir(cut_path):
        if os.path.isfile(os.path.join(cut_path, f)) and is_file_type_within_range(os.path.join(cut_path, f),
                                                                                   allowed_types):
            random_subset_cut.append(f)
    print("抽取的切图为：", random_subset_cut)
    # 获取样本需要预测的次数
    for_cut_count = (len(random_subset_cut) // predict_count) + (1 if len(random_subset_cut) % predict_count > 0 else 0)
    print("需要调用预测方法的数量为：", for_cut_count)
    # 单次预测的图片列表及图片名列表
    predict_list = list()
    file_name_list = list()
    area_list = list()
    for i in range(for_cut_count):
        final_count = min((i + 1) * predict_count, len(random_subset_cut))
        predict_list.clear()
        file_name_list.clear()
        for j in range(i * predict_count, final_count):
            file_path = cut_path + '/' + random_subset_cut[j]
            predict_list.append(file_path)
            file_name_list.append(random_subset_cut[j])
            key = random_subset_cut[j].split('_-_')[0] + "." + random_subset_cut[j].split('.')[1]
            area_cut = ((cut_size[0] * cut_size[1] * import_img_sampling_exit[key][4]) /
                        (import_img_sampling_exit[key][2] * import_img_sampling_exit[key][3]))
            area_list.append(area_cut)
        print("单词调用预测方法时的文件列表：", predict_list)
        print("单词调用预测方法时的名字列表：", file_name_list)
        print("单词调用预测方法时的区域大小列表：", area_list)
        # 获取图片预测结果
        list_counts, count_areas, class_ids, confidence, rects = predict.get_predict_counts_for_sampling(predict_list, file_name_list, predict_path, True,
                                                              area_list)
        print("预测结果：", list_counts)
        print("预测结果：", count_areas)
        # 记录每个抽样图片的识别结果数
        list_sampling.extend(count_areas)
        class_ids_list.extend(class_ids)
        confidence_list.extend(confidence)
        rects_list.extend(rects)
    return list_sampling, import_img_sampling_exit, import_file_choose_list, class_ids_list, confidence_list, rects_list


# 获取抽样结果
def get_result_sampling(list_sampling, z_num, sampling_count):
    # 计算平均值
    average = stats.hmean(list_sampling)
    print(f"平均值为：{average}")
    # 计算标准差  n-1   s
    std_dev = stats.sem(list_sampling, ddof=1)
    print(f"标准差为：{std_dev}")
    se = std_dev / math.sqrt(sampling_count)
    print(f"SE：{se}")
    confidence_left = average - (z_num * se)
    confidence_right = average + (z_num * se)
    confidence_percent = (average - confidence_left) / average
    return average, confidence_left, confidence_right, confidence_percent


def get_result_sampling_t(list_sampling, t_num, sampling_count):
    # 计算平均值
    print(list_sampling)
    average = sum(list_sampling) / len(list_sampling)
    print(f"平均值为：{average}")
    # 计算标准差  n-1   s
    variance = math.sqrt(sum((x - average) ** 2 for x in list_sampling) / (sampling_count - 1))
    print(f"variance:{variance}")
    confidence_left = average - (t_num * variance / math.sqrt(sampling_count))
    confidence_right = average + (t_num * variance / math.sqrt(sampling_count))
    confidence_percent = (t_num * variance / math.sqrt(sampling_count)) / average
    return average, confidence_left, confidence_right, confidence_percent, variance


# 获取结果
def get_sampling_result(import_file_choose_list, import_file_list, import_img_sampling_exit, download_path, n,
                        confidence, expected_percent,
                        cut_path,
                        predict_count, predict_path, allowed_types, cut_size):
    print("get_sampling_result()")
    # 对输入图片文件夹进行判断，数量小于n, 抽取全部, 计算应抽样数
    import_file_counts, import_img_sampling_exit = count_files_in_directory(import_img_sampling_exit, import_file_list,
                                                                            allowed_types)
    print("总的大图数量为：", len(import_file_list))
    if len(import_file_list) < n:
        sampling_count = len(import_file_list)
    else:
        sampling_count = n
    list_sampling, import_img_sampling_exit, import_file_choose_list, class_ids_list, confidence_list, rects_list = get_first_sampling_result(
        import_file_choose_list, sampling_count, import_img_sampling_exit, download_path, cut_path, predict_count,
        predict_path, allowed_types, cut_size)
    print("抽样列表，切图数量为：", list_sampling)
    # 获取标准正态分布值
    t_num = get_t_value_from_percentile(n - 1, confidence)
    print(f"t正态分布值为：{t_num}")
    average, confidence_left, confidence_right, confidence_percent, variance = get_result_sampling_t(list_sampling,
                                                                                                     t_num, n)
    print(
        f"初次计算的结果为：confidenct_left={confidence_left}, confidence_right={confidence_right}, confidence_percent={confidence_percent}")
    sampling_n = 0
    if average != 0:
        # 期望t
        t_dist = stats.t(n - 1)
        q = t_dist.ppf(expected_percent)
        print(f"t正态分布值为：{q}")
        print(f"expected_percent={expected_percent}")
        sampling_n = math.ceil((q * variance / (expected_percent * average)) ** 2)
        print("应该抽样的数量：", sampling_n)
    return average, confidence_left, confidence_right, confidence_percent, import_img_sampling_exit, sampling_n, import_file_choose_list, class_ids_list, confidence_list, rects_list


def save_return_img(import_img_sampling_exit, download_path, cut_path, final_path, predict_path):
    exit_set = set()
    for key in import_img_sampling_exit:
        if not import_img_sampling_exit[key][0]:
            exit_set.add(key)
    print(exit_set)
    for file_name in exit_set:
        # 创建一个新的图像来容纳所有小图像
        total_image = Image.open(download_path + '/' + file_name)
        path = ''
        f_name = ''
        for f in os.listdir(cut_path):
            if f.split('_-_')[0] == file_name.split('.')[0]:
                path = predict_path + '/' + f
                f_name = f.split('.')[0]
        image = Image.open(path)
        total_image.paste(image, (int(f_name.split('_-_')[1]), int(f_name.split('_-_')[2])))
        # 保存合并后的图像
        total_image.save(final_path + "/" + file_name)
        image.close()
        total_image.close()


def get_result(import_file_list, download_path, n, confidence, expected_percent, cut_size, cut_path, predict_count,
               predict_path, final_path, allowed_types, if_return_img):
    import_img_sampling_exit = dict()
    import_file_choose_list = list()
    # 获取置信区间等值
    average, confidence_left, confidence_right, confidence_percent, import_img_sampling_exit, sampling_n, import_file_choose_list, class_ids_list, confidence_list, rects_list = get_sampling_result(
        import_file_choose_list, import_file_list, import_img_sampling_exit, download_path, n, confidence,
        expected_percent, cut_path, predict_count, predict_path, allowed_types, cut_size)
    # 判断是否需要输出最终的拼图
    if if_return_img:
        # 拼图
        save_return_img(import_img_sampling_exit, download_path, cut_path, final_path, predict_path)
    return average, confidence_left, confidence_right, sampling_n, import_file_choose_list, class_ids_list, confidence_list, rects_list
