import numpy as np
import scipy.spatial as spatial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import math
import copy
import time
import networkx as nx
from datetime import datetime

# SIMULATION PARAMETERS
NUM_NODES = 100
NUM_COMMUNITES = 1
P_INTRA_COMMUNITY = 0.75
P_INTER_COMMUNITY = 0.2
P_DTN = 0.5

NUM_PACKETS = 1

B_THRESH = 1.0 / NUM_NODES
B_INIT = 1.0 / NUM_NODES
B_RESERVED = 1.0 / NUM_NODES ** 2

T = 200

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

    def __init__(self, node_id):
        self.id = node_id
        self.switched_off = False
        self.encounters_tbl = {self.id : Encounters(self.id)}
        self.burden = [B_INIT for i in xrange(0,NUM_NODES)]
        self.nodeset = [self.id]
        self.reached = [[False for i in xrange(0,NUM_PACKETS)] for j in xrange(0,NUM_NODES)]
        self.efficient_transmissions = 0
        self.inefficient_transmissions = 0
        
    def attempt_terminate(self):
        cnt = 0
        for i in xrange(0,NUM_NODES):
            if self.burden[i] >= B_THRESH and i != self.id:
                cnt+=1
        if cnt <= NUM_NODES * 0.1:
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
    
    def update_burden(self, node):
        #print 'updating burden for node %d with node %d' % (self.id, node.id)
        # transitive termination
        for i in xrange(0,NUM_NODES):
            if node.burden[i] == 0:
                self.burden[i] = 0
                
        # at least one has the packet (packet transfer)
        if self.reached[self.id][0] or node.reached[node.id][0]:
            #print 'at least one of %d, %d has the packet' % (self.id, node.id)
            self.burden[node.id] = 0
            self.burden[self.id] = 0
        # neither has the packet
        else:
            #print 'neither has packet'
            # and they have not met before
            if self.encounters_tbl[self.id].freq_tbl[node.id] == 1:
                #print 'updating self burdens'
                self.burden[node.id] += B_RESERVED
                self.burden[self.id] -= B_RESERVED

        for k in self.nodeset:
            if k!=self.id and k!=node.id and self.burden[k]!=0:
                if self.has_met(self.id, k) and self.has_met(node.id, k):
                    n_self_k = self.encounters_tbl[self.id].freq_tbl[k]
                    n_node_k = self.encounters_tbl[node.id].freq_tbl[k]
                    self.burden[k] = ( float(n_self_k) / (n_self_k + n_node_k) ) * (self.burden[k] + node.burden[k])
                elif not self.has_met(self.id, k) and self.has_met(node.id, k):
                    self.burden[k] -= B_RESERVED
                elif self.has_met(self.id, k) and not self.has_met(node.id, k) :
                    self.burden[k] += B_RESERVED
                else:
                    self.burden[k] = 0.5 * ( self.burden[k] + node.burden[k] )
        
        
    def __str__(self):
        s = ""
        s+= 'NODE\n'
        s+= 'node_id : %d\n' % self.id
        s+= 'switched_off : ' + str(self.switched_off) + '\n'
        s+= 'burden : ' + str(self.burden) + '\n'
        s+= 'nodeset : ' + str(self.nodeset) + '\n'
        s+= 'encounters_tbl ' + str(self.encounters_tbl) + '\n'
        return s

    def __repr__(self):
        s = ""
        s+= 'NODE\n'
        s+= 'node_id : %d\n' % self.id
        s+= 'switched_off : ' + str(self.switched_off) + '\n'
        s+= 'burden : ' + str(self.burden) + '\n'
        s+= 'nodeset : ' + str(self.nodeset) + '\n'
        s+= 'encounters_tbl ' + str(self.encounters_tbl) + '\n'
        return s
    
class Connection:

    @staticmethod
    def connect(node_i, node_j):
        #print 'processing connection between', node_i.id, ' and', node_j.id
        if not (node_i.switched_off or node_j.switched_off):
            node_i_copy = copy.deepcopy(node_i)
            node_j_copy = copy.deepcopy(node_j)
    
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

            if node_i.reached[node_i.id][0] == False and node_j.reached[node_j.id][0] == True:
                node_j.efficient_transmissions += 1
                node_i.reached[node_i.id][0] = node_i.reached[node_j.id][0] = True
                node_j.reached[node_j.id][0] = node_j.reached[node_i.id][0] = True

            if node_i.reached[node_i.id][0] == True and node_j.reached[node_j.id][0] == True:
                node_i.inefficient_transmissions += 1
                
            # update burdens
            node_i.update_burden(node_j_copy)
            node_j.update_burden(node_i_copy)

            node_i.attempt_terminate()
            node_j.attempt_terminate()
            
        elif node_i.switched_off and not node_j.switched_off:
            # transitive termination
            for k in xrange(0,NUM_NODES):
                if node_i.burden[k] == 0:
                    node_j.burden[k] = 0
                    
            node_j.attempt_terminate()
                    
        elif node_j.switched_off and not node_i.switched_off:
            # transitive termination
            for k in xrange(0,NUM_NODES):
                if node_j.burden[k] == 0:
                    node_i.burden[k] = 0
                    
            node_i.attempt_terminate()
                    
        return node_i, node_j
        
class Simulation:

    def __init__(self, num_nodes, num_communities, p_intra_community, p_inter_community, p_dtn, T = 100):
        self.nodes = [Node(i) for i in xrange(0,num_nodes)]
        self.p_intra_community = p_intra_community
        self.p_inter_community = p_inter_community
        self.p_dtn = p_dtn
        self.num_nodes = num_nodes
        self.num_communities = num_communities
        self.E_base = self.build_graph()
        self.E_dtn = []
        self.T = T
        
    def simulate(self):
        self.nodes[0].reached[0][0] = True
        t = 0
        
        while t < self.T :
            num_switched_off = len([node for node in self.nodes if node.switched_off == True])
            num_seeds = len([node for node in self.nodes if node.reached[node.id][0] == True])
            if num_switched_off == NUM_NODES:
                print 'BROADCAST COMPLETE at t = %d.' % t
                break;
            self.E_dtn = self.get_dtn_edges()
            print 't =', t
            print 'num switched off :', num_switched_off
            print 'num seeds :', num_seeds
            print 'E_dtn :', self.E_dtn
            for edge in self.E_dtn:
                self.nodes[edge[0]], self.nodes[edge[1]] = Connection.connect(self.nodes[edge[0]], self.nodes[edge[1]])
            for node in self.nodes:
                print node
            time.sleep(random.randint(0,1000) / 1000000.0)
            t += 1
            print '--------------------------------------------------------------------'
        
    def build_graph(self):
        nodes_per_community = int(self.num_nodes / self.num_communities)
        E = []

        # intra community edges
        residual_nodes = self.num_nodes % self.num_communities
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
        residual_nodes = self.num_nodes % self.num_communities
        expected_edges = int(self.p_inter_community *  nodes_per_community * nodes_per_community )
        for i in xrange(0,self.num_communities):
            for j in xrange(0,i):
                for k in xrange(0,expected_edges):
                    idx1 = random.randint(0,nodes_per_community-1) + i * nodes_per_community
                    idx2 = random.randint(0,nodes_per_community-1) + j * nodes_per_community
                    E.append([idx1, idx2])
                    #print 'appending inter edge', idx1, idx2
                    
        #print 'edges (possible duplicate) :', E
        return E

    def get_dtn_edges(self):
        E_dtn_temp = []
        E_dtn = []
        for edge in self.E_base:
            p = random.uniform(0,1)
            if p < self.p_dtn:
                E_dtn_temp.append(edge)
                
        deg = [0 for i in xrange(0,self.num_nodes)]
        for edge in E_dtn_temp:
            if deg[edge[0]] == 0 and deg[edge[1]] == 0:
                E_dtn.append(edge)
                deg[edge[0]] = deg[edge[1]] = 1
        return E_dtn        
        
if __name__ == "__main__":

    simulator = Simulation(NUM_NODES, NUM_COMMUNITES, P_INTRA_COMMUNITY, P_INTER_COMMUNITY, P_DTN, T)
    simulator.simulate()
