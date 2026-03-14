import os
import random
import shutil
from pathlib import Path
import yaml

# ---------------- 配置 ----------------
random.seed(42)  # 保证可复现

src_img_dir = Path('./datasets/mix/images')
src_lbl_dir = Path('./datasets/mix/labels')

dst_base = Path('./mix_datasets')
ratios = {'train': 0.8, 'val': 0.1, 'test': 0.1}

names = ['soybean', 'rice', 'corn']  # 类别名
# -------------------------------------


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p


def split_dataset():
    # 收集所有图片文件
    img_files = [f for f in src_img_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    img_files.sort()

    total = len(img_files)
    train_count = int(total * ratios['train'])
    val_count = int(total * ratios['val'])

    random.shuffle(img_files)

    splits = {
        'train': img_files[:train_count],
        'val': img_files[train_count:train_count + val_count],
        'test': img_files[train_count + val_count:]
    }

    for split, files in splits.items():
        img_out = ensure_dir(dst_base / 'images' / split)
        lbl_out = ensure_dir(dst_base / 'labels' / split)

        for img_path in files:
            lbl_path = src_lbl_dir / (img_path.stem + '.txt')
            if not lbl_path.exists():
                print(f"[WARN] 没有找到标签: {lbl_path}")
                continue
            shutil.copy2(img_path, img_out / img_path.name)
            shutil.copy2(lbl_path, lbl_out / lbl_path.name)

        print(f"[OK] {split}: {len(files)} 张图片")

    # 生成 data.yaml
    data_cfg = {
        'train': str(dst_base / 'images' / 'train'),
        'val': str(dst_base / 'images' / 'val'),
        'test': str(dst_base / 'images' / 'test'),
        'nc': len(names),
        'names': names
    }
    with open('data.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(data_cfg, f, allow_unicode=True)

    print("\n[INFO] 数据集划分完成，已生成 data.yaml")


if __name__ == "__main__":
    split_dataset()
