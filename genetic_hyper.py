from __future__ import print_function
import sys
import os.path

sys.path.insert(0, '')
import os
import neat
from neat.graphs import feed_forward_layers
from neat.six_util import itervalues
import random
import numpy as np
import evo_ai
import time
import pandas as pd

NR_TRIES_PER_GENOME = 1
NR_GENERATIONS_PER_SEARCH = 200

class EvolveHyperParam():
    def __init__(self,**kwargs):
        
        self.top_twenty_genomes = [0]*20
        local_dir = os.path.dirname(__file__)
        self.config_path = os.path.join(local_dir, 'config-hyper-gen')
        config_file = self.config_path
        self.config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_file)

        self.generation = 0
        self.prev_net = None
        self.max_genome = None
        self.max_cfg = None
        self.max_fitness=None

    def float_dec(self, x,n):
        p = 10**n
        return float(int(x*p))/p

    def square(self,args):
        s=0
        for x in args:
            s+=x**2
        return -s+5
        
    def get_config(self, args):
        confg = {}
        confg["bias_mutate_power"] = args[0]
        confg["bias_mutate_rate"] = args[1]
        confg["node_add_prob"] = args[2]
        confg["node_delete_prob"] = args[3]
        confg["weight_mutate_power"] = args[4]
        confg["weight_mutate_rate"] = args[5]
        confg["elitism"] = args[6] * 40
        confg["survival_threshold"] = args[7]
      #  confg["activation_mutate_rate"] = args[8]
        if args[8] > 0.5:
            confg["activation_default"] = "relu"
        else:
            confg["activation_default"] = "sigmoid"

        # if args[7] < 0.5:
        #     confg["bias_init_stdev"] = 1.0
        #     confg["weight_init_stdev"] = 1.0
        # else:
        #     confg["bias_init_stdev"] = 17.32
        #     confg["weight_init_stdev"] = 17.32

        
        return confg

    

    def eval_genomes(self, genomes, config):
        rez_list = []
        histories_for_plot = []
        d = {}

        for i,genome in genomes:
            
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            inp = np.array([1])
            config_list = net.activate(inp)
        
        #     for k, x in enumerate(config_list):
        #         if "y%d"%k in d:
        #             d["y%d"%k].append(x)
        #         else:
        #             d["y%d"%k]=[]
        # df = pd.DataFrame(d)
        # df.to_csv(os.path.join("data_visualization\\distribution.csv"), index=False)
        
            hyperparameters_genetic = self.get_config(config_list)
            s = 0
            tries = NR_TRIES_PER_GENOME
            
            for t in range(0,tries):
                eval = evo_ai.AI_Evolution(search_type="genetic_search")
                eval.set_config(hyperparameters_genetic)
                eval.init_population()
                rez = eval.runnn(NR_GENERATIONS_PER_SEARCH)

                #rez[0] = self.float_dec(rez[0],3)
                s+=rez[0]
                rez += ["nr_genome: %d | nr_try: %d"%(i, t)]
                rez_list.append(rez)

                rez_list=sorted(rez_list, key = lambda x: -x[0])

                with open("hyper_search\\genetic_search\\rez_generation_%d"%self.generation,"w") as w:
                    for el in rez_list:
                        w.write("%.3f | "%el[0])
                        for z in el[1:]:
                            w.write(str(z)+" | ")
                        w.write("\n")

            s = s/tries

            genome.fitness = s

            if self.max_fitness == None or genome.fitness>self.max_fitness:
                self.max_genome = genome
                self.max_cfg = config_list
                self.max_fitness = genome.fitness
                self.best_rez = rez
            
            
            rez_list=sorted(rez_list, key = lambda x:x[0])
                
        if(self.max_fitness>5):
            with open("hyper_search\\genetic_search\\best_rez_genetic","a") as w:
                for z in self.best_rez:
                    w.write(str(z)+"\n")

                w.write("\n")
        self.generation+=1
        

    def runnn(self, generations = 200):
        p = neat.Population(self.config)
       # load_nr = 4
       # p = neat.Checkpointer.restore_checkpoint('checkpoints\\genetic_hyper_evolution\\checkpoint-'+str(load_nr))
       # self.generation = 6#

        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)
        p.add_reporter(neat.Checkpointer(1, filename_prefix='checkpoints\\genetic_hyper_evolution\\checkpoint-'))
        winner = p.run(self.eval_genomes, generations)
        print(winner.fitness)

if __name__ == '__main__':
    random.seed(a=None, version=2)
    e = EvolveHyperParam()
    e.runnn()