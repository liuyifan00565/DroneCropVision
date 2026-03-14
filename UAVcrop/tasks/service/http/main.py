from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import logging
import os
import uvicorn
import threading
from tasks.service.http import config
from tasks.service.http import algo_config
from tasks.service.http.utils import upload_file
from tasks.detect.seedling import config as con
from tasks.detect.seedling.detect_both import get_detect_result
from typing import List, Dict, Any
import requests
import redis
import json
import time
from tasks.service.http.addTiff2Geoserver import deploy2Geserver

app = FastAPI()

# Setup logging
log_file_path = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

rcon = redis.StrictRedis(
    host='10.7.10.42',
    port=6379,
    db=0,  # ← 这里指定使用 0 号数据库
    password='Bdhxx@redis2025',
    decode_responses=True
)

def convert_area_to_mu(data):
    conversion_factor = 666.67  # 1亩 = 666.67平方米

    # 遍历数据中的每个图像对象
    for image in data["Data"]:
        # 将面积从平方米转换为亩
        image["area"] = round(image["area"] / conversion_factor, 4)

    return data


class ImageData(BaseModel):
    url: str
    area: float
    height: float
    width: float


class ProcAlgoRequest(BaseModel):
    TaskID: str = None
    TaskType: str = None
    # FlightHeight: float
    N: int = None
    Confidence: float = None
    Marginal_of_error: float = None
    request_id: str = None
    unique_id: str = None
    Area: str = None
    Data: list = None
    red_warn: str = None
    yellow_warn: str = None
    expect_counts: str = None

    class Config:
        extra = "ignore"


# 完整的响应模型
class AlgoOutput(BaseModel):
    success: bool
    code: int
    message: str
    data: dict

    def to_dict(self):
        return {'success': self.success, 'code': self.code, 'message': self.message, 'data': self.data}

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


# 定义请求模型
class SoybeanRequest(BaseModel):
    TaskID: str
    Area: str
    Urls: List[str]


@app.get("/api/v1/algo_config", response_model=List[Dict[str, Any]])
async def get_algo_config():
    """
    Returns the complete algorithm configuration from algo_config.py
    """
    return algo_config.list_info


# @app.post("/api/v1/seedling/")
def seedling(info_dict):
    """
    幼苗检测接口

    - **TaskID**: 任务ID
    - **TaskType**: 算法类型：1 全量识别, 2 抽样识别
    - **Data**: 包含图像像素的高height和宽width、图像对应区域的实际面积area，单位：平方米。
    """
    global urls
    logging.info("Processing request: %s", info_dict)

    task_id = info_dict["TaskID"]
    detect_type = int(info_dict["TaskType"])
    area = int(info_dict["Area"])
    unique_id = info_dict["unique_id"]
    request_id = int(info_dict["request_id"])
    red_warn = info_dict.get("red_warn", con.RED_WARN_SINGLE)
    yellow_warn = info_dict.get("yellow_warn", con.YELLOW_WARN_SINGLE)
    expect_counts = info_dict.get("expect_counts", con.EXPECT_COUNTS)
    n = info_dict.get("N", con.N)
    confidence = info_dict.get("Confidence", con.CONFIDENCE)
    marginal_of_error = info_dict.get("Marginal_of_error", con.EXPECTED_PERCENT)
    import_file_list = [image for image in info_dict["Data"]]

    # Set default values using a helper function
    def get_default(value, default):
        return value if value is not None else default

    count_area = dict()
    # Compute the detection results
    try:
        count_area = get_detect_result(task_id=task_id, detect_type=detect_type, area=area, import_file_list=import_file_list,
                                        red_warn_single=red_warn, yellow_warn_single=yellow_warn, expect_counts=expect_counts, n=n,
                                       confidence=confidence, expected_percent=marginal_of_error)

        if count_area['count_area'] <= 0:
            rcon.hset(f"{request_id}-{unique_id}", "status", "finish")
            rcon.hset(f"{request_id}-{unique_id}", "data", json.dumps(AlgoOutput(
                success=False,
                code=500,
                message=f"Seedling analysis Algorithm exception：没识别到幼苗",
                data={}
            ).to_dict()))
    except Exception as e:
        print(f"Seedling analysis Algorithm exception：{e}")
        rcon.hset(f"{request_id}-{unique_id}", "status", "finish")
        rcon.hset(f"{request_id}-{unique_id}", "data", json.dumps(AlgoOutput(
            success=False,
            code=500,
            message=f"Seedling analysis Algorithm exception：{e}",
            data={}
        ).to_dict()))
    count_area['count_area'] = int(count_area['count_area'] * 666.67)
    final_path = f"{con.RESULT_PATH}/{task_id}/final/"
    urls = []
    # Process and upload files
    if int(detect_type) == 2:
        # 去掉抽样算法标记处理
        # urls = [
        # {"url": url, "processedurl": upload_file(config.upload_url, os.path.join(final_path, url.split('/')[-1]))}
        # for url in import_file_list if url.split('/')[-1] in file_names
        # ]
        url_list = count_area['import_file_choose_list']
        rects_list = count_area['rects_list']
        for i in range(0, len(url_list)):
            urls.append({url_list[i]: rects_list[i]})
    elif int(detect_type) == 1:
        # 上传可见光结果到Geserver
        output_path_tif = f"Seedling_Complete_{task_id}.tif"
        resp = deploy2Geserver(final_path, output_path_tif)
        if resp == 201:
            urls = [
                {
                    "url": import_file_list[0],
                    "processedurl": upload_file(config.upload_url,
                                                os.path.join(final_path, f"Seedling_Complete_{task_id}.tif")),
                    "layer_name": f"Seedling_Complete_{task_id}",
                    "layer_baseurl": "http://10.7.10.42:30158/geoserver",
                    "layer_space": "bdhxx"
                }
            ]
    else:
        file_path = count_area['file_path']
        upload_file(config.upload_url, file_path)
        urls.append({'url': file_path})
    # Construct response data
    data = {"urls": urls}
    if int(detect_type) == 2:
        data.update({
            "confidence_left": count_area['confidence_left'],
            "confidence_right": count_area['confidence_right'],
            "sampling_n": count_area['sampling_n']
        })
    if int(detect_type) == 3:
        data.update({
            "result": count_area['res_test'],
            "total_counts": count_area['total_counts'],
            "count_area": count_area['count_area']
        })

    # 全量结果图标记说明
    # if int(detect_type) == 1:
    #    data.update({
    #        "yellow_warning": 0.9,
    #        "red_warning": 0.5,
    #    })

    # Log and return the response
    msg_dict = {"TaskID": task_id, "AreaCount": count_area['count_area'], "Data": data}
    logging.info("Processing seedling is done")
    rcon.hset(f"{request_id}-{unique_id}", "status", "finish")
    rcon.hset(f"{request_id}-{unique_id}", "data", json.dumps(AlgoOutput(
        success=True,
        code=200,
        message="Seedling analysis completed successfully.",
        data=msg_dict
    ).to_dict()))


def request_soybean_purity(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送大豆纯度检测请求并返回JSON响应

    Args:
        data: 包含 TaskID, Area 和 Urls 的字典

    Returns:
        解析后的JSON响应数据

    Raises:
        HTTPException: 封装所有异常为FastAPI的HTTP异常
    """
    url = "http://10.7.10.42:30092/api/v1/soybean_purity"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=data)  # timeout=10
    response.raise_for_status()
    return response.json()


# @app.post("/api/v1/soybean-purity", response_model=Dict[str, Any])
def get_soybean_purity(request_data):
    """
    大豆纯度检测接口

    - **TaskID**: 任务ID
    - **Area**: 区域
    - **Urls**: 图片URL列表
    """

    redis_client = redis.Redis(
        host='10.7.10.42',
        port=6379,
        db=0,  # ← 这里指定使用 0 号数据库
        password='Bdhxx@redis2025',
        decode_responses=True
    )
    unique_id = request_data["unique_id"]
    request_id = int(request_data["request_id"])
    try:
        # 将Pydantic模型转换为字典
        # request_data = request.dict()
        data = request_soybean_purity(request_data)
        redis_client.hset(f"{request_id}-{unique_id}", "status", "finish")
        redis_client.hset(f"{request_id}-{unique_id}", "data", json.dumps(AlgoOutput(
            success=True,
            code=200,
            message="Seedling analysis completed successfully.",
            data=data
        ).to_dict()))
    except Exception as e:
        redis_client.hset(f"{request_id}-{unique_id}", "status", "finish")
        redis_client.hset(f"{request_id}-{unique_id}", "data", json.dumps(AlgoOutput(
            success=True,
            code=200,
            message=f"服务器内部错误: {str(e)}",
            data={}
        ).to_dict()))


# 健康检查端点
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/task_request")
async def task_request(request: ProcAlgoRequest):
    logging.info("Processing request: %s", request.dict())

    # Extract and convert data
    # info_dict = convert_area_to_mu(request.dict())
    info_dict = request.dict()
    print(info_dict)
    unique_id = info_dict["unique_id"]
    request_id = int(info_dict["request_id"])
    pubsub_channel = 'task:pubsub:channel'
    if rcon.hget(f"{request_id}-{unique_id}", "status") == "doing":
        print("doing")
        return AlgoOutput(
            success=True,
            code=200,
            message="Seedling analysis is doing.",
            data={}
        )
    elif rcon.hget(f"{request_id}-{unique_id}", "status") == "finish":
        print("finish")
        res = rcon.hget(f"{request_id}-{unique_id}", "data")
        # await redis_client.delete(f"{request_id}-{unique_id}")
        if res is not None:
            return AlgoOutput.from_dict(json.loads(res))
        else:
            return AlgoOutput(
                success=True,
                code=200,
                message="Seedling analysis is beginning.",
                data={}
            )
    elif rcon.hget(f"{request_id}-{unique_id}", "status") is None:
        print("Nope+++++++++++++++")
        in_params = {f"{request_id}-{unique_id}": {
            "status": "doing",
            "params": info_dict
        }}
        # redis_client.lpush("task_queue", json.dumps(in_params))
        ps = rcon.pubsub()
        ps.subscribe(pubsub_channel)
        rcon.publish(pubsub_channel, json.dumps(in_params))
        return AlgoOutput(
            success=True,
            code=200,
            message="Seedling analysis is beginning.",
            data={}
        )


# @app.post("/api/v1/task_consumer_listener")
# def consumer():
#     redis_client = redis.Redis(
#         host='10.7.10.42',
#         port=6379,
#         db=0,  # ← 这里指定使用 0 号数据库
#         password='Bdhxx@redis2025',
#         decode_responses=True
#     )
#     while True:
#         task_list = redis_client.lrange("task_queue", 0, -1)
#         for data in task_list:
#             print(data)
#             json_data = json.loads(data)
#             key = list(json_data.keys())[0]
#             value = json_data.get(key)
#             if value['status'] == "doing":
#                 params = value['params']
#                 request_id = int(params["request_id"])
#                 unique_id = params["unique_id"]
#                 redis_client.hset(f"{request_id}-{unique_id}", "status", "doing")
#                 if request_id == 1:
#                     seedling(params)
#                 if request_id == 2:
#                     get_soybean_purity(params)
#                 redis_client.lrem("task_queue", 0, data)
#         time.sleep(1)  # 等待一段时间后再次检查队列


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
    threading.Thread(target=uvicorn.run,
                     args=(app,),
                     kwargs={'host': config.host, 'port': config.port}).start()
