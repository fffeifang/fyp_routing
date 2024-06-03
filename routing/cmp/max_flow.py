import networkx as nx
import numpy as np
from datetime import datetime
from random import shuffle
from random import sample 
from itertools import islice

import collections
import csv
import cvxpy as cp 
import random
from scipy import stats
import time
import sys

def OnPath(e, p):
	for i in range(len(p)-1):
		if (e[0], e[1]) == tuple(p[i:i+2]):
			return 1
	return 0

# TODO: modify this one 
def find_paths(G, src, dst): 
	local_G = G.copy()
	sub_G = nx.DiGraph() # weighted sub-graph constructed by probed paths 

	probing_messages = 0
	max_path_length = 0
	path_set = []
	cap_set = []
	# sample path 
	path = bfs_path(local_G, src, dst)
	while path: 
		path_set.append(path)

		path_cap = sys.maxsize
		for i in range(len(path)-1): 
			probing_messages += 1
			path_cap = np.minimum(path_cap, local_G[path[i]][path[i+1]]["capacity"])
			cap_in, cap_out = G[path[i]][path[i+1]]["capacity"], G[path[i+1]][path[i]]["capacity"]
			pfee_in, pfee_out = G[path[i]][path[i+1]]["proportion_fee"], G[path[i+1]][path[i]]["proportion_fee"]
			bfee_in, bfee_out = G[path[i]][path[i+1]]["base_fee"], G[path[i+1]][path[i]]["base_fee"] 
			sub_G.add_edge(
					# from
					path[i],
					# to
					path[i+1],
					capacity = cap_in,
					base_fee = bfee_in,
					proportion_fee = pfee_in,
				)
			sub_G.add_edge(
					# from
					path[i+1],
					# to
					path[i],
					capacity = cap_out,
					base_fee = bfee_out,
					proportion_fee = pfee_out,
				)
			# sub_G.add_edge(path[i], path[i+1], capacity = G[path[i]][path[i+1]]["capacity"], cost = G[path[i]][path[i+1]]["cost"])
			# sub_G.add_edge(path[i+1], path[i], capacity = G[path[i+1]][path[i]]["capacity"], cost = G[path[i+1]][path[i]]["cost"])
		cap_set.append(path_cap)

		if len(path)-1 > max_path_length: 
			max_path_length = len(path)-1

		for i in range(len(path)-1):
			# TODO: credit information in local is possible to be outdated
			local_G[path[i]][path[i+1]]["capacity"] = local_G[path[i]][path[i+1]]["capacity"]-path_cap
			local_G[path[i+1]][path[i]]["capacity"] = local_G[path[i+1]][path[i]]["capacity"]+path_cap

		path = bfs_path(local_G, src, dst)
	return cap_set, path_set, sub_G, probing_messages, max_path_length


def create_local_graph(G):
	# set credits for links on unexplored path to be infinity 
	local_G = nx.DiGraph()
	for e in G.edges(): 
		local_G.add_edge(e[0], e[1], capacity = sys.maxsize)
		local_G.add_edge(e[1], e[0], capacity = sys.maxsize)

	return local_G

def bfs_path(G, src, dst): 
	visited = []
	queue = collections.deque([(src, [src])])
	while queue: 
		(vertex, path) = queue.popleft()
		for next in set(list(G.neighbors(vertex)))-set(visited):
			if G[vertex][next]["capacity"] > 0:
				visited.append(next)
				if next == dst: 
					return path+[next]
				else: 
					queue.append((next, path+[next]))
	return []

# TODO cost. first max throughput, then min cost 
def max_flow_solver(G, cur_payment, d, paths):
	und_G = G.to_undirected()
	forwarding_edges = []
	reverse_edges = []
	for e in und_G.edges(): 
		forwarding_edges.append((e[0], e[1], G[e[0]][e[1]]["capacity"]))
		reverse_edges.append((e[1], e[0], G[e[1]][e[0]]["capacity"]))
	
	if len(paths) < 2:
		fee = 0
		path = paths[0]
		path_cap = sys.maxsize
		for i in range(len(path)-1):
			path_cap = np.minimum(path_cap, G[path[i]][path[i+1]]["capacity"])

			throughput = d if (path_cap > d) else path_cap
			for i in range(len(path)-1):
				G[path[i]][path[i+1]]["capacity"] -= throughput
				G[path[i+1]][path[i]]["capacity"] += throughput
				fee += G[path[i]][path[i+1]]["proportion_fee"]*throughput / 1000000+ G[path[i]][path[i+1]]["base_fee"] 

			return throughput, fee

	# edge-path coefficient 
	coe1 = np.zeros((len(forwarding_edges), len(paths)))
	coe2 = np.zeros((len(reverse_edges), len(paths)))

	for index_p in range(len(paths)):
		p = paths[index_p]
		index_e1 = 0
		index_e2 = 0

		for e in forwarding_edges: 
			coe1[index_e1][index_p] = OnPath(e, p)
			index_e1 = index_e1+1

		for e in reverse_edges:
			coe2[index_e2][index_p] = OnPath(e, p)
			index_e2 = index_e2+1

	# cost coefficient related to transaction amount 
	cost_coe1 = np.zeros((len(forwarding_edges), len(paths)))
	cost_coe2 = np.zeros((len(reverse_edges), len(paths)))

	for index_p in range(len(paths)):
		p = paths[index_p]
		index_e1 = 0
		index_e2 = 0

		for e in forwarding_edges: 
			cost_coe1[index_e1][index_p] = OnPath(e, p)*G[e[0]][e[1]]["proportion_fee"] / 1000000 + G[e[0]][e[1]]["base_fee"]
			index_e1 = index_e1+1

		for e in reverse_edges:
			cost_coe2[index_e2][index_p] = OnPath(e, p)*G[e[0]][e[1]]["proportion_fee"] / 1000000 + G[e[0]][e[1]]["base_fee"] 
			index_e2 = index_e2+1

	# capacity 
	Cap1 = np.zeros(len(forwarding_edges))
	Cap2 = np.zeros(len(reverse_edges))

	index_e1 = 0
	index_e2 = 0
	for e in forwarding_edges:
		Cap1[index_e1] = G[e[0]][e[1]]["capacity"]
		index_e1 = index_e1+1
	for e in reverse_edges:
		Cap2[index_e2] = G[e[0]][e[1]]["capacity"]
		index_e2 = index_e2+1

	# Construct the problem 
	x = cp.Variable(len(paths))
	# TODO how to make credits among paths to be balanced?
	objective = cp.Maximize(sum(x))
	# We only consider scaling fees here 
	constraints = [coe1*x - coe2*x <= Cap1, coe1*x - coe2*x >= -Cap2, sum(x) == d, 0 <= x]

	prob = cp.Problem(objective, constraints)
	start = time.time()
	result = prob.solve(solver=cp.GLPK)
	end = time.time()
	
	return x.value, sum(np.matmul(cost_coe1, x.value)+np.matmul(cost_coe2, x.value)) 

def routing(G, payment):
	src = payment[0]
	dst = payment[1]
	d = payment[2]

	cap_set = []
	path_set = []
	sub_G = nx.DiGraph()
	probing_messages = 0
	max_path_length = 0
	flows_to_send = []

	cap_set, path_set, sub_G, probing_messages, max_path_length = find_paths(G, src, dst)

	# could not find path
	if not path_set:
		return 0, 0, 0, 0
	if sum(cap_set) < payment[2]: 
		return 0, 0, probing_messages, 0

	solver_res, cost_res = max_flow_solver(sub_G, payment, d, path_set)

	if len(path_set) == 1: 
		flows_to_send.append(solver_res)
	else: 
		flows_to_send = solver_res

	# check whether credits are enough when launching payments 
	if not (sum(flows_to_send) < d-1e-6):
		index_p = 0
		payhops = []
		for index_p in range(len(path_set)):
			path = path_set[index_p]
			sent = flows_to_send[index_p]
			payhop = [0] * (len(path) - 1) 
			payhop[len(path)-2] = sent + sent * G[path[len(path)-2]][path[len(path)-1]]["proportion_fee"] / 1000000 + G[path[len(path)-2]][path[len(path)-1]]["base_fee"]
			# fee += sent * G[path[len(path)-2]][path[len(path)-1]]["proportion_fee"] / 1000000 + G[path[len(path)-2]][path[len(path)-1]]["base_fee"] 
			for i in range(1, len(path)-2):
				cur = len(path)-2-i 
				payhop[cur] = payhop[cur+1] + payhop[cur+1] * G[path[cur]][path[cur+1]]["proportion_fee"] / 1000000 + G[path[cur]][path[cur+1]]["base_fee"]
				# fee += payhop[cur+1] * G[path[cur]][path[cur+1]]["proportion_fee"] / 1000000 + G[path[cur]][path[cur+1]]["base_fee"]
			payhops.append(payhop)
			for i in range(len(path)-1):
				if ( G[path[i]][path[i+1]]["capacity"] < payhop[i]-1e-6):
					print(path[i], path[i+1], G[path[i]][path[i+1]]["capacity"], flows_to_send[index_p], "fail XXXXXXXX")
					for j in range(i-1):
							G[path[j]][path[j+1]]["capacity"] += payhop[i]
							G[path[j+1]][path[j]]["capacity"] -= payhop[i]
					# roll back
					for k in range(index_p):
						payhoptmp = payhops[k]
						p = path_set[k]
						for j in range(len(p) - 1):
							G[p[j]][p[j+1]]["capacity"] += payhoptmp[j]
							G[p[j+1]][p[j]]["capacity"] -= payhoptmp[j]
					return 0, 0, probing_messages, 0
				else: 
					# update channel states
					G[path[i]][path[i+1]]["capacity"] -= payhops[index_p][i]
					G[path[i+1]][path[i]]["capacity"] += payhops[index_p][i]
		return payment[2], cost_res, probing_messages, max_path_length 
	else: 
		# fail 
		return 0, 0, probing_messages, 0


