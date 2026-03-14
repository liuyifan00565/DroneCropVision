import os
import shutil
import random

# ---------------- Configuration ----------------
random.seed(42)  # 保证结果可复现

# 原始数据目录
src_img_dir = 'D:/StudyData/Projects/UAV/mix/images'
src_lbl_dir = 'D:/StudyData/Projects/UAV/mix/labels'

# 划分后数据目录
dst_base = 'datasets'

# 划分比例
ratios = {
    'train': 0.8,
    'val':   0.1,
    'test':  0.1
}

# 类别映射: class_id -> class_name
class_map = {
    0: 'soybean',
    1: 'rice',
    2: 'corn'
}

# 支持的图片后缀
img_exts = ['.jpg', '.jpeg', '.png']

# ---------------- 按类别读取并拆分 ----------------
for cls_id, cls_name in class_map.items():
    # 收集该类别所有图片文件
    files = []
    for fname in os.listdir(src_img_dir):
        name, ext = os.path.splitext(fname)
        if ext.lower() not in img_exts:
            continue
        # 读取标注文件，筛选 class_id
        label_path = os.path.join(src_lbl_dir, f"{name}.txt")
        if not os.path.exists(label_path):
            continue
        with open(label_path, 'r') as f:
            line = f.readline().strip()
            if not line:
                continue
            if int(line.split()[0]) == cls_id:
                files.append(fname)

    # 打乱并按比例划分
    random.shuffle(files)
    n_total = len(files)
    n_train = int(n_total * ratios['train'])
    n_val   = int(n_total * ratios['val'])

    splits = {
        'train': files[:n_train],
        'val':   files[n_train:n_train + n_val],
        'test':  files[n_train + n_val:]
    }

    # 创建该类别子目录
    for split in splits:
        os.makedirs(os.path.join(dst_base, cls_name, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(dst_base, cls_name, 'labels', split), exist_ok=True)

    # 复制文件
    print(f"类别 {cls_name} 共 {n_total} 张: train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")
    for split, file_list in splits.items():
        for img_name in file_list:
            base_name, _ = os.path.splitext(img_name)
            label_name = f"{base_name}.txt"

            shutil.copy(
                os.path.join(src_img_dir, img_name),
                os.path.join(dst_base, cls_name, 'images', split, img_name)
            )
            shutil.copy(
                os.path.join(src_lbl_dir, label_name),
                os.path.join(dst_base, cls_name, 'labels', split, label_name)
            )

print("各类别数据集拆分完成！")
