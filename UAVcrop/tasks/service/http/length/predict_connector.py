"""
时间: 2025-04-26
版本: 1.0.0
作者: luogy
功能: 玉米长宽检测API (支持GPU加速、日志记录、图片存储)
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image, UnidentifiedImageError
import io
import uvicorn
import torch

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="玉米长宽检测API",
    description="基于YOLO模型的玉米长宽检测服务",
    version="1.0.0"
)

# Configuration
MODEL_PATH = "best.pt"
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# GPU setup
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

def save_uploaded_image(file: UploadFile) -> str:
    """Save uploaded image with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = file.filename.split('.')[-1]
    save_path = os.path.join(UPLOAD_DIR, f"corn_{timestamp}.{file_ext}")
    
    with open(save_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    logger.info(f"Image saved to: {save_path}")
    return save_path

@app.get("/", tags=["Health Check"])
async def health_check():
    """API健康检查端点"""
    return {
        "message": "API运行正常",
        "status": "active",
        "device": device
    }

@app.get("/api/v1/reasoning/req/desc", tags=["Documentation"])
async def get_request_description():
    """获取接口使用说明"""
    return {
        "inputType": "图片",
        "modelIntro": "玉米长宽检测模型，返回图像中玉米的宽度和长度(像素)",
        "inputDesc": "上传包含玉米的JPG/PNG格式图片",
        "inputDemo": {"file": "example.jpg"},
        "outputDesc": "返回二维数组，每个元素代表[宽度,长度]（像素值）",
        "outputDemo": {
            "success": True,
            "code": 200,
            "msg": "success",
            "data": {"result": [[150, 200], [100, 120]]}
        }
    }

@app.post("/api/v1/reasoning", tags=["Prediction"])
async def predict_corn_dimensions(file: UploadFile = File(...)):
    """玉米长宽检测主接口"""
    try:
        # 1. Validate input is an image
        if not file.content_type.startswith('image/'):
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail="输入有问题：仅支持图片文件"
            )

        # 2. Save the uploaded image
        image_path = save_uploaded_image(file)
        file.file.seek(0)  # Reset file pointer after saving

        # 3. Load and verify image
        try:
            image_bytes = await file.read()
            img = Image.open(io.BytesIO(image_bytes))
        except UnidentifiedImageError:
            raise HTTPException(400, detail="输入有问题：无法识别的图片格式")

        # 4. Initialize model with GPU support
        model = YOLO(MODEL_PATH)
        model.to(device)
        logger.info(f"Model loaded on {device}")

        # 5. Run prediction
        results = model(img)
        res = []
        
        for result in results:
            if result.boxes is None:
                logger.warning("No corn detected in image")
                continue
                
            xywh = result.boxes.xywh
            logger.info(f"Detected {len(xywh)} corn objects")
            
            for row in xywh:
                width = round(row[2].item(), 2)
                length = round(row[3].item(), 2)
                logger.debug(f"Corn size - width: {width}, length: {length}")
                res.append([width, length])

        if not res:
            raise HTTPException(400, detail="未检测到玉米对象")

        return {
            "success": True,
            "code": 200,
            "msg": "success",
            "data": {
                "result": res,
                "image_path": image_path,
                "device_used": device
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "code": 500,
                "msg": "服务器内部错误"
            }
        )

if __name__ == "__main__":
    logger.info("Starting Corn Measurement API")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None
    )