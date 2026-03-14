import os
from collections import Counter

# 数据集路径
dataset_root = "newdatasets"

# 类别名称，要和 data.yaml 中的 names 对应
names = ["soybean", "rice", "corn"]

def check_labels():
    label_dir_list = []
    for crop in ["corn", "rice", "soybean"]:
        for split in ["train", "val", "test"]:
            label_dir_list.append(os.path.join(dataset_root, crop, "labels", split))

    class_counter = Counter()

    for label_dir in label_dir_list:
        if not os.path.exists(label_dir):
            continue
        for file in os.listdir(label_dir):
            if file.endswith(".txt"):
                path = os.path.join(label_dir, file)
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) > 0:
                            cls_id = int(parts[0])
                            class_counter[cls_id] += 1

    print("=== 检查结果 ===")
    if not class_counter:
        print("❌ 没有找到任何标签文件！")
        return

    print("出现过的类别 ID 及数量：")
    for cls_id, count in class_counter.items():
        if cls_id < len(names):
            print(f"  ID {cls_id} -> {names[cls_id]} : {count} 个")
        else:
            print(f"  ⚠️ ID {cls_id} 超出了 names 定义范围！ ({count} 个)")

    print("\n当前 data.yaml 中定义：")
    for i, name in enumerate(names):
        print(f"  ID {i} -> {name}")

if __name__ == "__main__":
    check_labels()
