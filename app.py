from flask import Flask, request, jsonify
from topology import STKTopo
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.cli import CLI
from threading import Thread
import subprocess
from modify_Link import modifyLink, modifyNode

app = Flask(__name__)

class Network:
    topo = {'topo': None}

    # 字典，名称：启动命令
    task_dict = {"default": "python3 /home/ubuntu/Downloads/graduation/stk-mininet/mininetTest/test.py"}

    # 字典，name：内容
    # 里面一层内容，node：node指针，pid：进程号，task：任务名，core：核心号
    node_dict = dict()

    numPlane = 0
    numSatellite = 0

    # 为各个node分配核
    def assignCore(self, n, m):
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


    # 生成节点名字
    def generateName(self,numOfPlane, numOfSatellite):
        return "node_{i}-{j}".format(i=numOfPlane, j=numOfSatellite)


    def changeCore(self,node, pid, new_core):
        cmd = 'taskset -cp {} {}'.format(new_core, pid)
        print("changeCore cmd: ", cmd)
        node.cmd(cmd)


    # 使用方法 requests.get(r'http://ip:8000/create/轨道数/轨道卫星数')
    @app.route('/create/<int:n>/<int:m>')
    def create(self,n,m):
        global numPlane
        global numSatellite
        numPlane = n
        numSatellite = m
        setLogLevel( 'info' )
        info( '*** Creating network\n' )
        # 暂时将init_list设置为均分，后面核多的话再改
        init_list = self.assignCore(n, m)
        net = Mininet(topo=STKTopo(n, m, init_list, self.node_dict))
        self.topo['topo'] = net

        net.start()

        t = Thread(target=CLI, args=(net, ), daemon=True)
        t.start()

        # CLI( net )
        return 'created'


    # 使用方法 requests.get(r'http://ip:8000/stop/')
    @app.route('/stop/')
    def stop(self):
        self.topo['topo'].stop()
        return 'stopped'


    # 使用方法 requests.post(r'http://ip:8000/modify/', data = param_list)
    # param_list 由若干个字典构成,每个字典包含{node1, node2, bw, delay, jitter, loss}
    # node1 node2 是要调整链接的两颗卫星
    @app.route('/modify/', methods=['POST'])
    def modify(self):
        modify_list = request.get_json()
        print("modify_list: ", modify_list)
        if not isinstance(modify_list, list):
            modify_list = list(modify_list)

        for param in modify_list:
            node1 = param.get('node1')
            node2 = param.get('node2')
            modifyNode(self.topo['topo'], node1, node2, param)

        return 'modify finish'


    # 这个先创建任务，再分配到指定的核上面去
    @app.route('/initTask/', methods=['POST'])
    def initTask(self):
        if self.topo['topo'] is None:
            return 'mininet not initialized'
        task_list = request.get_json()
        print("task_list: ", task_list)
        net = self.topo['topo']
        init_list = self.assignCore(numPlane, numSatellite)
        # 获取节点名称和任务名称
        # 发现一开始不能taskset任务，一开始先设成自由的，后面再改就行
        for task in task_list:
            node = task[0]
            task_name = self.task_dict[task[1]]
            self.node_dict[node]["task"] = task[1]
            host = net.get(node)
            # 给程序多传一个参数，方便后面找到这个进程
            cmd = task_name + " {} &".format(node)
            print("cmd: ", cmd)
            host.cmd(cmd)

        # 后面再把任务set到指定的核上面去
        # 使用这个函数更新一下pid的情况到字典
        self.getNodeInfo()
        # 然后再把任务分配到指定的核上面去
        for task in task_list:
            node = task[0]
            host = net.get(node)
            pid = self.node_dict[node]["pid"]
            nAndM = node.split('_')[1].split('-')
            core = init_list[int(nAndM[0])][int(nAndM[1])]
            self.changeCore(host, pid, core)

        return 'task initialized'


    # 改变这个节点上面任务所在的核
    @app.route('/modifyCore/', methods=['POST'])
    def modifyCore(self):
        modify_list = request.get_json()
        print("modify_list: ", modify_list)
        if not isinstance(modify_list, list):
            modify_list = list(modify_list)

        net = self.topo['topo']

        for param in modify_list:
            core = param['core']
            name = param['name']
            node = net.get(name)
            pid = self.node_dict[name]['pid']
            self.changeCore(node, pid, core)

        return 'modify finish'


    @app.route('/getNodeInfo/')
    def getNodeInfo(self):
        # 后续加一个接口，用pqos监测
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
        print("process_info: ", process_info)
        for i in process_info:
            name = i[3]
            self.node_dict[name]['pid'] = i[0]
        print("node_dict: ", self.node_dict)
        return jsonify(process_info)


# 添加路由
network = Network()
app.add_url_rule('/create/<int:n>/<int:m>', view_func=network.create)
app.add_url_rule('/stop/', view_func=network.stop)
app.add_url_rule('/modify/', view_func=network.modify)
app.add_url_rule('/initTask/', view_func=network.initTask)
app.add_url_rule('/modifyCore/', view_func=network.modifyCore)
app.add_url_rule('/getNodeInfo/', view_func=network.getNodeInfo)


if __name__ == "__main__":
    app.run('0.0.0.0', '8000', debug=True)