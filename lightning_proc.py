import networkx as nx
import numpy as np
import csv
import random
from scipy import stats
from sklearn.manifold import MDS
from sklearn.manifold import TSNE
from collections import Counter
import routing.greedy as gy
# returns network topology and transactions for Lightning

def setup():
	# load nodes (very hacky way to non-parse the JSON ...)
	nodes = []
	G = nx.DiGraph()
	with open('traces/nodes.txt', 'r') as f:
	#with open('traces/ex_nodes.txt', 'r') as f:
		for line in f:
			if 'id' in line:
				nodeid = line.split()[1]
				nodes.append(nodeid)
				G.add_node(
					len(nodes),
					node_id = nodeid,
					max_split = 100,
					#default max split
					#local path of frequent nodes
					local_path = [],
					localed_dst = [],
					pos = [],
					pos_index = [],
				)

	# load channels (very hacky way to non-parse the JSON ...)
	listC = []
	sourcelist = []
	destinationlist = []
	base_feelist = []
	proportion_feelist = []
	with open('traces/channels.txt', 'r') as f:
	#with open('traces/ex_channels.txt', 'r') as f:
		for line in f: 
			if 'source' in line: 
				source = line.split()[1]
				sourcelist.append(source)
			elif 'destination' in line: 
				destination = line.split()[1]
				destinationlist.append(destination)
			elif 'fee_base_msat' in line:
				base_fee = line.split()[1]
				base_feelist.append(float(base_fee))
			elif 'fee_proportional_millionths' in line:
				proportion_fee = line.split()[1]
				proportion_feelist.append(float(proportion_fee))
			elif 'htlc_maximum_msat' in line: 
				capacity = line.split()[1]
				listC.append(float(capacity))
				G.add_edge(
					# from
					int(nodes.index(source)),
					# to
					int(nodes.index(destination)),
					# capacity according to dataset
					capacity = float(capacity),
					# transaction fees: randomly sampled
					# cost = random.random()*10
					base_fee = float(base_fee),
					proportion_fee = float(proportion_fee),
				)

	#while  there are nodes with on channel, remove them
    #nodes = [node for node in nodes if node in sourcelist or node in destinationlist]
    # 需要删除的边
	edges_to_remove = []
	for a, b in G.edges():
		if not G.has_edge(b, a):
			edges_to_remove.append((a, b))
		if (G[a][b]["capacity"] is None) or (G[a][b]["base_fee"] is None) or (G[a][b]["proportion_fee"] is None):
			edges_to_remove.append((a, b))
			edges_to_remove.append((b, a))
	G.remove_edges_from(edges_to_remove)

	# 需要删除的点
	isolated_nodes = [node for node, degree in G.degree() if degree == 0]
	G.remove_nodes_from(isolated_nodes)
	#relabel
	mapping = dict(list(zip(G.nodes(), list(range(0, len(G))))))
	G = nx.relabel_nodes(G, mapping, copy=False)
	print("number of nodes", len(G))
	print('average channel capacity', float(sum(listC))/len(listC))
	print('avaerage channel base fee', float(sum(base_feelist)/len(base_feelist)))
	print('avaerage channel proportion fee', float(sum(proportion_feelist)/len(proportion_feelist)))
	print('num of edges', len(listC))
	print('num of edges', len(base_feelist))
	print('num of edges', len(proportion_feelist))
	listC_sorted = np.sort(listC)
	base_feelist_sorted = np.sort(base_feelist)
	proportion_feelist_sorted = np.sort(proportion_feelist)
	print('medium channel capacity', stats.scoreatpercentile(listC_sorted, 50))
	print('min channel capacity', stats.scoreatpercentile(listC_sorted, 0))
	print('max channel capacity', stats.scoreatpercentile(listC_sorted, 100))
	print('medium channel capacity', stats.scoreatpercentile(listC_sorted, 50))
	print('medium channel base fee', stats.scoreatpercentile(base_feelist_sorted, 50))
	print('max channel base fee', stats.scoreatpercentile(base_feelist_sorted, 99))
	print('medium channel proportion', stats.scoreatpercentile(proportion_feelist_sorted, 50))


	return G
def initcoordinate(G):#add property of coordinate
	#api layout
	#pos = nx.kamada_kawai_layout(G)
	#pos = nx.circular_layout(G)
	#pos = nx.spectral_layout(G)
	# for node, coordinates in pos.items():
	# 	G.nodes[node]["pos"] = coordinates

	#spanning tree
	G_undirected = G.to_undirected()
	connected_components = list(nx.connected_components(G_undirected))
	print(len(connected_components))
	index = 0
	#consider hops as distance
	for component in connected_components:
		subgraph = G_undirected.subgraph(component).copy()
		st = nx.minimum_spanning_tree(subgraph)
		length_matrix = np.zeros((len(subgraph), len(subgraph)))
		for i, node_i in enumerate(subgraph.nodes()):
			for j, node_j in enumerate(subgraph.nodes()):
				if i != j:
					length = nx.shortest_path_length(st, source=node_i, target=node_j)
					length_matrix[i, j] = length
		mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, n_init=4, max_iter=100)
		tmp_pos = mds.fit_transform(length_matrix)
		pos_dict = {node: tmp_pos[i] for i, node in enumerate(subgraph.nodes())}
		for node, coordinates in pos_dict.items():
			G.nodes[node]['pos'].append(coordinates)
			G.nodes[node]['pos_index'].append(index)
		index += 1
	

	# #t-SNE
	# # tsne = TSNE(n_components=2, random_state=42)
	# # pos_array = tsne.fit_transform(length_matrix)
	# # pos_dict = {node: pos for node, pos in zip(G.nodes(), pos_array)}
	return
def initlocalpath(G, flag):#generate local path information
	
	distribution = []
	with open('traces/ripple_val.csv', 'r') as f: 
			csv_reader = csv.reader(f, delimiter=',')
			for row in csv_reader:
				# only for positive payments
				if float(row[2]) > 0:
					# map Ripple nodes to Lightning nodes
					src = int(row[0]) % 6912
					dst = int(row[1]) % 6912

					if src == dst: 
						continue
					distribution.append((src,dst))
	distribution_counter = Counter(distribution)
	
	# with open('nodes_counts.txt', 'w') as file:
	# 	for tmp in list(G.nodes()):
	# 		file.write(f'{tmp}\n')
	for pair, count in distribution_counter.items():
		if(count > 30):# frequent pairs(80% pairs)
			sender = pair[0]
			receiver = pair[1]
			
			#G.nodes[sender]['local_path'].append((receiver,gy.greedy_pc(G,sender,receiver)))
			
			if nx.has_path(G, sender, receiver):
				if(flag == 0):#greedy decided by skewness
					G.nodes[sender]['local_path'].append((receiver,gy.greedy_fs(G,sender,receiver)))
				else:#greedy decided by capacity
					G.nodes[sender]['local_path'].append((receiver,gy.greedy_pc(G,sender,receiver)))
				G.nodes[sender]['localed_dst'].append(receiver)
				#print(sender,receiver)
	return
def get_random_sdpair(len, count):
	pairlist = []
	random.seed(12)
	i = 0
	while(i < count):
		src = random.randint(0, len-1)
		dst = random.randint(0, len-1)
		if src != dst:
			pairlist.append((src, dst))
			i = i + 1
	return pairlist

def get_stpair(num_nodes):
	st = []

	with open('traces/ripple_val.csv', 'r') as f: 
		csv_reader = csv.reader(f, delimiter=',')
		for row in csv_reader:
			# only for positive payments
			if float(row[2]) > 0:
				# map Ripple nodes to Lightning nodes
				src = int(row[0]) % num_nodes
				dst = int(row[1]) % num_nodes

				if src == dst: 
					continue

				st.append((int(src), int(dst)))

	return st

def generate_payments(seed, nflows, G):
	random.seed(seed)
	print(seed)
	payments = []
	#src_dst = get_random_sdpair(len(G), nflows*1000)
	src_dst = get_stpair(len(G))
	# sample transaction value from poisson distribution based on https://coinloan.io/blog/what-is-lightning-network-key-facts-and-figures/
	mean = 508484000 #msat
	quantity = np.random.poisson(mean, nflows)

	while True:
		# are we done yet?
		if len(payments) >= nflows:
			break

		# sample random src/dst pair for which there exists a path
		src, dst = random.choice(src_dst)
		tmp = list(G.nodes())
		#print(tmp)
		src, dst = tmp[src], tmp[dst]
		if not nx.has_path(G, src, dst):
			continue

		# sample transaction value
		val = random.choice(quantity)

		payments.append((src, dst, val, 1, 0))
		#print(src, dst)


	return payments



