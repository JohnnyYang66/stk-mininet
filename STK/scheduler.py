from STK import connectInterface


# 这个的主要目的是提供接口，包括建立星座，记录任务情况等
plane = 1
satellite = 8


# 启动STK，需求应该是输入轨道数量，卫星数量，建立星座
def startSatellite(numOfPlane, numOfSatellite):
    # 设置星座参数
    connectInterface.setArgs(numOfPlane, numOfSatellite)
    # 启动STK
    scenario, ts = connectInterface.startStk()
    # 设置卫星
    connectInterface.createSatellite(ts)


if __name__ == "__main__":
    # 记录星座情况
    sateList = []
    # 启动星座
    startSatellite(plane, satellite)
    #




