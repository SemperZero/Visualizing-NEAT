import random
from re import L
import time
import sys
import os.path
import numpy as np
import math

from snake import *
SCALE
class GameMass():
    def __init__(self, scene, nets, generation):
        print(len(nets))
        self.scene = scene
        self.grid_width = 9#11#8#math.ceil(math.sqrt(len(nets)))
        self.grid_height = 7#8#6#math.floor(len(nets)/self.grid_width)
        self.count_rend = self.grid_height * self.grid_width
        #self.count_rend = len(nets)
        self.nets = nets
        self.frame_count = 0
        self.snakes = []
        self.zoom_count = 0
        for net in self.nets:
                    
            g = Game(self.scene, net, None, False, None, SCALE/self.grid_width, single_game = False)
            self.snakes.append(g)
        self.init_grid()
        self.spawned = False
        
    def reshape(self, arr, height, width):
        grid = VGroup()
        s = arr[:width*height]
        k = 0
        for i in range(0, height):
            line = VGroup()
            for i in range(0, width):
                line.add(s[k])
                k+=1
            grid.add(line)
        
        if k < len(arr):
            print(k,len(arr))
            last_line = VGroup()
            for i in range(k,len(arr)):
                last_line.add(arr[i])
            grid.add(last_line)

        return grid

    def init_grid(self):

        for snake in self.snakes[:self.count_rend]:
            snake.toRend = True
            snake.network_mob = snake.add_network(snake.net)
            snake.render()

        self.snakes_grid = self.reshape(self.snakes[:self.count_rend], self.grid_height,self.grid_width)
        self.max_net_length = math.floor(max([x.get_width() for x in self.snakes[:self.count_rend]]))
        #TODO: vezi dc nu merge asa. too tired now
        #self.snakes_grid = VGroup(list(map(lambda i:VGroup(i), mat)))

       # self.snakes_grid = VGroup()
        
        
    def position_grid_elements(self):
        snake_to_snake_buff = 11
    #    max_net_length = max([len(x.layers) for x in self.nets[:self.count_rend]])
    #    len_neuron = self.snakes[0].network_mob.neuron_radius
  #      len_con = self.snakes[0].network_mob.layer_to_layer_buff
        
      #  print(self.max_net_length)
        print("SNAKES")
            #5 + len_neuron+(len_neuron+len_neuron)*max_net_length - (len_neuron+(len_neuron+len_neuron)*len(self.net.layers)))
        for lane in self.snakes_grid:
            for snake in lane:
                
                
                #print(snake.get_width())
                #padding = #max(5,0 + (len_neuron+len_con)*(max_net_length - len(snake.net.layers)))
                snake.arrange(RIGHT, buff = 0)
                if self.max_net_length < 40:
                    padding = 20 + self.max_net_length - snake.get_width()
                else:
                    padding = self.max_net_length-snake.get_width()
                snake.arrange(RIGHT, buff = padding)
            lane.arrange(RIGHT, buff = 2)

        self.snakes_grid.arrange(DOWN, buff = snake_to_snake_buff)
        #self.snakes_grid.move_to(FRAME_Y_RADIUS * UL)
        self.snakes_grid.to_corner(UL).shift(DOWN*2).shift(RIGHT*2)

    def fade_in_scene(self):
        anims =[]
        for lane in self.snakes_grid:
            for snake in lane:
                anims+=snake.fade_in_scene()
        return anims

    def delete_extra_lines_from_anim(self):
        for lane in self.snakes_grid:
            for snake in lane:
                #TODO: de ce la set_color nu se seteaza toate, dar la opacitate merge cum trebuie si seteaza tot?
                #de ce merge si color cum trebuie atunci cand ii fac un deepcopy la net apoi ii dau restore?
                #de ce trebuie sa fie deepcopy? e o liste de tip pointer si cand ii dau restore la valoarea initiala pur si simplu ia acelasi pointer cu lista modificata? care e lista?
                #return
                snake.network_mob = snake.copy_net_mob
               # self.copy_net_mob = []#self.network_mob.deepcopy()
    def zoom_out(self):
        spacing = (self.grid_width-1)/60
        for x in np.arange(1, self.grid_width*0.9 ,spacing):
            self.scene.camera.frame.set_width(self.snakes[self.count_rend//2].get_width()*1.2*x)
            self.scene.camera.frame.move_to(self.snakes[self.count_rend//2])
            self.scene.add(self.snakes_grid)
            #self.snakes_grid.to_corner(UL).shift(DOWN*2).shift(RIGHT*2)
            self.scene.wait(0.065)
        self.scene.clear()

    def zoom_intercalat(self):
        if self.zoom_count<len(self.zooms):
            x = self.zooms[self.zoom_count]
            self.scene.camera.frame.set_width(self.snakes[self.count_rend//2].get_width()*1.2*x)
            self.scene.camera.frame.move_to(self.snakes[self.count_rend//2]).shift(LEFT*self.snakes[self.count_rend//2].get_width()//10)
            self.scene.add(self.snakes_grid)
            #self.snakes_grid.to_corner(UL).shift(DOWN*2).shift(RIGHT*2)
            self.scene.wait(0.035)
            self.zoom_count+=1
            return True
        else:
            return False

    def smooth_zoom(self):
        max_val = self.grid_width*0.9
        total_steps = 100
        if self.zoom_count > total_steps:
            return False

        


        x = 1+ (max_val-1) * (self.zoom_count/total_steps) ** 2
        #middle_snake = self.snakes[self.count_rend//2]
        self.scene.camera.frame.set_width(self.snakes[self.count_rend//2].get_width()*1.2*x)
        self.scene.camera.frame.move_to(self.snakes[self.count_rend//2]).shift(LEFT*self.snakes[self.count_rend//2].get_width()//10)
        self.scene.wait(0.035)
        self.zoom_count +=1
        return True
        





    def render(self):
        self.scene.clear()
        self.position_grid_elements()
        if not self.spawned:
            #self.zoom_out()
            
            self.spawned = True
           # self.delete_extra_lines_from_anim()
            spacing = (self.grid_width-1)/100
            self.zooms = np.arange(1, self.grid_width*0.9 ,spacing)
            self.scene.camera.frame.set_width(self.snakes[self.count_rend//2].get_width()*1.2)
            self.scene.camera.frame.move_to(self.snakes[self.count_rend//2]).shift(LEFT*self.snakes[self.count_rend//2].get_width()//10)
            self.scene.play(FadeIn(self.snakes_grid, run_time=3,lag_ratio = 0))
       # else:

        self.scene.add(self.snakes_grid)
        #self.scene.wait(0.1)
        
        #TODO: adauga cumva padding ca sa fie bine puse una langa alta. calc length cel mai mult cu nr layere.. sau poate are el cv o functie. apoi pune la toate la dist_max-dist_lor un ob invizibil.. sau o bara?
    
    def play_all(self):
        nrLiveSnakes = len(self.snakes)
        k=0
        while nrLiveSnakes > 0:
            if self.frame_count%1==0:
                nrLiveSnakes = 0
                for snake in self.snakes:
                    if not snake.gameOver:
                        snake.play_step()
                        nrLiveSnakes+=1
                    else:
                        #if snake in self.snakes[:self.count_rend]:
                            #snake.render()
                        #snake=VGroup()
                        snake.set_opacity(0.2)
                        snake.set_color(RED)

            
                self.render()
          #  if k>20:
            if not self.smooth_zoom():
                self.scene.wait(0.02)
           # else:
                #if k ==0:
                    #self.scene.wait(1)
                #else:
                 #   self.scene.wait(0.07)
            #if k>300:
                #exit()

            self.frame_count+=1
            k+=1
            #if k>10:
             #   exit()
        #exit()
        
        self.scene.play(FadeOut(self.snakes_grid, run_time=4,lag_ratio = 0))

    def get_scores(self):
        return [(snake.score, snake.net) for snake in self.snakes]
