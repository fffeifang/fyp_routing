import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
def weighted_capacity(u, v, attrs):
    if(1/attrs["capacity"] > 0):
        return 1/attrs["capacity"]
    else:
        return sys.maxsize

def create_weighted_capacity_visited(visited):
    def weighted_capacity_visited(u, v, attrs):
        if attrs["capacity"] > visited.get((u, v), 0):
            return 1 / (attrs["capacity"] - visited.get((u, v), 0))
        else:
            sys.maxsize
    return weighted_capacity_visited

    
def recursive_probe(G, payment, visited, depth, truepath):
    print(depth)
    print(visited)
    src, dst, payment_size = payment
    if(depth > 10 or payment_size < 1):
        print("false a")
        return False, None
    weighted_capacity_function = create_weighted_capacity_visited(visited)
    #print(visited)
    ###############################################
    #方法一：改weighted_function()
    #方法二：手工greedy
    ###############################################
    #手工greedy
    try:
        paths_gen = nx.all_shortest_paths(G, src, dst, weight=weighted_capacity_function)
        paths = list(paths_gen)
    except nx.NetworkXNoPath:
        return False, None
    if not paths:
        print("没有找到路径")
        return False, None
    option = 0
    if (len(paths) > 1):
        max_cap = G[paths[0][0]][paths[0][1]]["capacity"] - visited.get((paths[0][0], paths[0][1]), 0)
        for i in range(1, len(paths)):
            tt = G[paths[i][0]][paths[i][1]]["capacity"] - visited.get((paths[i][0], paths[i][1]), 0)
            if (tt > max_cap):
                max_cap = tt
                option = i
    path = paths[option]
    print(path)
    #path = nx.shortest_path(G, src, dst, weight=weighted_capacity_function)
    path_cap = sys.maxsize
    for i in range(len(path) - 1):
        #需检查，不确定
        print(path[i])
        tmp = payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000  +  G[path[i]][path[i + 1]]["base_fee"] #中介费
        path_cap = np.minimum(path_cap, G[path[i]][path[i + 1]]["capacity"] - tmp)
        ################################################
        ###############################################
        if((path[i],path[i+1]) in visited.keys()):               
                if(visited[(path[i],path[i+1])] +  tmp + payment_size > G[path[i]][path[i + 1]]["capacity"]):
                    print("false b")
                    return False, None
                else:
                    visited[(path[i],path[i+1])] += tmp + payment_size
        else:
            visited[(path[i],path[i+1])] = tmp + payment_size
        if path_cap < payment_size:
            visited = {}
            print("不够")
            paths = nx.all_shortest_paths(G, path[i], dst)
            paths_list = list(paths)
            if len(paths_list) < 2:
                print("false c")
                print("没多的channel")
                return False, None
            payment_halved1 = [src, dst, payment_size / 2]
            payment_halved2 = [src, dst, payment_size / 2]
            success1, truepath1 = recursive_probe(G, payment_halved1, visited, depth+1, truepath)
            success2, truepath2 = recursive_probe(G, payment_halved2, visited, depth+1, truepath)

            if not (success1 and success2):
                print("false d")
                return False, None
            truepath = {k: truepath1.get(k, 0) + truepath2.get(k, 0) + truepath.get(k, 0) for k in set(truepath1) | set(truepath2) | set(truepath)}
            break
    print("probe成功")
    truepath[tuple(path)] = payment_size
    print(path,payment_size)
    return True, truepath

def recursive_routing(G, truepath):
    transactionfee = 0
    for key in truepath:
        path = list(key)
        payment_size = truepath[key]
        for i in range(len(path) - 1):
            fee = payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000  +  G[path[i]][path[i + 1]]["base_fee"]
            G[path[i]][path[i + 1]]["capacity"] -= payment_size + fee
            G[path[i + 1]][path[i]]["capacity"] += payment_size + fee
            transactionfee += fee
        print("splited!完成啦")
    return transactionfee


def direct_routing(G, payment):  
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    try:
        path = nx.shortest_path(G, src, dst, weight=weighted_capacity)
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
    num_splited = 0
    num_direct = 0
    num_nopath = 0
    total_probing_messages = 0
    overallpayment = 0
    throughput_total = 0
    #total_max_path_length = 0
    for payment in cur_payments:
        src = payment[0]
        dst = payment[1]
        payment_size = payment[2]
        payment_copy = [src, dst, payment_size]
        overallpayment += payment_size
        path = nx.shortest_path(G, src, dst, weight=weighted_capacity)
        total_probing_messages += len(path)-1
        print("============================")
        print(payment_size)
        path_cap = sys.maxsize
        flag_split = False
        success = False
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"] - payment_size * G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 - G[path[i]][path[i + 1]]["base_fee"])
            
            if path_cap < payment_size:
                flag_split = True
                print("can't direct",path[i])
                visited = {}
                truepath = {}
                success, truepath= recursive_probe(G, payment_copy, visited, 0, truepath)
                break
        if success and flag_split:
            print("im going to split")             
            transaction_fees = recursive_routing(G, truepath)
            if transaction_fees != -1:
                print("瓦达西真的split咯") 
                num_delivered += 1
                num_splited += 1
                throughput_total += payment_size + transaction_fees
                throughput_pay += payment_size
        elif not (flag_split):
            direct_success, transaction_fees = direct_routing(G, payment_copy)
            if direct_success is True:
                print("瓦达西真的direct咯") 
                num_delivered += 1
                num_direct += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees    


    #print(num_delivered)
    success_ratio = float(num_delivered/len(cur_payments))
    success_volume = throughput_pay/overallpayment
    print(num_splited)
    print(num_direct)
    print(num_nopath)
    success_ratio = float(num_delivered/len(cur_payments))
    success_volume = throughput_pay/overallpayment
    print(throughput_pay)
    print(overallpayment)
    print(throughput_total)
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume