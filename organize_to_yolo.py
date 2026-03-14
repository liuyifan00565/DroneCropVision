import os
import shutil
import argparse
from pathlib import Path

# ---------- 配置区（按需修改） ----------
DATASETS_DIR = Path("./datasets")

# 你的当前数据目录（图片与txt混在一起的源目录）
CLASSES = {
    "corn": [
        "corn/firstdata",
    ],
    "rice": [
        "rice/firstdata",
    ],
    "soybean": [
        "soybean/firstdata",
    ],
}

# 允许的扩展名
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".PNG", ".JPEG"}
LBL_EXT = ".txt"

# 是否移动文件（True）还是复制文件（False，默认更安全）
MOVE_FILES = False
# --------------------------------------


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_copy_or_move(src: Path, dst: Path, move: bool = False):
    """避免重名：若存在同名文件，则在文件名后加编号"""
    base = dst.stem
    ext = dst.suffix
    i = 1
    out = dst
    while out.exists():
        out = dst.with_name(f"{base}_{i}{ext}")
        i += 1
    if move:
        shutil.move(str(src), str(out))
    else:
        shutil.copy2(str(src), str(out))
    return out


def collect_pairs(folder: Path):
    """扫描混合目录，返回 (img_path, lbl_path) 成对列表；忽略缺失的一侧"""
    pairs = []
    files = list(folder.iterdir())
    name_to_img = {}
    name_to_lbl = {}
    for f in files:
        if f.suffix in IMG_EXTS:
            name_to_img[f.stem] = f
        elif f.suffix == LBL_EXT:
            name_to_lbl[f.stem] = f
    common = set(name_to_img.keys()) & set(name_to_lbl.keys())
    for stem in common:
        pairs.append((name_to_img[stem], name_to_lbl[stem]))
    # 也可打印缺失项提示
    missing_imgs = set(name_to_lbl.keys()) - set(name_to_img.keys())
    missing_lbls = set(name_to_img.keys()) - set(name_to_lbl.keys())
    if missing_imgs:
        print(f"[WARN] {folder} 有 {len(missing_imgs)} 个标签找不到同名图片")
    if missing_lbls:
        print(f"[WARN] {folder} 有 {len(missing_lbls)} 张图片找不到同名标签")
    return pairs


def organize_per_class():
    """分别整理到 datasets/<class>/{images,labels}"""
    for cls, rel_dirs in CLASSES.items():
        out_img = ensure_dir(DATASETS_DIR / cls / "images")
        out_lbl = ensure_dir(DATASETS_DIR / cls / "labels")
        total = 0
        for rel in rel_dirs:
            src_dir = DATASETS_DIR / rel
            if not src_dir.exists():
                print(f"[SKIP] 源目录不存在：{src_dir}")
                continue
            for img, lbl in collect_pairs(src_dir):
                # 防重名：文件名前加类名前缀
                stem_pref = f"{cls}_{img.stem}"
                dst_img = out_img / f"{stem_pref}{img.suffix}"
                dst_lbl = out_lbl / f"{stem_pref}{LBL_EXT}"
                safe_copy_or_move(img, dst_img, MOVE_FILES)
                safe_copy_or_move(lbl, dst_lbl, MOVE_FILES)
                total += 1
        print(f"[OK] {cls} 共整理 {total} 对文件 -> {out_img.parent}")


def organize_mix():
    """合并整理到 datasets/mix/{images,labels}"""
    out_img = ensure_dir(DATASETS_DIR / "mix" / "images")
    out_lbl = ensure_dir(DATASETS_DIR / "mix" / "labels")
    total = 0
    for cls, rel_dirs in CLASSES.items():
        for rel in rel_dirs:
            src_dir = DATASETS_DIR / rel
            if not src_dir.exists():
                print(f"[SKIP] 源目录不存在：{src_dir}")
                continue
            for img, lbl in collect_pairs(src_dir):
                # 防重名：加类名前缀
                stem_pref = f"{cls}_{img.stem}"
                dst_img = out_img / f"{stem_pref}{img.suffix}"
                dst_lbl = out_lbl / f"{stem_pref}{LBL_EXT}"
                safe_copy_or_move(img, dst_img, MOVE_FILES)
                safe_copy_or_move(lbl, dst_lbl, MOVE_FILES)
                total += 1
    print(f"[OK] mix 共整理 {total} 对文件 -> {out_img.parent}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mix", "per_class"], default="mix",
                        help="mix: 合并到 datasets/mix；per_class: 分别整理到 datasets/<class>")
    args = parser.parse_args()

    if args.mode == "per_class":
        organize_per_class()
        print("\n下一步：按类训练时，data.yaml 例子：\n"
              "train: ./datasets/corn/images\nval: ./datasets/corn/images\nnc: 1\nnames: ['corn']")
    else:
        organize_mix()
        print("\n下一步：运行 split_mix.py 进行 8/1/1 划分，然后写 data.yaml：\n"
              "train: ./mix_datasets/images/train\nval: ./mix_datasets/images/val\nnc: 3\nnames: ['soybean','rice','corn']")


if __name__ == "__main__":
    main()
