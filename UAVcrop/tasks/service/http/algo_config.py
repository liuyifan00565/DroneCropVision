res = dict()
list_info = [

    {"url": "http://10.7.13.1:31775/api/v1/seedling/", "method": "POST", "type_name": "全量亩苗数", "type_id": 1,
     "input_params": [
         {"param_name": "TaskID", "param_type": "str", "param_describe": "用于唯一标识每个任务的ID。",
          "if_necessary": "True"},
         {"param_name": "TaskType", "param_type": "int",
          "param_describe": "￮指定任务为全量识别或抽样识别。可选值: 1 全量识别, 2 抽样识别",
          "if_necessary": "True"},
         {"param_name": "Data", "param_type": "List[Dict]",
          "param_describe": "包含图像像素的高height和宽width、图像对应区域的实际面积area，单位：平方米。",
          "if_necessary": "True",
          "inner_dict": [
              {"param_name": "url", "param_type": "str", "param_describe": "全量tif文件路径",
               "if_necessary": "True"},
              {"param_name": "area", "param_type": "float", "param_describe": "占地面积",
               "if_necessary": "True"},
              {"param_name": "height", "param_type": "str", "param_describe": "tif文件高（像素）",
               "if_necessary": "True"},
              {"param_name": "width", "param_type": "str", "param_describe": "tif文件宽（像素）",
               "if_necessary": "True"}
          ]},
         {"param_name": "N", "param_type": "int",
          "param_describe": "进行抽样识别的样本数，如果不传入，将使用默认配置值30。", "if_necessary": "False"},
         {"param_name": "Confidence", "param_type": "float",
          "param_describe": "抽样检验的置信度，如果不传入，将使用默认配置值0.95。", "if_necessary": "False"},
         {"param_name": "Marginal_of_error", "param_type": "float", "param_describe": "float",
          "if_necessary": "False"}
     ],
     "output_params": [
         {"param_name": "success", "param_type": "str", "param_describe": "请求是否成功，True 或False。"},
         {"param_name": "code", "param_type": "int", "param_describe": "请求状态码，200 表示成功。"},
         {"param_name": "message", "param_type": "str", "param_describe": "本次请求描述。"},
         {"param_name": "data", "param_type": "dict",
          "param_describe": "data",
          "inner_dict": [{"param_name": "TaskID", "param_type": "str", "param_describe": "与请求中的任务ID匹配。"},
                         {"param_name": "AreaCount", "param_type": "int", "param_describe": "旱田：苗/亩；水田:穴/亩。"},
                         {"param_name": "Data", "param_type": "dict",
                          "param_describe": "处理后的图像结果列表jin，包含原图像URL及其处理后的URL。当调用抽样算法时，还会输出置信区间左右的值,和建议抽样数",
                          "inner_dict": [
                              {"param_name": "urls", "param_type": "List[Dict]", "param_describe": "全量tif文件路径",
                               "inner_dict": [
                                   {"param_name": "url", "param_type": "str", "param_describe": ""},
                                   {"param_name": "processedurl", "param_type": "str", "param_describe": ""}
                               ]}
                          ]}]}

     ]
     },
    {"url": "http://10.7.13.1:31775/api/v1/seedling/", "method": "POST", "type_name": "抽样亩苗数", "type_id": 2,
     "input_params": [
         {"param_name": "TaskID", "param_type": "str", "param_describe": "用于唯一标识每个任务的ID。",
          "if_necessary": "True"},
         {"param_name": "TaskType", "param_type": "int",
          "param_describe": "￮指定任务为全量识别或抽样识别。可选值: 1 全量识别, 2 抽样识别",
          "if_necessary": "True"},
         {"param_name": "Data", "param_type": "List[Dict]",
          "param_describe": "包含图像像素的高height和宽width、图像对应区域的实际面积area，单位：平方米。",
          "if_necessary": "True",
          "inner_dict": [
              {"param_name": "url", "param_type": "str", "param_describe": "全量tif文件路径",
               "if_necessary": "True"},
              {"param_name": "area", "param_type": "float", "param_describe": "占地面积",
               "if_necessary": "True"},
              {"param_name": "height", "param_type": "str", "param_describe": "tif文件高（像素）",
               "if_necessary": "True"},
              {"param_name": "width", "param_type": "str", "param_describe": "tif文件宽（像素）",
               "if_necessary": "True"}
          ]},
         {"param_name": "N", "param_type": "int",
          "param_describe": "进行抽样识别的样本数，如果不传入，将使用默认配置值30。", "if_necessary": "False"},
         {"param_name": "Confidence", "param_type": "float",
          "param_describe": "抽样检验的置信度，如果不传入，将使用默认配置值0.95。", "if_necessary": "False"},
         {"param_name": "Marginal_of_error", "param_type": "float", "param_describe": "float",
          "if_necessary": "False"}
     ],
     "output_params": [
         {"param_name": "success", "param_type": "str", "param_describe": "请求是否成功，True 或False。"},
         {"param_name": "code", "param_type": "int", "param_describe": "请求状态码，200 表示成功。"},
         {"param_name": "message", "param_type": "str", "param_describe": "本次请求描述。"},
         {"param_name": "data", "param_type": "dict",
          "param_describe": "data",
          "inner_dict": [
              {"param_name": "TaskID", "param_type": "str", "param_describe": "与请求中的任务ID匹配。"},
              {"param_name": "AreaCount", "param_type": "int", "param_describe": "旱田：苗/亩；水田:穴/亩。"},
              {"param_name": "Data", "param_type": "dict",
               "param_describe": "处理后的图像结果列表jin，包含原图像URL及其处理后的URL。当调用抽样算法时，还会输出置信区间左右的值,和建议抽样数",
               "inner_dict": [
                   {"param_name": "urls", "param_type": "List[Dict]", "param_describe": "全量tif文件路径",
                    "inner_dict": [
                        {"param_name": "url", "param_type": "str", "param_describe": ""},
                        {"param_name": "processedurl", "param_type": "str", "param_describe": ""}
                    ]},
                   {"param_name": "confidence_left", "param_type": "float", "param_describe": "置信区间左"},
                   {"param_name": "confidence_right", "param_type": "float", "param_describe": "置信区间右"},
                   {"param_name": "sampling_n", "param_type": "int", "param_describe": "建议抽样数量"}
               ]}
          ]}
     ]
     },
    {"url": "http://10.7.13.1:31775/api/v1/soybean_purity", "method": "POST", "type_name": "大豆杂株识别",
     "type_id": 3,
     "input_params": [
         {"param_name": "TaskID", "param_type": "str", "param_describe": "用于唯一标识每个任务的ID。",
          "if_necessary": "True"},
         {"param_name": "Area", "param_type": "str",
          "param_describe": "飞行范围 ，单位：亩。",
          "if_necessary": "True"},
         {"param_name": "Urls", "param_type": "List[str]",
          "param_describe": "图像url列表，可传多个。",
          "if_necessary": "True"}
     ],
     "output_params": [
         {"param_name": "success", "param_type": "str", "param_describe": "请求是否成功，True 或False。"},
         {"param_name": "code", "param_type": "int", "param_describe": "请求状态码，200 表示成功。"},
         {"param_name": "message", "param_type": "str", "param_describe": "本次请求描述。"},
         {"param_name": "data", "param_type": "dict",
          "param_describe": "project_name",
          "inner_dict": [
              {"param_name": "project_name", "param_type": "str", "param_describe": "项目名称，同任务 ID"},
              {"param_name": "hybrid_plant_num", "param_type": "int", "param_describe": "识别杂株个数（个）"},
              {"param_name": "create_time", "param_type": "str", "param_describe": "算法开始时间"},
              {"param_name": "end_time", "param_type": "str", "param_describe": "算法结束时间"},
              {"param_name": "purity", "param_type": "float", "param_describe": "纯度鉴定结果"},
              {"param_name": "purity_type", "param_type": "list[str]",
               "param_describe": "杂株性状，包括（round_leaf：圆叶；white_flower：白花）"},
              {"param_name": "plant_num", "param_type": "int", "param_describe": "地块总株数（评估值）"},
              {"param_name": "hybrid_plants", "param_type": "dict",
               "param_describe": "数据格式为dict，其中 key 每个 url中照片的名称，value 为杂株识别详情",
               "inner_dict": [
                   {"param_name": "每个url中照片的名称", "param_type": "dict", "param_describe": "为杂株识别详情",
                    "inner_dict": [
                        {"param_name": "block", "param_type": "List[Dict]", "param_describe": "数据格式为list，其中的每个元素为杂株详情截图相关参数",
                         "inner_dict": [
                             {"param_name": "image", "param_type": "str", "param_describe": "杂株截图名称"},
                             {"param_name": "type", "param_type": "str", "param_describe": "杂株类型"},
                             {"param_name": "iou", "param_type": "float", "param_describe": "识别准确度"},
                             {"param_name": "pos_1", "param_type": "list[int]", "param_describe": "原图中杂株的像素坐标 1"},
                             {"param_name": "pos_2", "param_type": "list[int]", "param_describe": "原图中杂株的像素坐标 2"},
                             {"param_name": "block_url", "param_type": "str", "param_describe": "杂株截图url"}
                         ]}
                    ]}
               ]}
          ]}
     ]
     }

]
