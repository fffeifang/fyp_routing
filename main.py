import lightning_proc
import lightning_proc_backup
import routing.proportion_splited_sp as proportion_splited_sp
import routing.recursive_halved_split_sp as recursive_halved_split_sp
import routing.proportion_splited_greedy as psg
import routing.proportion_greedy as pg
import routing.recursive_halve_greedy as rhg
import routing.backup as bp
import routing.flash as flash
import routing.shortest_path as sp

def main():
    #G, trans = lightning_proc_backup.setup()
    G = lightning_proc.setup()
    pay = lightning_proc.generate_payments(4, 1000,G)
    #pay = lightning_proc_backup.generate_payments(4, 10000, trans, G)


    #pay = [[1,2,40,1,0]]
    pg.routing(G, pay)

if __name__ == "__main__":
 	main()