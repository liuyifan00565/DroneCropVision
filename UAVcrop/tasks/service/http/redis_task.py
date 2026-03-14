import redis
import json
import main


class Task(object):

    def __init__(self):
        self.rcon = redis.StrictRedis(
            host='10.7.10.42',
            port=6379,
            db=0,  # ← 这里指定使用 0 号数据库
            password='Bdhxx@redis2025',
            decode_responses=True
        )
        # self.rcon = redis.StrictRedis(host='localhost', db=5)
        self.ps = self.rcon.pubsub()
        self.ps.subscribe('task:pubsub:channel')

    def listen_task(self):
        for i in self.ps.listen():
            if i['type'] == 'message':
                # redis_client = redis.Redis(
                #     host='10.7.10.42',
                #     port=6379,
                #     db=0,  # ← 这里指定使用 0 号数据库
                #     password='Bdhxx@redis2025',
                #     decode_responses=True
                # )
                print("Task get", i['data'])
                json_data = json.loads(i['data'])
                value = json_data[list(json_data.keys())[0]]
                if value['status'] == "doing":
                    params = value['params']
                    request_id = int(params["request_id"])
                    unique_id = params["unique_id"]
                    self.rcon.hset(f"{request_id}-{unique_id}", "status", "doing")
                    # 文件会在with语句块结束时自动关闭
                    if request_id == 1:
                        try:
                            main.seedling(params)
                        except Exception as e:
                            print(e)
                        finally:
                            print("Task done")
                    if request_id == 2:
                        try:
                            main.get_soybean_purity(params)
                        except Exception as e:
                            print(e)
                        finally:
                            print("Task done")
                    print("Task done")
                    # redis_client.lrem("task_queue", 0, data)



if __name__ == '__main__':
    print('listen task channel')
    Task().listen_task()
