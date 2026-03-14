import jpype
import jpype.imports
try:
    jvmPath = jpype.getDefaultJVMPath()
    jpype.startJVM(classpath=['/opt/rocketmq-all-4.9.0-bin-release/lib/*', ])
except Exception as e:
    print(str(e))

import json
import configparser
from pyrocketmq.common.message import Message
from pyrocketmq.client.producer import Producer, SendStatus


con = configparser.ConfigParser()
con.read('./config.ini', encoding='utf-8')
items = con.items('push_message')
#items = con.items('message')
items = dict(items)
print('items:', items)

address = items['address']
topic = items['topic']
producer = items['producer']
tags = items['tags']

class RocketMQProducer(object):
    def __init__(self):
        self.producer = Producer(producer)

    def start_producer(self):
        self.producer.setNamesrvAddr(address)
        self.producer.start()

    def stop_producer(self):
        self.producer.shutdown()
        #jpype.shutdownJVM()

    def send_message(self, msg):
        msg = Message(topic=topic, body=msg, tags=tags)
        print('msg.tags', msg.tags)
        print('msg.body', msg.body)
        sr = self.producer.send(msg)
        assert (sr.sendStatus == SendStatus.SEND_OK)


if __name__ == '__main__':
    dit = {"TaskId": 88888888,
           "OrgCode": "8601080102",
           "StartYearList": ["2022", "2023", "2024"],
           "PlotYear": "2024",
            "FertilizeType": "jifei"}
    msg = json.dumps(dit).encode('utf-8')
    producer = RocketMQProducer()
    producer.start_producer()
    producer.send_message(msg)
    producer.stop_producer()