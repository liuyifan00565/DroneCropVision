# https://docs.ultralytics.com/modes/

# Train
TRAIN_MODEL = "../../../models/yolo11x.pt"  # 预训练模型地址

# Train Settings
TRAIN_DATA = "data.yaml"
TRAIN_EPOCHS = 100
TRAIN_BATCH = 16
TRAIN_IMGSZ = 1024
TRAIN_SAVE = True
TRAIN_DEVICE = 0, 1
TRAIN_WORKERS = 8
TRAIN_SINGLE_CLS = False
TRAIN_PLOTS = True

# Augmentation Settings and Hyperparameters
TRAIN_TRANSLATE = 0.1
TRAIN_SCALE = 0.5
TRAIN_MOSAIC = 1.0
TRAIN_MIXUP = 0.0
TRAIN_COPY_PASTE = 0.0

# Predict

# 模型地址
MODEL_PATH = "models/best_20241106.pt"

# 测试图像
PREDICT_SOURCE = "E:/pyProject/ultralytics/tasks/seedling/datasets/validation/9HAa92TJbhEHwRuTgyj_852.JPG"
TXT_PATH = "E:/pyProject/local/plant_total/txt&jpg/total/9HAa92TJbhEHwRuTgyj_852.txt"
URL_OUTPUT = "E:/pyProject/ultralytics/tasks/seedling/after/9HAa92TJbhEHwRuTgyj_852-2.JPG"

# Inference arguments
PREDICT_CONF = 0.3
PREDICT_IOU = 0.15
PREDICT_MAX_DET = 600

# Visualization arguments
PREDICT_SAVE = False
PREDICT_SHOW_LABELS = False


# Seedling arguments
# ---------------通用参数---------------
# 调用的模型接口路径
PREDICT_URL = 'http://10.7.24.3:30096/api/v1/seedinglist' # 线上
# PREDICT_URL = 'http://10.7.24.3:30096/api/v1/seedinglist' # 测试
# 传入文件+配置参数的接口
BATCH_FILE_URL = "http://10.7.24.3:30099/api/v1/seedingBatchFile" # 修改上传文件版
# 预测结果保存路径
RESULT_PATH = '/opt/image/new_UAV/'
# RESULT_PATH = '/home/ubuntu/sj/ultralytics/weishan_yumi_res'
# 允许预测的图片类型集合
ALLOWED_TYPES = {'jpg', 'png', 'jpeg', 'JPG'}
# 切图尺寸
CUT_SIZE = (1024, 1024)
# 预测时，单次识别的图片数量
PREDICT_BATCH_SIZE = 50
# 最大标框数
MAX_DET = 1200
# 是否需要调用对预测结果进行处理的方法（去掉一些过小的框，使预测结果数量减少）
IF_REDUCE_QUANTITY = False
# 字体文件位置
FONT_URL = '/opt/image/new_UAV/SimHei.ttf'

# ---------------全量相关参数---------------
# 是否绘制目标框
PLOT = True
# 是否根据阈值涂色
COLORING = True
# 苗周围画框颜色
TOTAL_COLOR = (1, 255, 159)
# 是否将画框信息(rect:(左上x，左上y，右下x，右下y))保存到txt中
IF_SAVE_RECT_TXT_TOTAL = True
# 预测结果警戒值————数值版（全量暂时使用中）
RED_WARN = 50
YELLOW_WARN = 100
# 切割的tif文件像素大小
TIFF_SIZE = (15360, 15360)
# 当tif文件大于这个值（单位GB）时，将tif文件按照上个参数的尺寸进行切割
FILE_CUT_LIMIT = 2

# ---------------抽样相关参数---------------
# 抽样数量（样本数量大于等于抽样数量时，抽取N；样本数量小于抽样数量时，抽取样本数量）
N = 30
# 置信度。例：0.95，用于获取标准正态分布值
CONFIDENCE = 0.95
# 期望的误差百分比
EXPECTED_PERCENT = 0.05
# 是否返回识别后的结果图片
IF_RETURN_IMG = True
# 抽样画框颜色
SAMPLING_COLOR = (1, 255, 159)
# 是否将画框信息(rect:(左上x，左上y，右下x，右下y))保存到txt中
IF_SAVE_RECT_TXT_SAMPLING = False

# ---------------单张相关参数---------------
# 期望的亩苗数/亩穴数
EXPECT_COUNTS = 2000
# 单张画框颜色
SINGLE_COLOR = (1, 255, 159)
# 单张中，颜色遮罩计算的小窗尺寸
SINGLE_LITTLE_SIZE = (640, 640)
# 是否将画框信息(rect:(左上x，左上y，右下x，右下y))保存到txt中
IF_SAVE_RECT_TXT_SINGLE = True
# 预测结果警戒值————占比版
RED_WARN_SINGLE = 0.8
YELLOW_WARN_SINGLE = 0.95

