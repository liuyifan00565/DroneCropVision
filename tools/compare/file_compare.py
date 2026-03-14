# 写一段python代码，统计两个文件夹下所有txt的sha1和md5，将值相同的文件列出。

import hashlib
import os
from collections import defaultdict


def calculate_hashes(file_path):
    """计算给定文件的SHA-1和MD5哈希值"""
    sha1_hash = hashlib.sha1()
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha1_hash.update(byte_block)
            md5_hash.update(byte_block)
    return (sha1_hash.hexdigest(), md5_hash.hexdigest())


def find_matching_hashes(folder1, folder2):
    """在两个文件夹中查找具有相同哈希值的.txt文件"""
    hashes_dict = defaultdict(list)

    # 遍历第一个文件夹
    for root, dirs, files in os.walk(folder1):
        for file in files:
            if file.lower().endswith(".txt"):
                file_path = os.path.join(root, file)
                sha1, md5 = calculate_hashes(file_path)
                hashes_dict[(sha1, md5)].append(file_path)

    # 遍历第二个文件夹，检查哈希值是否已存在于字典中
    for root, dirs, files in os.walk(folder2):
        for file in files:
            if file.lower().endswith(".txt"):
                file_path = os.path.join(root, file)
                sha1, md5 = calculate_hashes(file_path)
                if (sha1, md5) in hashes_dict and file_path not in hashes_dict[(sha1, md5)]:
                    hashes_dict[(sha1, md5)].append(file_path)

    # 列出哈希值相同的文件对
    for hash_value, files in hashes_dict.items():
        if len(files) > 1:
            print(f"Files with matching hashes {hash_value}: {files}")


# 示例用法
folder1 = r"E:/pyProject/local/datasets/labels/train_change"
folder2 = r"E:/pyProject/local/datasets/labels/train"
find_matching_hashes(folder1, folder2)
