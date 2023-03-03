import sys
import os.path

from neuralNet import *

class EvolutionAnimation():
    def __init__(self, scene):
        self.scene = scene
        self.net = None
        self.net_mob = None
        self.prev_net = None
        self.prev_net_mob = None

    def add_network(self, net):
        network_mob_config = {}
        network_mob = NetworkMobject(net, None, None, **network_mob_config)
        return network_mob
        
    def spawn_net(self, net):
        self.net = net
        self.net_mob = self.add_network(self.net)

        self.scene.clear()
        self.scene.add(self.net_mob)

        for obj in self.scene.mobjects:
            FadeIn(obj, run_time = 4, lag_ratio=0)
        self.scene.wait(0.05)
    def transform_one_net(self, new_net):
        self.prev_net = self.net
        self.prev_net_mob = self.net_mob

        self.net = new_net
        self.net_mob = self.add_network(self.net)

        self.scene.play(Transform(self.prev_net_mob, target_mobject = self.net_mob, run_time=0.5))

        self.scene.wait(0)

    def transform_net(self, net1, net2, runtime = 1.5):
        anims = []
        fadeOuts = []
        fadeIns = []
        for layer in net1.layers:
            for neuron in layer.neurons:
                neuron.transform = VGroup()
                neuron.transform.add(neuron)
        for layer in net2.layers:
            for neuron in layer.neurons:
                neuron.transform = VGroup()
                neuron.transform.add(neuron)

        for layer in net1.layers:
            for neuron in layer.neurons:
                if neuron.id in net2.map_id_visual_neurons:
                    neuron.transform = VGroup()
                    neuron.transform.add(neuron)
                    neuron.target = net2.map_id_visual_neurons[neuron.id]
                    anims.append(Transform(neuron.transform, target_mobject=net2.map_id_visual_neurons[neuron.id].transform, run_time=runtime))

                else:
                    neuron.transform = VGroup()
                    neuron.transform.add(neuron)
                    neuron.transform.add(neuron.edges_out)
                    neuron.transform.add(neuron.edges_in)
                    temp = SmallDot(radius =0,opacity = 0)
                    temp.move_to(neuron)
                    
                    fadeOuts.append(Transform(neuron.transform, target_mobject=temp, run_time=runtime))
        for layer in net2.layers:
            for neuron in layer.neurons:
                if neuron.id not in net1.map_id_visual_neurons:
                    neuron.transform = VGroup()
                    neuron.transform.add(neuron)
                    neuron.transform.add(neuron.edges_out)
                    neuron.transform.add(neuron.edges_in)
                    temp = SmallDot(radius =0,opacity = 0)
                    temp.move_to(neuron)
                    fadeIns.append(Transform(temp, target_mobject = neuron.transform, run_time=runtime))

        for edge1 in net1.map_id_visual_connections:
            e1 = net1.map_id_visual_connections[edge1]
            if edge1 in net2.map_id_visual_connections:
                e2 = net2.map_id_visual_connections[edge1]
                anims.append(Transform(e1, target_mobject=e2, run_time=runtime))
            else:
                if (edge1[0] in net1.map_id_visual_neurons and edge1[1] in net1.map_id_visual_neurons 
                    and edge1[0] in net2.map_id_visual_neurons and edge1[1] in net2.map_id_visual_neurons):
                    
                    temp = SmallDot(radius =0,opacity = 0)
                    temp.move_to(net2.map_id_visual_neurons[edge1[1]])
                    fadeOuts.append(FadeOut(e1, run_time = runtime, lag_ratio = 0.1))
        for edge2 in net2.map_id_visual_connections:
            e2 = net2.map_id_visual_connections[edge2]
            if edge2 not in net1.map_id_visual_connections:
                if (edge2[0] in net1.map_id_visual_neurons and edge2[1] in net1.map_id_visual_neurons 
                    and edge2[0] in net2.map_id_visual_neurons and edge2[1] in net2.map_id_visual_neurons):
                    
                    temp = SmallDot(radius =0,opacity = 0)
                    temp.move_to(net1.map_id_visual_neurons[edge2[0]])
                    fadeIns.append(FadeIn(e2, run_time=runtime,lag_ratio = 0.5))
            
        anims = AnimationGroup(*anims, run_time = runtime, lag_ratio = 0)
        fadeIns = AnimationGroup(*fadeIns, run_time = runtime, lag_ratio = 0)
        fadeOuts = AnimationGroup(*fadeOuts, run_time = runtime, lag_ratio = 0)
        
        self.scene.play(AnimationGroup(*[fadeOuts,anims,fadeIns],run_time = 1.1*runtime,  lag_ratio = 0.2))

    def transform_nets_list(self, nets):
        nets_mob = []
        for net in nets:
            nets_mob.append(self.add_network(net))
        self.scene.clear()
        labels = VGroup()
        
        label = Tex("\mathrm{Evolving\ Neural\ Network\ -\ Through\ Generations}").set_height(SCALE*1.2).move_to(TOP).shift(SCALE*DOWN*1.25)
        labels.add(label)
        self.scene.add(nets_mob[0])
        self.scene.play(FadeIn(labels, run_time = 1))
        
        print(1)
        for i in range(1, len(nets_mob)):
            self.scene.clear()
            self.scene.add(labels)
            self.transform_net(nets_mob[i-1],nets_mob[i])

        fad = VGroup()
        fad.add(nets_mob[-1])
        fad.add(labels)
        self.scene.clear()
        self.scene.add(fad)
        self.scene.play(FadeOut(fad, run_time = 1))
        self.scene.clear()