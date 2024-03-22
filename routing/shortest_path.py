import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import time

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
    
def routing(G, cur_payments):  
  throughput_pay = 0
  transaction_fees = 0
  num_delivered = 0
  throughput_total = 0
  overall_pay = 0 
  for payment in cur_payments:
    src = payment[0]
    dst = payment[1]
    payment_size = payment[2]
    overall_pay += payment_size
    try:
      path = nx.shortest_path(G, src, dst)
    except nx.NetworkXNoPath:
      continue


    path_cap = sys.maxsize
    for i in range(len(path)-1): 
      path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])

    if(path_cap > payment_size):
        success, fee = direct_routing(G, path, payment)
        if success:
          print("win!!")
          transaction_fees += fee
          num_delivered += 1
          throughput_pay += payment_size
          throughput_total += payment_size + transaction_fees
      
  print(num_delivered)
  success_ratio = float(num_delivered/len(cur_payments))
  success_volume = throughput_pay/overall_pay
  print(throughput_pay)
  print(overall_pay)
  print(throughput_total)
  return num_delivered, throughput_pay, throughput_total, success_ratio, success_volume

