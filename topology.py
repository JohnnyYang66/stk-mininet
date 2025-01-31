

from mininet.topo import Topo
from mininet.util import irange
from mininet.log import error
from mininet.node import Node
from mininet.link import TCIntf
from mininet.node import CPULimitedHost
from modify_Link import get_next

from config import Config



#!  卫星node的ip分配问题, 分配node的时候会默认分配ip








class STKTopo(Topo):
    def build(self, n_obit, sat_per_obit, core_list, node_dict):
        self.node_list = [[] for i in range(n_obit) ]

        # 创建中级卫星
        mid_sat = self.addSwitch('mid1')

        # 创建node
        for n in range(n_obit):
            for m in range(sat_per_obit):
                ip_ = f'10.{n}.{m}.1' # 用于连接中继卫星
                node = self.addNode(f'node_{n}-{m}', ip = ip_)
                name = f'node_{n}-{m}'
                # node = self.addHost(f'node_{n}-{m}', cls=CPULimitedHost, ip=ip_, cores=core_list[n][m])
                node_dict[name] = dict()
                node_dict[name]["node"] = node
                node_dict[name]["core"] = core_list[n][m]


                self.node_list[n].append(node)
                self.addLink(node, mid_sat, intf=TCIntf,
                             params1={
                                'ip': f'10.{n}.{m}.1/8',
                                'bw': Config.mid_bw,
                                'delay': Config.mid_delay,
                                'jitter': Config.mid_jitter,
                                'loss': Config.mid_loss
                            },
                            params2={
                                'bw': Config.mid_bw,
                                'delay': Config.mid_delay,
                                'jitter': Config.mid_jitter,
                                'loss': Config.mid_loss
                            }
                            )

        # link
        for n in range(n_obit):
            for m in range(sat_per_obit):
                this_node = self.node_list[n][m]
                n_, m_ = get_next(n,m, n_obit, sat_per_obit)
                next_node1 = self.node_list[n][m_]
                # next_node2 = self.node_list[n_][m]
                self.addLink(this_node, 
                            next_node1, 
                            intf=TCIntf, 
                            params1={ #? ip最后一位, 1,2,3,4 分别对应 右 下 左 上
                                'ip': f'10.{n}.{m}.2/8',  # 连接右侧卫星
                                'bw': Config.bw,
                                'delay': Config.delay,
                                'jitter': Config.jitter,
                                'loss': Config.loss
                            },
                            params2={
                                'ip': f'10.{n}.{m_}.3/8',  # 连接左侧卫星
                                'bw': Config.bw,
                                'delay': Config.delay,
                                'jitter': Config.jitter,
                                'loss': Config.loss
                            }
                            )

                #* 只考虑同轨道面的通信，跨轨道面的改用中继卫星
                # self.addLink(this_node, 
                #             next_node2,
                #             intf=TCIntf, 
                #             params1={
                #                 'ip': f'10.{n}.{m}.2/8',  
                #                 'bw': config.bw,
                #                 'delay': config.delay,
                #                 'jitter': config.jitter,
                #                 'loss': config.loss
                #             },
                #             params2={
                #                 'ip': f'10.{n_}.{m}.4/8',  
                #                 'bw': config.bw,
                #                 'delay': config.delay,
                #                 'jitter': config.jitter,
                #                 'loss': config.loss
                #             })