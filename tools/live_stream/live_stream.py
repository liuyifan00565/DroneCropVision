import requests
import cv2
from ultralytics import YOLO
from flask import Flask, Response, request

#  -------参数-------
#  获取直播流地址 必传
# live_stream_url = 'http://10.7.10.105:8089/api/web/api/v1/live/streams/start/4TADL2E001003L'
# 必传, 如果不通过接口调用, 直接访问直播流会出现问题
# access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ3b3Jrc3BhY2VfaWQiOiI3OThlZjZmNi03N2U4LTQyOWEtOWM0Yy04MjI3MjA2MTYxNjUiLCJzdWIiOiJNdW5pdVVBViIsInVzZXJfdHlwZSI6IjEiLCJuYmYiOjE3MzkxNDgyNzMsImxvZyI6IkxvZ2dlcltjb20uZGppLnNhbXBsZS5jb21tb24ubW9kZWwuQ3VzdG9tQ2xhaW1dIiwiaXNzIjoiTVVOSVUiLCJpZCI6Ijc2ODg3MThkLWFhZDEtNGViNS1hZjQzLThhM2VlYzlmMGNiNiIsImV4cCI6MTgyNTU0ODI3MywiaWF0IjoxNzM5MTQ4MjczLCJ1c2VybmFtZSI6IjE3NTQ1NTY1MDI0In0.Fhwb8GgbwrGjXDd1C1EUoc5eSJNIJxweuKuX31cQaxI'
#  host
host = '10.11.89.44'
#  port
port = 5000

model = YOLO('../../../models/yolo11n.pt')  # 加载一个官方的检测模型
# model = YOLO('yolov8n-seg.pt')  # 加载一个官方的分割模型
# model = YOLO('yolov8n-pose.pt')  # 加载一个官方的姿态模型
# model = YOLO('path/to/best.pt')  # 加载一个自定义训练的模型

app = Flask(__name__)


def gen_frames(live_stream_url, access_token):
    # 自定义的headers
    headers = {
        'x-auth-token': access_token
    }
    # 发送请求
    response = requests.get(live_stream_url, headers=headers)
    response = response.json()
    rtmp_url = ''
    if response['code'] == 0:
        data = response['data']
        print(data)
        rtmp_url = data['rtmp_url']
    # 打印响应内容
    print(rtmp_url)
    cap = cv2.VideoCapture(rtmp_url)
    frame_interval = 5  # 每 frame_interval 帧检测一次
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count % frame_interval == 0:  # 每5帧进行一次检测
            results = model.track(frame)

        # 在帧上可视化结果
        annotated_frame = results[0].plot()

        ret, buffer = cv2.imencode(".jpg", annotated_frame)
        annotated_frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + annotated_frame + b'\r\n\r\n')
        # 显示带有标注的帧
        # cv2.imshow("YOLOv8 推理", annotated_frame)
        # # cv2.imshow('Live Stream', frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
    cap.release()
    cv2.destroyAllWindows()


@app.route('/video_feed')
def video_feed():
    live_stream_url = request.args.get('live_stream_url')
    access_token = request.args.get('access_token')
    return Response(gen_frames(live_stream_url, access_token), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host=host, port=port)  # 在所有可用网络接口上运行，端口5000
