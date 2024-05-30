import requests

n = 5
m = 10
url = f'http://192.168.232.15:8000/create/{n}/{m}'

# 发送 GET 请求
response = requests.get(url)

# 打印响应内容
print(response.text)