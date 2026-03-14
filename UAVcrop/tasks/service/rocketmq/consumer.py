# -*- coding: utf-8 -*-
import os
import configparser
import json
import logging
import threading
import time
from typing import List
import jpype.imports
try:
    jvmPath = jpype.getDefaultJVMPath()
    # rocketmq包下载地址：https://rocketmq.apache.org/release-notes/
    jpype.startJVM(classpath=['/opt/rocketmq-all-4.9.0-bin-release/lib/*', ])
except Exception as e:
    print(str(e))
from mmengine.logging import print_log
from pyrocketmq.client.consumer.consumer import MessageSelector, PushConsumer
from pyrocketmq.client.consumer.listener import (
    ConsumeConcurrentlyContext,
    ConsumeConcurrentlyStatus,
    MessageListenerConcurrently,
)
from pyrocketmq.common.common import ConsumeFromWhere
from pyrocketmq.common.message import MessageExt
from publisher import RocketMQProducer
import pandas as pd
from tasks.detect.seedling.detect_both import get_detect_result
from utils import upload_file


con = configparser.ConfigParser()
# 读取文件
con.read('./config.ini', encoding='utf-8')
items = dict(con.items('seedling'))
upload_url = items['upload_url']
res_path = items['res_path']



class MyMessageListenerConcurrently(MessageListenerConcurrently):
    @staticmethod
    def _consumeMessage(msgs: List[MessageExt], context: ConsumeConcurrentlyContext) -> ConsumeConcurrentlyStatus:
        print('Concurrently', context.ackIndex)
        for msg in msgs:
            try:
                print(json.loads(msg.body), msg.tags)
                proc_algo(msg.body)
            except Exception as e:
                print("proc_splicing error is :", str(e))
        return ConsumeConcurrentlyStatus.CONSUME_SUCCESS


class RocketMQServer(object):
    ADDRESS = None
    CONSUMER = None
    TOPIC = None
    TAG = None
    LOG = None

    @classmethod
    def init_config(cls):
        con = configparser.ConfigParser()
        con.read('./config.ini', encoding='utf-8')
        items = con['message']
        cls.ADDRESS = items['address']
        cls.CONSUMER = items['consumer']
        cls.TOPIC = items['topic']
        cls.TAG = items['tags']
        cls.LOG = items['log']
        logging.basicConfig(level=logging.INFO,  # 控制台打印的日志级别
                            filename=cls.LOG,
                            filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                            # a是追加模式，默认如果不写的话，就是追加模式
                            format=
                            '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                            # 日志格式
                            )

    @classmethod
    def create_connection(cls):
        connection = PushConsumer(cls.CONSUMER)
        connection.setNamesrvAddr(cls.ADDRESS)
        selector = MessageSelector.byTag(None)
        # 过滤tag
        #selector = MessageSelector.byTag(cls.TAG)
        ml = MyMessageListenerConcurrently()
        connection.registerMessageListener(ml)
        connection.subscribe(cls.TOPIC, selector)
        connection.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET)
        connection.start()
        return connection


class RocketConsumer(RocketMQServer):
    @classmethod
    def start_consumer(cls):
        while True:
            try:
                time.sleep(3600 * 24 * 365)
            except KeyboardInterrupt:
                print("\nShutting down consumer...")
                cls.connection.shutdown()

    @classmethod
    def run(cls):
        cls.init_config()
        cls.connection = cls.create_connection()
        cls.start_consumer()


def convert_area_to_mu(data):
    conversion_factor = 666.67  # 1亩 = 666.67平方米

    # 遍历数据中的每个图像对象
    for image in data["Data"]:
        # 将面积从平方米转换为亩
        image["area"] = round(image["area"] / conversion_factor, 4)

    return data


def proc_algo(info):
    """
    Args:

        info:
            {
              "TaskID": "string",        // 任务ID：用于唯一标识每个任务
              "TaskType:": "string",      // 任务类型：可选值：'full'（全量识别）或'sample'（抽样识别）
              "FlightHeight": "number",  // 飞行高度
              "Data": [                // 图像列表
                {
                  "url": "string",       // 图像的URL
                  "area": "number",      // 图像的面积
                  "hight": "number",    // 图像的高度
                  "width": "number"      // 图像的宽度
                }
              ]
            }

    Returns:

    """
    logging.info("------>")
    logging.info(info)
    print("info:", info)
    info_dict = json.loads(info)
    logging.info(info_dict)
    info_dict = convert_area_to_mu(info_dict)
    task_id = info_dict["TaskID"]
    detect_type = info_dict["TaskType"]
    images = info_dict["Data"]
    # flightHeight = info_dict["FlightHeight"]
    import_file_url = [image['url'] for image in images]
    # hight = images[0]['hight'] if images else None
    # width = images[0]['width'] if images else None
    # file_size = (width, hight)
    # area_total = images[0]['area'] if images else None

    count_area = get_detect_result(task_id, detect_type, images)
    logging.info("Processing seedling")
    download_path = f"{res_path}/{task_id}/download/"
    file_names = os.listdir(download_path)
    data = []
    for url in import_file_url:
        url_img_name = url.split('/')[-1]
        if url_img_name in file_names:
            localoath = download_path + url_img_name
            processedurl = upload_file(upload_url, localoath)
            data.append({
                "url": url, "processedurl": processedurl
            })

    msg_dit = {
        "TaskID": task_id,
        "AreaCount": count_area,
        "Data": data
    }
    message = json.dumps(msg_dit).encode('utf-8')
    logging.info("Processing seedling is done")
    push_message(message)


def push_message(message):

    producer = RocketMQProducer()
    producer.start_producer()
    producer.send_message(message)
    producer.stop_producer()
    logging.info('push_message is success')
    print_log('push_message is success')
    print_log('End==========')


if __name__ == '__main__':
    # 启动线程接收
    print("开始服务")
    threading.Thread(target=RocketConsumer.run).start()