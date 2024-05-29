# from STK import connectInterface
import requests


# 这个的主要目的是提供接口，包括建立星座，记录任务情况等
plane = 1
satellite = 8
ip = "192.168.232.13"
port = 8000


# 生成节点名字
def generateName(numOfPlane, numOfSatellite):
    return "node_{i}-{j}".format(i=numOfPlane, j=numOfSatellite)


# 初始化星座列表
def initSateList(sateList, numOfPlane, numOfSatellite):
    for i in range(numOfPlane):
        sateList.append(dict())
        for j in range(numOfSatellite):
            name = generateName(i, j)
            sateList[i][name] = list()
    print(sateList)


# 启动STK，需求应该是输入轨道数量，卫星数量，建立星座
def startSatellite(numOfPlane, numOfSatellite):
    # 设置星座参数
    connectInterface.setArgs(numOfPlane, numOfSatellite)
    # 启动STK
    scenario, ts = connectInterface.startStk()
    # 设置卫星
    connectInterface.createSatellite(scenario, ts)


# 给远程主机发送指令，创建Mininet拓扑
def createMN(numOfPlane, numOfSatellite):
    res = requests.get(r'http://{ip}:{port}/create/{n}/{m}'.format(ip=ip, port=port, n=numOfPlane, m=numOfSatellite))
    print(res.text)


# 为节点初始化任务
def initTask(numOfPlane, numOfSatellite):
    task_list = []
    for i in range(numOfPlane):
        for j in range(numOfSatellite):
            name = generateName(i, j)
            task_list.append([name, 'default'])
    res = requests.post(r'http://{ip}:{port}/initTask/'.format(ip=ip, port=port), json=task_list)
    print(res.text)


# 获得节点cpu信息
def getNodeInfo():
    res = requests.get(r'http://{ip}:{port}/getNodeInfo/'.format(ip=ip, port=port))
    print(res.text)



if __name__ == "__main__":
    # # 记录星座情况
    # sateList = []
    # # 启动星座
    # startSatellite(plane, satellite)
    # # 初始化列表
    # initSateList(sateList, plane, satellite)
    # 发送命令，在mininet上创建网络
    # createMN(plane, satellite)
    # # 为mininet上的节点初始化任务
    # initTask(plane, satellite)
    # 获得节点cpu信息
    getNodeInfo()




