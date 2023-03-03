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
from C_API import *

NR_C_THREADS = 3
NR_GAMES_PLAYED = 100
MIN_BOARD_SIZE = 15
MAX_BOARD_SIZE = 25

class NetworkScene(Scene):
    def __init__(self,**kwargs):
        Scene.__init__(self, **kwargs)
    def construct(self):
        random.seed(a=None, version=2)
        load_search_type = "genetic_search"
        load_search = 0 
        load_save = None
        nr_threads = None
        e = AI_Evolution(load_search_type, load_search, load_save, parallel_evaluation=False, nr_threads = nr_threads, manim_scene = self)
        e.init_population()
        e.runnn()

class AI_Evolution():
    def __init__(self,search_type="training",load_search_index=None, load_save_index = None, parallel_evaluation = False, nr_threads = 1, manim_scene = None, **kwargs):
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
        self.manim_scene = manim_scene
        self.C_API = CAPI()
        #self.init_population()
       
    def init_population(self):
        if self.load_save_file is None:
            self.p = neat.Population(self.config)
        else:
            self.p = neat.Checkpointer.restore_checkpoint(self.load_save_file)

        self.p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        self.p.add_reporter(stats)
        self.p.add_reporter(neat.Checkpointer(30, filename_prefix='%s\\save-'%self.save_dir))

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
        self.config.genome_config.elitism = confg["elitism"]
        self.config.genome_config.survival_threshold = confg["survival_threshold"]
    #   self.config.genome_config.activation_mutate_rate = confg["activation_mutate_rate"]
        self.config.genome_config.activation_default = confg["activation_default"]
    #   self.config.genome_config.bias_init_stdev = confg["bias_init_stdev"]
    #   self.config.genome_config.weight_init_stdev = confg["weight_init_stdev"]
  
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

    def eval_genomes_c(self, genomes, config):
        max_genome_fitness = None
        max_net = None

        gen_c = self.C_API.c_create_c_generation(len(genomes), self.generation)

        for _, genome in genomes:
            genome.fitness = 0
            net_c = C_FeedForwardNetwork.create_c_net(genome, config, self.C_API, False)
            self.C_API.c_add_c_net(gen_c, net_c.neat_nn)
        
        c_res_ptr = self.C_API.c_create_array(len(genomes))

        self.C_API.c_play_c_generation(gen_c, c_res_ptr, len(genomes), MIN_BOARD_SIZE, MAX_BOARD_SIZE, NR_GAMES_PLAYED, NR_C_THREADS)
        self.C_API.c_clean_gen_memory(gen_c)
        
        i=0
        for genome in genomes:
            genome[1].fitness = c_res_ptr[i]
            i+=1
        self.C_API.c_clean_array(c_res_ptr)

        best_genome = None
        for genome in genomes:
            fitness = genome[1].fitness
            if (max_genome_fitness == None) or (fitness >= max_genome_fitness):
                max_genome_fitness = fitness
                best_genome = genome[1]
               
            m=min(self.top_twenty_genomes)
            if(fitness > m):
                self.top_twenty_genomes.remove(m)
                self.top_twenty_genomes.append(fitness)

        ######################## render best net in C console.. api is unfriendly for this :(
        #can create api to play a single game, without having c_generation. just call play on net

        # gen_c = c_create_c_generation(self.generation, 1)
        # net_c = c_net.C_FeedForwardNetwork.create_c_net(best_genome, config, True)
        # c_add_c_net(gen_c, net_c.neat_nn)
        
        # c_res_ptr = c_create_array(1)

        # c_play_c_generation(gen_c, c_res_ptr, 1, BOARD_WIDTH, BOARD_HEIGHT, 5, 1)
        # c_clean_memory(gen_c)
       
       ############# render best net in python
       
       
        # print("BEST GENOME FITNESS IS: ", best_genome.fitness)
        # best_net = neat.nn.FeedForwardNetwork.create(best_genome, config)
        # export_structure(best_net, best_genome, config)
        # game = Game(self.manim_scene, best_net, self.generation, True, None, boardWidth = 15, boardHeight = 15, saveHistory=False)
        # new_fit = game.play()

        ###########################

        self.fitness_history.append(max_genome_fitness)

        self.generation+=1
       
        pruning_no_elit_experiment = { 40 : 1.5, 60: 4, 80: 8, 90: 10, 100: 15, 120: 25, 130: 35 }

        #with this aggressive pruning, we eliminate the chance for latent configurations which may emerge later, with a better end game evolution
        #but we explore more. do soft, check how graphs look after say 10-20 generations and then maybe add hard pruning
        pruning_aggressive = { 40 : 2, 50: 4, 60: 8, 70: 10, 90: 15, 110: 20, 120: 30, 130: 35 }

        # ~10% loss on good genomes 
        pruning_soft = { 70: 4, 80: 6, 90: 9, 110: 20, 120: 30, 130: 35 }

        # current_gen_threshold = 0
        # for gen_nr in sorted(pruning_aggressive.keys()):#sort to make sure on all py versions
        #     if gen_nr > self.generation:
        #         break
        #     current_gen_threshold = gen_nr


        # if current_gen_threshold > 0 and max_genome_fitness < pruning_aggressive[current_gen_threshold]:
        #    for genome in genomes:
        #        genome[1].fitness = -1 # will cause break in population.run() overwritten library
       
    def runnn(self, generations = 30000):

        winner = self.p.run(self.eval_genomes_c, generations)

        return [sum(self.top_twenty_genomes)/len(self.top_twenty_genomes), 
                self.fitness_history, 
                self.top_twenty_genomes, 
                self.custom_config,
                "search_index: %d"%self.load_search_index,
                len(self.fitness_history)]
    
    def run_step(self):
        self.p.run_step(self.eval_genomes)

def export_structure(net, genome, config):
    # changing structure of the net so that we can draw it easier. could call this in render, but we need genome and config too
    connections = [cg.key for cg in itervalues(genome.connections) if cg.enabled]
    
    net.layers = [config.genome_config.input_keys] + [sorted(list(x)) for x in feed_forward_layers(config.genome_config.input_keys, config.genome_config.output_keys, connections) ]
    
    for l in range(0,len(net.layers)-1):
        to_remove_nodes = []
        for nod in net.layers[l]:
            if nod in net.output_nodes:
                to_remove_nodes.append(nod)

        for nod in to_remove_nodes:    
            net.layers[l].remove(nod)
            net.layers[-1].append(nod)
    
    net.layers[-1] = config.genome_config.output_keys.copy()

if __name__ == '__main__':
    #random.seed(a=None, version=2)
    load_search_type = "genetic_search"
    load_search = 0 
    load_save = None
    nr_threads = None
    e = AI_Evolution(load_search_type, load_search, load_save, parallel_evaluation=False, nr_threads = nr_threads)
    # e.p.config.pop_size = 200
    # e.set_config({'bias_mutate_power': 0.0, 'bias_mutate_rate': 0.739276, 'node_add_prob': 0.446649, 'node_delete_prob': 0.665184, 'weight_mutate_power': 0.656472, 'weight_mutate_rate': 0.734493})
    e.init_population() #call this here in order to have custom config. or can add config as optional param in constructor which will call set_config if set
    e.runnn()

    #TODO run python training, then load it in c and see if you get same results (or reverse)