import queue
import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
from scipy import stats
#from routing.greedy import greedy_fs
from queue import Queue
import heapq
import copy
import lightning_proc
import routing.recursive_halve as rh

def findpaths(G, payment, k = 16):
    retry = 0
    local_G = copy.deepcopy(G)
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    path_set = []
    cap_set = []
    solved_size  = 0
    q = queue.Queue()
    q.put([src, dst, payment_size, -1, payment_size])#-1 -> last, as the node before split 
    loop = 0
    while solved_size < payment_size:
        loop += 1
        if(loop > 50): # limit on loop
            return None, None
        if(not q.empty()):
            cur_payment = q.get()
        else:
            return None, None
        cur_src = cur_payment[0]
        cur_dst = cur_payment[1]
        cur_paymentsize = cur_payment[2]
        cur_last = cur_payment[3]
        real_paymentsize = cur_payment[4]
        success1, bp, cur_path, flagattack = probpath(local_G, cur_src, cur_dst, cur_paymentsize)
        while flagattack:
            if (retry > k):
               return None, None
            success1, bp, cur_path, flagattack = probpath(local_G, cur_src, cur_dst, cur_paymentsize) 
            retry += 1
        if cur_path == []:
            return None, None
        if success1 :
            if(cur_last != -1):
                cur_path = [cur_last] + cur_path
            update_graph_capacity(local_G, cur_path, cur_paymentsize) 
            path_set.append(cur_path)
            cap_set.append(real_paymentsize) 
            solved_size += cur_paymentsize
        else:
            success2, nextlist = find_next_nodes_balanced(local_G, bp, dst, cur_paymentsize)
            if success2:
                if(bp != cur_src):
                    path_set.append(cur_path)
                    cap_set.append(real_paymentsize)
                for i in range(len(nextlist)):
                    (next_node, next_payment) = nextlist[i]
                    q.put([next_node, dst, next_payment+0.5, bp, next_payment])
            else:#fail or roll back?
                return None, None
    return path_set, cap_set 


def find_next_nodes_balanced(G, bp, dst, paymentsize):
    tmp_nextlist = []
    nextlist = []
    sklist = []
    sum_cap = 0
    for next in set(G.neighbors(bp)):
        if nx.has_path(G, next, dst):
            if (dis_Manhattan(G, next, dst) < dis_Manhattan(G, bp, dst)):
                fund = G[bp][next]["capacity"]
                fund_sum = G[bp][next]["capacity"] + G[next][bp]["capacity"]
                fund_avg = fund_sum/2
                psi = (fund - fund_avg)/fund_sum
                tmp_nextlist.append((next, fund, psi))
                sklist.append(psi)
                sum_cap += G[bp][next]["capacity"]

    if(paymentsize > 0.9 * sum_cap):
        return False, []
    else:
        sklist_sorted = np.sort(sklist)
        maxsk = stats.scoreatpercentile(sklist_sorted, 100)
        minsk = stats.scoreatpercentile(sklist_sorted, 0)
        sumsk = sum(sklist)
        sum_weighted_next = sum_cap*(sumsk - len(sklist)*minsk)/(maxsk - minsk)
        for item in tmp_nextlist:
            (next, next_cap , next_psi) = item
            mapped_psi = (next_psi - minsk)/(maxsk -minsk)
            weighted_next = mapped_psi * next_cap / sum_weighted_next
            nextlist.append((next, weighted_next*paymentsize))
        for item in tmp_nextlist:
            (next, next_cap, next_psi) = item
            mapped_psi = (next_psi - minsk) / (maxsk - minsk) if maxsk != minsk else 1
            weighted_cap = next_cap/sum_cap
            weighted_next = (mapped_psi * weighted_cap )* paymentsize / len(tmp_nextlist)  # intialize with average
            adjusted_payment = min(weighted_next, 0.9 * next_cap)  
            nextlist.append((next, adjusted_payment))

        total_adjusted_payment = sum(payment for _, payment in nextlist)
        if total_adjusted_payment < paymentsize:
            scale_factor = paymentsize / total_adjusted_payment
            nextlist = [(next, min(payment * scale_factor, 0.9 * next_cap)) for next, payment in nextlist]
        
        total_adjusted_payment = sum(payment for _, payment in nextlist)
        if total_adjusted_payment < paymentsize:
            scale_factor = paymentsize / total_adjusted_payment
            nextlist = [(next, min(payment * scale_factor, 0.9 * next_cap)) for next, payment in nextlist]
        else:
            return True, nextlist
        if total_adjusted_payment < paymentsize:
            success, nextlist = find_next_nodes_proportion(G, bp, dst, paymentsize)
            return success, nextlist
        else:

            return True, nextlist

def find_next_nodes_proportion(G, bp, dst, paymentsize):
    tmp_nextlist = []
    nextlist = []
    sum_cap = 0
    for next in set(G.neighbors(bp)):
        if nx.has_path(G, next, dst):
            if (dis_Manhattan(G, next, dst) < dis_Manhattan(G, bp, dst)):
                tmp_nextlist.append((next, G[bp][next]["capacity"]))
                sum_cap += G[bp][next]["capacity"]
    if(paymentsize > 0.9 * sum_cap):
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

def probpath(G, src, dst, payment_size):
    flagattacker = False
    path_cap_max = -1
    if dst in G.nodes[src]['local_dst']:
        print(G.nodes[src]['local_dst'])
        pathset = G.nodes[src]['local_path'][dst]
        print(pathset)
        cnt_path = 0
        path = []
        while (cnt_path < 8): #cnt_path can change
            path_candidate = weightchoosenormal(pathset)
            if path_candidate != []:
                path_cap = sys.maxsize
                for i in range(len(path_candidate)-1): 
                    path_cap = np.minimum(path_cap, G[path_candidate[i]][path_candidate[i+1]]["capacity"]) 
                if payment_size/path_cap > 0.9:
                    if(path_cap > path_cap_max):
                        path = path_candidate
                        path_cap_max = path_cap
                else:
                    path = path_candidate
                    path_cap_max = path_cap
                    break
            cnt_path += 1 
    else:
        path = greedy(G, src, dst)
        retry = 0
        while(retry < 8 and path == -1): # retry attacker
            path = greedy(G, src, dst)
        if(path == -1):
            flagattacker = True
        print("greedy path")
    path_cap = sys.maxsize
    if(not flagattacker):
        for i in range(len(path)-1): 
                    path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
                    
                    if payment_size/path_cap > 0.9 :
                        p =  i 
                        return False, path[p], path[:p+1], flagattacker
    return True, 0, path, flagattacker


import collections

def greedy(G, src, dst):
    frontier = []
    heapq.heappush(frontier, (-sys.maxsize, [src], src))
    maxpathcap = 0
    firstpath = []
    visited = set()
    
    if G.nodes[src]['pos_index'] != G.nodes[dst]['pos_index']:
        return []
    malicious_node = []
    while frontier:
        #print(maxpathcap)
        mincap, path, vertex = heapq.heappop(frontier)
        malicious_node += G.nodes[vertex]["flag_attacker"]
        visited.add(vertex) 
        mincap = -mincap
        if(mincap < maxpathcap):
            continue
        if vertex == dst:
            if mincap > maxpathcap:
                maxpathcap = mincap
                firstpath = path
            continue
        for next in G.neighbors(vertex):
            if nx.has_path(G, next, dst) and G.nodes[next]['pos_index'] == G.nodes[dst]['pos_index'] and (next not in malicious_node):
                if (dis_Manhattan(G, next, dst) < dis_Manhattan(G, vertex, dst)) and (next not in path) and (next not in visited):
                    new_mincap = min(mincap, G[vertex][next]['capacity'])
                    if new_mincap > maxpathcap:
                        new_path = path + [next]
                        #print(new_mincap, new_path)
                        heapq.heappush(frontier, (-new_mincap, new_path, next))
    if(len(firstpath) > 1):
        for i in range(len(firstpath)-1): 
            if G[firstpath[i]][firstpath[i+1]]['base_fee'] > 10000 or G[firstpath[i]][firstpath[i+1]]['proportion_fee'] > 1000:
                for k in range(i + 1):
                    G.nodes[firstpath[k]]["flag_attacker"].append(firstpath[i+1]) 
                    if(k != i):
                        G.nodes[firstpath[k]]["flag_attacker"].append(firstpath[i]) # try
                return -1    
        return firstpath
    else:
        return []
    
            

def dis_Manhattan(G,a,b): 
    x1, y1 = G.nodes[a]['pos'][0], G.nodes[a]['pos'][1]
    x2, y2 = G.nodes[b]['pos'][0], G.nodes[b]['pos'][1]
    dis = abs(x1 - x2) + abs(y1 - y2)
    return dis
    
def split_routing(G, Pset, C, payment):
    transaction_fees = 0
    breakpoint_p = -1
    breakpoint_i = -1
    tosents = []
    for j in range(len(Pset)):
        path = Pset[j]
        sent = C[j]
        if len(path) > 2:
            tosent = [0] * (len(path) - 1) 
            tosent[len(path)-2] = sent + sent * G[path[len(path)-2]][path[len(path)-1]]["proportion_fee"] / 1000000 + G[path[len(path)-2]][path[len(path)-1]]["base_fee"]
            for i in range(1, len(path)-1):
                cur = len(path)-2-i 
                tosent[cur] = tosent[cur+1] + tosent[cur+1] * G[path[cur]][path[cur+1]]["proportion_fee"] / 1000000 + G[path[cur]][path[cur+1]]["base_fee"]
            transaction_fees += tosent[0] - sent
            tosents.append(tosent)
            for i in range(len(path)-1):
                if G[path[i]][path[i+1]]['base_fee'] > 10000 or G[path[i]][path[i+1]]['proportion_fee'] > 1000:
                    for k in range(i+1):
                        G.nodes[path[k]]["flag_attacker"].append(path[i+1])
                        if(k != i):
                            G.nodes[path[k]]["flag_attacker"].append(path[i]) # try
                    breakpoint_p = j
                    breakpoint_i = i
                    break
                G[path[i]][path[i+1]]["capacity"] -= tosent[i]
                G[path[i+1]][path[i]]["capacity"] += tosent[i]
                if(path[0] == payment[0]):
                    transaction_fees += tosent[0] - sent
                if(G[path[i]][path[i+1]]["capacity"] < 0):
                    breakpoint_p = j
                    breakpoint_i = i
                    break
        elif len(path) == 2:
            if G[path[0]][path[1]]['base_fee'] > 10000 or G[path[0]][path[1]]['proportion_fee'] > 1000:
                    G.nodes[path[0]]["flag_attacker"].append(path[1])
                    G.nodes[path[0]]["flag_attacker"].append(path[0]) # try
                    breakpoint_p = j - 1
                    breakpoint_i = len(Pset[j-1]) - 2
                    break
            tosent = [sent + sent * G[path[0]][path[1]]['proportion_fee'] + G[path[0]][path[1]]['base_fee']]
            tosents.append(tosent)
            if(path[0] == payment[0]):
                    transaction_fees += tosent[0] - sent
        else:
            breakpoint_p = j - 1
            breakpoint_i = len(Pset[j-1]) - 2
    if(breakpoint_p != -1):# roil back
        for j in range(breakpoint_p+1):
            path = Pset[j]
            sent = C[j]
            tosent = tosents[j]
            if j != breakpoint_p:
                rb  = len(path) - 1
            else:
                rb = breakpoint_i 
            for i in range(rb):
                print(breakpoint_i)
                print(path)
                print(i)
                G[path[i]][path[i+1]]["capacity"] += tosent[i]
                G[path[i+1]][path[i]]["capacity"] -= tosent[i]
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
    # path_cap = sys.maxsize

    #double check(?)
    for i in range(len(path)-1): 
    #   path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - G[path[i]][path[i + 1]]["capacity"] * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
        if G[path[i]][path[i+1]]['base_fee'] > 10000 or G[path[i]][path[i+1]]['proportion_fee'] > 1000:
            for k in range(i+1):
                G.nodes[path[k]]["flag_attacker"].append(path[i+1])
                if k != i:
                    G.nodes[path[k]]["flag_attacker"].append(path[i]) # try
    # if (path_cap > payment_size):
    #     sent = payment_size
    # else:
    #     return False, None
    #print("============================")
    tosent = [0] * (len(path) - 1) 
    tosent[len(path)-2] = payment_size + payment_size * G[path[len(path)-2]][path[len(path)-1]]["proportion_fee"] / 1000000 + G[path[len(path)-2]][path[len(path)-1]]["base_fee"]
    transaction_fees = tosent[0] -  payment_size
    for i in range(1, len(path)-2):
        cur = len(path)-2-i 
        tosent[cur] = tosent[cur+1] + tosent[cur+1] * G[path[cur]][path[cur+1]]["proportion_fee"] / 1000000 + G[path[cur]][path[cur+1]]["base_fee"]
        if G[path[i]][path[i+1]]['base_fee'] > 10000 or G[path[i]][path[i+1]]['proportion_fee'] > 1000:
            for k in range(i + 1):
                G.nodes[path[k]]["flag_attacker"].append(path[i+1])
                if k != i:
                    G.nodes[path[k]]["flag_attacker"].append(path[i]) # try
            return False, None


    for i in range(len(path)-1):
        if( G[path[i]][path[i+1]]["capacity"] < tosent[i]-1e-6):
            breakpoint = i
            break
        else:
            G[path[i]][path[i+1]]["capacity"] -= tosent[i]
            G[path[i+1]][path[i]]["capacity"] += tosent[i]


    if(breakpoint != -1):# fail, roll back
        for i in range(breakpoint):
            G[path[i]][path[i+1]]["capacity"] += tosent[i]
            G[path[i+1]][path[i]]["capacity"] -= tosent[i]
        # remove atomicity
        return False, None

    else: 
        print("direct成功")
        return True, transaction_fees            

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
    # total_probing_messages = 0
    overallpayment = 0
    throughput_total = 0
    num_splited = 0
    num_direct = 0
    cnt = 0
    #total_max_path_length = 0
    for payment in cur_payments:
        cnt += 1
        if (cnt == 50):# update local path
            distribution = lightning_proc.updatelocalpath(G, 0)
            cnt = 0
        src = payment[0]
        dst = payment[1]
        payment_size = payment[2]
        payment_copy = [src, dst, payment_size]
        overallpayment += payment_size
        print("============================")
        print(src, dst, payment_size)
        #path = nx.shortest_path(G, src, dst, weight=weighted_capacity)
        if not nx.has_path(G, src, dst):
            continue
        print("============================")
        print(payment_size)
        flag_split = False
        success = False
        flag_rh = False
        if dst in G.nodes[src]['local_dst']:
            cnt_path = 0
            print("local_dst")
            print(G.nodes[src]['local_dst'])
            pathset = G.nodes[src]['local_path'][dst]
            path_cap_max = 0
            path = []
            while (cnt_path < 8): #cnt_path can change
                path_candidate = weightchoosenormal(pathset)
                if path_candidate != []:
                    print(path)
                    path_cap = sys.maxsize
                    for i in range(len(path_candidate)-1): 
                        path_cap = np.minimum(path_cap, G[path_candidate[i]][path_candidate[i+1]]["capacity"]) 
                    if payment_size/path_cap > 0.9:
                        flag_split = True
                        if(path_cap > path_cap_max):
                            path = path_candidate
                            path_cap_max = path_cap
                    else:
                        path = path_candidate
                        flag_split = False
                        break
                cnt_path += 1
            if path == []:
                flag_split = True
            if flag_split:
                Pset, C = findpaths(G, payment_copy)
                if not (Pset is None or C is None):
                    success = True
                else:
                    Pset, C = rh.findpaths(G, payment_copy)
                    if not (Pset is None or C is None):
                        flag_rh = True
                        success = True 
        if (dst not in G.nodes[src]['local_dst']) or (dst in  G.nodes[src]['local_dst'] and flag_split and not success ):
            path = greedy(G, src, dst)
            print("greedy path")
            # total_probing_messages += len(path)-1
            if path != [] and path != -1:
                print(path)
                path_cap = sys.maxsize
                for i in range(len(path)-1): 
                    path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"]) 
                    
                    if payment_size/path_cap > 0.9:
                        print("split prob")
                        flag_split = True
                        Pset, C = findpaths(G, payment_copy)
                        if not (Pset is None or C is None):
                            success = True
                        else:
                            Pset, C = rh.findpaths(G, payment_copy)
                            if not (Pset is None or C is None):
                                success = True
                                flag_rh = True
                            else:
                                print("split prob fail !!")
                        break
            else:
                print("split prob")
                flag_split = True
                Pset, C = findpaths(G, payment_copy)
                if not (Pset is None or C is None):
                    success = True
                else:
                    Pset, C = rh.findpaths(G, payment_copy)
                    if not (Pset is None or C is None):
                        success = True
                        flag_rh = True
                    else:
                        print("split prob fail !!")

        if success and flag_split:
            split_success, transaction_fee = split_routing(G, Pset, C, payment_copy)
            if split_success is True:
                print("split!") 
                num_delivered += 1
                num_splited += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fee
                transaction_fees += transaction_fee
        elif not (flag_split):
            direct_success, transaction_fee = direct_routing(G, path, payment_copy)
            if direct_success is True:
                print("direct!") 
                num_delivered += 1
                num_direct += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fee
                transaction_fees += transaction_fee
                #update(G, src, dst)    


    print(num_delivered)
    print(num_splited)
    print(num_direct)
    success_ratio = float(num_delivered/len(cur_payments))
    print(success_ratio)
    success_volume = throughput_pay/overallpayment
    print(success_volume)
    print(throughput_pay)
    print(overallpayment)
    print(transaction_fees)
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume, transaction_fees
 