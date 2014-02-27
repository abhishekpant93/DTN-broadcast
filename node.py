import numpy as np
import scipy.spatial as spatial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

class Node:



    def __init__ ( self, position , data = None):
        self.position = position
        self.data = data
        if data:
            self.complete =True
        else:
            self.complete = False
            
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

    def handle_neighbour(self , node):
        return self.push_data(node)
        
    def push_data(self, node):
        return node.receive_data( self.data)

    def pull_data(self, node ):
        return node.push_data(self)

    def receive_data(self , data):
        if not self.complete :
            self.data = data
            self.complete = True
            return True
        else:
            return False

    def set_position(self ,position):
        self.position = position
        
    


class NodeAnalyzer :
    

    def __init__(self,  number , connection_dist , data = 1 , initial_data_holders=5):
        self.number = number
        self.connection_dist = connection_dist
        self.nodes = []
        self.data = data
        for i in range(  0 , self.number):
            self.nodes.append( Node( np.random.random(2)))
        if initial_data_holders== 0 :
            self.initial_data_holders = 1
        else:
            self.initial_data_holders = initial_data_holders
        count =0
        while count != self.initial_data_holders:
            n = self.nodes[random.randrange(0 ,number)]
            if not n.complete:
                n.receive_data(data)
                count = count +1
                

    def rehash( self):
        for node in self.nodes:
            node.set_position(np.random.random(2))
        
        self.tree = spatial.KDTree([ n.position for n in self.nodes])
        self.closest_pairs = self.tree.query_pairs(self.connection_dist)


    def update(self):
        self.rehash()
        self.current_connections = []
        for i ,node in enumerate(self.nodes):
            neighbour_idxs = self.getNeighbours(i)
            for neighbour_idx in neighbour_idxs:
                if node.handle_neighbour(self.nodes[neighbour_idx]):
                    self.current_connections.append( (i , neighbour_idx))
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
        return [ n for n in self.nodes if not n.complete]


            

na = NodeAnalyzer(200 , .01 )


def update_line(num, na , complete , incomplete ):
    na.update()
    newcomplete = na.completeNodes()
    newincomplete = na.incompleteNodes()
    complete.set_data([ n.position[0] for n in newcomplete] , [ n.position[1] for n in newcomplete])
    incomplete.set_data([ n.position[0] for n in newincomplete] , [ n.position[1] for n in newincomplete])
    return complete,incomplete ,

fig1 = plt.figure()
complete, = plt.plot([], [], 'go')
incomplete, = plt.plot([], [] , 'ro')
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.xlabel('x')
plt.title('test')
line_ani = animation.FuncAnimation(fig1, update_line, 25, fargs=(na , complete , incomplete),
                                   interval=1000)

plt.show()
