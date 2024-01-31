import numpy as np
import networkx as nx 
import random
from random import shuffle 
from itertools import islice
import sys
import time

def routing(G, cur_payments):  
  throughput = 0
  transaction_fees = 0
  num_delivered = 0
  overall_pay = 0
  
  for payment in cur_payments:
    fee = 0 
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


    sent = payment_size if (path_cap > payment_size) else path_cap

    for i in range(len(path)-1):
      G[path[i]][path[i+1]]["capacity"] -= sent
      G[path[i+1]][path[i]]["capacity"] += sent

      #fee += G[path[i]][path[i + 1]]["proportion_fee"] / 1000000 + G[path[i]][path[i + 1]]["base_fee"]
       

    # fail, roll back 
    if sent < payment[2]:
        for i in range(len(path)-1):
          G[path[i]][path[i+1]]["capacity"] += sent
          G[path[i+1]][path[i]]["capacity"] -= sent 
        # remove atomicity
        # throughput += sent

    else: 
     
      num_delivered += 1
      throughput += sent
      transaction_fees += fee
  print(num_delivered)
  print(throughput)
  print(throughput+transaction_fees)
  print(overall_pay)
  return throughput, transaction_fees, num_delivered

