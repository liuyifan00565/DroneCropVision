# trans
# voc_to_yolo.py

import os
import xml.etree.ElementTree as ET
from fnmatch import fnmatch

# 转换之前先修改类别和路径
# 这个就是文件夹中，classes.txt文件从上到下的类型顺序
classes = ['大豆', '水稻', '玉米']
# 将指定路径的xml文件转换为txt文件
IN_PATH = r"E:\pyProject\local\ymsdddXmlFile\different\xml&jpg\ym"  # xml文件夹路径
OUT_PATH = r"E:\pyProject\local\ymsdddXmlFile\different\txt&jpg\ym"  # txt文件夹路径

# 一般情况不修改：类别起始编号start_number
start_number = 0


# 其中，xml格式以图像的标记框的左上角、右下角的像素坐标为记录值，分别记作(box[0],box[2]),(box[1],box[3])，图像像素大小宽高为（size[0],size[1]）;
# 其中，yolo标注格式txt以图像的标记框中心点的像素坐标，以及标记框的宽，高相对图像的宽高比值作为记录值，分别为x,y,w,h;
def convert(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x = (box[0] + box[1]) / 2.0
    y = (box[2] + box[3]) / 2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return x, y, w, h


def convert_annotation(in_path, out_path, img_id):
    # 重新拼接路径及文件名称获得文件路径
    i_p = os.path.join(in_path, img_id + '.xml')
    # 读取二进制文件
    in_file = open(i_p, 'rb')
    # 拼接输入的文件路径
    o_p = os.path.join(out_path, img_id + '.txt')
    # 只写该文件
    out_file = open(o_p, 'w')
    # 解析称ElementTree对象
    tree = ET.parse(in_file)
    # 获取根节点
    root = tree.getroot()
    # 获取size标签
    size = root.find('size')
    # 获取width标签的内容
    w = int(size.find('width').text)
    # 获取height标签的内容
    h = int(size.find('height').text)
    # 循环object标签
    for obj in root.iter('object'):
        # 获取difficult标签的值
        difficult = obj.find('difficult').text
        # 获取name标签的值（在文件中表明了类型）
        cls = obj.find('name').text
        # 将cls类型和声明的classes进行对比，判断cls是否在其中
        if cls not in classes or int(difficult) == 1:
            # classes包括cls或者difficult为1时继续
            continue
        # 计算在类型中的位置——如果类型为水稻，cls_id为1
        cls_id = classes.index(cls) + start_number
        # 获取bndbox标签
        xmlbox = obj.find('bndbox')
        # 获取坐标值
        b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text),
             float(xmlbox.find('ymax').text))
        # 调用方法得出txt中需要的坐标值
        bb = convert((w, h), b)
        # 写文件
        out_file.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')
    in_file.close()
    out_file.close()

###
# in_path xml文件夹路径
# out_path txt输出文件夹路径
###
def xml2txt(in_path, out_path):
    # 获取文件夹的文件列表
    file_lst = os.listdir(in_path)
    # 循环文件列表
    for f in file_lst:
        # 判断查找是xml文件的
        if fnmatch(f, '*.xml'):
            # 获取该xml的文件名
            img_id = f.split('.')[0]
            print("xml文件，fileName：", img_id, '.xml')
            # 调用转换方法
            convert_annotation(in_path, out_path, img_id)

# 执行转换方法
xml2txt(IN_PATH, OUT_PATH)

