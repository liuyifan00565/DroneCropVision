# -*- coding: utf-8 -*-
"""
时间: 2025-04-26
版本: 1.0.0
作者: luogy
"""

from ultralytics import YOLO

if __name__ == '__main__':

    # Load a model
    model = YOLO(model=r'/home/bdhapp/lgy/yolo/model/runs/detect/train4/weights/best.pt')
    model.predict(source=r'/home/bdhapp/lgy/yolo/dataset/images/val/7.jpg',
                  save=True,
                  show=True,)