import time
from tqdm import tqdm

startTime = time.time()
from comtypes.gen import STKObjects, STKUtil, AgStkGatorLib
from comtypes.client import CreateObject, GetActiveObject, GetEvents, CoGetObject, ShowEvents
import requests
import time

"""
SET TO TRUE TO USE ENGINE, FALSE TO USE GUI
"""
useStkEngine = False
Read_Scenario = False
############################################################################
# Scenario Setup
############################################################################


if useStkEngine:
    # Launch STK Engine
    print("Launching STK Engine...")
    stkxApp = CreateObject("STK11.Application")

    # Disable graphics. The NoGraphics property must be set to true before the root object is created.
    stkxApp.NoGraphics = True

    # Create root object
    stkRoot = CreateObject('AgStkObjects11.AgStkObjectRoot')

else:
    # Launch GUI
    print("Launching STK...")
    if not Read_Scenario:
        uiApp = CreateObject("STK11.Application")
    else:
        uiApp = GetActiveObject("STK11.Application")
    uiApp.Visible = True
    uiApp.UserControl = True

    # Get root object
    stkRoot = uiApp.Personality2

# Set date format
stkRoot.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")
# Create new scenario
print("Creating scenario...")
if not Read_Scenario:
    # stkRoot.NewScenario('Kuiper')
    stkRoot.NewScenario('StarLink')
scenario = stkRoot.CurrentScenario
scenario2 = scenario.QueryInterface(STKObjects.IAgScenario)
scenario2.StartTime = '24 Sep 2020 16:00:00.00'
scenario2.StopTime = '25 Sep 2020 16:20:00.00'
dt='24 Sep 2020 16:00:00'
ts = int(time.mktime(time.strptime(dt, "%d %b %Y %H:%M:%S")))


totalTime = time.time() - startTime
print("---Total time: {b:4.3f} sec ---".format(b=totalTime))


# 创建星座
def Creat_satellite(numOrbitPlanes=72, numSatsPerPlane=22, hight=550, Inclination=53, name='node_'):
    # Create constellation object
    print("--- create satellite ,total num :{a}    ---".format(a=numOrbitPlanes * numSatsPerPlane))
    constellation = scenario.Children.New(STKObjects.eConstellation, name)
    constellation2 = constellation.QueryInterface(STKObjects.IAgConstellation)

    # Insert the constellation of Satellites
    for orbitPlaneNum in range(numOrbitPlanes):  # RAAN in degrees
        print("---create sat on orbitPlane {a} ---".format(a=orbitPlaneNum))

        for satNum in range(numSatsPerPlane):  # trueAnomaly in degrees
            # Insert satellite
            satellite = scenario.Children.New(STKObjects.eSatellite, f"{name}{orbitPlaneNum}-{satNum}")
            satellite2 = satellite.QueryInterface(STKObjects.IAgSatellite)

            # Select Propagator
            satellite2.SetPropagatorType(STKObjects.ePropagatorTwoBody)

            # Set initial state
            twoBodyPropagator = satellite2.Propagator.QueryInterface(STKObjects.IAgVePropagatorTwoBody)
            keplarian = twoBodyPropagator.InitialState.Representation.ConvertTo(
                STKUtil.eOrbitStateClassical).QueryInterface(STKObjects.IAgOrbitStateClassical)

            keplarian.SizeShapeType = STKObjects.eSizeShapeSemimajorAxis
            keplarian.SizeShape.QueryInterface(
                STKObjects.IAgClassicalSizeShapeSemimajorAxis).SemiMajorAxis = hight + 6371  # km
            keplarian.SizeShape.QueryInterface(STKObjects.IAgClassicalSizeShapeSemimajorAxis).Eccentricity = 0

            keplarian.Orientation.Inclination = int(Inclination)  # degrees
            keplarian.Orientation.ArgOfPerigee = 0  # degrees
            keplarian.Orientation.AscNodeType = STKObjects.eAscNodeRAAN
            RAAN = 360 / numOrbitPlanes * orbitPlaneNum
            keplarian.Orientation.AscNode.QueryInterface(STKObjects.IAgOrientationAscNodeRAAN).Value = RAAN  # degrees

            keplarian.LocationType = STKObjects.eLocationTrueAnomaly
            trueAnomaly = 360 / numSatsPerPlane * satNum
            keplarian.Location.QueryInterface(STKObjects.IAgClassicalLocationTrueAnomaly).Value = trueAnomaly

            # Propagate
            satellite2.Propagator.QueryInterface(STKObjects.IAgVePropagatorTwoBody).InitialState.Representation.Assign(
                keplarian)
            satellite2.Propagator.QueryInterface(STKObjects.IAgVePropagatorTwoBody).Propagate()

            # Add to constellation object
            constellation2.Objects.AddObject(satellite)


# 为每个卫星加上发射机和接收机
def Add_transmitter_receiver(sat_list):
    print("--- add transmitter and reciver for sat ---")
    for each in sat_list:
        Instance_name = each.InstanceName
        #  new transmitter and receiver
        transmitter = each.Children.New(STKObjects.eTransmitter, "Transmitter_" + Instance_name)
        reciver = each.Children.New(STKObjects.eReceiver, "Reciver_" + Instance_name)
        # sensor = each.Children.New(STKObjects.eSensor, 'Sensor_' + Instance_name)


# 设置发射机参数
def Set_Transmitter_Parameter(transmitter, frequency=12, EIRP=20, DataRate=14):
    transmitter2 = transmitter.QueryInterface(STKObjects.IAgTransmitter)  # 建立发射机的映射，以便对其进行设置
    transmitter2.SetModel('Simple Transmitter Model')
    txModel = transmitter2.Model
    txModel = txModel.QueryInterface(STKObjects.IAgTransmitterModelSimple)
    txModel.Frequency = frequency  # GHz range:10.7-12.7GHz
    txModel.EIRP = EIRP  # dBW
    txModel.DataRate = DataRate  # Mb/sec


# 设置接收机参数
def Set_Receiver_Parameter(receiver, GT=20, frequency=12):
    receiver2 = receiver.QueryInterface(STKObjects.IAgReceiver)  # 建立发射机的映射，以便对其进行设置
    receiver2.SetModel('Simple Receiver Model')
    recModel = receiver2.Model
    recModel = recModel.QueryInterface(STKObjects.IAgReceiverModelSimple)
    recModel.AutoTrackFrequency = False
    recModel.Frequency = frequency  # GHz range:10.7-12.7GHz
    recModel.GOverT = GT  # dB/K
    return receiver2


# 获得接收机示例，并设置其参数
def Get_sat_receiver(sat, GT=20, frequency=12):
    receiver = sat.Children.GetElements(STKObjects.eReceiver)[0]  # 找到该卫星的接收机
    receiver2 = Set_Receiver_Parameter(receiver=receiver, GT=GT, frequency=frequency)
    return receiver2


def get_time():
    timeNow = time.strftime("%d %b %Y %H:%M:%S", time.localtime(ts))
    timeNowLong = str(timeNow) + ".00"
    return timeNowLong



# 计算传输链路
def Compute_access(access):
    # print("---computer access---")
    access.ComputeAccess()
    accessDP = access.DataProviders.Item('Link Information')
    accessDP2 = accessDP.QueryInterface(STKObjects.IAgDataPrvTimeVar)
    Elements = ["Range"]
    results = accessDP2.ExecSingleElements(get_time(), Elements)
    # results2 = accessDP2.ExecSingleElements(scenario2.StopTime, Elements)
    # Times = results.DataSets.GetDataSetByName('Time').GetValues()  # 时间
    # EbNo = results.DataSets.GetDataSetByName('Eb/No').GetValues()  # 码元能量
    # BER = results.DataSets.GetDataSetByName('BER').GetValues()  # 误码率
    # Link_Name = results.DataSets.GetDataSetByName('Link Name').GetValues()
    # Prop_Loss = results.DataSets.GetDataSetByName('Prop Loss').GetValues()
    # Xmtr_Gain = results.DataSets.GetDataSetByName('Xmtr Gain').GetValues()
    # EIRP = results.DataSets.GetDataSetByName('EIRP').GetValues()

    Range = results.DataSets.GetDataSetByName('Range').GetValues()
    # Range2=results2.DataSets.GetDataSetByName('Range').GetValues()
    # print(results2)
    return Range


def Creating_All_Access():
    # 首先清空场景中所有的链接
    print('--- Clearing All Access ---')
    print('--- create Access ---')
    stkRoot.ExecuteCommand('RemoveAllAccess /')

    # 计算某个卫星与其通信的四颗卫星的链路质量，并生成报告
    for each_sat in sat_list:
        now_sat_name = each_sat.InstanceName
        now_plane_num = int(now_sat_name.split('-')[0][5:])
        now_sat_num = int(now_sat_name.split('-')[1])
        now_sat_transmitter = each_sat.Children.GetElements(STKObjects.eTransmitter)[0]  # 找到该卫星的发射机
        Set_Transmitter_Parameter(now_sat_transmitter, EIRP=20)
        # 发射机与接收机相连
        # 与后面的卫星的接收机相连
        B_Name = sat_dic['node_' + str(now_plane_num) + '-' + str((now_sat_num + 1) % 10)].InstanceName
        F_Name = sat_dic['node_' + str(now_plane_num) + '-' + str((now_sat_num - 1) % 10)].InstanceName
        L_Name = sat_dic['node_' + str((now_plane_num - 1) % 10) + '-' + str(now_sat_num)].InstanceName
        R_Name = sat_dic['node_' + str((now_plane_num + 1) % 10) + '-' + str(now_sat_num)].InstanceName
        access_backward = now_sat_transmitter.GetAccessToObject(
            Get_sat_receiver(sat_dic['node_' + str(now_plane_num) + '-' + str((now_sat_num + 1) % 10)]))
        # 与前面的卫星的接收机相连
        access_forward = now_sat_transmitter.GetAccessToObject(
            Get_sat_receiver(sat_dic['node_' + str(now_plane_num) + '-' + str((now_sat_num - 1) % 10)]))
        # 与左面的卫星的接收机相连
        access_left = now_sat_transmitter.GetAccessToObject(
            Get_sat_receiver(sat_dic['node_' + str((now_plane_num - 1) % 10) + '-' + str(now_sat_num)]))
        # 与右面的卫星的接收机相连
        access_right = now_sat_transmitter.GetAccessToObject(
            Get_sat_receiver(sat_dic['node_' + str((now_plane_num + 1) % 10) + '-' + str(now_sat_num)]))
        B_Range = Compute_access(access_backward)
        F_Range = Compute_access(access_forward)
        # L_Range = Compute_access(access_left)
        # R_Range = Compute_access(access_right)
        B_Dict = {'node1': now_sat_name, 'node2': B_Name, 'bw': 20, 'delay': str(int(B_Range[0] / 300))+'ms', 'jitter': '1ms',
                  'loss': 0}
        F_Dict = {'node1': now_sat_name, 'node2': F_Name, 'bw': 20,
                  'delay': str(int(F_Range[0] / 300))+'ms', 'jitter': '1ms','loss': 0}
        # L_Dict = {'node1': now_sat_name, 'node2': L_Name, 'bw': 20, 'delay': str(int(L_Range[0] / 300))+'ms', 'jitter': '1ms',
        #           'loss': 0}
        # R_Dict = {'node1': now_sat_name, 'node2': R_Name, 'bw': 20, 'delay':str(int(R_Range[0] / 300))+'ms', 'jitter': '1ms',
        #           'loss': 0}
        data_list.append(B_Dict)
        data_list.append(F_Dict)
        # data_list.append(L_Dict)
        # data_list.append(R_Dict)
        # print('{0}\r', B_Range, F_Range, L_Range, R_Range)
    # stkRoot.ExecuteCommand('RemoveAllAccess /')


def Change_Sat_color(sat_list):
    # 修改卫星及其轨道的颜色
    print('Changing Color of Satellite')
    for each_sat in sat_list:
        now_sat_name = each_sat.InstanceName
        now_plane_num = int(now_sat_name.split('_')[0][3:])
        now_sat_num = int(now_sat_name.split('_')[1])
        satellite = each_sat.QueryInterface(STKObjects.IAgSatellite)
        graphics = satellite.Graphics
        graphics.SetAttributesType(1)  # eAttributesBasic
        attributes = graphics.Attributes
        attributes_color = attributes.QueryInterface(STKObjects.IAgVeGfxAttributesBasic)
        attributes_color.Inherit = False
        # 16436871 浅蓝色
        # 2330219 墨绿色
        # 42495 橙色
        # 9234160 米黄色
        # 65535 黄色
        # 255 红色
        # 16776960 青色
        color_sheet = [16436871, 2330219, 42495, 9234160, 65535, 255, 16776960]
        if now_sat_name[2] == 'A':
            color = 255
        elif now_sat_name[2] == 'B':
            color = 42495
        elif now_sat_name[2] == 'C':
            color = 16436871
        attributes_color.Color = color
        # 找出轨道对应的属性接口
        orbit = attributes.QueryInterface(STKObjects.IAgVeGfxAttributesOrbit)
        orbit.IsOrbitVisible = False  # 将轨道设置为不可见

def mid_link():
    for each_sat in sat_list:
        now_sat_name = each_sat.InstanceName
        tmpparam={'node1': now_sat_name, 'node2': "mid1", 'bw': 20, 'delay': "20ms", 'jitter': '1ms',
                  'loss': 0}
        data_list.append(tmpparam)



# 如果不是读取当前场景，即首次创建场景
if not Read_Scenario:
    Creat_satellite(numOrbitPlanes=10, numSatsPerPlane=10, hight=550, Inclination=53)  # Starlink
    # Kuiper
    # Creat_satellite(numOrbitPlanes=34, numSatsPerPlane=34, hight=630, Inclination=51.9, name='KPA')  # Phase A
    # Creat_satellite(numOrbitPlanes=32, numSatsPerPlane=32, hight=610, Inclination=42, name='KPB')  # Phase B
    # Creat_satellite(numOrbitPlanes=28, numSatsPerPlane=28, hight=590, Inclination=33, name='KPC')  # Phase C
    sat_list = stkRoot.CurrentScenario.Children.GetElements(STKObjects.eSatellite)
    Add_transmitter_receiver(sat_list)

# 创建卫星的字典，方便根据名字对卫星进行查找
sat_list = stkRoot.CurrentScenario.Children.GetElements(STKObjects.eSatellite)
sat_dic = {}
# 这个list是传过去的json，到底应该传什么过去呢
data_list = []
print('--- Creating Satellite Dictionary ---')
for sat in sat_list:
    sat_dic[sat.InstanceName] = sat
Plane_num = []
for i in range(0, 10):
    Plane_num.append(i)
Sat_num = []
for i in range(0, 10):
    Sat_num.append(i)

for i in range(0,10):
    Creating_All_Access()
    ts+=600
    res = requests.post(r'http://192.168.232.15:8000/modify/', json=data_list)
    print("--- topo uptade ---")
    data_list.clear()
    if i==0:
        mid_link()
        res = requests.post(r'http://192.168.232.15:8000/modify/', json=data_list)
    print(i)
    time.sleep(30)
print("end")
