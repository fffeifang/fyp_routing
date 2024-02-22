import networkx as nx
import numpy as np
import csv
import random
from scipy import stats
from sklearn.manifold import MDS
from sklearn.manifold import TSNE

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
	#mapping = dict(list(zip(G.nodes(), list(range(0, len(G))))))
	#G = nx.relabel_nodes(G, mapping, copy=False)
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
	#add property of coordinate

	#api layout
	#pos = nx.kamada_kawai_layout(G)
	#pos = nx.circular_layout(G)
	#pos = nx.spectral_layout(G)
	# for node, coordinates in pos.items():
	# 	G.nodes[node]["pos"] = coordinates

	#spanning tree
	# G_undirected = G.to_undirected()
	# connected_components = list(nx.connected_components(G_undirected))
	# print(len(connected_components))
	# spanning_trees = []
	# node_to_tree = {} 
	# for k, component in  enumerate(connected_components):
	# 	subgraph = G_undirected.subgraph(component).copy()
	# 	st = nx.minimum_spanning_tree(subgraph)
	# 	spanning_trees.append(st)
	# 	for node in component:
	# 		node_to_tree[node] = k

	# length_matrix = np.zeros((len(G), len(G)))

	# #consider hops as distance
	# for i, node_i in enumerate(G.nodes()):
	# 	for j, node_j in enumerate(G.nodes()):
	# 		if i != j:
	# 			if node_i in node_to_tree and node_j in node_to_tree and node_to_tree[node_i] == node_to_tree[node_j]:
	# 				tree_index = node_to_tree[node_i]
	# 				length = nx.shortest_path_length(spanning_trees[tree_index], node_i, node_j)
	# 				length_matrix[i, j] = length
		
	# #MDS
	# mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, n_init=4, max_iter=100)
	# pos = mds.fit_transform(length_matrix)
	# pos_dict = {node: pos[i] for i, node in enumerate(G.nodes())}
	# #t-SNE
	# # tsne = TSNE(n_components=2, random_state=42)
	# # pos_array = tsne.fit_transform(length_matrix)
	# # pos_dict = {node: pos for node, pos in zip(G.nodes(), pos_array)}

	# for node, coordinates in pos_dict.items():
	# 	G.nodes[node]['pos'] = coordinates
	return G
def get_sdpair(len, count):
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
def generate_payments(seed, nflows, G):
	random.seed(seed)
	print(seed)
	payments = []
	src_dst = get_sdpair(len(G), nflows*1000)
    
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
		# if not nx.has_path(G, src, dst):
		# 	continue

		# sample transaction value
		val = random.choice(quantity)

		payments.append((src, dst, val, 1, 0))
		print(src, dst)


	return payments

def changemaxsplit(G, nodeindex, new_split):
	G.nodes[nodeindex]['maxsplit'] = new_split
	return 