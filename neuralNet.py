import sys
import os.path
from manimlib import *
#from network import *
import time
import random
import numpy as np

class NetworkMobject(VGroup):
    CONFIG = {
        "neuron_radius" : 0.35,
        "neuron_to_neuron_buff" : 0.35,
        "layer_to_layer_buff" : 1.75,
        "neuron_stroke_color" : WHITE,
        "neuron_stroke_width" : 8,
        "neuron_fill_color" : WHITE,
        "edge_color" : GREY_B,
        "edge_stroke_width" : 5,
        "edge_propogation_color" : YELLOW,
        "edge_propogation_time" : 1,
        "max_shown_neurons" : 100,
        "brace_for_large_layers" : True,
        "average_shown_activation_of_large_layer" : True,
        "include_input_output_labels" : True,
    }
    def __init__(self, neatNet, input_labels, output_labels, scale = SCALE, **kwargs):
        VGroup.__init__(self, **kwargs)
        self.scale_net(scale)
        self.neatNet = neatNet
        self.layer_sizes = self.getNeatLayers(self.neatNet)
        connections = self.get_connection_from_neat_eval_genomes(self.neatNet)
        self.text_input_labels = input_labels
        self.text_output_labels = output_labels
        self.map_id_visual_neurons = {}
        self.map_id_visual_connections = {}
        self.neuron_opacities = {}
        self.all_edges = []
        self.add_neurons()
        self.map_neurons()
        self.add_edges(connections)
        self.get_impulses()
        self.normalize_weights_colors()
        self.add_to_back(self.edge_groups)
        self.add(self.layers)

    def scale_net(self, scale):
        self.neuron_radius = scale * self.neuron_radius
        self.neuron_to_neuron_buff = scale * self.neuron_to_neuron_buff
        self.layer_to_layer_buff = scale * self.layer_to_layer_buff
        self.neuron_stroke_width = scale * self.neuron_stroke_width
        self.edge_stroke_width = scale * self.edge_stroke_width

    def getNeatLayers(self, net):
        layer_sizes = []
        for layer in net.layers:
            layer_sizes.append(len(layer))
        return layer_sizes

    def get_connection_from_neat_eval_genomes(self, net):
        connections = {}
        for n in self.neatNet.node_evals:
            nod_id = n[0]
            nod_conns = n[5]
            connections[nod_id] = nod_conns
        
        return connections

    def add_neurons(self):
        layers = VGroup(*[
            self.get_layer(size,i)
            for i,size in enumerate(self.layer_sizes)
        ])
        layers.arrange(RIGHT, buff = self.layer_to_layer_buff)
        self.layers = layers

    def map_neurons(self):
        for l, layer in enumerate(self.layers):
            for n, neuron in enumerate(layer.neurons):
                neuron.id = self.neatNet.layers[l][n]
                neuron.layer = l
                self.map_id_visual_neurons[neuron.id] = neuron
    
    def get_layer(self, size,i):
        layer = VGroup()
        n_neurons = size
        if n_neurons > self.max_shown_neurons:
            n_neurons = self.max_shown_neurons
 
        neurons = VGroup(*[
            Circle(
                radius = self.neuron_radius,
                stroke_color = self.neuron_stroke_color,
                stroke_width = self.neuron_stroke_width,
                fill_color = self.neuron_fill_color,
                fill_opacity = 0,
            )
            for x in range(n_neurons)
        ])
        neurons.arrange(
            DOWN, buff = self.neuron_to_neuron_buff
        )
        for neuron in neurons:
            neuron.edges_in = VGroup()
            neuron.edges_out = VGroup()
        layer.neurons = neurons
        layer.add(neurons)

        return layer

    def add_edges(self, connections):
        self.edge_groups = VGroup()

        for l, layer in enumerate(self.layers[1:]):
            edge_group = VGroup()
            for nod1 in layer.neurons:
                if nod1.id in connections:
                    for con in connections[nod1.id]:
                        nod2_id = con[0]
                        weight = con[1]
                        nod2 = self.map_id_visual_neurons[nod2_id]
                        edge = self.get_edge(nod2, nod1, weight)
                        edge.weight = weight
                        edge.across_n_layers = nod1.layer - nod2.layer
                        edge_group.add(edge)
                        nod2.edges_out.add(edge)
                        nod1.edges_in.add(edge)
                        self.map_id_visual_connections[(nod1.id,nod2.id)] = edge
                        self.all_edges.append(edge)
            self.edge_groups.add(edge_group)
            
    def get_edge(self, neuron1, neuron2, weight):
        if weight <0:
            color = RED_D
        else:
            color = BLUE_D
        return Line(
            neuron1.get_center(),
            neuron2.get_center(),
            buff = self.neuron_radius/2,
            stroke_color = color,
            stroke_width = self.edge_stroke_width,
            stroke_opacity = 1
        )

    def normalize_weights_colors(self):

        all_weights = []
        for layer in self.layers[1:]:
            for nod in layer.neurons:
                for edge in nod.edges_in:
                    all_weights.append(edge.weight)
        if len(all_weights)==0:
            return
        w = np.array(all_weights)
        mean = np.mean(w)
        stdev = np.std(w)
        max_ = np.min(w)
        min_ = np.max(w)

        for layer in self.layers[1:]:
            for nod in layer.neurons:
                for edge in nod.edges_in:

                    edge.weight = (edge.weight - mean)/(stdev)
                    if stdev<1.3:
                        edge.weight/=2
                    edge.set_stroke(color=edge.stroke_color, width=edge.stroke_width, opacity=abs(edge.weight))
               
    def normalize_neuron_opacities(self, layer):
            opacities = [self.neatNet.values[neuron.id] for neuron in layer.neurons]
            o = np.array(opacities)
            mean = np.mean(o)
            stdev = np.std(o)
            max_ = np.min(o)
            min_ = np.max(o)
            for neuron in layer.neurons:
                self.neuron_opacities[neuron.id] = self.neatNet.values[neuron.id]/2
                        

    def get_edge_propogation_animations(self, runtime = 4):
        edge_group_copy = VGroup()
        for layer in self.layers:
            for nod in layer.neurons:
                for edge in nod.edges_out:
                    edge_group_copy.add(edge)
        return ShowCreation(edge_group_copy, run_time = runtime, lag_ratio = 0.05)

    def get_impulses(self):
        for layer in self.layers:
            layer.impulses_in = VGroup()
            layer.impulses_out = VGroup()
            targets = VGroup()
            for nod in layer.neurons:
                for edge in nod.edges_out:
                    start = edge.get_start()
                    end = edge.get_end()
                    impulse = Dot(start, color = edge.stroke_color, radius = 0.15)
                    impulse.target = Dot(end, color = edge.stroke_color, radius = 0.15)
                    impulse.path = edge
                    impulse.across_n_layers = edge.get_length()
                    layer.impulses_out.add(impulse)
                    targets.add(impulse.target)
                for edge in nod.edges_in:
                    start = edge.get_start()
                    end = edge.get_end()
                    impulse = Dot(start, color = edge.stroke_color, radius = 0.15)
                    impulse.target = Dot(end, color = edge.stroke_color, radius = 0.15)
                    impulse.path = edge
                    impulse.across_n_layers = edge.get_length()
                    layer.impulses_in.add(impulse)
                    targets.add(impulse.target)
    def clear_opacities(self, scene):
        for layer in self.layers:
            for neuron in layer.neurons:
                neuron.set_fill(opacity = 0)


    def light_last_neuron(self):
        layer = self.layers[-1]
        for neuron in layer.neurons:
            neuron.set_fill(opacity = 0)
        if self.neatNet.last_neuron_fired!=None:
            n = self.layers[-1].neurons[self.neatNet.last_neuron_fired]
            n.set_fill(opacity =1, color = YELLOW)
        
    def update_layer_opacities(self, layer):  
        if layer!=self.layers[-1]:
            self.normalize_neuron_opacities(layer)
            for neuron in layer.neurons:
                
                neuron.set_fill(opacity = self.neuron_opacities[neuron.id], color = WHITE)
        else:
            self.light_last_neuron()
        
    def update_opacities(self):
        self.clear_opacities(None)
        for layer in self.layers:
            self.update_layer_opacities(layer)


    def get_impulse_animations(self, layer,i,n):

        all_edges = []
        for nod in layer.neurons:
            for edge in nod.edges_in:
                all_edges.append(edge.copy().set_stroke(color=YELLOW, width=edge.stroke_width, opacity=0.5))
        
        all_edges = VGroup(*sorted(all_edges, key = lambda x:x.get_y(), reverse=True))
        edge_animation = ShowCreationThenDestruction(
            all_edges,
            run_time = 0.4,
            lag_ratio = 0.1,
            remover = True,
        )
        
        return edge_animation

    def get_feed_forward_animation(self, scene):
        a=[]
        i=0
        self.clear_opacities(scene)
        self.update_layer_opacities(self.layers[0])
        for layer in self.layers:
            
            layer_copy = layer.deepcopy()
            scene.play(self.get_impulse_animations(layer_copy,i,len(self.layers)-1), rate_func = linear)
            scene.wait(0.01)
            self.update_layer_opacities(layer)
            i+=1
        scene.wait(0.2)

    def add_input_labels(self):
        
        self.input_labels = VGroup()
        self.input_labels_dict = {}
        for n, neuron in enumerate(self.layers[0].neurons):
            label = Tex(self.text_input_labels[n])
            label.set_height(0.75*neuron.get_height())
            label.move_to(neuron)
            label.shift(neuron.get_width()*LEFT*2.7)
            self.input_labels.add(label)
            self.input_labels_dict[self.text_input_labels[n]] = label
    def activate_input_labels(self):
        self.add(self.input_labels)
        
    def add_output_labels(self):
        
        self.output_labels = VGroup()
        self.output_labels_dict = {}
        for n, neuron in enumerate(self.layers[-1].neurons):
            label = Tex(self.text_output_labels[n])
            label.set_height(0.75*neuron.get_height())
            label.move_to(neuron)
            label.shift(neuron.get_width()*RIGHT*1.2)
            self.output_labels.add(label)
            self.output_labels_dict[self.text_input_labels[n]] = label
    def activate_output_labels(self):
        self.add(self.output_labels)

    def spawn_neural_net(self, added_anims = None, runtime = 3):
        if added_anims is None:
            added_anims = []
        anims = []
        for i, layer in enumerate(self.layers):
            anims.append(FadeIn(layer.neurons, lag_ratio=0.5, run_time = runtime))
        from pprint import pprint

        edge_propag_anim = self.get_edge_propogation_animations(runtime = runtime)

        anims.append(edge_propag_anim)
        
        return(anims)