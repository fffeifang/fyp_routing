import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
import copy
def findpaths(G, payment, k = 16):
    local_G = copy.deepcopy(G)
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
    if(solved_size >= payment_size):
        return path_set, cap_set
    else:
        return None, None

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
    path, min_path_cap =  greedy(G, src, dst)
    print(path, min_path_cap)
    if payment_size/min_path_cap <= 0.8 :
        return True, 0, path
    else:
        path_cap = sys.maxsize
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
            
            if payment_size/path_cap > 0.8 :
                p =  i 
                return False, p, path
        return True, 0, path
    
    
import collections

def greedy(G, src, dst, k = 16):
    paths = []
    first_path = nx.shortest_path(G, src, dst)
    paths.append(first_path)
    candidates = []

    for i in range(1, k):
        if not paths:
            break
        last_path = paths[-1]
        for j in range(len(last_path) - 1):

            cap_in, cap_out = G[last_path[j]][last_path[j+1]]["capacity"], G[last_path[j+1]][last_path[j]]["capacity"]
            pfee_in, pfee_out = G[last_path[j]][last_path[j+1]]["proportion_fee"], G[last_path[j+1]][last_path[j]]["proportion_fee"]
            bfee_in, bfee_out = G[last_path[j]][last_path[j+1]]["base_fee"], G[last_path[j+1]][last_path[j]]["base_fee"] 
            
            G.remove_edge(last_path[j],last_path[j+1])

            try:
                new_path = nx.shortest_path(G, src, dst)
                if new_path not in candidates and new_path not in paths:
                    candidates.append(new_path)
            except nx.NetworkXNoPath:
                pass

            G.add_edge(
					# from
					last_path[j],
					# to
					last_path[j+1],
					capacity = cap_in,
					base_fee = bfee_in,
					proportion_fee = pfee_in,
				)
            
            G.add_edge(
					# from
					last_path[j+1],
					# to
					last_path[j],
					capacity = cap_out,
					base_fee = bfee_out,
					proportion_fee = pfee_out,
				)
        if not candidates:
            break
        candidates.sort(key = len)
        paths.append(candidates.pop(0))
    max_path_cap = -np.inf
    max_path = None
    for path in paths:
        path_cap = sys.maxsize
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
        if path_cap > max_path_cap:
            max_path_cap = path_cap
            max_path = path
   
    return max_path, max_path_cap


def split_routing(G, Pset, C):
    transaction_fees = 0
    for j in range(len(Pset)):
        path = Pset[j]
        sent = C[j]
        bp = -1
        for i in range(len(path)-1):
            G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            if(G[path[i]][path[i+1]]["capacity"] < 0):
                bp = i
                break
            transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        # fail, roll back 
        if(bp != -1):
            for i in range(bp+1):
                G[path[i]][path[i+1]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
                G[path[i+1]][path[i]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]   
            for k in range(j+1):
                tmp_path = Pset[k]
                tmp_sent = C[k] 
                for x in range(len(tmp_path)-1):
                    G[tmp_path[x]][tmp_path[x+1]]["capacity"] += tmp_sent + tmp_sent * G[tmp_path[x]][tmp_path[x + 1]]["proportion_fee"] / 1000000 + G[tmp_path[x]][tmp_path[x + 1]]["base_fee"]
                    G[tmp_path[x+1]][tmp_path[x]]["capacity"] -= tmp_sent + tmp_sent * G[tmp_path[x]][tmp_path[x + 1]]["proportion_fee"] / 1000000 + G[tmp_path[x]][tmp_path[x + 1]]["base_fee"]
            return False, None
    return True, transaction_fees

def direct_routing(G, path, payment):  
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    #total_probing_messages += len(path)-1
    transaction_fees = 0
    sent = payment_size
    bp = -1
    #print("============================")
    for i in range(len(path)-1):
        G[path[i]][path[i+1]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        G[path[i+1]][path[i]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
        if(G[path[i]][path[i+1]]["capacity"] < 0):
            bp = i
            break
        transaction_fees += sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]

    # fail, roll back 
    if(bp != -1):
        for i in range(bp+1):
            G[path[i]][path[i+1]]["capacity"] += sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
            G[path[i+1]][path[i]]["capacity"] -= sent + sent * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]   
        return False, None
  
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
        path, path_cap = greedy(G, src, dst)
        total_probing_messages += len(path)-1
        print("============================")
        print(payment_size)
        if payment_size/path_cap > 0.8:
            print("split prob")
            Pset, C = findpaths(G, payment_copy)
            if not (Pset is None or C is None):
                success_split, transaction_fees = split_routing(G, Pset, C)
                if success_split:
                    print("split!") 
                    num_delivered += 1
                    num_splited += 1
                    throughput_pay += payment_size
                    throughput_total += payment_size + transaction_fees 
            
        else:
            success_direct, transaction_fees = direct_routing(G, path, payment_copy)
            if success_direct:
                print("direct!") 
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
 