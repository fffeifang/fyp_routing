for example, when i run a set of 100 transaction
recursively halved:
37 no weighted function(the cost of every edge is 1)
48 weighted function
52 split method
split accorrding to proportion:
48 weighted function
49 split method

judge whether it can route directly at first.


always split at the first nodes(to calculate different paths) , do not take the same prefix  into consider(handled by prob-visited towards the insufficient conditions). 
//the total paths to choose at first increase, so it can devided into smaller payment(unit) to increase success ratio, disadvantage add up fees.

1. something improper with the shortest path function(weighted function). there are two weighted function in current algrithon, the first one is return 1/capacity and the second one is for prob retrun 1/(capacity - used capacity of visited nodes). althrough it takes capacity into consider, it is still shortest path (?). So when I run the proportion split, many transactions shows that there are only one or two channels from the beginning.

2. In proportion split, the distribution is decided by the minimum capacity of the whole path. When there is a shared channel if the sum of the payment is larger than the capacity, the prob fail. //(or we should split from the the first node that is insuffcient and its  distribution is decided by the channels of current node and **the next nodes**)


greedy capcacity, distance, (degree)//try
distance :**shortest path** or / cooridinate(api) **amounted scoling** hop count


12.19

routing/recursive_halved_greedy_revised.py

def dijkstra_greedy(G, source, target, cost_function, theset):
+ payment_size 
+ sorted_capacity(k as coefficient) && choose the nearest one

1.3
if paymentsize > path_cap:
all_derived: 9402
splited: 49
direct: 9353
4780761685708
5084834890954
4788342250182.036

if payment_size/path_cap > 0.8:

(10000)
all_derived:9390
splited:54
direct:9336
throughput_pay:4774665104069
overallpayment:5084841341545
throughput_pay+fee:4783535503582.338


(20000)
all_derived:18802
splited:128
direct:18674
throughput_pay:9560515965492
overallpayment:10169678857727
throughput_pay+fee:9574714014662.965

(30000)
all_derived:28250
splited:152
direct:28098
throughput_pay:14364679404594
overallpayment:15254527107698
throughput_pay+fee:14379860211957.16

(40000)
all_derived:37647
splited:281
direct:37366
throughput_pay:19142900620270
overallpayment:20339364070512
throughput_pay+fee:19164191234634.7

(50000)
all_derived:47086
splited:289
direct:46797
throughput_pay:23942482695746
overallpayment:25424205449826
throughput_pay+fee:23963612059941.605

(100000)
all_derived:93300
splited:464
direct:140259
throughput_pay:47441545622363
overallpayment:50848388213305
throughput_pay+fee:47475234226276.74

(15000)
all_derived:140994
splited:735
direct:92836
throughput_pay:71693196853777
overallpayment:76272605418135
throughput_pay+fee:71734458995962.98

（筛过）
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

average payment size: 508484000msat
transaction set: poison distribution
 0.00508484 BTC

(10000)
all_derived:8037
splited:98
direct:7939
throughput_pay:1056890116350.0
overallpayment:1333775187607.0

(100000)
all_derived:83464
splited:335
direct:83129
throughput_pay:19715583998338.0
overallpayment:22567552576081.0

#####remove active:false

(10000)
all_derived:8755
splited:113
direct:8642
throughput_pay:1275399132877.0
overallpayment:1599166658956.0

（100000）
all_derived:83872
splited:343
direct:83529
throughput_pay:10595270699918.0
overallpayment:13154183682265.0

number of nodes 1773
average channel cap 2980362.868527236
num of edges 29740
medium channel capacity 600000.09
num of transactions 1000000

1.12

the result of topologyset:
po
94%
split less than 1%
26% sp
47% sp+split the 2 shortest path(weighted capacity)

data from offchain
87%
1% splited        
12% sp
(consider active and reverse direction)
(original paper in 20-50%)

set threshold

1.23
mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42, n_init=4, max_iter=100)
(actually I don't think its decentralized because when I precompute the metrix I use shortest path to count the hop)

3.1
Currently, the greedy algrithom based on yen'k shortest path combined with path_capacity and fund skewness is uesd for initialize the whole graph. The frequenly used node pairs are decide by the ripple transaction whose times above 20. The fund skewness calculated before we have transaction,so I use the average transaction quantity to evaluate it. And after the node pair run actual transaction, the pathset will be updated locally. and the decentralized greedy algrithom is in process. I have some prooblems that for frequenly used node pairs when we need to split the payment, during pathfind should we use local pathset or run the decentralized greedy algrithom.

3.8
I change the defination of frequent node pairs, and currently it contains about 80% transactions. And I think it would be better to update the pathset in local after using the frequent node pair, becasue it may be reused again very soon. for coordinates, first find connected components of the network until it contains all nodes build spanning tree of each connected component and then construct the length metrix with the distance of 2 nodes are in the same spanning tree, then use the multi dimension scaling to assign cooridinates. and the problem is we just use part of the connect component, but there might be no path between the 2 nodes or they are connected in other connected component. it takes too long to calculate all connect components

I wanna check if the whole logic is right.
the transactions are devided into the frequent node pair and others. In local the pathset of frequent node pair is calculated by k shorteset path with the parameter of path capacity or path skewness to sort paths. when we run the transactions,  others use greedy to find path. when it comes to a breakpoint, it further split by recursively halved, proportion or balanced.the frequent node pairs first use local pathset, when it comes to  a breakpoint ,should it try to split with the other local path like from the sender or it try to use greedy or other local path in breakpoint?

3.15
I've almost finished writing the scripts, the greedy function still have some problem maybe caused by the coordinate. According to the ripple dataset, 8% node pairs runs 80% transaction, so the local pathset can be used up quickly. And if we update after using the pair, would it be centralized and it seems can't speed up the routing? and if we make it heristic as last time you said, how to assign the posssibiliy.

3.22
The new balanced split algrithom is that the parameter is the weighted fund skewness of each channel times the proportion of capacity. first try to split with the parameter times average capacity and then scaling them or achieve 90% of the capacity until it reach the original transaction quantity. if it fails, then use proportion split. And there's still sth wrong about the coordinate, I 'll update if I find the excat problem. 