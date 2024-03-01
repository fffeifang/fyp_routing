import csv
from collections import Counter

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

with open('distribution_counts.txt', 'w') as file:
    for pair, count in distribution_counter.items():
        file.write(f'{pair}: {count} \n')