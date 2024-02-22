# scheme

## roll back

### prob

目前打算prob实现

#### shortest path of original（二分）

Flag 区分path

### trace

暂不考虑

## atomicity

compare(lab) success rate && success value

(Paper)

## fee

argument->trade-off

## algrithom(split)

### porpotion of capacity

### make single channel more balanced

## maxium split number

### overall split

?one transaction/the whole system

### property of nodes

## routing

Shortest path as baseline(only compare the split performance)

### Shortest path + argument

Coeffcient capacity&&length

### Networkx :shortestpath with capacity

### Greedy

### Longer path with sufficient capacity better

?shortest is greedy

##### before

number of nodes 12920
average channel cap 5642008503.95671
num of edges 72326
medium channel capacity 1487541000.0

##### after pruming nodes with 0 degree

number of nodes 6912
average channel capacity 5642008503.95671
avaerage channel base fee 320018.3033487266
avaerage channel proportion fee 258412.76076376406
num of edges 72326
num of edges 72326
num of edges 72326
medium channel capacity 1487541000.0
medium channel base fee 1.0
medium channel proportion 20.0

# what to do next
yen's k  shortest path/nx.all_shortest_paths