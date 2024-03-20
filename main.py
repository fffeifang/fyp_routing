import lightning_proc

import routing.recursive_halve as rhgf


def main():
    #G, trans = lightning_proc_backup.setup()
    G = lightning_proc.setup()
    lightning_proc.initcoordinate(G)
    distribution = lightning_proc.initlocalpath(G)
    pay = lightning_proc.generate_payments(4, 1000, G, distribution)
    #pay = lightning_proc_backup.generate_payments(4, 10000, trans, G)


    #pay = [[1,2,40,1,0]]
    rhgf.routing(G, pay)

if __name__ == "__main__":
 	main()