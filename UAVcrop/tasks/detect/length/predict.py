"""
时间: 2025-04-26
版本: 1.0.0
作者: luogy
"""


"""
str,str
"""

from ultralytics import YOLO
def img_predict(image_str):
    model_str = "best.pt"
    DPI = 96
    model = YOLO(model_str)
    results = model(image_str)
    res = []
    # Access the results
    for result in results:
        xywh = result.boxes.xywh  # center-x, center-y, width, height
        print("xywh:",xywh)
        
        for row  in xywh:
            print("width_cm:",row[2]*2.54/DPI,"length_cm:",row[3]*2.54/DPI)
            res.append([row[2]*2.54/DPI,row[3]*2.54/DPI])
    return res

if __name__ == '__main__':
    image_str = '10.jpg'
    result = img_predict(image_str)
    print("result:",result)

    


    
