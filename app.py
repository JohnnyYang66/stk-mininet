from flask import Flask, request, jsonify
from topology import STKTopo
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.cli import CLI
from threading import Thread
import subprocess
from modify_Link import modifyLink, modifyNode

app = Flask(__name__)

topo={'topo':None}

task_dict = {"default": "python3 /home/ubuntu/Downloads/graduation/stk-mininet/mininetTest/test.py"}


# 为各个node分配核
def assignCore(n, m):
    init_list = []
    for i in range(n):
        temp_list = []
        k = 0
        for j in range(m):
            temp_list.append(k % 4)
            k += 1
        init_list.append(temp_list)
    print("init_list: ", init_list)
    return init_list


def changeCore(node, pid, new_core):
    node.cmd('taskset -cp {core} {pid}'.format(new_core, pid))


# 使用方法 requests.get(r'http://ip:8000/create/轨道数/轨道卫星数')
@app.route('/create/<int:n>/<int:m>')
def creat(n,m):
    setLogLevel( 'info' )
    info( '*** Creating network\n' )
    # TODO:暂时将init_list设置为均分，后面核多的话再改
    init_list = assignCore(n, m)
    net = Mininet(topo=STKTopo(n, m, init_list))
    topo['topo'] = net

    net.start()

    t = Thread(target=CLI, args=(net, ), daemon=True)
    t.start()

    # CLI( net )
    print("here's the ")
    return 'created'


# 使用方法 requests.get(r'http://ip:8000/stop/')
@app.route('/stop/')
def stop():
    topo['topo'].stop()
    return 'stopped'


# 使用方法 requests.post(r'http://ip:8000/modify/', data = param_list)
# param_list 由若干个字典构成,每个字典包含{node1, node2, bw, delay, jitter, loss}
# node1 node2 是要调整链接的两颗卫星
@app.route('/modify/', methods=['POST'])
def modify():
    modify_list = request.get_json()
    print("modify_list: ", modify_list)
    if not isinstance(modify_list, list):
        modify_list = list(modify_list)

    for param in modify_list:
        node1 = param.get('node1')
        node2 = param.get('node2')
        modifyNode(topo['topo'], node1, node2, param)

    return 'modify finish'


@app.route('/initTask/', methods=['POST'])
def initTask():
    if topo['topo'] is None:
        return 'mininet not initialized'
    task_list = request.get_json()
    print("task_list: ", task_list)
    net = topo['topo']
    # 获取节点名称和任务名称
    for task in task_list:
        node = task[0]
        task_name = task_dict[task[1]]
        host = net.get(node)
        # 给程序多传一个参数，方便后面找到这个进程
        cmd = task_name + " {} &".format(node)
        print("cmd: ", cmd)
        host.cmd(cmd)
    return 'task initialized'


# 改变这个节点上面任务所在的核
@app.route('/modifyCore/', methods=['POST'])
def modifyCore():
    modify_list = request.get_json()
    print("modify_list: ", modify_list)
    if not isinstance(modify_list, list):
        modify_list = list(modify_list)

    net = topo['topo']

    for param in modify_list:
        pid = param['pid']
        core = param['core']
        node = net.get(param['node'])
        changeCore(node, pid, core)

    return 'modify finish'


@app.route('/getNodeInfo/')
def getNodeInfo():
    # TODO：后续加一个接口，用pqos监测
    command = 'ps -e -o pid,psr,%cpu,cmd | grep \"test.py\"'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    # 处理输出结果
    print("getNodeInfo: ", stdout)
    lines = stdout.splitlines()
    process_info = []
    for line in lines:
        if "grep" in line:
            continue
        parts = line.split()
        if len(parts) >= 4:
            pid = parts[0]
            psr = parts[1]
            cpu = parts[2]
            cmd = parts[-1]
            process_info.append((pid, psr, cpu, cmd))
    return jsonify(process_info)


if __name__ == "__main__":
    # 20240530 modifyCore这个接口还没测，回头看看
    app.run('0.0.0.0', '8000', debug=True)