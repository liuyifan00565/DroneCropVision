import tasks.detect.seedling.total_predict_tiff_gdal as tp
import os
import requests
import tasks.detect.seedling.sampling_predict_middle_cut as spmc
import tasks.detect.seedling.config as config
import tasks.detect.seedling.single_pic_predict as spp


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
    file_name = url.split('?')[0].split('/')[-1]
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


def delete_files_in_directory(directory):
    """
    删除文件夹中的文件
    Args:
        directory: 要删除的文件夹目录
    """
    # 获取目录中的所有项
    items = os.listdir(directory)
    for item in items:
        # 构建完整的文件路径
        item_path = os.path.join(directory, item)
        # 判断是否是文件
        if os.path.isfile(item_path):
            # 删除文件
            os.remove(item_path)
            print(f"已删除文件：{item_path}")


def get_detect_result(task_id: str, detect_type: int, area, import_file_list: list, red_warn_single=None, yellow_warn_single=None, expect_counts=None,
                      n=config.N,
                      confidence=config.CONFIDENCE,
                      expected_percent=config.EXPECTED_PERCENT,
                      cut_size=config.CUT_SIZE,
                      allowed_types=config.ALLOWED_TYPES,
                      predict_count=config.PREDICT_BATCH_SIZE,
                      red_warn_total=config.RED_WARN,
                      yellow_warn_total=config.YELLOW_WARN,
                      if_return_img=config.IF_RETURN_IMG,
                      total_plot=config.PLOT,
                      total_coloring=config.COLORING,
                      total_box_color=config.TOTAL_COLOR,
                      sampling_box_color=config.SAMPLING_COLOR,
                      single_box_color=config.SINGLE_COLOR,
                      little_size=config.SINGLE_LITTLE_SIZE
                      ):
    """ 方法参数说明：
     task_id：任务id
     detect_type：预测类型（1：全量    2/其他：抽样）
     area: 全量中代表图片或tif代表的实际面积，单张中代表每像素值的实际厘米数，抽样暂未计算
     file_size：文件大小（全量的是tif的大小，抽样的是每张图片的大小。例：宽高：(1024, 1024)）
     area_total：图片的实际面积（全量的是总面积，抽样的是单张图片的实际面积）
     import_file_list：输入文件的列表。例：[{'url':'', 'area': 1, 'width': 2048, 'height': 2048, ... ...]
     res_path：用来保存文件的文件夹地址（会在其下建立task_id的文件夹），可以配置在config中，我这里直接接参，避免后续修改
     cut_size：切图大小。例：宽高：(1024, 1024)）
     allowed_types：允许预测的图片类型集合。例：{'jpg', 'png', 'jpeg'}
     predict_count：单次预测的图片数量。例：10
     red_warn：红标（低于总的苗/亩数50%）。例：0.5
     yellow_warn：黄标（低于总的苗/亩数90%）。例：0.9
     n：抽样数量。例：30
     expected_percent：期望值。例：0.05
     confidence：置信度。例：0.95
     if_return_img：抽样是否保存结果图片。例：True
    """
    res_path = config.RESULT_PATH
    download_path = f"{res_path}/{task_id}/download"
    os.makedirs(download_path, exist_ok=True)
    cut_path = f"{res_path}/{task_id}/cut"
    os.makedirs(cut_path, exist_ok=True)
    predict_path = f"{res_path}/{task_id}/predict"
    os.makedirs(predict_path, exist_ok=True)
    final_path = f"{res_path}/{task_id}/final"
    os.makedirs(final_path, exist_ok=True)
    delete_files_in_directory(download_path)
    delete_files_in_directory(cut_path)
    delete_files_in_directory(predict_path)
    delete_files_in_directory(final_path)
    # detect_type:  1(全量)  2(抽样)
    # 全量
    if detect_type == 1:
        # 1. 下载文件到download_path
        tif_file_dict = import_file_list[0]
        # 文件下载，如果是接口调用，需要打开下一行的代码注释，将tif文件下载到本地
        file_url, file_name = download_image(tif_file_dict, download_path)
        # 保存文件目录
        # 2. 调用全量方法，获取总的苗/亩数
        count_area, red_percent, yellow_percent = tp.get_result(task_id, file_url, cut_path, predict_path, final_path,
                                                                cut_size, allowed_types,
                                                                predict_count, area, red_warn_total, yellow_warn_total,
                                                                total_plot, total_coloring, total_box_color)
        return {"count_area": count_area, "red_percent": red_percent, "yellow_percent": yellow_percent}
    # 抽样
    elif detect_type == 2:
        count_area, confidence_left, confidence_right, sampling_n, import_file_choose_list, class_ids_list, confidence_list, rects_list = spmc.get_result(
            import_file_list, download_path, int(n), float(confidence), float(expected_percent), cut_size, cut_path, predict_count,
            predict_path, final_path, allowed_types, if_return_img, sampling_box_color, area)
        return {"count_area": count_area, "confidence_left": confidence_left, "confidence_right": confidence_right,
                "sampling_n": sampling_n,
                "import_file_choose_list": import_file_choose_list, "class_ids_list": class_ids_list,
                "confidence_list": confidence_list, "rects_list": rects_list}
    # 单张
    else:
        # 1. 下载文件到download_path
        pic_file_dict = import_file_list[0]
        file_url, file_name = download_image(pic_file_dict, download_path)
        # 保存文件目录
        # 2. 调用单张方法
        res_test, total_counts, count_area, file_path = spp.get_result(area, file_url, file_name, red_warn_single, yellow_warn_single, expect_counts,cut_path, predict_path, final_path, cut_size, predict_count, single_box_color, little_size)
        return {"res_test": res_test, "total_counts": total_counts, "count_area": count_area, "file_path": file_path}


if __name__ == '__main__':
    """
    更改调用方法的步骤：
        1. 修改一个新的task_id，避免覆盖之前有用的结果数据
        2. 修改detect_type（1-全量  2-抽样  3-单张）
        3. 修改get_detect_result参数中，第三个参数引用的数据集
    """
    # 下面两个是通用的参数
    task_id = 'result_test_0612'
    detect_type = 1
    # 下面三个是单张的参数
    red_warn_single, yellow_warn_single, expect_counts = config.RED_WARN_SINGLE, config.YELLOW_WARN_SINGLE, 500
    # 全量
    import_file_list_ql = ['/home/ubuntu/Desktop/seed-tif/heshan/114-121/little/121result_01_01.tif']
        # {'area': 8766.5, 'height': 2048, 'width': 2048, 'url': '/home/ubuntu/sj/ultralytics/temp-temp小.tif'}]
    # 单张
    import_file_list_dz = ["http://10.7.10.100:8443/bdh-pro/default/be4a3f3cf6e1486ea1c0b795bccd32051748916850960.JPG"]
    # 抽样
    import_file_list_cy = ["http://10.7.10.100:8443/bdh-pro/default/be4a3f3cf6e1486ea1c0b795bccd32051748916850960.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/db6dc1467c7242ac9f243dc5a793af731748916852831.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/d85f960e6e674c55b93956261ae967311748916854549.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/57cb25dc974a4777a373b8509e77deda1748916856049.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/100e9871817a495aa026877cedc511241748916857533.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/48f9ce56cb744162aa5d379b01df600d1748916859117.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/67613e46fa28402192d992d14692cfd01748916861014.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/d8ff59f2bc384223beeba539337000b51748916863316.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/054a6f548af34aa8a34e9a04bb005a321748916865406.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/ca3763f9c2494e8dbb3974397e57fdbf1748916867145.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/99d228e96df94a94b3592359fe0ed46a1748916868802.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/03bebfbce3b9467daac0c382f23d4d951748916870270.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/c033ec19bcb742edbdc9599c18f8d74d1748916872480.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/8d79976ba0464199a9be98bef98b0a8d1748916875061.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/20005a2443f94473b9e2c44b6b8e6db91748916878645.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/1f243fe001cf48f482782323d8b915501748916881250.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/a8740b2e96024eb7b8eefd69e1a7f7621748916884577.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/65b4e8ba7596456ba6a170d2d15216271748916886437.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/a22e6dac4d6b4fc9b9fd9e0c6934a46a1748916888179.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/5b45bc3c28c1490684c174fa309ca94e1748916891470.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/084b751113184879b023baa7bf8a663b1748916897501.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/46578515c317487685a4e247d4b40df01748916902839.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/586b0d4d79df45ec834f120762ac49001748916908475.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/291c1c8ceadf4fc1abacd52da5c72faa1748916912273.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/b00e1c11b7d34dbe8abedff8ab81ffd51748916915228.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/97dbb21acfd549f6b3e8ab956d083f381748916917207.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/f9ff3589b9894fd0ac46a1ebee6cb0fe1748916919195.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/7201f765ffdc48efa11059756fa87d4b1748916920875.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/c9e4b2f9f6b1499d98b4f440fecf19ae1748916922383.JPG",
                           "http://10.7.10.100:8443/bdh-pro/default/01b63705cd314956911130be930b9e6d1748916924174.JPG"]
    # print(get_detect_result(task_id, detect_type, import_file_list_ql, red_warn_single, yellow_warn_single, expect_counts))
