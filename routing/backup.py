import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
def findpaths(G, payment, k):
    local_G = G.copy()
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    #sub_G = nx.DiGraph()
    path_set = []
    cap_set = []
    solved_size  = 0
    flagfail = False
    while(solved_size < payment_size):
        tmp = payment_size - solved_size
        if(len(path_set) > k):
            print(solved_size,payment_size)
            print("flase a")
            return None, None
        path = greedy(local_G, src, dst)
        print(path)
        #path = nx.shortest_path(local_G, src, dst, weight=weighted_capacity)
        if (path == []):
            print("flase b")
            return None, None
        path_set.append(path)
        path_cap = sys.maxsize
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, local_G[path[i]][path[i+1]]["capacity"])
            #sub_G.add_edge(path[i], path[i+1], capacity = G[path[i]][path[i+1]]["capacity"])
            #sub_G.add_edge(path[i+1], path[i], capacity = G[path[i+1]][path[i]]["capacity"])
        #print(path_cap, tmp)
        while(path_cap < tmp):
            tmp = tmp/2
        cap_set.append(tmp)
        for i in range(len(path)-1):
            local_G[path[i]][path[i+1]]["capacity"] = local_G[path[i]][path[i+1]]["capacity"]-tmp
            local_G[path[i+1]][path[i]]["capacity"] = local_G[path[i+1]][path[i]]["capacity"]+tmp
        solved_size += tmp
        

        print(solved_size)
              
    return path_set, cap_set

import collections

def greedy(G, src, dst):
    visited = set()
    queue = collections.deque([(src, [src])])
    while queue:
        (vertex, path) = queue.popleft()
        visited.add(vertex)
        k = 5 #coefficient
        next_vertex = None
        top_k_nodes = []
        for next in set(G.neighbors(vertex)) - visited:
            capacity = G[vertex][next]["capacity"]
            if(capacity > 0):
                top_k_nodes.append((next, capacity))        
        top_k_nodes.sort(key=lambda x: x[1], reverse=True)
        #print("topk", top_k_nodes)
        if(len(top_k_nodes) > k):
            top_k_nodes = top_k_nodes[:k]
        tmp = sys.maxsize
        tmp_cap = 0
        for next, cap in top_k_nodes:
            path_len = nx.shortest_path_length(G, next, dst)
            if(path_len < tmp):
                tmp = path_len
                tmp_cap = cap
                next_vertex = next
            elif(path_len == tmp):
                if(cap > tmp_cap):
                    tmp = path_len
                    tmp_cap = cap
                    next_vertex = next 

        if next_vertex is not None:
            visited.add(next_vertex)
            if next_vertex == dst:
                return path + [next_vertex]
            else:
                queue.append((next_vertex, path + [next_vertex]))
    return []


def split_routing(G, Pset, C, payment_size):
    #transaction_fees = 0
    cur = 0
    for j in range(len(Pset)-1):
        path = Pset[j]
        sent = C[j]
        if(sent + cur > payment_size):
            sent = payment_size - cur
        for i in range(len(path)-1):
            #G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            #G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            #transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i]][path[i+1]]["capacity"] -= sent 
            G[path[i+1]][path[i]]["capacity"] += sent
        cur += sent
    #judge fee && roil back
    return True

def direct_routing(G, payment):  
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    try:
        #path = nx.shortest_path(G, src, dst, weight=weighted_capacity)
        path = greedy(G, src, dst)
    except nx.NetworkXNoPath:
        False, None
    #total_probing_messages += len(path)-1
    #transaction_fees = 0

    path_cap = sys.maxsize

    for i in range(len(path)-1): 
        #path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - G[path[i]][path[i + 1]]["capacity"] * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
        path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
    if (path_cap > payment_size):
        sent = payment_size
    else:
        return False, None
    #print("============================")
    for i in range(len(path)-1):
        #G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        #G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        G[path[i]][path[i+1]]["capacity"] -= sent
        G[path[i+1]][path[i]]["capacity"] += sent
        #transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]

      #fee += G[path[i]][path[i+1]]["cost"]*sent

    # fail, roll back 
    if sent < payment[2]:
        for i in range(len(path)-1):
          #G[path[i]][path[i+1]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
          #G[path[i+1]][path[i]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i]][path[i+1]]["capacity"] += sent
            G[path[i+1]][path[i]]["capacity"] -= sent
        # remove atomicity
        # throughput += sent
        return False

    else: 
        print("direct成功")
        return True

def routing(G, cur_payments):
    throughput_pay = 0
    #transaction_fees = 0
    num_delivered = 0
    total_probing_messages = 0
    overallpayment = 0
    throughput_total = 0
    num_splited = 0
    num_direct = 0
    num_nopath = 0
    #total_max_path_length = 0
    for payment in cur_payments:
        src = payment[0]
        dst = payment[1]
        payment_size = payment[2]
        payment_copy = [src, dst, payment_size]
        overallpayment += payment_size
        #path = nx.shortest_path(G, src, dst, weight=weighted_capacity)
        if not nx.has_path(G, src, dst):
            num_nopath += 1
            continue
        path = greedy(G, src, dst)
        total_probing_messages += len(path)-1
        print("============================")
        print(payment_size)
        path_cap = sys.maxsize
        flag_split = False
        success = False
        for i in range(len(path)-1): 
            #path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
            path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
            if payment_size/path_cap > 0.8 :
                flag_split = True
                Pset, C = findpaths(G, payment_copy, 10)
                if not (Pset is None or C is None):
                    success = True
                break
        if success and flag_split:
            split_success = split_routing(G, Pset, C, payment_size)
            if split_success is True:
                print("瓦达西真的split咯") 
                num_delivered += 1
                num_splited += 1
                throughput_pay += payment_size
                throughput_total += payment_size
        elif not (flag_split):
            direct_success= direct_routing(G, payment_copy)
            if direct_success is True:
                print("瓦达西真的direct咯") 
                num_delivered += 1
                num_direct += 1
                throughput_pay += payment_size
                throughput_total += payment_size  


    print(num_delivered)
    print(num_splited)
    print(num_direct)
    print(num_nopath)
    success_ratio = float(num_delivered/len(cur_payments))
    success_volume = throughput_pay/overallpayment
    print(throughput_pay)
    print(overallpayment)
    print(throughput_total)
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume
