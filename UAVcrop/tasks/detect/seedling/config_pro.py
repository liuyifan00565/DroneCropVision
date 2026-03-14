
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
#RESULT_PATH = '/home/ubuntu/sj/ultralytics/weishan_yumi_res'
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

