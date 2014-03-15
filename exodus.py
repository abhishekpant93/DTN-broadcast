import numpy as np
import scipy.spatial as spatial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import math
import copy
from datetime import datetime

NUM_NODES = 10
NUM_PACKETS = 1

B_THRESH = 1.0 / NUM_NODES
B_INIT = 1.0 / NUM_NODES
B_RESERVED = (1.0 / NUM_NODES) ** 2

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
        print 'ENCOUNTERS TABLE'
        print 'node_id : ' + self.id
        print 'last_updated : ' + self.timestamp
        print 'freq_table : ' + self.encounters
        print ''
        
class Node:

    def __init__(self, node_id):
        self.id = node_id
        self.switched_off = False
        self.encounters_tbl = {self.id : Encounters(self.id)}
        self.burden = [B_INIT for i in xrange(0,NUM_NODES)]
        self.nodeset = []
        self.reached = [[False for i in xrange(0,NUM_PACKETS)] for j in xrange(0,NUM_NODES)]

    def attempt_terminate(self):
        for i in xrange(0,NUM_NODES):
            if burden[i] >= B_THRESH and i != self.id:
                return
        print 'node ' + self.id + ' switching off'
        self.switched_off = True

    def update_nodeset(self, node):
        self.nodeset = list(set(self.nodeset + node.nodeset))

    def add_encounter(self, node):
        self.encounters_tbl[self.id].add_encounter(node.id)
            
    # true if node_id1 has met node_id2
    def has_met(self, node_id1, node_id2):
        return node_id2 in self.encounters_tbl[node_id1].freq_tbl

    def union_encounters_tbl(node):
        for k in node.encounters_tbl:
            if k in self.encounters_tbl:
                self.encounters_tbl[k].update(node.encounters_tbl[k])
            else:
                self.encounters_tbl[k] = node.encounters_tbl[k]
    
    def update_burden(self, node):
        # transitive termination
        for i in xrange(0,NUM_NODES):
            if node.burden[i] == 0:
                self.burden[i] = 0
                
        # at least one has the packet (packet transfer)
        if self.reached[self.id][0] or node.reached[node.id][0]:
            self.burden[node.id] = 0
        # neither has the packet and have not met before
        elif node.id not in self.encounters_tbl[self.id].freq_tbl:
            self.burden[node.id] += B_RESERVED
            self.burden[self.id] -= B_RESERVED

        for k in nodeset:
            if k!=self.id and k!=node.id and self.burden[k]!=0:
                if has_met(self.id, k) and has_met(node.id, k):
                    n_self_k = self.encounters_tbl[self.id].freq_tbl[k]
                    n_node_k = self.encounters_tbl[node.id].freq_tbl[k]
                    self.burden[k] = ( float(n_self_k) / (n_self_k + n_node_k) ) * (self.burden[k] + node.burden[k])
                elif not has_met(self.id, k) and has_met(node.id, k):
                    self.burden[k] -= B_RESERVED
                elif has_met(self.id, k) and not has_met(node.id, k) :
                    self.burden[k] += B_RESERVED
                else:
                    self.burden[k] = 0.5 * ( self.burden[k] + node.burden[k] )
        
        
    def __str__(self):
        print ''
        print 'NODE'
        print 'node_id : ' + self.id
        print 'switched_off : ' + self.switched_off
        print 'burden : ' + self.burden
        print 'nodeset : ' + self.nodeset
        print 'encounters_tbl' + self.encounters_tbl

        
class Connection:

    def __init__(self, node_i, node_j):
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

            # transfer packet if possible
            if node_i.reached[node_i.id][0] ^ node_j.reached[node_j.id][0]:
                node_i.reached[node_i.id][0] = node_i.reached[node_j.id][0] = True
                node_j.reached[node_j.id][0] = node_j.reached[node_i.id][0] = True
                
            # update burdens
            node_i.update_burdens(node_j_copy)
            node_j.update_burdens(node_i_copy)

            node_i.attempt_terminate()
            node_j.attempt_terminate()
            
    

