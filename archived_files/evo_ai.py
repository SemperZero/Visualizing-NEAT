from __future__ import print_function
import multiprocessing
from re import search
import sys
import os.path

sys.path.insert(0, '')
import os
import neat
from neat.graphs import feed_forward_layers
from neat.six_util import itervalues
import threading
from snake import *
import concurrent.futures

from multiprocessing import Pool
from multiprocessing import cpu_count, get_context, Pool
from random import randint
import c_net
import ctypes

create_c_generation = c_net.C_Func(cfunc = c_net.clibrary.create_c_generation, argtypes = [ctypes.c_int, ctypes.c_int], restype = ctypes.c_void_p)
add_c_net = c_net.C_Func(cfunc = c_net.clibrary.add_c_net, argtypes = [ctypes.c_void_p, ctypes.c_void_p], restype = None)
play_c_generation = c_net.C_Func(cfunc = c_net.clibrary.play_c_generation, argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int], restype = None)
clean_memory = c_net.C_Func(cfunc = c_net.clibrary.clean_memory, argtypes = [ctypes.c_void_p], restype = None)
clean_array = c_net.C_Func(cfunc = c_net.clibrary.clean_array, argtypes = [ctypes.c_void_p], restype = None)
create_array = c_net.C_Func(cfunc = c_net.clibrary.create_array, argtypes = [ctypes.c_int], restype = ctypes.POINTER(ctypes.c_longdouble))

NR_C_THREADS = 2
NR_GAMES_PLAYED = 1000
BOARD_WIDTH = 15
BOARD_HEIGHT = 15

def unpacker_eval_chunk_c(args):
    return eval_chunk_c(*args)

def eval_chunk_c(genome_chunk, config):
    rez = []

    gen_c = create_c_generation(0, len(genome_chunk))

    for genome in genome_chunk:
        genome.fitness = 0
        net_c = c_net.C_FeedForwardNetwork.create_c_net(genome, config)
        add_c_net(gen_c, net_c.neat_nn)
    
    c_res_ptr = create_array(len(genome_chunk))

    play_c_generation(gen_c, c_res_ptr, len(genome_chunk), BOARD_WIDTH, BOARD_HEIGHT, NR_GAMES_PLAYED, NR_C_THREADS)
    clean_memory(gen_c)
    
    i=0
    for i in range(0,len(genome_chunk)):
        #  print(c_res_ptr[i])
        rez.append(c_res_ptr[i])
        i+=1

    clean_array(c_res_ptr)

    return rez

class AI_Evolution():
    def __init__(self,search_type="training",load_search_index=None, load_save_index = None, parallel_evaluation = False, nr_threads = 1, **kwargs):
        self.top_twenty_genomes = [0]*20
        self.set_config_path()

        self.generation = 0
        self.parallel_evaluation = parallel_evaluation
        self.nr_threads = nr_threads

        self.fitness_history = []

        self.search_type = search_type
        self.load_save_index = load_save_index
        self.load_search_index = load_search_index
        self.load_save_file = None
        self.set_checpoint_config()
        self.init_population()
       
    def init_population(self):
        if self.load_save_file is None:
            self.p = neat.Population(self.config)
        else:
            self.p = neat.Checkpointer.restore_checkpoint(self.load_save_file)

        self.p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        self.p.add_reporter(stats)
        self.p.add_reporter(neat.Checkpointer(1, filename_prefix='%s\\save-'%self.save_dir))

    def set_config_path(self):
        self.local_dir = os.path.dirname(__file__)
        self.config_path = os.path.join(self.local_dir, 'config-feedforward')
        config_file = self.config_path
        self.config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_file)

    def set_config(self, confg):
        self.custom_config = confg
        self.config.genome_config.bias_mutate_power = confg["bias_mutate_power"]
        self.config.genome_config.bias_mutate_rate = confg["bias_mutate_rate"]
        self.config.genome_config.node_add_prob = confg["node_add_prob"]
        self.config.genome_config.node_delete_prob = confg["node_delete_prob"]
        self.config.genome_config.weight_mutate_power = confg["weight_mutate_power"]
        self.config.genome_config.weight_mutate_rate = confg["weight_mutate_rate"]
  
    def set_checpoint_config(self):
        if self.load_save_index is not None and self.load_search_index is not None:
            self.save_dir = '%s\\checkpoints\\%s\\search-%d'%(self.local_dir, self.search_type, self.load_search_index)
            self.load_save_file = '%s\\save-%d'%(self.save_dir, self.load_save_index)
        elif self.load_search_index is not None:
            self.save_dir = '%s\\checkpoints\\%s\\search-%d'%(self.local_dir, self.search_type, self.load_search_index)
            max_index = max([int(x.split("save-")[1]) for x in os.listdir(self.save_dir)])
            self.load_save_file = '%s\\save-%d'%(self.save_dir, max_index)
        else:
            self.save_dir = self.get_new_save_folder()

    def get_new_save_folder(self):
        existing_indexes = []
        save_dir = "%s\\checkpoints\\%s"%(self.local_dir,self.search_type)
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        for file in os.listdir(save_dir):
            if "search-" in file:
                index = int(file.split("search-")[1])
                existing_indexes.append(index)
        if len(existing_indexes)==0:
            index = 0
        else:
            index = max(existing_indexes)+1
        self.load_search_index = index
        new_folder =  "%s\\checkpoints\\%s\\search-%d"%(self.local_dir, self.search_type, index)
        os.mkdir(new_folder)
        return new_folder

    def delete_save_folder(self):
        pass

    def eval_genomes_c_parallel(self, genomes, config):
        max_genome_fitness = None

        genomes = [g[1] for g in genomes]
        chunk_size = math.ceil(len(genomes)/self.nr_threads)
        chunked_genomes = [genomes[i:i+chunk_size] for i in range(0,len(genomes),chunk_size)]
        #print(chunked_genomes)
        p = multiprocessing.Pool(processes = self.nr_threads)
        p_rez = p.map(unpacker_eval_chunk_c,[[chunk, config] for chunk in chunked_genomes])
        p.close()
        p.join()

        #list of list to list
        rez = []
        for r in p_rez:
            rez += r

        for i in range(0,len(genomes)):
            genomes[i].fitness = rez[i]
            if (max_genome_fitness == None) or (genomes[i].fitness >= max_genome_fitness):
                max_genome_fitness = genomes[i].fitness
              
            m=min(self.top_twenty_genomes)
            if(genomes[i].fitness > m):
                self.top_twenty_genomes.remove(m)
                self.top_twenty_genomes.append(genomes[i].fitness)
        self.fitness_history.append(max_genome_fitness)

        self.generation+=1

    def eval_genomes_c(self, genomes, config):
        #t1 = time.time()
        max_genome_fitness = None
        max_net = None
        #genomes = [g[1] for g in genomes]

        
        gen_c = create_c_generation(self.generation, len(genomes))

        for _, genome in genomes:
            genome.fitness = 0
            net_c = c_net.C_FeedForwardNetwork.create_c_net(genome, config)
            add_c_net(gen_c, net_c.neat_nn)
        
        c_res_ptr = create_array(len(genomes))

        play_c_generation(gen_c, c_res_ptr, len(genomes), BOARD_WIDTH, BOARD_HEIGHT, NR_GAMES_PLAYED, NR_C_THREADS)
        clean_memory(gen_c)
        
        i=0
        for genome in genomes:
          #  print(c_res_ptr[i])
            genome[1].fitness = c_res_ptr[i]
            i+=1
        clean_array(c_res_ptr)

        for genome in genomes:
            fitness = genome[1].fitness
            if (max_genome_fitness == None) or (fitness >= max_genome_fitness):
                max_genome_fitness = fitness
               # max_net = net

            m=min(self.top_twenty_genomes)
            if(fitness > m):
                self.top_twenty_genomes.remove(m)
                self.top_twenty_genomes.append(fitness)

        
        self.fitness_history.append(max_genome_fitness)

        self.generation+=1
        time.sleep(0.010)
        # if ((max_genome_fitness < 0.5 and self.generation>20)
        #     or (max_genome_fitness < 1 and self.generation>50)
        #     or (max_genome_fitness < 3 and self.generation>100)
        #     or (max_genome_fitness < 5 and self.generation>200)):
        #     for genome in genomes:
        #         genome[1].fitness = 0
       
    def runnn(self, generations = 30000):

        winner = self.p.run(self.eval_genomes_c, generations)
        #stats.save_genome_fitness()

        #if self.generation<generations:
            #self.delete_save_folder()

        #stuff for hyperparameter search
        return [sum(self.top_twenty_genomes)/len(self.top_twenty_genomes), 
                self.fitness_history, 
                self.top_twenty_genomes, 
                self.custom_config,
                "search_index: %d"%self.load_search_index,
                len(self.fitness_history)]
    
    def run_step(self):
        self.p.run_step(self.eval_genomes)

if __name__ == '__main__':
    random.seed(a=None, version=2)
    load_search_type = "training"
    load_search = None 
    load_save = None
    nr_threads = 4
    e = AI_Evolution(load_search_type, load_search, load_save, parallel_evaluation=False, nr_threads = nr_threads)
   # e.p.config.pop_size = 200
    #e.set_config({'bias_mutate_power': 0.0, 'bias_mutate_rate': 0.0066928509242848554, 'node_add_prob': 0.18017912323716065, 'node_delete_prob': 0.0066928509242848554, 'weight_mutate_power': 0.8732587380488285, 'weight_mutate_rate': 0.05374657709529802})
    e.runnn()

    #TODO run python training, then load it in c and see if you get same results