import lightning_proc

import routing.recursive_halve as rh

import routing.shortest_path as sp

def main():
    #G, trans = lightning_proc_backup.setup()
    G = lightning_proc.setup()
    lightning_proc.initcoordinate(G)
    #distribution = lightning_proc.initlocalpath(G, 0)
    #lightning_proc.read_coordinate(G)
    #pay = lightning_proc.generate_payments(4, 100, G, distribution)
    #pay = lightning_proc_backup.generate_payments(4, 10000, trans, G)


    #pay = [[1,2,40,1,0]]
    #rh.routing(G, pay)

if __name__ == "__main__":
 	main()