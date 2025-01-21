from STK.ConnectInterface import ConnectInterface
import requests


# 这个的主要目的是提供接口，包括建立星座，记录任务情况等
plane = 1
satellite = 8
ip = "192.168.232.15"
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
    sat_list, sat_dic = connectInterface.createSatellite(scenario, ts)
    return sat_list, sat_dic


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
    print("initTask: ", res.text)


# 获得节点cpu信息
def getNodeInfo():
    res = requests.get(r'http://{ip}:{port}/getNodeInfo/'.format(ip=ip, port=port))
    print("getNodeInfo: ", res.text)


# 获得STK的链路信息
def getSTKInfo(sat_list, sat_dic):
    data_list = connectInterface.getLinkChange(sat_list, sat_dic)
    print("getSTKInfo: ", data_list)


# 改变指定卫星上任务的核心，
def changeTaskCore(plane, satellite, new_core):
    name = generateName(plane, satellite)
    # new_core从0开始
    task_list = [{'name': name, 'core': new_core}]
    res = requests.post(r'http://{ip}:{port}/modifyCore/'.format(ip=ip, port=port), json=task_list)
    print("changeTaskCore: ", res.text)



if __name__ == "__main__":
    # # 记录星座情况
    # sateList = []
    # # 启动星座
    # sat_list, sat_dic = startSatellite(plane, satellite)
    # # 初始化列表
    # initSateList(sateList, plane, satellite)
    # # 同步节点时延等信息
    # getSTKInfo(sat_list, sat_dic)
    # 发送命令，在mininet上创建网络
    createMN(plane, satellite)
    # 为mininet上的节点初始化任务
    initTask(plane, satellite)
    # 获得节点cpu信息
    getNodeInfo()
    # 改变节点上面运行任务占用的核心
    changeTaskCore(0, 0, 2)







