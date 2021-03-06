import matplotlib.pyplot as plt
import random
import time
from datetime import datetime
import time
import networkx as nx
import sys
import getopt

DEBUG = False

# LISTS TO HOLD SIMULATION RESULTS
active_nodes = []
num_seeds_total = []
efficient_exodus = []
efficient_push = []
efficient_push_pull = []
inefficient_exodus = []
inefficient_push = []
inefficient_push_pull = []
    
class Encounters:
    
    def __init__(self, node_id):
        self.id = node_id
        self.last_updated = datetime.now()
        self.freq_tbl = {}

    def add_encounter(self, node_id):
        self.last_updated = datetime.now()
        if node_id in self.freq_tbl:
            self.freq_tbl[node_id] += 1
        else:
            self.freq_tbl[node_id] = 1

    def update(self, new_encounters):
        if new_encounters.last_updated > self.last_updated and self.id == new_encounters.id:
            self.freq_tbl = new_encounters.freq_tbl
            self.last_updated = new_encounters.last_updated

    def __str__(self):
        s = ""
        s+= 'ENCOUNTERS TABLE\n'
        s+= 'node_id : %d\n' % self.id
        s+= 'last_updated : ' + str(self.last_updated) + '\n'
        s+= 'freq_table : ' + str(self.freq_tbl) + '\n'
        return s

    def __repr__(self):
        s = ""
        s+= 'ENCOUNTERS TABLE\n'
        s+= 'node_id : %d\n' % self.id
        s+= 'last_updated : ' + str(self.last_updated) + '\n'
        s+= 'freq_table : ' + str(self.freq_tbl) + '\n'
        return s
        
class Node:

    def __init__(self, node_id, num_nodes, B_INIT, B_THRESH, B_RESERVED, ETA, num_pkts = 1):
        self.id = node_id
        self.switched_off = False
        self.encounters_tbl = {self.id : Encounters(self.id)}
        self.B_INIT = B_INIT
        self.B_THRESH = B_THRESH
        self.B_RESERVED = B_RESERVED
        self.ETA = ETA
        self.burden = [B_INIT for i in xrange(0,num_nodes)]
        self.nodeset = [self.id]
        self.reached = [[False for i in xrange(0,num_pkts)] for j in xrange(0,num_nodes)]
        self.efficient_transmissions = 0
        self.inefficient_transmissions = 0
        self.packets = [False for i in xrange(0,num_pkts)]
        self.num_nodes = num_nodes
        
    @staticmethod    
    def copy(node):
        n = Node(node.id, node.num_nodes, node.B_INIT, node.B_THRESH, node.B_RESERVED, node.ETA, len(node.packets))
        n.switched_off = node.switched_off
        n.encounters_tbl = node.encounters_tbl
        n.burden = node.burden
        n.nodeset = node.nodeset
        n.reached = node.reached
        n.efficient_transmissions = node.efficient_transmissions
        n.inefficient_transmissions = node.inefficient_transmissions
        n.packets = node.packets
        return n
    
    def attempt_terminate(self):
        cnt = 0
        if not self.reached[self.id][0]:
            return
        
        for i in xrange(0, self.num_nodes):
            if self.burden[i] >= self.B_THRESH and i != self.id:
                cnt+=1
        if cnt <= self.num_nodes * self.ETA:
            if DEBUG:
                print 'node', self.id, ' switching off'
            self.switched_off = True

    def update_nodeset(self, node):
        self.nodeset = list(set(self.nodeset + node.nodeset))

    def add_encounter(self, node):
        self.encounters_tbl[self.id].add_encounter(node.id)
            
    # true if node_id1 has met node_id2
    def has_met(self, node_id1, node_id2):
        return node_id2 in self.encounters_tbl[node_id1].freq_tbl

    def union_encounters_tbl(self, node):
        for k in node.encounters_tbl:
            if k in self.encounters_tbl:
                self.encounters_tbl[k].update(node.encounters_tbl[k])
            else:
                self.encounters_tbl[k] = node.encounters_tbl[k]

    @staticmethod
    def update_burden( nodei , nodej):
        # transitive termination
        for i in xrange(0,nodei.num_nodes):
            if nodej.burden[i] == 0:
                nodei.burden[i] = 0

        for i in xrange(0,nodej.num_nodes):
            if nodei.burden[i] == 0:
                nodej.burden[i] = 0

        # at least one has the packet (packet transfer)
        if nodei.reached[nodei.id][0] or nodej.reached[nodej.id][0]:
            nodei.burden[nodej.id] = 0
            nodei.burden[nodei.id] = 0
            nodej.burden[nodei.id] = 0
            nodej.burden[nodej.id] = 0
            
        for k in nodei.nodeset:
            if k!=nodei.id and k!=nodej.id and nodei.burden[k]!=0:
                temp = nodei.burden[k]
                case = -1
                if nodei.has_met(nodei.id, k) and nodei.has_met(nodej.id, k):
                    case = 1
                    n_nodei_k = nodei.encounters_tbl[nodei.id].freq_tbl[k]
                    n_nodej_k = nodei.encounters_tbl[nodej.id].freq_tbl[k]
                    nodei_old_burden = nodei.burden[k]
                    nodei.burden[k] = ( float(n_nodei_k) / (n_nodei_k + n_nodej_k) ) * (nodei.burden[k] + nodej.burden[k])
                    nodej.burden[k] = ( float(n_nodej_k) / (n_nodei_k + n_nodej_k) ) * (nodei_old_burden + nodej.burden[k])
                elif not nodei.has_met(nodei.id, k) and nodei.has_met(nodej.id, k) and nodei.encounters_tbl[nodei.id].freq_tbl[nodej.id] == 1:
                    case = 2
                    nodei.burden[k] -= nodei.B_RESERVED
                    nodej.burden[k] += nodej.B_RESERVED
                elif nodei.has_met(nodei.id, k) and not nodei.has_met(nodej.id, k) and nodei.encounters_tbl[nodei.id].freq_tbl[nodej.id] == 1:
                    case = 3
                    nodei.burden[k] += nodei.B_RESERVED
                    nodej.burden[k] -= nodej.B_RESERVED
                else:
                    case = 4
                    nodei_old_burden = nodei.burden[k]
                    nodei.burden[k] = 0.5 * ( nodei.burden[k] + nodej.burden[k] )
                    nodej.burden[k] = 0.5 * ( nodei_old_burden + nodej.burden[k] )
                    
                if DEBUG:
                    print 'burden update : node id ', nodei.id, 'for k = ', k, ' new = ', nodei.burden[k], ' old = ', temp,' case = ', case
        
    def __str__(self):
        s = ""
        s+= 'NODE\n'
        s+= 'node_id : %d\n' % self.id
        s+= 'switched_off : ' + str(self.switched_off) + '\n'
        s+= 'burden : ' + str(self.burden) + '\n'
        if DEBUG:
            s+= 'nodeset : ' + str(self.nodeset) + '\n'
            s+= 'encounters_tbl ' + str(self.encounters_tbl[self.id]) + '\n'
        return s

    def __repr__(self):
        s = ""
        s+= 'NODE\n'
        s+= 'node_id : %d\n' % self.id
        s+= 'switched_off : ' + str(self.switched_off) + '\n'
        s+= 'burden : ' + str(self.burden) + '\n'
        if DEBUG:
            s+= 'nodeset : ' + str(self.nodeset) + '\n'
            s+= 'encounters_tbl ' + str(self.encounters_tbl[self.id]) + '\n'
        return s

class Connection:
            
    @staticmethod
    def connect_exodus(node_i, node_j):
        
        inefficient = 0
        efficient = 0
        
        if not (node_i.switched_off or node_j.switched_off):
            
            node_i_copy = Node.copy(node_i)
            node_j_copy = Node.copy(node_j)
            
            # update self frequency tables
            node_i.add_encounter(node_j_copy)
            node_j.add_encounter(node_i_copy)
            
            # merge the encounters arrays
            node_i.union_encounters_tbl(node_j_copy)
            node_j.union_encounters_tbl(node_i_copy)
            
            # update the nodesets
            node_i.update_nodeset(node_j_copy)
            node_j.update_nodeset(node_i_copy)
            
            # transfer packet if possible and update efficiency stats
            if node_i.reached[node_i.id][0] == True and node_j.reached[node_j.id][0] == False:
                node_i.efficient_transmissions += 1
                node_i.reached[node_i.id][0] = node_i.reached[node_j.id][0] = True
                node_j.reached[node_j.id][0] = node_j.reached[node_i.id][0] = True
                efficient += 1
                if DEBUG:
                    print 'exodus : efficient transmission : ', node_i.id, node_j.id

            if node_i.reached[node_i.id][0] == False and node_j.reached[node_j.id][0] == True:
                node_j.efficient_transmissions += 1
                node_i.reached[node_i.id][0] = node_i.reached[node_j.id][0] = True
                node_j.reached[node_j.id][0] = node_j.reached[node_i.id][0] = True
                efficient += 1
                if DEBUG:
                    print 'exodus : efficient transmission : ', node_i.id, node_j.id

            if node_i.reached[node_i.id][0] == True and node_j.reached[node_j.id][0] == True:
                if DEBUG:
                    print 'exodus - inefficient transmission : ', node_i.id, node_j.id
                node_i.inefficient_transmissions += 1
                inefficient += 1    

            if node_i.reached[node_i.id][0] == False and node_j.reached[node_j.id][0] == False:
                if DEBUG:
                    print 'exodus - inefficient transmission : ', node_i.id, node_j.id
                node_i.inefficient_transmissions += 1
                inefficient += 1    
                
            # update burdens
            Node.update_burden(node_i , node_j)

            node_i.attempt_terminate()
            node_j.attempt_terminate()
            
        elif node_i.switched_off and not node_j.switched_off:
            # transitive termination
            for k in xrange(0,node_i.num_nodes):
                if node_i.burden[k] == 0:
                    node_j.burden[k] = 0
            node_j.inefficient_transmissions+= 1
            inefficient += 1        
            if DEBUG:
                print 'exodus - inefficient transmission  (switched off): ', node_i.id, node_j.id
            node_j.attempt_terminate()
                    
        elif node_j.switched_off and not node_i.switched_off:
            # transitive termination
            for k in xrange(0,node_j.num_nodes):
                if node_j.burden[k] == 0:
                    node_i.burden[k] = 0
            node_i.inefficient_transmissions+= 1
            inefficient += 1
            if DEBUG:
                print 'exodus - inefficient transmission (switched off): ', node_i.id, node_j.id
            node_i.attempt_terminate()

        efficient_exodus[-1] += efficient
        inefficient_exodus[-1] += inefficient
        return node_i, node_j
        
class Simulation:

    # def __init__(self, modes = [],  T = 100, num_pkts = 1, edge_file = None, plot = False, p = None, num_communities = None):
    def __init__(self, params):
        
        self.params = params
        self.p_inter_community = self.params['P_INTER_CLUSTER']
        self.p_intra_community = self.params['P_INTRA_CLUSTER']
        self.num_communities = self.params['NUM_CLUSTERS']
        self.p_dtn = self.params['P_DTN']
        self.num_nodes = self.params['NUM_NODES']
        self.E_base = self.build_graph(self.params['EDGEFILE'])
        self.draw_base_graph()
        self.E_dtn = []
        self.T = self.params['T']
        self.exodus = self.push = self.push_pull = False
        self.modes = list(set([mode.lower() for mode in self.params['MODES']]))
        self.plot = self.params['PLOT']
        
        B_RESERVED = 1.0 / self.num_nodes ** 2
        #self.burdens = [ self.num_nodes * self.params['B_INIT'] for j in xrange(self.num_nodes)]
        
        if "exodus" in self.modes:
            start = time.time()
            print 'making nodes for exodus'
            self.exodus = True
            self.nodes_exodus = [Node(i, self.num_nodes, self.params['B_INIT'], self.params['B_THRESH'],B_RESERVED, self.params['ETA']) for i in xrange(0,self.num_nodes)]
            finish = time.time()
            print 'time to make nodes :', finish - start
            
        if "push" in self.modes:
            print 'making nodes for push'
            self.push = True
            self.nodes_push = [Node(i, self.num_nodes, self.params['B_INIT'], self.params['B_THRESH'],B_RESERVED, self.params['ETA']) for i in xrange(0,self.num_nodes)]

        if "push-pull" in self.modes:
            print 'making nodes for push-pull'
            self.push_pull = True
            self.nodes_push_pull = [Node(i, self.num_nodes, self.params['B_INIT'], self.params['B_THRESH'],B_RESERVED, self.params['ETA']) for i in xrange(0,self.num_nodes)]
                    

    def simulate(self):
        print 'starting simulation ...'
        if self.exodus:
            self.nodes_exodus[0].reached[0][0] = True
        if self.push:
            self.nodes_push[0].packets[0] = True
        if self.push_pull:
            self.nodes_push_pull[0].packets[0] = True
        t = 0
        status = status_exodus = status_push = status_push_pull = "running"
        t_push = t_push_pull = t_exodus = 0
        while t < self.T and status_exodus == "running":
            self.E_dtn = self.get_dtn_edges()
            print 't :', t
            print 'len E_dtn :', len(self.E_dtn)
            if self.push and status_push == "running":
                print 'simulating push step ...'
                if self.simulate_step_push() or status_exodus == "terminated":
                    status_push = "terminated"
                print 'done'
                print '----------------------------------------------------'
                t_push += 1
            if self.push_pull and status_push_pull == "running":
                print 'simulating push-pull step ...'
                if self.simulate_step_push_pull()  or status_exodus == "terminated":
                    status_push_pull = "terminated"
                print 'done'
                print '----------------------------------------------------'
                t_push_pull += 1
            if self.exodus and status_exodus == "running":
                print 'simulating exodus step ...'        
                if self.simulate_step_exodus():
                    status_exodus = "terminated"
                print 'done'
                print '----------------------------------------------------'
                t_exodus += 1
            
            if not (status_exodus == "running" or status_push == "running" or status_push_pull == "running"):
                break
            t += 1
            print '########################################################'
            
        self.statistics(t_push, t_push_pull, t_exodus)

        if DEBUG:
            tot = 0
            for i in xrange(self.num_nodes):
                b = 0
                for node in self.nodes_exodus:
                    b += node.burden[i]
                    tot += b
            print 'total burden for i = ', i, ' is ', b  
            print 'total burden in system = ', tot, ' | should be ', self.num_nodes
            
        if self.plot:            
            fig1 = plt.figure()
            print len(active_nodes) , t_exodus

            plt.plot( range(0 , len(active_nodes)) , [float(active)/self.num_nodes for active in active_nodes]  , 'b-' , label = "switched off nodes")
            plt.plot(   range(0 , len(num_seeds_total)) , [float(seeds)/self.num_nodes for seeds in num_seeds_total],  'r-' ,  label = "num_seeds" )
            plt.title('Node Status vs Time')
            plt.legend()

            fig1 = plt.figure()
            plt.plot(   range(0 , len(efficient_exodus)) , [ efficient_exodus[i] / ( float(inefficient_exodus[i] + efficient_exodus[i]) if float(inefficient_exodus[i] + efficient_exodus[i]) else 1 )for i in xrange( len(efficient_exodus))],  'g-' ,  label = "Exodus efficiency" )
            plt.plot(   range(0 , len(efficient_push)) , [ efficient_push[i] / (float(inefficient_push[i] + efficient_push[i]) if float(inefficient_push[i] + efficient_push[i]) else 1 )for i in xrange( len(efficient_push))],  'y-' ,  label = "Push efficiency" )
            plt.legend()
            plt.title('Efficiency vs Time')
            
            fig2 = plt.figure()
            plt.plot(   range(0 , len(efficient_exodus)) ,  efficient_exodus,  'g-' ,  label = "Exodus efficient" )
            plt.plot(   range(0 , len(inefficient_exodus)) ,  inefficient_exodus,  'r-' ,  label = "Exodus inefficient" )
            plt.legend()
            plt.title('Efficient vs Time - Exodus')
            
            fig3 = plt.figure()
            plt.plot(   range(0 , len(efficient_push)) ,  efficient_push,  'g-' ,  label = "Push efficient" )
            plt.plot(   range(0 , len(inefficient_push)) ,  inefficient_push,  'r-' ,  label = "Push inefficient" )
            plt.title('Efficient vs Time - Push')
            plt.legend()
            
            plt.show()
        eff_exodus = sum([node.efficient_transmissions for node in self.nodes_exodus])
        ineff_exodus = sum([node.inefficient_transmissions for node in self.nodes_exodus])
        return { "exodus_time" : t_exodus, 'exodus-efficiency' : 100.0 * float(eff_exodus) / ((eff_exodus if eff_exodus else 1) + ineff_exodus) }
                    
                    
    def statistics(self, t_push, t_push_pull, t_exodus):
        print '\n\n##### STATISTICS #####'
        print 'num_nodes = ', self.num_nodes
        print 'T = ', self.T
        if self.push:
            print 'PUSH :'
            print 'Broadcast complete time :', t_push
            eff = sum([node.efficient_transmissions for node in self.nodes_push])
            ineff = sum([node.inefficient_transmissions for node in self.nodes_push])
            print 'Efficient Transmissions :', eff
            print 'Inefficient Transmissions :', ineff
            print 'Success Transmission % :', 100.0 * float(eff) / ( (eff if eff else 1) + ineff)
            print 'Coverage : ', 100.0 * len([node for node in self.nodes_push if node.packets[0]]) / self.num_nodes
            print '----------------------------------------'
        if self.push_pull:
            print 'PUSH-PULL :'
            print 'Broadcast complete time :', t_push_pull
            eff = sum([node.efficient_transmissions for node in self.nodes_push_pull])
            ineff = sum([node.inefficient_transmissions for node in self.nodes_push_pull])
            print 'Efficient Transmissions :', eff
            print 'Inefficient Transmissions :', ineff
            print 'Success Transmission % :', 100.0 * float(eff) / ((eff if eff else 1) + ineff)
            print 'Coverage : ', 100.0 * len([node for node in self.nodes_push_pull if node.packets[0]]) / self.num_nodes
            print '----------------------------------------'
        if self.exodus:
            print 'EXODUS :'
            print 'Broadcast complete time :', t_exodus
            eff = sum([node.efficient_transmissions for node in self.nodes_exodus])
            ineff = sum([node.inefficient_transmissions for node in self.nodes_exodus])
            print 'Efficient Transmissions :', eff
            print 'Inefficient Transmissions :', ineff
            print 'Success Transmission % :', 100.0 * float(eff) / ((eff if eff else 1) + ineff)
            print 'Coverage : ', 100.0 * len([node for node in self.nodes_exodus if node.reached[node.id][0]]) / self.num_nodes
            print '----------------------------------------'  
        print''
            
    def simulate_step_push(self):
        num_seeds = len([node for node in self.nodes_push if node.packets[0]])
        efficient = 0
        inefficient = 0
        print 'PUSH - num seeds :', num_seeds
        for edge in self.E_dtn:
            node_i = self.nodes_push[edge[0]]
            node_j = self.nodes_push[edge[1]]
            if node_i.packets[0] and node_j.packets[0]:
                node_i.inefficient_transmissions += 1
                inefficient +=1
                if DEBUG:
                    print 'push : inefficient transmission : ', node_i.id, node_j.id
            if node_i.packets[0] and not node_j.packets[0]:
                node_i.efficient_transmissions += 1
                node_j.packets[0] = True
                if DEBUG:
                    print 'push : efficient transmission : ', node_i.id, node_j.id
                efficient +=1 
            if not node_i.packets[0] and node_j.packets[0]:
                node_j.efficient_transmissions += 1
                if DEBUG:
                    print 'push : efficient transmission : ', node_i.id, node_j.id
                efficient +=1
                node_i.packets[0] = True
            self.nodes_push[edge[0]] = node_i
            self.nodes_push[edge[1]] = node_j
        efficient_push.append(efficient)
        inefficient_push.append(inefficient)    
        return False

    def simulate_step_push_pull(self):
        num_seeds = len([node for node in self.nodes_push_pull if node.packets[0]])
        efficient = 0
        inefficient = 0
        print 'PUSH-PULL - num seeds :', num_seeds
        
        if num_seeds < 0.8 * self.num_nodes:
            print 'push'
            for edge in self.E_dtn:
                node_i = self.nodes_push_pull[edge[0]]
                node_j = self.nodes_push_pull[edge[1]]
                if node_i.packets[0] and node_j.packets[0]:
                    node_i.inefficient_transmissions += 1
                    inefficient +=1
                if node_i.packets[0] and not node_j.packets[0]:
                    node_i.efficient_transmissions += 1
                    node_j.packets[0] = True
                    efficient +=1 
                if not node_i.packets[0] and node_j.packets[0]:
                    node_j.efficient_transmissions += 1
                    efficient +=1
                    node_i.packets[0] = True

                self.nodes_push_pull[edge[0]] = node_i
                self.nodes_push_pull[edge[1]] = node_j
                    
        else:
            print 'pull'
            for edge in self.E_dtn:
                node_i = self.nodes_push_pull[edge[0]]
                node_j = self.nodes_push_pull[edge[1]]
                if not node_i.packets[0] and not node_j.packets[0]:
                    node_i.inefficient_transmissions += 1
                    inefficient +=1
                if node_i.packets[0] and not node_j.packets[0]:
                    node_i.efficient_transmissions += 1
                    node_j.packets[0] = True
                    efficient +=1 
                if not node_i.packets[0] and node_j.packets[0]:
                    node_j.efficient_transmissions += 1
                    efficient +=1
                    node_i.packets[0] = True

                self.nodes_push_pull[edge[0]] = node_i
                self.nodes_push_pull[edge[1]] = node_j
                    
        efficient_push_pull.append(efficient)
        inefficient_push_pull.append(inefficient)    
        return False
            
    def simulate_step_exodus(self):
        num_switched_off = len([node for node in self.nodes_exodus if node.switched_off])
        active_nodes.append( num_switched_off)
        num_seeds = len([node for node in self.nodes_exodus if node.reached[node.id][0]])
        num_seeds_total.append(num_seeds)
        if num_switched_off == self.num_nodes:
            print 'EXODUS - BROADCAST COMPLETE'
            return True
        print 'EXODUS - num switched off :', num_switched_off
        print 'EXODUS - num seeds :', num_seeds
        efficient_exodus.append(0)
        inefficient_exodus.append(0)
        for edge in self.E_dtn:
            self.nodes_exodus[edge[0]], self.nodes_exodus[edge[1]] = Connection.connect_exodus(self.nodes_exodus[edge[0]], self.nodes_exodus[edge[1]])
        
    def build_graph(self, edge_file = None):
        E = []
        num_nodes = self.num_nodes
        if edge_file is None :    
            # intra community edges
            nodes_per_community = int(num_nodes / self.num_communities)
            residual_nodes = num_nodes % self.num_communities
            expected_edges = int(self.p_intra_community * nodes_per_community * (nodes_per_community - 1) * 0.5)
            for i in xrange(0,self.num_communities):
                n = nodes_per_community
                if i == self.num_communities - 1:
                    n += residual_nodes
                for j in xrange(0,2*expected_edges):
                    idx1 = random.randint(0,n-1) + i * nodes_per_community
                    idx2 = random.randint(0,n-1) + i * nodes_per_community
                    if idx1 < idx2:
                        E.append([idx1, idx2])
                        
            # inter community edges
            if self.num_communities > 1:
                residual_nodes = num_nodes % self.num_communities
                expected_edges = int(self.p_inter_community *  nodes_per_community * nodes_per_community )
                for i in xrange(0,self.num_communities):
                    for j in xrange(0,i):
                        for k in xrange(0,expected_edges):
                            idx1 = random.randint(0,nodes_per_community-1) + i * nodes_per_community
                            idx2 = random.randint(0,nodes_per_community-1) + j * nodes_per_community
                            E.append([idx1, idx2])
	                    
        else :
            E_tmp = [[int(x) for x in line.strip().split()] for line in open(edge_file)]
            E = [e for e in E_tmp if len(e) == 2]
                
        print 'built base graph'
        
        print 'num_nodes :', num_nodes    
        return E

    def draw_base_graph(self):
        print 'writing base graphml ...'
        G = nx.Graph()
        G.add_nodes_from(xrange(self.num_nodes))
        G.add_edges_from(self.E_base)
        nx.write_graphml(G,'exodus.graphml')
        print 'done ... (load in Gephi)'

    def get_dtn_edges(self):
        E_dtn_temp = []
        E_dtn = []
        num_edges = len(self.E_base)
        expected = int(self.p_dtn * num_edges + 1)
        for i in xrange(0,expected):
            E_dtn_temp.append(self.E_base[random.randint(0,num_edges-1)])

        deg = [0 for i in xrange(0,self.num_nodes)]
        for edge in E_dtn_temp:
            if deg[edge[0]] == 0 and deg[edge[1]] == 0:
                E_dtn.append(edge)
                deg[edge[0]] = deg[edge[1]] = 1
      
        if DEBUG:
            print E_dtn
        return E_dtn        

def reset_data():
    del active_nodes[:]
    del num_seeds_total[:]
    del efficient_exodus[:]
    del efficient_push_pull[:]
    del inefficient_exodus[:]
    del inefficient_push[:]
    del efficient_push[:]
    del inefficient_push_pull[:]

def parse_args(argv):
    try:
        opts, args = getopt.getopt(argv,"hi:b:k:e:n:t:c:p:q:r:")
    except getopt.GetoptError:
        print 'python exodus.py -h'
        sys.exit(2)

    # Defaults:
    params = {}
    params['EDGEFILE'] = None
    params['NUM_NODES'] = 1000
    params['T'] = 350
    params['B_INIT'] = None
    params['B_THRESH'] = None
    params['ETA'] = 0.1
    params['NUM_CLUSTERS'] = 2
    params['P_INTRA_CLUSTER'] = 0.15
    params['P_INTER_CLUSTER'] = 0.05
    params['P_DTN'] = 0.01
    
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage : python exodus.py [OPTIONS]\n'
            print 'Options (default in parentheses) :\n'
            print '-i <edgefile> (default : synthetic graph)'
            print '-n <NUM_NODES> (1000)'
            print '-t <T> (350)'
            print '-b <B_INIT> (1 / NUM_NODES)'
            print '-k <B_THRESH> (1 / NUM_NODES)'
            print '-e <ETA> (0.1)'
            print '-c <NUM_CLUSTERS> (2)'
            print '-p <P_INTRA_CLUSTER> (0.15)'
            print '-q <P_INTER_CLUSTER> (0.05)'
            print '-r <P_DTN> (0.01)'
            print ''
            sys.exit()
        elif opt in ("-i", "--ifile"):
            params['EDGEFILE'] = arg
        elif opt == "-b":
            params['B_INIT'] = float(arg)
        elif opt == "-k":
            params['B_THRESH'] = float(arg)
        elif opt == "-e":
            params['ETA'] = float(arg)
        elif opt == "-n":
            params['NUM_NODES'] = int(arg)
        elif opt == "-t":
            params['T'] = int(arg)
        elif opt == '-c':
            params['NUM_CLUSTERS'] = int(arg)
        elif opt == "-p":
            params['P_INTRA_CLUSTER'] = float(arg)
        elif opt == "-q":
            params['P_INTER_CLUSTER'] = float(arg)
        elif opt == "-r":
            params['P_DTN'] = float(arg)
            
    if params['EDGEFILE'] is not None:
        params['NUM_CLUSTERS'] = None
        params['P_INTRA_CLUSTER'] = None
        params['P_INTER_CLUSTER'] = None
        E_tmp = [[int(x) for x in line.strip().split()] for line in open(params['EDGEFILE'])]
        E = [e for e in E_tmp if len(e) == 2]
        nodes = []
        for e in E:
            nodes.append(e[0])
            nodes.append(e[1])
        params['NUM_NODES'] = len(set(nodes))

    if params['B_INIT'] is None:
        params['B_INIT'] = 1.0 / params['NUM_NODES']
    if params['B_THRESH'] is None:
        params['B_THRESH'] = 1.0 / params['NUM_NODES']

    params['MODES'] = ["exodus", "push"]
    params['PLOT'] = True
    return params
        
if __name__ == "__main__":
    
    params = parse_args(sys.argv[1:])
    
    print 'SIMULATION PARAMETERS :\n'
    for k,v in params.items():
        if v is not None:
            print k, " : ", v
    print '----------------------------------------------\n\n'
                          
    simulator = Simulation(params)
    simulator.simulate()
