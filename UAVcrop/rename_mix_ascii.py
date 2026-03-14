import os
from pathlib import Path
from collections import Counter
import shutil

# -------- 配置 --------
SRC_IMG_DIR = Path("./datasets/mix/images")
SRC_LBL_DIR = Path("./datasets/mix/labels")

DST_IMG_DIR = Path("./datasets/mix_ascii/images")
DST_LBL_DIR = Path("./datasets/mix_ascii/labels")

# 若你的标签里类别 id 映射是：0=soybean, 1=rice, 2=corn
CLASS_MAP = {0: "soybean", 1: "rice", 2: "corn"}   # 用不到类别也没关系，会自动 fallback 为 "mix"
# ---------------------

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".PNG", ".JPEG"}


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p


def infer_class_from_label(lbl_path: Path):
    """从 YOLO 标签文件中推断主类（取出现次数最多的类别 id）"""
    try:
        ids = []
        with open(lbl_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if parts and parts[0].isdigit():
                    ids.append(int(parts[0]))
        if ids:
            main_id = Counter(ids).most_common(1)[0][0]
            return CLASS_MAP.get(main_id, "mix")
    except Exception:
        pass
    return "mix"


def main():
    if not SRC_IMG_DIR.exists() or not SRC_LBL_DIR.exists():
        raise SystemExit(f"源目录不存在：{SRC_IMG_DIR} 或 {SRC_LBL_DIR}")

    ensure_dir(DST_IMG_DIR)
    ensure_dir(DST_LBL_DIR)

    # 收集所有图片（与标签同名）
    img_files = [p for p in SRC_IMG_DIR.iterdir() if p.suffix in IMG_EXTS]
    img_files.sort()

    counter_by_prefix = {}

    renamed = 0
    skipped = 0

    for img in img_files:
        stem = img.stem
        lbl = SRC_LBL_DIR / f"{stem}.txt"
        if not lbl.exists():
            print(f"[WARN] 找不到同名标签：{lbl.name}，跳过")
            skipped += 1
            continue

        prefix = infer_class_from_label(lbl)  # soybean / rice / corn / mix
        counter_by_prefix.setdefault(prefix, 0)
        counter_by_prefix[prefix] += 1
        new_stem = f"{prefix}_{counter_by_prefix[prefix]:06d}"

        dst_img = DST_IMG_DIR / f"{new_stem}{img.suffix.lower()}"
        dst_lbl = DST_LBL_DIR / f"{new_stem}.txt"

        # 复制（更安全），如需“移动”可改为 shutil.move
        shutil.copy2(img, dst_img)
        shutil.copy2(lbl, dst_lbl)
        renamed += 1

    print(f"\n[OK] 重命名完成：复制 {renamed} 对文件到 {DST_IMG_DIR.parent}")
    if skipped:
        print(f"[INFO] 有 {skipped} 张图片缺少同名标签，已跳过。")
    print("[NEXT] 后续请把 data.yaml 或 split_mix.py 的输入路径改为 datasets/mix_ascii。")


if __name__ == "__main__":
    main()
