from PIL import Image
import os


# 切分图片
def split_image(name, image_path, output_dir, size):
    # 获取图片的宽高
    img = Image.open(image_path)
    w, h = img.size

    # 循环宽高
    for x in range(0, w, size):
        for y in range(0, h, size):
            # 切分的大小左上右下
            box = (x, y, x + size, y + size)
            # 宽度超出
            if box[2] > w:
                box = (w - size, box[1], w, box[3])
            # 高度超出
            if box[3] > h:
                box = (box[0], h - size, box[2], h)
            img.crop(box).save(f"{output_dir}/{name}_{x}_{y}.png")


in_folder = "E:/pyProject/local/cut/吕佳谦华为倒伏筛选100张"
out_folder_total = "E:/pyProject/local/cut/result/total"
if not os.path.exists(out_folder_total):
    os.makedirs(out_folder_total)
# 获取文件夹中的文件列表
files = os.listdir(in_folder)
# 遍历文件列表
for file in files:
    out_folder = "E:/pyProject/local/cut/result"
    # 打印文件名
    file1_path = os.path.join(in_folder, file)
    # out_folder += "/" + file.split(".")[0]
    # if not os.path.exists(out_folder):
    #     os.makedirs(out_folder)
    # 使用示例
    split_image(file.split(".")[0], file1_path, out_folder_total, 1024)
