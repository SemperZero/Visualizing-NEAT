from __future__ import print_function
from re import L
import sys
import os.path
import os
import neat
from neat.graphs import feed_forward_layers
from neat.six_util import itervalues

from manimlib import *
sys.path.insert(0, '')

from evolution_anim import *
from game_mass import *

DISPLAY_ONCE_X_GENERATION = 3
nr_tries = 5

class NetworkScene(Scene):
    def construct(self):
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, 'config-feedforward')
        self.generation = 0
        self.prev_net = None
        self.runnn(config_path)

    def eval_genomes(self, genomes, config):
        max_genome = None
        max_net = None
        
        nets = []
        for genome_id, genome in genomes:
            genome.fitness = 0
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            self.export_structure(net, genome, config)
            nets.append(net)

        snakes = GameMass(self, nets, self.generation)
        snakes.play_all()
        scores = snakes.get_scores()

        i=0
        for genome_id, genome in genomes:
            genome.fitness = scores[i]
            i+=1
        self.generation+=1

    def eval_genome(self, genome, config):
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        
        fitness = 0
        for i in range(0,nr_tries):
            game = Game(self, net, self.generation, False)
            fitness += game.play()

        return fitness / nr_tries

    def runnn(self,config_file):
        config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_file)
        p = neat.Population(config)

        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)
        p.add_reporter(neat.Checkpointer(50, filename_prefix='checkpoints\\neat-checkpoint-'))
        
        winner = p.run(self.eval_genomes, 3000)

    def export_structure(self, net, genome, config):
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

        sorted(net.layers[-1])

   
