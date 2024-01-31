import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys


def weighted_capacity(u, v, attrs):
    if(1/attrs["capacity"] > 0):
        return 1/attrs["capacity"]


def proportion_probe(G, payment, truepath):
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    try:
        paths = nx.all_shortest_paths(G, src, dst)
    except nx.NetworkXNoPath:
        print("False a")
        False, None
    valuedistribution = []
    path_cap = []
    count = 0
    shared_path = {}
    paths_list = list(paths)
    print("channel数", len(paths_list))
    for path in paths_list:
        tmp = sys.maxsize
        for i in range(len(path) - 1):
            if((path[i],path[i+1]) in shared_path.keys()):               
                shared_path[(path[i],path[i+1])].append(count)
            else:
                shared_path[(path[i],path[i+1])] = [count]
            fee_base = G[path[i]][path[i + 1]]["base_fee"]
            tmp = np.minimum(tmp, G[path[i]][path[i + 1]]["capacity"] - fee_base)
        path_cap.append(tmp)
        print(tmp)
        count += 1
    print("sum", sum(path_cap))
    if (sum(path_cap) < payment_size):
        print("False b")
        return False, None
    for i in range(len(path_cap)):
        valuedistribution.append(path_cap[i]/sum(path_cap)*payment_size)
        path = paths_list[i]
        for j in range(len(path) - 1):
            tmp = valuedistribution[i] + valuedistribution[i] * G[path[j]][path[j + 1]]["proportion_fee"] / 1000000 + G[path[j]][path[j + 1]]["base_fee"]
            if(tmp > G[path[j]][path[j + 1]]["capacity"]):
                print("False c")
                return False, None
    for key in shared_path:
        if(len(shared_path[key]) > 1):
            sum_tmp = 0 
            m,n = key
            for i in range(len(shared_path[key])):
                tmp = shared_path[key][i]
                sum_tmp +=  valuedistribution[tmp] + valuedistribution[tmp] * G[m][n]["proportion_fee"] / 1000000 + G[m][n]["base_fee"]
            if G[m][n]["capacity"] < sum_tmp:
                print("False d")
                return False, None
    for i in range(len(list(paths))):
        truepath[tuple(paths[i])] = valuedistribution[i]
    print("probe成功")
    return True, truepath


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


def proportion_routing(G, truepath):
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

def routing(G, cur_payments):
    throughput_pay = 0
    transaction_fees = 0
    num_delivered = 0
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
                truepath = {}
                success, truepath= proportion_probe(G, payment_copy, truepath)
                break
        if success and flag_split:
            print("im going to split")             
            transaction_fees = proportion_routing(G, truepath)
            if transaction_fees != -1:
                print("瓦达西真的split咯") 
                num_delivered += 1
                throughput_total += payment_size + transaction_fees
                throughput_pay += payment_size
        elif not (flag_split):
            direct_success, transaction_fees = direct_routing(G, payment_copy)
            if direct_success is True:
                print("瓦达西真的direct咯") 
                num_delivered += 1
                throughput_pay += payment_size
                throughput_total += payment_size + transaction_fees    


    print(num_delivered)
    success_ratio = float(num_delivered/len(cur_payments))
    success_volume = throughput_pay/overallpayment
    return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume