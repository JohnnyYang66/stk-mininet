from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.log import setLogLevel


class MyTopo(Topo):
    def build(self):
        # 添加交换机
        s1 = self.addSwitch('s1')

        # 添加主机
        h1 = self.addHost('h1', cls=CPULimitedHost, cpu=0.1)
        h2 = self.addHost('h2', cls=CPULimitedHost, cpu=0.1)

        # 创建主机与交换机之间的链接
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)


def run():
    # 创建自定义拓扑
    topo = MyTopo()

    # 创建 Mininet 网络，使用自定义拓扑
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)

    # 启动网络
    net.start()

    # 获取主机
    h1 = net.get('h1')
    h2 = net.get('h2')

    # 使用 taskset 设置 CPU 亲和性并运行 Python 脚本
    h1.cmd('taskset -c 1 python3 test.py &')
    h2.cmd('taskset -c 2 python3 test.py &')

    # 启动命令行接口
    CLI(net)

    # 停止网络
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
