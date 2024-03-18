import queue
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
    path_set = []
    cap_set = []
    solved_size  = 0
    q = queue.Queue()
    q.put((src, dst, payment_size, -1))#-1 -> last, as the node before split 
    loop = 0
    while (not q.empty()) or solved_size < payment_size:
        loop += 1
        if(loop > 50): # limit on loop
            return None, None
        cur_payment = q.get()
        cur_src = cur_payment[0]
        cur_dst = cur_payment[1]
        cur_paymentsize = cur_payment[2]
        cur_last = cur_paymentsize[3]
        success1, bp, cur_path = probpath(local_G, cur_src, cur_dst, cur_paymentsize)
        if success1:
            if(cur_last != -1):
                cur_path = [cur_last] + cur_path
            update_graph_capacity(local_G, cur_path, cur_paymentsize) 
            solved_size += cur_paymentsize
        else:
            success2, nextlist = find_next_nodes(local_G, bp, dst, cur_paymentsize)
            if success2:
                if(bp != cur_src):
                    path_set.append(cur_path)
                    cap_set.append(cur_paymentsize)
                for i in range(len(nextlist)):
                    (next_node, next_payment) = nextlist[i]
                    q.put(next_node, dst, next_payment, bp)
            else:#fail or roll back?
                return None, None
    return path_set, cap_set 


def find_next_nodes(G, bp, dst, paymentsize):
    tmp_nextlist = []
    nextlist = []
    sum_cap = 0
    for next in set(G.neighbors(bp)):
        if nx.has_path(G, next, dst):
            if (dis_Manhattan(next, dst) < dis_Manhattan(bp, dst)):
                tmp_nextlist.append((next, G[bp][next]["capacity"]))
                sum_cap += G[bp][next]["capacity"]
    if(paymentsize > sum_cap):
        return False, []
    else:
        for item in tmp_nextlist:
            (next, next_cap) = item
            nextlist.append((next, next_cap/sum_cap*paymentsize))
    return True, nextlist
         
def update_graph_capacity(G, path, payment):
    for i in range(len(path) - 1):
        G[path[i]][path[i+1]]["capacity"] -= payment 
        G[path[i+1]][path[i]]["capacity"] += payment 

def find_next_nodes(G, last, bp, dst, k):
    tmp = 0
    nextlist_all = []
    nextlist = []
    for next in set(G.neighbors(bp)) - {last}:
        capacity = G[bp][next]["capacity"]
        if nx.has_path(G, next, dst) and capacity > 0:
            tmp += 0.8 * G[bp][next]["capacity"]
            nextlist_all.append((next, capacity))        
    nextlist_all.sort(key=lambda x: x[1], reverse=True)
    if(len(nextlist_all) > k):
        nextlist_all = nextlist_all[:k]
    for next, _ in nextlist_all:
        nextlist.append(next)
    return nextlist, tmp

def probpath(G, src, dst, payment_size):
    if dst in G.nodes[src]['localed_dst']:
        for item in G.nodes[src]['local_path']:
            (receiver, pathset) = item 
            if(receiver == dst):
                path = weightchoosenormal(pathset)
            print("local path")
    else:
        path = greedy(G, src, dst)
        print("greedy path")
    path_cap = sys.maxsize
    for i in range(len(path)-1): 
                path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
                
                if payment_size/path_cap > 0.8 :
                    p =  i 
                    return False, path[p], path[:p+1]
    return True, 0, path


import collections

def greedy(G, src, dst):
    frontier = Queue()
    frontier.put((src,[src],sys.maxsize))
    maxpathcap = 0
    firstpath = []
    src_pos_index_set = set(G.nodes[src]['pos_index'])
    dst_pos_index_set = set(G.nodes[dst]['pos_index'])
    if not src_pos_index_set.intersection(dst_pos_index_set):
        return []
    while not(frontier.empty()):
        (vertex, path, mincap) = frontier.get()
        if(vertex == dst):
            if(mincap > maxpathcap):
                maxpathcap = mincap
                firstpath = path
        for next in G.neighbors(vertex):
            if nx.has_path(G, next, dst):
                next_pos_index_set = set(G.nodes[next]['pos_index'])
                if next_pos_index_set.intersection(dst_pos_index_set):
                    if (dis_Manhattan(G, next, dst) < dis_Manhattan(G, vertex, dst)) and (next not in path) and mincap > maxpathcap:
                        if(G[vertex][next]['capacity'] < mincap):
                            mincap = G[vertex][next]['capacity']
                        path.append(next)
                        frontier.put((next, path, mincap))
    return firstpath
    
def split_routing(G, Pset, C, payment_size):
    transaction_fees = 0
    breakpoint_p = -1
    breakpoint_i = -1
    for j in range(len(Pset)-1):
        path = Pset[j]
        sent = C[j]
        for i in range(len(path)-1):
            G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            if(G[path[i]][path[i+1]]["capacity"] < 0):
                breakpoint_p = j
                breakpoint_i = i
                break
    if(breakpoint_p != -1):# roil back
        for j in range(breakpoint_p+1):
            path = Pset[j]
            sent = C[j]
            for i in range(breakpoint_i+1):
                G[path[i]][path[i+1]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
                G[path[i+1]][path[i]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        # remove atomicity
        return False, None
    else:
        print("split成功")    
        return True, transaction_fees

def direct_routing(G, path, payment):  
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    #total_probing_messages += len(path)-1
    transaction_fees = 0
    breakpoint = -1 
    path_cap = sys.maxsize

    #double check(?)
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
        if( G[path[i]][path[i+1]]["capacity"] < 0):
            breakpoint = i
        transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]

    if(breakpoint != -1):# fail, roll back
        for i in range(breakpoint+1):
            G[path[i]][path[i+1]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i+1]][path[i]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"] 
        # remove atomicity
        return False, None

    else: 
        print("direct成功")
        return True, transaction_fees            

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



def weightchoosenormal(pathset):
    samples = np.random.normal(0, 1, 100000)

    samples_positive = samples[samples > 0]

    samples_scaled = (samples_positive / np.max(samples_positive)) * len(pathset)
    samples_transformed = np.round(samples_scaled) 

    weights_discrete = np.zeros(len(pathset))
    for value in range(len(pathset)):
        weights_discrete[value] = np.sum(samples_transformed == value)

    weights_normalized = weights_discrete / np.sum(weights_discrete)

    (path, pathsk) = random.choices(pathset, weights_normalized, k=1)[0]
    
    return path


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
                    path = weightchoosenormal(pathset)
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
