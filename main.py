import lightning_proc

import routing.recursive_halve as rh
import routing.proportion as p
import routing.balanced as b
import routing.cmp.shortest_path as sp
import routing.cmp.speedymurmurs as sm
import routing.cmp.flash as f
import routing.backup as bp
import time
def main():
    G = lightning_proc.setup()
    #lightning_proc.initcoordinate(G)
    distribution = lightning_proc.initlocalpath(G, 0)
    lightning_proc.read_coordinate(G)
    # caution! local path num
    pay, threshold = lightning_proc.generate_payments(4, 100, G, distribution)
    # caution! retry 
    start_time = time.time()
    bp.routing(G, pay)
    # num_delivered, throughput_pay, throughput_total, success_ratio, success_volume, transaction_fee = b.routing(G, pay)
    # f.routing(G, pay, threshold, 4)
    # sm.routing(G,pay)
    # sp.routing(G, pay)
    end_time = time.time()
    execution_time = end_time - start_time
    print('=============================================================')
    # print(num_delivered, throughput_pay, throughput_total, success_ratio, success_volume, transaction_fee)
    print(execution_time)
    # sp.routing(G, pay)
if __name__ == "__main__":
 	main()