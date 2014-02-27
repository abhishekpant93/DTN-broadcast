import networkx as nx
import matplotlib.pyplot as plt
import random
import time
import copy
import os

#Number of packets to be transmitted
P = int(raw_input("Number of packets (eg 5): "))

DEBUG = False
saveGIF = False

class node:
    def __init__(self, lbl, P):
        self.packets = [False for i in xrange(P)]
        self.received = []
        self.label = lbl
        
    def __str__(self):
        s = "Node : Label = %d | Packets = %s | Received = %s" % (self.label, self.packets, self.received)
        #s = str(self.label)
        return s

    def __repr__(self):
        s = "Node : Label = %d | Packets = %s | Received = %s" % (self.label, self.packets, self.received)
        #s = str(self.label)
        return s

def getColor(nodes, u):
    pkts = len(nodes[u].received)
    clr = 0.0
    delta = 1.0 / (P + 1)
    clr = (pkts + 1) * delta
    return clr
    
def genEdges(V,E):
    x = []
    for i in xrange(0,E):
        u = v = -1
        while u == v:
            u = random.randint(0,V-1)
            v = random.randint(0,V-1)
        x.append((u,v))
    return x

def push(G, nodes):
    nodes_old = copy.deepcopy(nodes)
    nodes_new = copy.deepcopy(nodes)

    wasteful = 0
    successful = 0
    
    print "Starting to PUSH"
    print ""
    for i in xrange(0,len(G)):
        # print "Node :", nodes_old[i].label
        p = len(nodes_old[i].received)
        if p > 0:
            #print "Node has", p, "packets :", nodes_old[i].received
            x = random.randint(0,p-1)
            pkt = nodes_old[i].received[x]
            #print "Selecting packet", pkt, "for transmission"
            nbrs = G.neighbors(i)
            
            if len(nbrs) > 0:
                #print "Neighbours :", nbrs
                n = nbrs[random.randint(0,len(nbrs)-1)]
                #print "Selecting neighbour :", n

                if nodes_new[n].packets[pkt] :
                    #print "WASTEFUL - Neighbour already had this packet"
                    wasteful += 1
                else:
                    #print "SUCCESSFUL - Neighbour did not have this packet"
                    successful += 1
                    nodes_new[n].packets[pkt] = True
                    nodes_new[n].received.append(pkt)
                    #print nodes_new[n]
                    
            else:
                # print "No neighbours!"
                pass
                
        else:
            #print "Node has no packets"
            pass
        
        #print ""
        
    cnt = 0
    for i in xrange(len(nodes)):
        if len(nodes_new[i].received) == P:
            cnt += 1
    print "Percentage of seeds (have all packets) = ", 100.0 * cnt / len(nodes)
            
    if(successful + wasteful > 0):
        success = 100.0 * successful / (successful + wasteful)
        print "Successful : ", success, "%"
        print "Wasteful : ", (100 - success), "%"
    else:
        success = -1
        print "No transmissions possible"
    
    print ""
    print "PUSH Complete"
    print "----------------------------------"
    print ""
    
    return nodes_new, success 
    
def main():
    
    #Graph
    V = int(raw_input("Number of nodes (eg 1000) : "))
    nodes = []
    edges = []
    
    #Time steps
    T = int(raw_input("Time steps (eg 100) : "))
    print "\nNumber of packets : %d\n" % (P)
    
    G = nx.Graph()
    nodes = [node(i,P) for i in xrange(V)]

    #Node 0 is source
    nodes[0].packets = [True for i in xrange(0,P)]
    nodes[0].received = [i for i in xrange(0,P)]
    
    G.add_nodes_from([i for i in xrange(0,V)])
    pos = nx.random_layout(G)
    
    t = 0
    efficiency = []
    while t < T :
        G.remove_edges_from(edges)
        
        # assume sparse graph
        E = random.randint(0,int(V*0.3))
        edges = genEdges(V,E)
        G.add_edges_from(edges)

        print "Time =", t, "\n"
        nodes, success = push(G,nodes)

        if(success!=-1):
            efficiency.append(success)
            
        clr_values = [getColor(nodes,u) for u in G.nodes()]
            
        if DEBUG:
            for i in xrange(0,len(nodes)):
                print nodes[i]
                
            # for u in G.nodes():
            #     print u, " | ", getColor(nodes, u)

        if saveGIF:
            #### Bug in this function? Sometimes drawing wrong color even when passed correctly
            nx.draw(G, pos, cmap = plt.get_cmap('YlGnBu'), node_color = clr_values)

            plt.savefig( "Snapshots/push_t%04d.png" %(t) )
            plt.clf()
        
        t = t + 1

    print "\nPUSH SIMULATION COMPLETE\n"
        
    x = [i for i in xrange(0,len(efficiency))]    
    plt.plot(x, efficiency, 'ro')
    plt.axis([0, len(efficiency), 0, 100])
    plt.savefig("efficiency_vs_time.png")
    plt.show()
    
    if saveGIF:
        print "Creating GIF ..."
        os.system("convert -delay 20 -loop 1 Snapshots/*.png DTNpush.gif")
        print "GIF created successfully"
    
main()
