import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import collections
import copy

def greedy_pc(G, src, dst, k = 16):
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
    res = []
    for path in paths:
        path_cap = sys.maxsize
        for i in range(len(path)-1): 
            path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])
        res.append((path, path_cap))
    res.sort(key=lambda x: x[1], reverse=True)
    return res

def greedy_fs(G, src, dst, k = 16):# choose the avarage paymentsize to initialize
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
    res = []
    for path in paths:
        #while calculating skewness, its reasonable to have negative capacity
        path_sk1 = path_sk_before(G,path)
        path_sk2 = path_sk_after(G,path)
        path_sk = abs(path_sk2) - abs(path_sk1)
        res.append((path, path_sk))
    res.sort(key=lambda x: x[1], reverse=True)
    return res 

def path_sk_before(G, path):
    path_sk = 0
    for i in range(len(path)-1): 
        fund = G[path[i]][path[i+1]]["capacity"]
        fund_sum = G[path[i]][path[i+1]]["capacity"] + G[path[i+1]][path[i]]["capacity"]
        fund_avg = fund_sum/2
        psi = (fund - fund_avg)/fund_sum
        if(psi < 0):
            psi = - psi*psi
        else:
            psi = psi*psi
        path_sk += psi
    path_sk /= len(path)
    return path_sk

def path_sk_after(G, path):# choose the avarage paymentsize to initialize && without considering fee
    path_sk = 0
    for i in range(len(path)-1): 
        fund = G[path[i]][path[i+1]]["capacity"] -  508484000
        fund_sum = G[path[i]][path[i+1]]["capacity"] + G[path[i+1]][path[i]]["capacity"]
        fund_avg = fund_sum/2
        psi = (fund - fund_avg)/fund_sum
        if(psi < 0):
            psi = - psi*psi
        else:
            psi = psi*psi
        path_sk += psi
    path_sk /= len(path)
    return path_sk