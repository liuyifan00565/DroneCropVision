FROM harbor.host.com/public/mcvision2.0-base:latest

RUN yum install -y python38 python38-devel
RUN yum install -y  postgresql-devel*

#COPY bdh-shifei-rocketmq/rocketmq-client-cpp-2.0.0-centos7.x86_64.rpm /opt
#RUN cd /opt && rpm -ivh rocketmq-client-cpp-2.0.0-centos7.x86_64.rpm
#RUN ln -s /usr/local/lib/librocketmq.so /usr/lib && ldconfig

RUN mkdir ~/.pip
RUN echo '[global]' >> ~/.pip/pip.conf
RUN echo 'index-url = https://pypi.tuna.tsinghua.edu.cn/simple/' >> ~/.pip/pip.conf

RUN python3 -m pip install --upgrade pip
RUN pip3 install psycopg2-binary==2.9.3
RUN pip3 install requests==2.28.1
RUN pip3 install numpy==1.23.2
RUN pip3 install pandas==1.4.4
RUN pip3 install geojson==2.5.0
RUN pip3 install shapely==1.8.4
RUN pip3 install geopandas==0.12.2
RUN pip3 install mmengine==0.10.1
RUN pip3 install rocketmq-client-python==2.0.0
RUN pip3 install JPype1==1.5.0
RUN pip3 install pyrocketmq==0.3.4
RUN pip3 install rasterio==1.3.11
RUN pip3 install scipy==1.10.1

COPY tasks/service/rocketmq /opt
COPY tasks/detect/seedling /opt/tasks/detect/seedling
COPY tasks/tools /opt/tasks/tools
RUN cd /opt/tasks/detect/seedling && mv config_pro.py  config.py

# copy rocketmq客户端驱动4.8.0
RUN cd /opt && unzip rocketmq-all-4.9.0-bin-release.zip

RUN cd /opt && chmod 755 consumer.py
RUN cd /opt && chmod 755 entrypoint.sh

ENTRYPOINT cd /opt && ./entrypoint.sh>>/app/logs/bdh-ai-seedlingmq.log
