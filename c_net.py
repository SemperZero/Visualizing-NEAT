from neat.graphs import feed_forward_layers
from neat.six_util import itervalues
import ctypes
import numpy as np
import C_API


class C_FeedForwardNetwork(object):
    def __init__(self, neat_nn, c_api):
        self.neat_nn = neat_nn
        self.c_api = c_api

    def activate(self, inputs, c_api):
    
        np_inputs = np.array(inputs)
        c_inputs_ptr = np_inputs.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
        x = self.c_api.c_activate_net(self.neat_nn, c_inputs_ptr, len(np_inputs))
        return x

    @staticmethod
    def create_c_net(genome, config, c_api):
        #maybe create python c structs and send everything at once. then allocate it directly (no pointers) in c, or call malloc. or send everything in one void* buffer. need to make bytes* in python i think

        #start python genome decoding
        connections = [cg.key for cg in itervalues(genome.connections) if cg.enabled]
        layers = feed_forward_layers(config.genome_config.input_keys, config.genome_config.output_keys, connections)
        
        #prep input
        input_nodes = np.array(config.genome_config.input_keys)
        c_input_nodes_ptr = input_nodes.ctypes.data_as(ctypes.POINTER(ctypes.c_longdouble))#not sure if data_as is needed
        
        output_nodes = np.array(config.genome_config.output_keys)
        c_output_nodes_ptr = output_nodes.ctypes.data_as(ctypes.POINTER(ctypes.c_longdouble))

        #create net
        c_neat_nn = c_api.c_create_net(c_input_nodes_ptr, len(input_nodes), c_output_nodes_ptr, len(output_nodes))

        #parse decoded genome and create c_net
        for layer in layers:
            for node_id in layer:
                ng = genome.nodes[node_id]
                c_node = c_api.c_create_node(node_id, ng.bias, ng.response, ctypes.c_char_p(ng.activation.encode('ascii')), ctypes.c_char_p(ng.aggregation.encode('ascii')))
               # print("c node is: ", type(c_node))
                for conn_key in connections:
                    inode, onode = conn_key
                    if onode == node_id:
                        cg = genome.connections[conn_key]
                        c_api.c_add_connection(c_node, C_API.Connection(inode, cg.weight))

                c_api.c_add_node(c_neat_nn, c_node)            
                
        return C_FeedForwardNetwork(c_neat_nn, c_api)

    
