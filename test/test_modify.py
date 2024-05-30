import requests




print(requests.get(r'http://192.168.232.15:8000/getNodeInfo/').text)

# res = requests.post(r'http://192.168.232.15:8000/modifyCore/', json=[{'pid': 7084, 'core': 0, 'node':'node_0-5'}])
