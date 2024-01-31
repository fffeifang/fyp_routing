import networkx as nx
import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
def dijkstra_greedy(G, source, target, cost_function, theset):
    print(source, target)
    distance = {node: float('infinity') for node in G.nodes}
    distance[source] = 0
    visited = set()
    current_node = source
    while current_node != target:
        visited.add(current_node)
        for neighbor in G.neighbors(current_node):
            edge_weight = cost_function(G, current_node, neighbor, target)
            new_distance = distance[current_node] + edge_weight
            if new_distance < distance[neighbor]:
                distance[neighbor] = new_distance   
        next_node = None
        min_distance = float('infinity')
        for node in G.nodes:
            if node not in visited and distance[node] < min_distance:
                next_node = node
                min_distance = distance[node]

        current_node = next_node
        if current_node is None:
            return None  

    
    path = []
    while target is not None:
        path.append(target)
        min_distance = float('infinity')
        next_target = None
        for neighbor in G.neighbors(target):
            if distance[neighbor] < min_distance and neighbor not in path:
                next_target = neighbor
                min_distance = distance[neighbor]
        target = next_target if min_distance != float('infinity') else None
        print(path)
    return path[::-1]  

def custom_cost_function(G, node1, node2, target):
    a = 1
    b = 1
    #coefficient need to test
    return  - a * G[node1][node2]["capacity"] + b  * nx.shortest_path_length(G, node2, target)

def main():
    G = nx.DiGraph()
    G.add_nodes_from([
        (1, {"color": "red"}),
        (2, {"color": "green"}),
        (3, {"color": "red"}),
        (4, {"color": "green"}),
        (5, {"color": "red"}),
        (6, {"color": "green"}),
        (7, {"color": "red"}),
        (9, {"color": "green"}),
    ])
    G.add_edge(1,5,capacity = 1)
    G.add_edge(5,9,capacity = 1)
    G.add_edge(1,5,capacity = 1)
    G.add_edge(1,2,capacity = 2)
    G.add_edge(2,3,capacity = 2)
    G.add_edge(3,6,capacity = 2)
    G.add_edge(6,9,capacity = 2)
    tmp = list(G.nodes)
    path = nx.shortest_path(G,tmp[0] , tmp[1])
    print (tmp)
