# modelarts_to_labelimg

    华为云ModelArts格式转LabelImg格式

## classes = ['大豆', '水稻', '玉米']
    需要所有的作物类型数组

## IN_PATH = r"E:\pyProject\local\ymsdddXmlFile\ymXmlFile"  # xml文件夹路径
## OUT_PATH = r"E:\pyProject\local\ymsdddXmlFile\ym"  # txt文件夹路径
    需要每种作物的jpg图片以及xml格式的数据

## classes.txt
    转换完成后，jpg文件和txt文件应该在一个目录下且同名
    需要在该目录下新增classes.txt文件，标明所有作物类型
    classes.txt示例

        dadou
        shuidao
        yumi

## labelImg
    转换完成的文件夹，可以用labelImg打开，会自动进行标注