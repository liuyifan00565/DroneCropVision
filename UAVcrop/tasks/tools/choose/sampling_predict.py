import os
import random
import scipy.stats as stats
import math
from tasks.detect.seedling import predict as predict
from time import time
from PIL import Image


# 切图大小
cut_size = (1024, 1024)
img_size = (2048, 2048)
for_w_count = (img_size[0] // cut_size[0]) + (1 if img_size[0] % cut_size[0] > 0 else 0)
for_h_count = (img_size[1] // cut_size[1]) + (1 if img_size[1] % cut_size[1] > 0 else 0)
# 输入图片文件夹地址
import_path = 'E:/pyProject/local/datasets_sd/images/train'
# 预测类型 0:大豆 1:水稻 2:玉米
# class_id = 0
# 置信度
confidence = 0.95
# 抽样数量
n = 30
# 期望值
expected_percent = 0.05
# 判断文件是否被抽取过的字典（大图）
import_img_sampling_exit = dict()
# 判断文件是否被抽取过的字典（小图）
cut_img_sampling_exit = dict()
# 获取当前时间戳
timestamp = int(time())
# 切小图的保存地址
cut_path = f'E:/pyProject/output_image/sampling/{timestamp}/cut'
os.makedirs(cut_path, exist_ok=True)
# 预测结果图片输出地址
output_path = f'E:/pyProject/output_image/sampling/{timestamp}/predict'
os.makedirs(output_path, exist_ok=True)
# 每次预测的图片数量
predict_count = 10
# 预测的图片类型
allowed_types = {'jpg', 'png', 'jpeg'}
# 单张大图的实际面积
area = 1
# 是否将有过抽样小图的大图重新合成并生成文件
if_return_img = True
# 合成图片保存地址
final_result_img = f'E:/pyProject/output_image/sampling/{timestamp}/result'
os.makedirs(final_result_img, exist_ok=True)


# 检查文件扩展名是否在指定的文件类型列表内
def is_file_type_within_range(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()[1:]  # 获取文件扩展名
    return file_extension in allowed_types


# 获取文件夹中的文件数量
def count_files_in_directory(directory, type_in):
    print("count_files_in_directory()")
    count = 0
    for f in os.listdir(directory):
        if type_in == 0:
            import_img_sampling_exit[f] = True
        else:
            if f not in cut_img_sampling_exit:
                cut_img_sampling_exit[f] = (True, -1, -1)
        if os.path.isfile(os.path.join(directory, f)) and is_file_type_within_range(os.path.join(directory, f)):
            count += 1
    return count


# 获取标准正太分布值
def get_z_value_from_percentile(p):
    # 获取标准正态分布的Z值
    z_value = stats.norm.interval(p, loc=0, scale=1)
    return z_value


# 切分图片
def split_image(name, image_path, output_dir):
    print("split_image()", image_path)
    # 获取图片的宽高
    img = Image.open(image_path)
    print(for_w_count)
    print(for_h_count)
    for i in range(for_w_count):
        for j in range(for_h_count):
            # 切分的大小左上右下
            box = (i * cut_size[0], j * cut_size[1], min((i + 1) * cut_size[0], img_size[0]), min((j + 1) * cut_size[1], img_size[1]))
            print(box)
            img.crop(box).save(f"{output_dir}/{name}_-_{i}_-_{j}.jpg")


# 获取图片宽高
def get_image_dimensions_pil(image_path):
    with Image.open(image_path) as image:
        width, height = image.size
    return width, height


# 获取图片预测结果
def get_first_sampling_result(sampling_count):
    print("get_first_sampling_result()", sampling_count)
    list_sampling = list()
    # 抽取的样品图片列表和切图的列表
    list_sampling_total = list()
    list_sampling_cut = list()
    # 在字典中找到没有被抽样过的文件放入集合
    for key in import_img_sampling_exit:
        if import_img_sampling_exit[key]:
            list_sampling_total.append(key)
    if len(list_sampling_total) >= sampling_count:
        # 选出30张样本图片进行切图
        random_subset = random.sample(list_sampling_total, sampling_count)
    else:
        random_subset = list_sampling_total
    print("抽取的大图为：", random_subset)
    # 遍历抽样列表
    for import_img in random_subset:
        # 更改图片抽取状态
        import_img_sampling_exit[import_img] = False
        # 获取文件名
        import_img_name = import_img.split(".")[0]
        # 切图
        split_image(import_img_name, import_path + "/" + import_img, cut_path)
    # 获取预测样本总数
    cut_file_counts = count_files_in_directory(cut_path, 1)
    print("切图的总数为：", cut_file_counts)
    # 遍历可以样本字典找到可以抽取的样本
    for key in cut_img_sampling_exit:
        if cut_img_sampling_exit[key][0]:
            list_sampling_cut.append(key)
    # 抽取n个样本
    if len(list_sampling_cut) >= sampling_count:
        random_subset_cut = random.sample(list_sampling_cut, sampling_count)
    else:
        random_subset_cut = list_sampling_cut
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
            cut_img_sampling_exit[random_subset_cut[j]] = (False, -1, -1)
            file_path = cut_path + '/' + random_subset_cut[j]
            predict_list.append(file_path)
            file_name_list.append(random_subset_cut[j])
            width, height = get_image_dimensions_pil(cut_path + '/' + random_subset_cut[j])
            # 切图的实际面积
            area_cut = (width * height) * area/(img_size[0] * img_size[1])
            area_list.append(area_cut)
        print("单词调用预测方法时的文件列表：", predict_list)
        print("单词调用预测方法时的名字列表：", file_name_list)
        print("单词调用预测方法时的区域大小列表：", area_list)
        # 获取图片预测结果
        list_counts = predict.get_predict_counts(predict_list, file_name_list, output_path, True, area_list)
        print("预测结果：", list_counts)
        # 记录每个抽样图片的识别结果数
        for k in range(len(list_counts)):
            count = list_counts[k]
            index_count = i * predict_count + k
            width, height = get_image_dimensions_pil(cut_path + '/' + random_subset_cut[index_count])
            # 切图的实际面积
            area_cut = (width * height) * area/(img_size[0] * img_size[1])
            cut_img_sampling_exit[random_subset_cut[index_count]] = (False, count, area_cut)
        list_sampling.extend(list_counts)
    return list_sampling, cut_file_counts


# 获取抽样结果
def get_result(list_sampling, z_num, sampling_count):
    # 计算平均值
    print(list_sampling)
    average = stats.hmean(list_sampling)
    print(f"平均值为：{average}")
    # 计算标准差
    std_dev = stats.sem(list_sampling, ddof=1)
    print(f"标准差为：{std_dev}")
    se = std_dev / math.sqrt(sampling_count)
    print(f"SE：{se}")
    confidence_left = average - (z_num * se)
    confidence_right = average + (z_num * se)
    confidence_percent = (average - confidence_left) / average
    return confidence_left, confidence_right, confidence_percent


# 获取结果
def get_sampling_result():
    print("get_sampling_result()")
    # 对输入图片文件夹进行判断，数量小于30返回空
    import_file_counts = count_files_in_directory(import_path, 0)
    print("总的大图数量为：", import_file_counts)
    if import_file_counts < n:
        return ()
    else:
        # 图片预测结果集合
        list_sampling, cut_file_counts = get_first_sampling_result(n)
        print("抽样列表，切图数量为：", list_sampling, cut_file_counts)
        # 计算结果
        # 获取标准正态分布值
        z_num = get_z_value_from_percentile(confidence)[1]
        print(f"正态分布值为：{z_num}")
        confidence_left, confidence_right, confidence_percent = get_result(list_sampling, z_num, n)
        print(f"初次计算的结果为：confidenct_left={confidence_left}, confidence_right={confidence_right}, confidence_percent={confidence_percent}")
        # 偏差大于期待值
        if confidence_percent > expected_percent:
            sampling_n = round(z_num * z_num * (n / cut_file_counts) * (1 - (n / cut_file_counts)) / (expected_percent * expected_percent))
            print("应该抽样的数量：", sampling_n)
            # 计算得出的抽样样本大于30，从总图片中抽取sampling_n - n个大图进行再次切图
            if sampling_n > 30:
                sampling_second, cut_file_counts_second = get_first_sampling_result(sampling_n - n)
                if sampling_second == -1:
                    return "sampling_counts > total_counts"
                else:
                    list_sampling.extend(sampling_second)
                    confidence_left, confidence_right, confidence_percent = get_result(list_sampling, z_num, sampling_n)
        print("confidence left: ", confidence_left, " confidence right: ", confidence_right,
                          " confidence percent: ",
                          confidence_percent)
        return confidence_left, confidence_right, confidence_percent


def save_return_img():
    exit_set = set()
    for key in cut_img_sampling_exit:
        if not cut_img_sampling_exit[key][0]:
            exit_set.add(key.split('_-_')[0] + "." + key.split('.')[1])
    print(exit_set)
    for file_name in exit_set:
        # 创建一个新的图像来容纳所有小图像
        total_image = Image.new('RGB', (img_size[0], img_size[1]))
        for i in range(for_w_count):
            for j in range(for_h_count):
                f = f"{file_name.split('.')[0]}_-_{i}_-_{j}.{file_name.split('.')[1]}"
                if cut_img_sampling_exit[f][0]:
                    path = os.path.join(cut_path, f)
                else:
                    path = os.path.join(output_path, f)
                if os.path.isfile(path):
                    image = Image.open(path)
                    total_image.paste(image, (1024 * i, 1024 * j))
                    image.close()
        # 保存合并后的图像
        total_image.save(final_result_img + "/" + file_name.split('.')[0] + "." + file_name.split('.')[1])


# 获取置信区间等值
confidence_left, confidence_right, confidence_percent = get_sampling_result()
# 判断是否需要输出最终的拼图
if if_return_img:
    # 拼图
    save_return_img()

