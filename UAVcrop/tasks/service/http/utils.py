# 上传文件
import json
import requests

def upload_file(uploadurl, localoath):
    """
    上传文件
    :return:图片url
    """
    file = open(localoath, 'rb')
    files = {'file': (localoath, file, 'application/octet-stream',
                      {'Expires': '0'})}  # 字段名files 以及类型和application/octet-stream 和抓取到的接口一致
    headers = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Length': '41669',
        'Pragma': 'no-cache',
        "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G988N Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36"
    }
    #try:
    # r = requests.post(url=uploadurl, files=files, headers=headers, timeout=(2, 10))  # post传递数据
    r = requests.post(url=uploadurl, files=files, headers=headers)
    print(r.text)
    jsonObj = json.loads(r.text)  # 转为json对象
    print("jsonObj:", jsonObj)
    return jsonObj['data']
    #except Exception as e:
    #    print(e)
    #    return None

if __name__ == "__main__":
    # 生产
    uploadurl = "http://10.7.13.1:32111/file/obs/upload?keyCode=6521e74c5ca64ec886e7d299df453873"
    # 测试
    #uploadurl = "http://10.11.14.214:31111/file/obs/upload?keyCode=6521e74c5ca64ec886e7d299df453873"
    # 开发
    #uploadurl = "http://10.11.14.214:31111/file/obs/upload?keyCode=6521e74c5ca64ec886e7d299df453873"
    localoath = "/Users/macq1/Downloads/7d61382c3f184aa0a4f274b73e3131591747381352942.jpeg"

    res = upload_file(uploadurl, localoath)
    print(res)