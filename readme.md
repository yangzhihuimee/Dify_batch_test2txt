### 功能
批量执行dify具体工作流并接收回复，写成txt文件


### 需要手动添加：
1. utils/dify_client_v2.py：
base_url
inputs处的入参

2. batch_test.py：
具体某一工作流的 api_key
测试文件路径，如 query.txt
输出文件路径，如 result.txt

3.测试问题集 query.txt


### 输出含图片URL的解决办法
可修改代码输出为md文件，或将txt文件转为md文件，将输出md文件和原图片放在一个目录下，用支持md渲染的软件打开

-输出目录/
|——原图片
|——输出文件.md

