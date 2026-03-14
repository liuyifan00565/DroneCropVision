import os
import glob

# 定义文件所在目录
directory = 'E:/pyProject/local/ymsdddXmlFile/txt&jpg_less_than_300/total'

# 获取目录下所有文件
files = glob.glob(os.path.join(directory, '*.txt'))  # 假设是文本文件

# 检查每个文件的行数，并打印少于300行的文件名
for file in files:
    lines = len(open(file, 'r').readlines())
    if lines < 300:
        # 小于三百行打印文件名
        print(file)
    else:
        # 超出部分删除
        os.remove(file)
        file_jpg = file.split(".")[0] + ".jpg"
        file_JPG = file.split(".")[0] + ".JPG"
        print("no !!!!", file)
        if os.path.exists(file_jpg):
            os.remove(file_jpg)
        if os.path.exists(file_JPG):
            os.remove(file_JPG)
