import os
from ultralytics import YOLO

def main():
    # 可选：减少 CUDA 内存碎片化
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    # 加载预训练的YOLO模型
    # model_path指定了自定义模型的路径，这里使用的是yolo11s架构的预训练权重
    # model_path = "/home/bdhapp/shuli/yolo11s.pt"
    model = YOLO("yolo11s.pt")

    # 如果有残留的 CUDA 缓存，先清空
    import torch
    torch.cuda.empty_cache()

    # 在自定义数据集上训练模型
    model.train(
        data="./data2.yaml",  # 数据集配置文件路径
        epochs=100,  # 训练轮次，控制模型学习的迭代次数

        # 数据预处理与增强配置
        imgsz=512,  # 输入图像尺寸，增大尺寸有助于检测小目标 改前1024
        batch=4,  # 批次大小，影响内存使用和训练稳定性 改16为8，再改为4
        amp=True,  # 半精度训练，显存减半
        device=0,  # 指定GPU设备ID，0表示使用第一块GPU

        workers=0,  # 改：关闭多进程加载，避免 spawn 引发的错误

        # 训练策略配置
        rect=True,  # 矩形训练，根据图像长宽比调整批次内图像尺寸，减少填充
        resume=False,  # 是否从上次中断处恢复训练（默认False）

        # 数据增强配置 - 针对小目标检测的优化设置
        mosaic=1.0,  # 马赛克增强概率，将多个图像拼接以增加复杂场景
        mixup=0.5,  # 混合增强概率，将不同图像混合以处理遮挡问题
        scale=0.5,  # 缩放增强范围，模拟不同距离的目标
        translate=0.1,  # 平移增强范围，模拟部分可见的目标
        copy_paste=0.3,  # 复制粘贴增强概率，处理密集和重叠目标
        classes=[2]     #只训练某一类
    )

if __name__ == '__main__':
    # Windows 下如果要打包 exe，还可以调用 freeze_support()
    # from multiprocessing import freeze_support
    # freeze_support()
    main()