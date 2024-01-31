
import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
def findpaths(G, payment, k):
    local_G = G.copy()
    src, dst, payment_size = payment
    path_set = []
    cap_set = []
    solved_size = 0
    cur_pay = payment_size 
    cur_node = src

    while solved_size < payment_size and k > 0:
        success, bp, path = probpath(local_G, cur_node, dst, cur_pay)
        if success:
            update_graph_capacity(local_G, path, cur_pay)
            path_set.append(path)
            cap_set.append(cur_pay)
            solved_size += cur_pay
        else:
            nextlist, tmp = find_next_nodes(G, path, bp, dst)
            if tmp < cur_pay:
                return None, None

            split_pay = split_payment(nextlist, local_G, path, bp, tmp, cur_pay, dst)
            if not split_pay:
                return None, None

            path_set.extend(split_pay[0])
            cap_set.extend(split_pay[1])
            solved_size += sum(split_pay[1])
            k -= 1
            cur_node = path[bp]

        cur_pay = payment_size - solved_size

    return path_set, cap_set

def find_next_nodes(G, path, bp, dst):
    nextlist = []
    tmp = 0
    for next in set(G.neighbors(path[bp])) - {path[bp - 1]}:
        if nx.has_path(G, next, dst):
            tmp += 0.8 * G[path[bp]][next]["capacity"]
            nextlist.append(next)
    return nextlist, tmp

def split_payment(nextlist, G, path, bp, tmp, cur_pay, dst):
    split_path_set = []
    split_cap_set = []
    for next in nextlist:
        new_pay = cur_pay * G[path[bp]][next]["capacity"] / tmp
        success, new_bp, new_path = probpath(G, next, dst, new_pay)
        if success:
            split_path_set.append(new_path)
            split_cap_set.append(new_pay)
            return split_path_set, split_cap_set
    return None

def update_graph_capacity(G, path, payment):
    for i in range(len(path) - 1):
        G[path[i]][path[i+1]]["capacity"] -= payment
        G[path[i+1]][path[i]]["capacity"] += payment



def probpath(G, src, dst, payment_size):
    path =  greedy(G, src, dst)
    for i in range(len(path)-1): 
                path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
                
                if payment_size/path_cap > 0.8 :
                    p =  i 
                    return False, p, path
    return True, 0, []
    
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
        if(len(top_k_nodes) > k):
            top_k_nodes = top_k_nodes[:k]
        tmp = sys.maxsize
        (x2, y2) = G.nodes[dst]["pos"]
        for next, cap in top_k_nodes:
            (x1, y1) = G.nodes[next]["pos"]
            path_len = (x1 - x2)**2 + (y1 - y2)**2
            if(path_len < tmp):
                tmp = path_len
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
        path = greedy(G, src, dst)
        total_probing_messages += len(path)-1
        print("============================")
        print(payment_size)
        path_cap = sys.maxsize
        flag_split = False
        success = False
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
            
            if payment_size/path_cap > 0.8 :
                flag_split = True
                Pset, C = findpaths(G, payment_copy, 10)
                if not (Pset is None or C is None):
                    success = True
                break
        if success and flag_split:
            split_success, transaction_fees = split_routing(G, Pset, C, payment_size)
            if split_success is True:
                print("瓦达西真的split咯") 
                num_delivered += 1
                num_splited += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees  
        elif not (flag_split):
            direct_success, transaction_fees = direct_routing(G, payment_copy)
            if direct_success is True:
                print("瓦达西真的direct咯") 
                num_delivered += 1
                num_direct += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees    


    print(num_delivered)
    print(num_splited)
    print(num_direct)
    success_ratio = float(num_delivered/len(cur_payments))
    success_volume = throughput_pay/overallpayment
    print(throughput_pay)
    print(overallpayment)
    print(throughput_total)
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume


