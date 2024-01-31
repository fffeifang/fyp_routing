import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
import queue
def findpaths(G, payment, k):
    local_G = G.copy()
    payment_size = payment[2]
    path_set = []
    cap_set = []
    solved_size  = 0
    q = queue.Queue()
    q.put(payment)
    bp_backup = -1
    loop = 0
    while (not q.empty()) or solved_size < payment_size:
        loop+=1
        if(loop > 50):
            return None, None
        cur_payment = q.get()
        cur_src = cur_payment[0]
        cur_dst = cur_payment[1]
        cur_paymentsize = cur_payment[2]
        success, bp, cur_path = probpath(local_G, cur_src, cur_dst, cur_paymentsize)
        if cur_path == []:
            if bp_backup == -1:
                return None, None
            else:
                next_payment = [bp_backup, cur_dst, cur_paymentsize]
                q.put(next_payment)
                continue
        path_set.append(cur_path)
        cap_set.append(cur_paymentsize)
        update_graph_capacity(local_G, cur_path, cur_paymentsize)
        #print(cur_path)
        if not success:
            nextlist, tmp = find_next_nodes(local_G, cur_path[-1], bp, cur_dst, k)
            if(tmp < cur_paymentsize):
                return None, None
            else:
                for next in nextlist:
                    next_paymentsize = 0.8 * local_G[bp][next]["capacity"] / tmp * cur_paymentsize
                    #bp-next update
                    bp_backup = bp
                    next_payment = [next, cur_dst, next_paymentsize]
                    q.put(next_payment)
        else:
            if(bp_backup != -1):
                local_G[bp_backup][cur_src]["capacity"] -= cur_paymentsize + cur_paymentsize * local_G[bp_backup][cur_src]["proportion_fee"] / 1000000 + local_G[bp_backup][cur_src]["base_fee"]
                local_G[cur_src][bp_backup]["capacity"] += cur_paymentsize + cur_paymentsize * local_G[bp_backup][cur_src]["proportion_fee"] / 1000000 + local_G[bp_backup][cur_src]["base_fee"]
            solved_size += cur_paymentsize
    return path_set, cap_set

def update_graph_capacity(G, path, payment):
    for i in range(len(path) - 1):
        G[path[i]][path[i+1]]["capacity"] -= payment + payment * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        G[path[i+1]][path[i]]["capacity"] += payment + payment * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]

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
    path =  greedy(G, src, dst)
    path_cap = sys.maxsize
    for i in range(len(path)-1): 
                path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
                
                if payment_size/path_cap > 0.8 :
                    p =  i 
                    return False, path[p], path[:p]
    return True, 0, []
 
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
    qwq = 0
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
            
            if payment_size/path_cap > 0.8 or path == []:
                qwq+=1
                flag_split = True
                Pset, C = findpaths(G, payment_copy, 5)
                if not (Pset is None or C is None):
                    success = True
                break
        if success and flag_split:
            split_success, transaction_fees = split_routing(G, Pset, C, payment_size)
            if split_success is True:
                print("split") 
                num_delivered += 1
                num_splited += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees  
        elif not (flag_split):
            direct_success, transaction_fees = direct_routing(G, payment_copy)
            if direct_success is True:
                print("direct") 
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
    print("qwq",qwq)
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume
