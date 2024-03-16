import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
#from routing.greedy import greedy_fs
from queue import Queue
def findpaths(G, payment, k):
    local_G = G.copy()
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    sub_G = nx.DiGraph()
    path_set = []
    cap_set = []
    solved_size  = 0
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
            print("false")
            return None, None
        path_set.append(path)
        path_cap = sys.maxsize
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, local_G[path[i]][path[i+1]]["capacity"])
            sub_G.add_edge(path[i], path[i+1], capacity = G[path[i]][path[i+1]]["capacity"])
            sub_G.add_edge(path[i+1], path[i], capacity = G[path[i+1]][path[i]]["capacity"])
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
    frontier = Queue()
    frontier.put((src,[src],sys.maxsize))
    maxcap = 0
    firstpath = []
    src_pos_index_set = set(G.nodes[src]['pos_index'])
    dst_pos_index_set = set(G.nodes[dst]['pos_index'])
    if not src_pos_index_set.intersection(dst_pos_index_set):
        return []
    while not(frontier.empty()):
        (vertex, path, mincap) = frontier.get()
        if(vertex == dst):
            if(mincap > maxcap):
                maxcap = mincap
                firstpath = path
        for next in G.neighbors(vertex):
            if nx.has_path(G, next, dst):
                next_pos_index_set = set(G.nodes[next]['pos_index'])
                if next_pos_index_set.intersection(dst_pos_index_set):
                    if (dis_Manhattan(G, next, dst) < dis_Manhattan(G, vertex, dst)) and (next not in path):
                        if(G[vertex][next]['capacity'] < mincap):
                            mincap = G[vertex][next]['capacity']
                        path.append(next)
                        frontier.put((next, path, mincap))
    return firstpath
    
            

def dis_Manhattan(G,a,b):
    a_pos_index_set = set(G.nodes[a]['pos_index'])
    b_pos_index_set = set(G.nodes[b]['pos_index'])
    min_dis = sys.maxsize
    for pos_index in a_pos_index_set.intersection(b_pos_index_set):
        tmp = G.nodes[a]['pos_index'].index(pos_index) 
        (x1, y1) = G.nodes[a]['pos'][tmp]
        (x2, y2) = G.nodes[b]['pos'][tmp]
        dis = abs(x1 - x2) + abs(y1 - y2)
        if(dis < min_dis):
            min_dis = dis 
    return min_dis
def split_routing(G, Pset, C, payment_size):
    transaction_fees = 0
    cur = 0
    for j in range(len(Pset)-1):
        path = Pset[j]
        sent = C[j]
        if(sent + cur > payment_size):
            sent = payment_size - cur
        for i in range(len(path)-1):
            G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        cur += sent
    #judge fee && roil back
    return True, transaction_fees

def direct_routing(G, path, payment):  
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    #total_probing_messages += len(path)-1
    transaction_fees = 0

    path_cap = sys.maxsize

    for i in range(len(path)-1): 
      path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - G[path[i]][path[i + 1]]["capacity"] * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
    
    if (path_cap > payment_size):
        sent = payment_size
    else:
        return False, None
    #print("============================")
    for i in range(len(path)-1):
        G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]

      #fee += G[path[i]][path[i+1]]["cost"]*sent

    print("sent is", sent," payment is", payment[2])
    # fail, roll back 
    if sent < payment[2]:
        for i in range(len(path)-1):
          G[path[i]][path[i+1]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
          G[path[i+1]][path[i]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        # remove atomicity
        # throughput += sent
        return False, None

    else: 
        print("direct成功")
        return True, transaction_fees
    
def weightchoose(pathset):
    samples = np.random.normal(0, 1, 100000)

    samples_positive = samples[samples > 0]

    samples_scaled = (samples_positive / np.max(samples_positive)) * len(pathset)
    samples_transformed = np.round(samples_scaled) 

    weights_discrete = np.zeros(len(pathset))
    for value in range(len(pathset)):
        weights_discrete[value] = np.sum(samples_transformed == value)

    weights_normalized = weights_discrete / np.sum(weights_discrete)

    random.choice(pathset, weights_normalized)


def routing(G, cur_payments):
    throughput_pay = 0
    transaction_fees = 0
    num_delivered = 0
    total_probing_messages = 0
    overallpayment = 0
    throughput_total = 0
    num_splited = 0
    num_direct = 0
    #total_max_path_length = 0
    for payment in cur_payments:
        src = payment[0]
        dst = payment[1]
        payment_size = payment[2]
        payment_copy = [src, dst, payment_size]
        overallpayment += payment_size
        #path = nx.shortest_path(G, src, dst, weight=weighted_capacity)
        if not nx.has_path(G, src, dst):
            continue
        if dst in G.nodes[src]['localed_dst']:
            for item in G.nodes[src]['local_path']:
                (receiver, pathset) = item 
                if(receiver == dst):
                    weightchoose(pathset)
                    path, path_sk = pathset[0]
                print("local path")
        else:
            path = greedy(G, src, dst)
            print("greedy path")
        total_probing_messages += len(path)-1
        print("============================")
        print(payment_size)
        path_cap = sys.maxsize
        flag_split = False
        success = False
        if path != []:
            print(path)
            for i in range(len(path)-1): 
                path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"]) 
                
                if payment_size/path_cap > 0.8:
                    print("split prob")
                    flag_split = True
                    Pset, C = findpaths(G, payment_copy, 10)
                    if not (Pset is None or C is None):
                        success = True
                    break
        else:
            print("split prob")
            flag_split = True
            Pset, C = findpaths(G, payment_copy, 10)
            if not (Pset is None or C is None):
                success = True

        if success and flag_split:
            split_success, transaction_fees = split_routing(G, Pset, C, payment_size)
            if split_success is True:
                print("split!") 
                num_delivered += 1
                num_splited += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees  
        elif not (flag_split):
            direct_success, transaction_fees = direct_routing(G, path, payment_copy)
            if direct_success is True:
                print("direct!") 
                num_delivered += 1
                num_direct += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees
                #update(G, src, dst)    


    print(num_delivered)
    print(num_splited)
    print(num_direct)
    success_ratio = float(num_delivered/len(cur_payments))
    success_volume = throughput_pay/overallpayment
    print(throughput_pay)
    print(overallpayment)
    print(throughput_total)
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume