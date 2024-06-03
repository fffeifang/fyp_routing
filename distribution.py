# -*- coding: UTF-8 -*-
import csv
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib import rcParams
rcParams['font.family'] = 'SimHei'
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

sorted_distribution = sorted(distribution_counter.items(), key=lambda item: item[1], reverse=True)

# with open('distribution_counts.txt', 'w') as file:
#     for pair, count in sorted_distribution:
#         file.write(f'{pair}: {count} \n')
# sum_count = 0
# tmp_count = 0
# cnt_pair = 0
# for pair, count in sorted_distribution:
#     sum_count += count
# for pair, count in sorted_distribution:
# 	tmp_count += count
# 	if(cnt_pair  >= 0.01 * len(sorted_distribution)):
# 		print(pair)
# 		print(count)
# 		print(tmp_count/sum_count)
# 		print(sum_count)
# 		break
# 	cnt_pair += 1
# print(stats.scoreatpercentile(sorted_distribution, 50))
sum_count = 0
for pair, count in sorted_distribution:
    sum_count += count
tmp = 0
count_pair = 0
print(len(sorted_distribution))
for pair, count in sorted_distribution:
    tmp += count
    count_pair += 1 
    if(tmp >= 0.3 * sum_count):
        print(count)
        print(count_pair)
        break
        
    