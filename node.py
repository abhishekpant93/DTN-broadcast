import numpy as np
import scipy.spatial as spatial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import math

class Node:

    def __init__ ( self, position ,idx, data_no ):
        self.position = position
        self.data_no = data_no
        self.data = [False for i in range(0 , data_no)]
        self.inefficient_tranmission = 0
        self.efficient_tranmission = 0
        self.complete = False
        self.idx = idx
    def __str__(self):
        return "Index: %d , Complete: %s , Data: %s" % (self.idx, self.complete , self.data)
    
    def update(self):
        nearest = getNeighbours(self)
        for n in nearest:
            if self.complete:
                n.push_data(self.data)
            else:
                data = n.pull()
                if data:
                    self.data = data
                    self.complete = True

    def handle_neighbour(self , node , mode):
        if mode == "PUSH":
            if self.complete:
                return self.push_data(node)
        elif mode == "PULL":
            return self.pull_data(node)
        
    def push_data(self, node):

        idx = node.first_incomplete_idx()
        if idx == self.data_no:
            self.inefficient_tranmission +=1
        else:
            node.receive_data(idx)
            self.efficient_tranmission += 1
        
    def pull_data(self, node ):
        if not self.complete:
            if node.complete:
                return node.push_data(self)
            else:
                self.inefficient_tranmission+=1

    def receive_data(self , idx):
        "Receive data for packet index i"
        if self.data[idx]:
            print "Problemo"
            return False
        else:
            self.data[idx] = True
            self.complete = all(self.data)
            return True

    def first_incomplete_idx(self):
        for i in range(0 , self.data_no):
            if not self.data[i]:
                return i
        return self.data_no

    def set_position(self ,position):
        self.position = position

class NodeAnalyzer :

    def __init__(self,  number , connection_dist , mode ="PUSH" , data_no = 5 , initial_data_holders=1 ):
        self.number = number
        self.connection_dist = connection_dist
        self.nodes = []
        self.data_no = data_no
        self.current_connections = []
        self.mode = mode
        for i in range(  0 , self.number):
            self.nodes.append( Node( np.random.random(2)  , i , data_no))
            
        if initial_data_holders== 0 :
            self.initial_data_holders = 1
        else:
            self.initial_data_holders = initial_data_holders
        count =0
        while count != self.initial_data_holders:
            n = self.nodes[random.randrange(0 ,number)]
            if not n.complete:
                for i in range( 0 , data_no):
                    n.receive_data(i)

                assert( n.complete)
                count = count +1
    
    def rehash( self):

        for node in self.nodes:
            while True:
                angle = random.uniform( 0 , 2*math.pi)
                length = random.paretovariate(1.5) / 50
                
                node.position[0] +=  math.cos(angle) *length
                node.position[1] += math.sin(angle) *length
                if  (  0 < node.position[0] < 1 and 0 < node.position[1] < 1):
                    break
                else:
                    node.position[0] -=  math.cos(angle) *length
                    node.position[1] -= math.sin(angle) *length
                
        self.tree = spatial.KDTree([ n.position for n in self.nodes])
        self.closest_pairs = self.tree.query_pairs(self.connection_dist)



    def update(self):
        self.rehash()
        self.current_connections = []
        if  float(len(self.completeNodes())) / len(self.nodes)  > .5:
            self.mode = "PULL"
        for i ,node in enumerate(self.nodes):
            neighbour_idxs = self.getNeighbours(i)
            if len(neighbour_idxs) != 0:
                neighbour_idx= random.choice( neighbour_idxs)
                # print "BEFORE ITERATION"
                # print "Sender: " , node
                # print "Receiver: ", na.nodes[neighbour_idx]
            #for neighbour_idx in neighbour_idxs:
            
                if node.handle_neighbour(self.nodes[neighbour_idx] , self.mode):
                    self.current_connections.append( (i , neighbour_idx))
                # print "AFTER ITERATION"
                # print "Sender: " , node
                # print "Receiver: ", na.nodes[neighbour_idx]

        print "%d more nodes got packets in this iteration" % len(self.current_connections)
        print "%d complete nodes" % len(self.completeNodes())
        print "%d incomplete nodes" % len(self.incompleteNodes())

    def getNeighbours(self , index):
        neighbours = []

        for pair in self.closest_pairs:
            if pair[0] == index:
                neighbours.append(pair[1])
            elif  pair[1] == index:
                neighbours.append(pair[0])

        return neighbours

    def completeNodes(self):
        return [ n for n in self.nodes if n.complete]

    
    def incompleteNodes(self):
        return [ n for n in self.nodes if any(n.data) and not all(n.data)]

    def emptyNodes(self):
        return [ n for n in self.nodes if not any(n.data)]

    def animate(self):
        def update_line(num, na , complete , incomplete , empty):
            na.update()
            newcomplete = na.completeNodes()
            newincomplete = na.incompleteNodes()
            newempty = na.emptyNodes()
            complete.set_data([ n.position[0] for n in newcomplete] , [ n.position[1] for n in newcomplete])
            incomplete.set_data([ n.position[0] for n in newincomplete] , [ n.position[1] for n in newincomplete])
            empty.set_data([ n.position[0] for n in newempty] , [ n.position[1] for n in newempty])
            return complete,incomplete ,empty,

        fig1 = plt.figure()
        complete, = plt.plot([], [], 'go' , label = "Complete Points")
        incomplete, = plt.plot([], [] , 'yo' , label = "Intermediate Points")
        empty, = plt.plot([], [] , 'ro' , label = "Empty Points")
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.title('Delay Tolerant Network')
        line_ani = animation.FuncAnimation(fig1, update_line, 25, fargs=(self , complete , incomplete, empty),
                                           interval=250)
        plt.legend()
        plt.show()



if __name__ == "__main__":
    node_number = 100
    na = NodeAnalyzer(node_number , .05 , "PUSH")

    iteration = 0
    efficiencies = []
    seed_eff = [0 for i in range( 0 , node_number+1)]
    seed_ineff = [0 for i in range( 0 , node_number+1)]
    while not all( [n.complete for n in na.nodes]):
        for n in na.nodes:
            n.efficient_tranmission =0
            n.inefficient_tranmission = 0
        na.update()
        efficiency =0
        inefficiency =0
        for n in na.nodes:
            efficiency +=  n.efficient_tranmission
            inefficiency += n.inefficient_tranmission
        denom = inefficiency + efficiency
        if inefficiency + efficiency == 0:
            if len(efficiencies) == 0:
                efficiencies.append(1)
            else:
                efficiencies.append( efficiencies[-1])
        else :
            efficiencies.append(efficiency / float( denom ))
        ncomp =  len( na.completeNodes())
        seed_eff[ncomp] += efficiency
        seed_ineff[ncomp] += inefficiency
        iteration += 1

    fig1 = plt.figure()
    plt.plot( range(0 , iteration) , efficiencies ,  'b-' )
    plt.title('Efficiency vs Time')
    plt.show()

    for i in range( 0 , node_number+1):
        denom = seed_eff[i] + seed_ineff[i]
        if denom ==0 :
            denom = 1
        num = seed_eff[i]
        seed_eff[i] = num / float(denom)

    fig1 = plt.figure()
    plt.plot( [ i for i in range( 0 , node_number + 1) if seed_eff[i] != 0], [ seed_eff[i] for i in range( 0 , node_number + 1) if seed_eff[i] != 0] ,  'go' )
    plt.title('Efficiency vs number of seeds')
    plt.show()


        

