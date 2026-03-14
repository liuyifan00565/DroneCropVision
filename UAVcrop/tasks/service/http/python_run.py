import requests
import time


if __name__ == '__main__':
    time.sleep(30)
    url = "http://127.0.0.1:31775/api/v1/task_consumer_listener"
    response = requests.request("POST", url)
