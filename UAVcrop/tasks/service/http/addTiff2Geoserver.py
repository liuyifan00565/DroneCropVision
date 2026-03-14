#!/usr/bin/python3
# -*-coding:utf-8 -*-

import requests
import os.path as osp
import sys
import getopt
import os
from tasks.service.http import config


def deploy2Geserver(base_dir, inf):
    try:
        # 获取配置
        host = config.geoserver_host
        port = config.geoserver_port
        user = config.geoserver_user
        pswd = config.geoserver_pswd
        workspace = config.geoserver_workspace

        # 处理文件路径
        base_name = osp.splitext(osp.basename(inf))[0]
        tif_path = osp.join(base_dir, f"{base_name}.tif")

        # 读取文件内容
        with open(tif_path, 'rb') as f:
            tif_data = f.read()

        # 创建存储
        create_url = f"http://{host}:{port}/geoserver/rest/workspaces/{workspace}/coveragestores/{base_name}/file.geotiff"

        # 上传文件
        headers = {'Content-type': 'image/tiff'}
        resp = requests.put(
            create_url,
            auth=(user, pswd),
            data=tif_data,
            headers=headers
        )
        return resp.status_code
        print(f"成功上传并部署 {base_name} 到GeoServer")

    except Exception as e:
        print(f"部署失败: {str(e)}", file=sys.stderr)
        return 500