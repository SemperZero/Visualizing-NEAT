import random
import time
import sys
import os.path
import numpy as np
import math
from manimlib import *
from neuralNet import *


class Location():
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

class Fruit():
    def __init__(self, snake, boardWidth, boardHeight):
        self.x = None
        self.y = None
        self.respawn(snake, boardWidth, boardHeight)

    def respawn(self, snake, boardWidth, boardHeight):
        #TODO: vezi intervalul <= sau <
        ok = 0
        while ok == 0:
            #prev value is value of current head, right? no need to use that
            ok =1
            x = random.randint(1,boardWidth-2)
            y = random.randint(1,boardHeight-2)

            if x == self.x and y == self.y:
                ok = 0
            if x == snake.head.x and y == snake.head.y:
                ok = 0
            for seg in snake.tail.segments:
                if seg.x == x and seg.y == y:
                    ok = 0
        self.x=x
        self.y=y  

    def set_coord(self, loc):
        self.x = loc.x
        self.y = loc.y


class Tail():
    def __init__(self, initialSize = 0):
        self.segments = []
    def addSegment(self, loc):
        self.segments.append(loc)

class LoadHistory():
    def __init__(self):
        self.spawnpoint = None
        self.first_dir = None
        self.fruit_history = []
        self.history_point = 0

    def get_next_fruit(self):
        a = self.fruit_history[self.history_point]
        self.history_point += 1
        return a

    def add_fruit_history(self, loc):
        self.fruit_history.append(loc)
        
class Snake():
    def __init__(self, spawnPoint = (10,10), size = 1, spawndir = (0,1)):
        self.head = Location(spawnPoint[0], spawnPoint[1])
        self.tail = Tail()
        self.start_size = size
        self.size = size
        self.directions = ["UP", "DOWN", "LEFT", "RIGHT"]
        self.map_dirs_poz = { "UP" : (0,1), "DOWN" : (0,-1), "LEFT" : (-1, 0), "RIGHT" : (1, 0) }
        self.t = spawndir

        for i in range(1, size+1):
            ii, jj = self.t
            self.tail.addSegment(Location(self.head.x + ii, self.head.y + jj))
        self.direction = random.choice(self.directions)
        self.newLoc = None


    def getNewLoc(self):
        x,y = self.map_dirs_poz[self.direction]
        self.newLoc = Location(self.head.x + x, self.head.y + y)

    def move(self):
        for i in range(len(self.tail.segments)-1, 0, -1):
            self.tail.segments[i] = self.tail.segments[i-1]

        self.tail.segments[0] = self.head
        self.head = self.newLoc

    def grow(self):
        last_tail_seg = self.tail.segments[-1]
        self.tail.addSegment(Location(last_tail_seg.x, last_tail_seg.y))
        self.size += 1

class Game(VGroup):
    def __init__(self, scene, net, generation, toRend, times, render_scale = SCALE, single_game = True, boardWidth = 15, boardHeight = 15, saveHistory = False, loadHistory = None, **kwargs):
        VGroup.__init__(self, **kwargs)
       # random.seed(a=None, version=2)
        random.seed(a=None, version=2)
        self.boardWidth = boardWidth
        self.boardHeight = boardHeight
        self.scene = scene
        self.toRend = toRend
        self.net = net
      #  self.net_c = net_c
        #self.prev_net = prev_net
        self.generation = generation
        self.loadHistory = loadHistory
        self.saveHistory = saveHistory
 
        if self.saveHistory:
            self.history = LoadHistory()
        else:
            self.history = None

        if loadHistory is None:
            self.spawnpoint = (random.randint(2,self.boardWidth-3), random.randint(2,self.boardHeight-3))
            tail_spawn_dirs = [(0,1), (1,0), (0, -1), (-1,0)]
            self.first_dir = random.choice(tail_spawn_dirs)
            self.snake = Snake(spawnPoint = self.spawnpoint, size = 1, spawndir = self.first_dir)
            self.fruit = Fruit(self.snake, self.boardWidth, self.boardHeight)
            
            if self.saveHistory:
                self.history.spawnpoint = self.spawnpoint
                self.history.first_dir = self.first_dir
                self.history.add_fruit_history(Location(self.fruit.x, self.fruit.y))
        else:
            self.spawnpoint = loadHistory.spawnpoint
            self.first_dir = loadHistory.first_dir
            self.snake = Snake(spawnPoint = self.spawnpoint, size = 1, spawndir = self.first_dir)
            self.fruit = Fruit(self.snake, self.boardWidth, self.boardHeight)
            self.fruit.set_coord(loadHistory.get_next_fruit())
            
        
        self.gameOver = False
        self.score = 0
        self.nr_moves = 0
        self.nr_moves_since_last_fruit = 0
        self.frameCount = 0
        self.boardPaddingX = 0.5
        self.boardPaddingY = 0.3
        self.render_scale = render_scale
        self.single_game = single_game
        self.hashes_states={}
        self.why_it_died = None
        self.head_square = None
        self.overlay = Explain_Details(self.boardHeight, self.boardWidth, self.render_scale)
        if toRend:
            self.network_mob = self.add_network(self.net)
            self.net.last_neuron_fired = None
        self.py_took = 0
        self.c_took = 0

    def checkGameOver(self, newLoc):
        if newLoc.x == 0 or newLoc.y == 0 or newLoc.x == self.boardWidth-1 or newLoc.y == self.boardHeight-1:
            return True
        #if self.nr_moves_since_last_fruit >=100:#self.boardHeight*self.boardWidth:
           # return True
        for seg in self.snake.tail.segments:
            if newLoc.x == seg.x and newLoc.y == seg.y:
                return True
        if self.check_loop():
            self.why_it_died = "loop"
            return True
        

        return False

    def check_loop(self):
        #loop hash technology
        #maxsize should be around board dimension.. small dict
        current_state = []
        current_state.append(self.snake.head.x)
        current_state.append(self.snake.head.y)
        for seg in self.snake.tail.segments:
            current_state.append(seg.x)
            current_state.append(seg.y)
        current_state_tuple = tuple(current_state)
        
        if current_state_tuple in self.hashes_states:
            self.hashes_states[current_state_tuple] += 1
        else:
            self.hashes_states[current_state_tuple] = 1
        
        if self.hashes_states[current_state_tuple] >= 3:
            return True
        return False

    def play(self):
        while not self.gameOver:
            self.play_step()
        return self.snake.size-self.snake.start_size

    def get_history(self):
        return self.history

    def play_game_over_animation(self):
        self.scene.wait(2)
        fade_group = VGroup()
        fade_group.add(self.boardGroup)
        fade_group.add(self.labels)

        if self.generation != 1529:
            self.scene.play(FadeOut(fade_group, run_time=1,lag_ratio = 0))
        else:
            fade_group.add(self.network_mob)
            self.scene.play(FadeOut(fade_group, run_time=5,lag_ratio = 0))

    def play_step(self):
        
        self.getInputAI4()
        
        
        if self.toRend:
            self.render()
        self.snake.getNewLoc()
        
        self.gameOver = self.checkGameOver(self.snake.newLoc)
        
        
        if self.gameOver:
            if self.toRend and self.single_game:
                self.play_game_over_animation()



            return
        
        if self.snake.newLoc.x == self.fruit.x and self.snake.newLoc.y == self.fruit.y:
            self.snake.grow()
            
            
            if self.loadHistory is None:#or out of next fruits
                self.fruit.respawn(self.snake, self.boardWidth, self.boardHeight)
                if self.saveHistory:
                    self.history.add_fruit_history(Location(self.fruit.x,self.fruit.y))
               
            else:
                self.fruit.set_coord(self.loadHistory.get_next_fruit())


            self.nr_moves_since_last_fruit = 0
            self.score+=1
            self.hashes_states = {}
        
        self.snake.move()
                
        self.nr_moves+=1
        self.nr_moves_since_last_fruit +=1
        
    def renderSquare(self, x, y, color, length, opacity):
        
        #transform from my board to manim's board coordinate system.
        borderSquare = Square(color=color, side_length=self.render_scale*length, fill_opacity=opacity)
        borderSquare.set_x(-FRAME_X_RADIUS + self.render_scale*x + self.render_scale*self.boardPaddingX)
        borderSquare.set_y(self.render_scale*y + self.render_scale*self.boardPaddingY)

        self.boardGroup.add(borderSquare)
        return borderSquare

    def renderBoard(self):
        for i in range(1,self.boardWidth-1):   
            self.renderSquare(i,0,WHITE, 0.7, 0.6)
            self.renderSquare(i,self.boardHeight-1,WHITE, 0.7, 0.6)

        for i in range(0,self.boardHeight):
            self.renderSquare(0,i,WHITE, 0.7, 0.6)
            self.renderSquare(self.boardWidth-1,i,WHITE, 0.7, 0.6)

    def renderSnake(self):
        self.head_square = self.renderSquare(self.snake.head.x,self.snake.head.y,YELLOW, 0.6, 1)
        for seg in self.snake.tail.segments:
            seg.square = self.renderSquare(seg.x,seg.y,GREEN, 0.6, 1)

        self.fruit_square = self.renderSquare(self.fruit.x,self.fruit.y,RED, 0.6, 1)

    def renderNet(self):
        return

    def fade_in_scene(self):
        
        anims = []
        
        self.copy_net_mob = self.network_mob.deepcopy()
    

        for obj in self.snake_net_group:
            if(obj != self.network_mob):
                anims.append(FadeIn(obj, run_time = 2, lag_ratio=0))
        if self.single_game:
            anims.append(FadeIn(self.labels, run_time = 2, lag_ratio=0))
        anims += self.network_mob.spawn_neural_net(runtime = 4)
        
        return anims
            
    def render(self):
        self.set_submobjects([])
        self.snake_net_group = VGroup()
        self.boardGroup = VGroup()

        self.renderBoard()
        self.renderSnake()
        
        self.snake_net_group.add(self.boardGroup)
        self.snake_net_group.add(self.network_mob)
        
        if self.single_game:
            snake_net_padding = 30
        else:
            snake_net_padding = 5
        self.snake_net_group.arrange(RIGHT, buff = snake_net_padding)
        if self.single_game:
            self.scene.clear()
            self.boardGroup.to_corner(UL)
            self.network_mob.move_to(ORIGIN)
            if self.network_mob.get_center()[0] - self.network_mob.get_width()/2 < self.boardGroup.get_center()[0] + self.boardGroup.get_width()/2:
                target = ORIGIN + self.boardGroup.get_right()
                target[0]+=self.network_mob.get_width()/2 + 1 * self.render_scale
                target[1]=0
                self.network_mob.move_to(target)
            
            self.labels = VGroup()                                                       
            label = Tex("\mathrm{Best\ of\ Generation\ \#"+str(self.generation)+"}").set_height(SCALE*1.2).move_to(TOP).shift(SCALE*DOWN*1.25)
            score = Tex("\mathrm{size: "+str(self.snake.size)+"}").set_height(SCALE*1).move_to(BOTTOM+LEFT_SIDE).shift(SCALE*UP*1.25).shift(SCALE*RIGHT*2.75)
            score.next_to(self.boardGroup, DOWN+LEFT, buff=1*SCALE)
            score.shift(RIGHT*1.3*score.get_width())
            self.labels.add(label)
            self.labels.add(score)

            if self.frameCount == 0:
                
                self.scene.add(self.labels)
                self.scene.play(*self.fade_in_scene())
            else:
                self.scene.clear()
                self.scene.add(self.snake_net_group)

            waitings = {0:0.1, 9:0.1, 29:0.1, 49:0.1, 99:0.1, 139:0.1, 199:0.075, 239:0.075, 459:0.04, 569:0.04, 699:0.03, 809:0.03, 929:0.03, 1049:0.03, 1529:0.03}
                                                        
            self.scene.wait(0.1)    
        self.add(self.snake_net_group)
        self.add(Square(color=RED, side_length=0, fill_opacity=0, stroke_opacity = 0))
        self.frameCount+=1

        
    def peak_curve_point(self, peak):
        return -(peak-1)**2/(2*peak-1)

    def normalize_space(self, x, peak):
        #TODO: mai verifica daca stretchurile sunt cum trebuie
        stretch = self.boardWidth
        real_peak = peak/stretch
        t = self.peak_curve_point(real_peak)

        return 2*(t-1/( x/stretch * 1/(t*(t-1)) + 1/t))-1
   
    def normalize_space_sig(self, x, peak):
    
        return 2  / (1+math.exp(-(x- peak))) - 1
    
    
    def get_min(self,a,b):
        if a<b:
            return a
        else:
            return b
    def sign(self, a):
        if a<0:
            return -1
        else:
            return 1

    def getInputAI4(self):
        
        dirs = ["N", "S", "W", "E", "N-E", "S-E", "S-W", "N-W"]
        vision = {"Wall":{}, "Tail":{}, "Fruit":{}}
        #TODO: make sure min and max values are ok below, due to boardHeight-1 stuff
        sin_45 = 0.7071

        dist_n = self.boardHeight - self.snake.head.y
        dist_e = self.boardWidth - self.snake.head.x
        vision["Wall"]["N"] = dist_n
        vision["Wall"]["S"] = self.snake.head.y
        vision["Wall"]["W"] = self.snake.head.x
        vision["Wall"]["E"] = dist_e
        vision["Wall"]["N-E"] = self.get_min(dist_n, dist_e)/sin_45
        vision["Wall"]["S-E"] = self.get_min(dist_e, self.snake.head.y) / sin_45
        vision["Wall"]["S-W"] = self.get_min(self.snake.head.x, self.snake.head.y) / sin_45
        vision["Wall"]["N-W"] = self.get_min(self.snake.head.x, dist_n) / sin_45
        
        
        
        for key in dirs:
            vision["Tail"][key] = self.boardHeight

        for seg in self.snake.tail.segments:
            #TODO: vezi daca e cu minus daca are rost sa fie pus. poate ar trebui sa pui un if si apoi vezi daca pui in "N" sau in "S" in fct de semn
            if seg.x == self.snake.head.x:
                if seg.y > self.snake.head.y:
                    vision["Tail"]["N"] = self.get_min(vision["Tail"]["N"], (seg.y - self.snake.head.y))
                else:
                    vision["Tail"]["S"] = self.get_min(vision["Tail"]["S"], (self.snake.head.y - seg.y))

            if seg.y == self.snake.head.y:
                if seg.x>self.snake.head.x:
                    vision["Tail"]["E"] = self.get_min(vision["Tail"]["E"], (seg.x - self.snake.head.x))
                else:
                    vision["Tail"]["W"] = self.get_min(vision["Tail"]["W"], (self.snake.head.x - seg.x))

            if abs(seg.y - self.snake.head.y) == abs(seg.x-self.snake.head.x):
                #e pe diag
                dist = math.sqrt( (seg.y - self.snake.head.y)**2 + (seg.x-self.snake.head.x)**2 )
                if seg.y > self.snake.head.y: #N
                    if seg.x > self.snake.head.x: #E
                        vision["Tail"]["N-E"] = self.get_min(vision["Tail"]["N-E"], dist)
                    else: #W
                        vision["Tail"]["N-W"] = self.get_min(vision["Tail"]["N-W"], dist)
                else:#S
                    if seg.x > self.snake.head.x: #E
                        vision["Tail"]["S-E"] = self.get_min(vision["Tail"]["S-E"], dist)
                    else:#W
                        vision["Tail"]["S-W"] = self.get_min(vision["Tail"]["S-W"], dist)
        
      
                
        #TODO: incearca cu incentive 0 daca e negativ
        vision["Fruit"]["N"] = self.sign(self.fruit.y - self.snake.head.y)
        vision["Fruit"]["S"] = self.sign(-(self.fruit.y - self.snake.head.y))
        vision["Fruit"]["W"] = self.sign(self.fruit.x - self.snake.head.x)
        vision["Fruit"]["E"] = self.sign(-(self.fruit.x - self.snake.head.x))
        
        
        
        
        fruit_dist = math.sqrt((self.fruit.y - self.snake.head.y)**2 + (self.fruit.x - self.snake.head.x)**2)
        
        
        
        
        #todo: fa-l sa vada si in spate.
        # direction_rotate = {"UP":   {"LEFT":"W", "UP":"N", "RIGHT": "E", "UP-LEFT": "N-W", "UP-RIGHT": "N-E"},
        #                     "RIGHT":{"LEFT":"N", "UP":"E", "RIGHT": "S", "UP-LEFT": "N-E", "UP-RIGHT": "S-E"}, 
        #                     "DOWN": {"LEFT":"E", "UP":"S", "RIGHT": "W", "UP-LEFT": "S-E", "UP-RIGHT": "S-W"}, 
        #                     "LEFT": {"LEFT":"S", "UP":"W", "RIGHT": "N", "UP-LEFT": "S-W", "UP-RIGHT": "N-W"}
        #                     }

        # simplified_vision = {"Wall":{}, "Tail":{}, "Fruit":{}}
        # simplified_directions = ["LEFT", "UP-LEFT", "UP", "UP-RIGHT", "RIGHT" ]

        # for key in simplified_directions:
        #     rotated_cardianl = direction_rotate[self.snake.direction][key]
        #     simplified_vision["Wall"][key] = vision["Wall"][rotated_cardianl]
        #     simplified_vision["Tail"][key] = vision["Tail"][rotated_cardianl]

        # for key in ["LEFT", "UP", "RIGHT"]:   
        #     simplified_vision["Fruit"][key] = vision["Fruit"][rotated_cardianl]
       # print(simplified_vision)
        
       
        
        self.inp = []
        for key in dirs:
            w = self.normalize_space_sig(vision["Wall"][key], peak = 4)
            self.inp.append(w)
            #self.inp.append(1-simplified_vision["Wall"][key]/self.boardHeight)
        
        for key in dirs:
           # self.inp.append(1-simplified_vision["Tail"][key]/self.boardHeight)
          #  print(vision["Tail"][key])
          #  print(self.normalize_space(vision["Tail"][key], peak = 3))
            t = self.normalize_space_sig(vision["Tail"][key], peak = 4)
            self.inp.append(t)

        for key in ["N","W","E","S"]:#["LEFT", "UP", "RIGHT", "DOWN"]:
            self.inp.append(vision["Fruit"][key])

        hot = {"UP":0, "DOWN":0, "LEFT":0, "RIGHT":0}
        hot[self.snake.direction] = 1
        for key in hot:
            self.inp.append(hot[key])
        self.inp.append(self.snake.size)
        self.inp.append(fruit_dist)

        #print(self.inp)
        #f_x = self.snake.head.x - self.fruit.x
        #f_y = self.snake.head.y - self.fruit.y

        #self.inp.append(1-f_x/self.boardHeight)
       # self.inp.append(1-f_y/self.boardHeight)

######### py
        
        for i in range(0,len(self.inp)):
            self.inp[i] = round(self.inp[i], 6)
        
        rez = self.net.activate(self.inp)
  
        maxval = max(rez)
        final = [i for i in range(len(rez)) if rez[i] == maxval]
        
        i = random.choice(final)

########## c
      #  i = self.net_c.activate(self.inp)       
        self.net.last_neuron_fired = i
        
     
        
        # output_direction_rotate = {
        #     "UP":   ("LEFT", "UP", "RIGHT"),
        #     "RIGHT":("UP", "RIGHT", "DOWN"),
        #     "DOWN": ("RIGHT", "DOWN", "LEFT"),
        #     "LEFT": ("DOWN", "LEFT", "UP")
        # }

        prevdir = self.snake.direction
      #  newdir = output_direction_rotate[self.snake.direction][i]
        newdir = self.snake.directions[i]
        if prevdir == "DOWN" and newdir == "UP":
            newdir = prevdir
        elif prevdir =="UP" and newdir == "DOWN":
            newdir = prevdir
        elif prevdir == "LEFT" and newdir == "RIGHT":
            newdir = prevdir
        elif prevdir =="RIGHT" and newdir =="LEFT":
            newdir = prevdir
        
        self.snake.direction = newdir
        
    def getInputAI3(self):
        
        dirs = ["N", "S", "W", "E", "N-E", "S-E", "S-W", "N-W"]
        vision = {"Wall":{}, "Tail":{}, "Fruit":{}}
        #TODO: make sure min and max values are ok below, due to boardHeight-1 stuff
        sin_45 = 0.7071

        dist_n = self.boardHeight - self.snake.head.y
        dist_e = self.boardWidth - self.snake.head.x
        vision["Wall"]["N"] = dist_n
        vision["Wall"]["S"] = self.snake.head.y
        vision["Wall"]["W"] = self.snake.head.x
        vision["Wall"]["E"] = dist_e
        vision["Wall"]["N-E"] = self.get_min(dist_n, dist_e)/sin_45
        vision["Wall"]["S-E"] = self.get_min(dist_e, self.snake.head.y) / sin_45
        vision["Wall"]["S-W"] = self.get_min(self.snake.head.x, self.snake.head.y) / sin_45
        vision["Wall"]["N-W"] = self.get_min(self.snake.head.x, dist_n) / sin_45
        
        
        
        for key in dirs:
            vision["Tail"][key] = self.boardHeight

        for seg in self.snake.tail.segments:
            if seg.x == self.snake.head.x:
                if seg.y > self.snake.head.x:
                    vision["Tail"]["N"] = self.get_min(vision["Tail"]["N"], (seg.y - self.snake.head.y))
                else:
                    vision["Tail"]["S"] = self.get_min(vision["Tail"]["S"], (self.snake.head.y - seg.y))

            if seg.y == self.snake.head.y:
                if seg.x>self.snake.head.x:
                    vision["Tail"]["E"] = self.get_min(vision["Tail"]["E"], (seg.x - self.snake.head.x))
                else:
                    vision["Tail"]["W"] = self.get_min(vision["Tail"]["W"], (self.snake.head.x - seg.x))

            if abs(seg.y - self.snake.head.y) == abs(seg.x-self.snake.head.x):
                #e pe diag
                dist = math.sqrt( (seg.y - self.snake.head.y)**2 + (seg.x-self.snake.head.x)**2 )
                if seg.y > self.snake.head.y: #N
                    if seg.x > self.snake.head.x: #E
                        vision["Tail"]["N-E"] = self.get_min(vision["Tail"]["N-E"], dist)
                    else: #W
                        vision["Tail"]["N-W"] = self.get_min(vision["Tail"]["N-W"], dist)
                else:#S
                    if seg.x > self.snake.head.x: #E
                        vision["Tail"]["S-E"] = self.get_min(vision["Tail"]["S-E"], dist)
                    else:#W
                        vision["Tail"]["S-W"] = self.get_min(vision["Tail"]["S-W"], dist)
        
      
        vision["Fruit"]["N"] = self.sign(self.fruit.y - self.snake.head.y)
        vision["Fruit"]["S"] = self.sign(-(self.fruit.y - self.snake.head.y))
        vision["Fruit"]["W"] = self.sign(self.fruit.x - self.snake.head.x)
        vision["Fruit"]["E"] = self.sign(-(self.fruit.x - self.snake.head.x))
        
       
        
        
        fruit_dist = math.sqrt((self.fruit.y - self.snake.head.y)**2 + (self.fruit.x - self.snake.head.x)**2)
        
        
        
        direction_rotate = {"UP":   {"LEFT":"W", "UP":"N", "RIGHT": "E", "UP-LEFT": "N-W", "UP-RIGHT": "N-E"},
                            "RIGHT":{"LEFT":"N", "UP":"E", "RIGHT": "S", "UP-LEFT": "N-E", "UP-RIGHT": "S-E"}, 
                            "DOWN": {"LEFT":"E", "UP":"S", "RIGHT": "W", "UP-LEFT": "S-E", "UP-RIGHT": "S-W"}, 
                            "LEFT": {"LEFT":"S", "UP":"W", "RIGHT": "N", "UP-LEFT": "S-W", "UP-RIGHT": "N-W"}
                            }

        simplified_vision = {"Wall":{}, "Tail":{}, "Fruit":{}}
        simplified_directions = ["LEFT", "UP-LEFT", "UP", "UP-RIGHT", "RIGHT" ]

        for key in simplified_directions:
            rotated_cardianl = direction_rotate[self.snake.direction][key]
            simplified_vision["Wall"][key] = vision["Wall"][rotated_cardianl]
            simplified_vision["Tail"][key] = vision["Tail"][rotated_cardianl]

        for key in ["LEFT", "UP", "RIGHT"]:   
            simplified_vision["Fruit"][key] = vision["Fruit"][rotated_cardianl]        
       
        self.inp = []
        for key in simplified_directions:
            w = self.normalize_space(simplified_vision["Wall"][key], peak = 3)
            self.inp.append(2*w)
        
        for key in simplified_directions:
            t = self.normalize_space(simplified_vision["Tail"][key], peak = 3)
            self.inp.append(2*t)
        for key in ["N","W","E","S"]:#["LEFT", "UP", "RIGHT", "DOWN"]:
            self.inp.append(vision["Fruit"][key])
        hot = {"UP":0, "DOWN":0, "LEFT":0, "RIGHT":0}
        hot[self.snake.direction] = 1
        for key in hot:
            self.inp.append(hot[key])
        self.inp.append(self.snake.size)
        self.inp.append(fruit_dist)

        rez = self.net.activate(self.inp)
        
     
        maxval = max(rez)
        final = [i for i in range(len(rez)) if rez[i] == maxval]
        
        i = random.choice(final)
        self.net.last_neuron_fired = i
        
        output_direction_rotate = {
            "UP":   ("LEFT", "UP", "RIGHT"),
            "RIGHT":("UP", "RIGHT", "DOWN"),
            "DOWN": ("RIGHT", "DOWN", "LEFT"),
            "LEFT": ("DOWN", "LEFT", "UP")
        }

        prevdir = self.snake.direction
        newdir = output_direction_rotate[self.snake.direction][i]
        #newdir = self.snake.directions[i]
        # if prevdir == "DOWN" and newdir == "UP":
        #     newdir = prevdir
        # elif prevdir =="UP" and newdir == "DOWN":
        #     newdir = prevdir
        # elif prevdir == "LEFT" and newdir == "RIGHT":
        #     newdir = prevdir
        # elif prevdir =="RIGHT" and newdir =="LEFT":
        #     newdir = prevdir
        
        self.snake.direction = newdir
    
    
    def add_network(self, net):
        network_mob_config = {}
        inputs = ["Wall\ N", "Wall\ S", "Wall\ W", "Wall\ E", "Wall\ NE", "Wall\ SE", "Wall\ SW", "Wall\ NW", 
        "Tail\ N", "Tail\ S", "Tail\ W", "Tail\ E", "Tail\ NE", "Tail\ SE", "Tail\ SW", "Tail\ NW",
        "Fruit\ N", "Fruit\ S", "Fruit\ W", "Fruit\ E", 
        "UP", "DOWN", "LEFT", "RIGHT", 
        "Size", 
        "F\ dist"]

        outputs = ["U", "D", "L", "R"]
        network_mob = NetworkMobject(
            net,
            inputs,
            outputs,
            scale = self.render_scale,
            **network_mob_config
        )
        
        return network_mob

class Explain_Details():
    def __init__(self, board_height, board_width, render_scale, **kwargs):
        self.board_height = board_height
        self.board_width = board_width
        self.render_scale = render_scale

    def render_overlay_lines(self, head_square, head_coord, fruit, tail):
        lines = VGroup()
        x = head_square.get_x()
        y = head_square.get_y()
        h = Square()
        h.set_x(x)
        h.set_y(y)

        lines.add(self.get_wall_lines(h,head_square, head_coord))
        

        return lines

    def get_extra_info(self, t):
        messages = {
            "wall": [1.1,'The snake sees in 8 directions.|In each direction it looks |for the closest wall.'],
            "tail": [1.1,'The snake sees in 8 directions.|In each direction it looks |for the closest tail segment.'],
            "fruit": [1.1,'It also sees the direction the |fruit is in and its distance to it'],
            "directions":[1.1, 'Further, it knows its own |size and the direction it is currently going in']
            }
        
        return messages[t][0], messages[t][1].split("|")
    def play_text_animation(self):
        s,t = self.get_extra_info()
        
        messages = VGroup()
        for i, message in enumerate(t):
            m = '\mathrm{' + message.replace(' ', '\ ') +"}"
            message = Tex(m).scale(2.5*SCALE*s)#.move_to(TOP).shift(SCALE*DOWN*1.25)
            if i == 0:
                message.next_to(self.network_mob, RIGHT, buff=2*SCALE).shift(UP*SCALE*((s+0.5)*((len(t)-1)/2)))
            else:
                message.next_to(messages[i-1], DOWN, buff=0.5*SCALE)
            messages.add(message)

        for m in messages:   
            r = 2
            if len(m.tex_strings[0].split(" "))==1:
                r = 1
            self.scene.play(Write(m, run_time = r))

        self.scene.wait(2)
        fade_group = VGroup()
        fade_group.add(self.boardGroup)
        fade_group.add(messages)
        fade_group.add(self.labels)

        if self.generation != 1529:
            self.scene.play(FadeOut(fade_group, run_time=1,lag_ratio = 0))
        else:
            fade_group.add(self.network_mob)
            self.scene.play(FadeOut(fade_group, run_time=5,lag_ratio = 0))    
    def initial_explanation(self, scene,  net, head_square, head_coord, fruit,tail):
        x = head_square.get_x()
        y = head_square.get_y()
        h = Square()
        h.set_x(x)
        h.set_y(y)
        wall_lines = self.get_wall_lines(h,head_square, head_coord)
        tail_lines = self.get_tail_lines(h,head_coord, tail)
        fruit_lines = self.get_fruit_lines(h,head_coord,fruit)
        net.add_input_labels()
        net.add_output_labels()
        anims = []

        inputs = ["Wall\ N", "Wall\ S", "Wall\ W", "Wall\ E", "Wall\ NE", "Wall\ SE", "Wall\ SW", "Wall\ NW", 
        "Tail\ N", "Tail\ S", "Tail\ W", "Tail\ E", "Tail\ NE", "Tail\ SE", "Tail\ SW", "Tail\ NW",
        "Fruit\ N", "Fruit\ S", "Fruit\ W", "Fruit\ E", 
        "UP", "DOWN", "LEFT", "RIGHT", 
        "Size", 
        "F\ dist"]

                
        for c in inputs[:8]:
            obj = self.wall_lines_dict[c.split("\ ")[1]].copy()
            target = net.input_labels_dict[c]
            anims.append(Transform(obj,target,run_time = 3))
        
        scene.play(AnimationGroup(*anims))

        anims = []
        for c in inputs[8:16]:
            card = c.split("\ ")[1]
            if card in self.tail_lines_dict:
                obj = self.tail_lines_dict[card].copy()
            else:
                obj = self.wall_lines_dict[card].copy()
            target = net.input_labels_dict[c]
            anims.append(Transform(obj,target,run_time = 3))
        scene.play(AnimationGroup(*anims))    

        anims = []
        for i in range(0,4):
            obj = self.fruit_line.copy()
            target = net.input_labels_dict[inputs[i+16]]
            anims.append(Transform(obj,target,run_time = 3))
        scene.play(AnimationGroup(*anims))   
        net.activate_input_labels()

        return anims
    
    def get_wall_lines(self, h, head_square, head_coord):
        wall_lines = VGroup()
        x = head_square.get_x()
        y = head_square.get_y()
        s = self.render_scale

        dist_n = s*(-1+self.board_height - head_coord.y)
        dist_e = s*(-1+self.board_width - head_coord.x)
        dist_s = s * head_coord.y
        dist_w = s * head_coord.x

        coords = {"N": (x, y + dist_n), 
                  "S": (x, y - dist_s), 
                  "W": (x - dist_w, y), 
                  "E": (x + dist_e, y),
                  "NE": (x + min(dist_n,dist_e), y + min(dist_n,dist_e)),
                  "SE": (x + min(dist_s, dist_e), y - min(dist_s, dist_e)),
                  "SW": (x - min(dist_s, dist_w), y - min(dist_s, dist_w)),
                  "NW": (x - min(dist_n, dist_w), y + min(dist_n, dist_w))
                  }

        labels_shift = {"N":RIGHT, "S":RIGHT, "W":UP, "E":UP, "NE":DOWN+RIGHT, "SE":UP+RIGHT, "SW":UP+LEFT, "NW":DOWN+LEFT}
        self.wall_lines_dict = {}
        for cardinal in coords:
            C = Square()
            C.set_x(coords[cardinal][0])
            C.set_y(coords[cardinal][1])
            if cardinal in ["N","W", "S","E"]:
                padding = self.render_scale * 0.2
            else:
                padding = self.render_scale * 0.26
            red_line = Line(h.get_center(), C.get_center(), buff = padding, stroke_color = RED, stroke_width = 15*SCALE, stroke_opacity = 0.5)
            wall_lines.add(red_line)
        
            label = Tex(cardinal)
            label.set_height(0.35*self.render_scale)
            label.move_to(red_line.get_center())
            label.shift(labels_shift[cardinal]*SCALE/2.5)
            wall_lines.add(label)
            self.wall_lines_dict[cardinal] = red_line
        
        return wall_lines

    def get_fruit_lines(self, h, head_coord, fruit):
        fruit_lines = VGroup()
        F = Square()
        F.set_x(fruit.get_x())
        F.set_y(fruit.get_y())
        blue_line = Line(h.get_center(), F.get_center(), buff = self.render_scale * 0.2, stroke_color = BLUE, stroke_width = 15*SCALE, stroke_opacity = 1)
        fruit_lines.add(blue_line)

        label = Tex("F")
        label.set_height(0.35*self.render_scale)
        label.move_to(blue_line.get_center())
        label.shift((RIGHT+DOWN)*SCALE/2.5)
        fruit_lines.add(label)
        self.fruit_line=blue_line

        return fruit_lines

    def get_tail_lines(self, h, head_coord, tail):
        tail_squares = {"N":None,"S":None,"W":None,"E":None,"NE":None,"SE":None,"SW":None,"NW":None}
        tail_lines = VGroup()
        tail_distances = {}
        for key in tail_squares:
            tail_distances[key] = self.board_width

        for seg in tail.segments:
            if seg.x == head_coord.x:
                if seg.y > head_coord.x:
                    if seg.y - head_coord.y < tail_distances["N"]:
                        tail_distances["N"] = seg.y - head_coord.y
                        tail_squares["N"] = seg.square
                else:
                    if head_coord.y - seg.y < tail_distances["S"]:
                        tail_distances["S"] = head_coord.y - seg.y
                        tail_squares["S"] = seg.square
            if seg.y == head_coord.y:
                if seg.x>head_coord.x:
                    if tail_distances["E"] > (seg.x - head_coord.x):
                        tail_distances["E"] = (seg.x - head_coord.x)
                        tail_squares["E"] = seg.square
                else:
                    if tail_distances["W"]> (head_coord.x - seg.x):
                        tail_distances["W"] = (head_coord.x - seg.x)
                        tail_squares["W"] = seg.square

            if abs(seg.y - head_coord.y) == abs(seg.x-head_coord.x):
                #e pe diag
                dist = math.sqrt( (seg.y - head_coord.y)**2 + (seg.x-head_coord.x)**2 )
                if seg.y > head_coord.y: #N
                    if seg.x > head_coord.x: #E
                        if tail_distances["NE"] > dist:
                            tail_distances["NE"] = dist
                            tail_squares["NE"] = seg.square
                    else: #W
                        if (tail_distances["NW"]> dist):
                            tail_distances["NW"] = dist
                            tail_squares["NW"] = seg.square
                else:#S
                    if seg.x > head_coord.x: #E
                        if tail_distances["SE"]> dist:
                            tail_distances["SE"] =  dist
                            tail_squares["SE"] = seg.square
                    else:#W
                        if (tail_distances["SW"]> dist):
                            tail_distances["SW"] = dist
                            tail_squares["SW"] = seg.square

        line_shift = {"N":RIGHT,"S":LEFT,"W":UP,"E":DOWN,"NE":DOWN+RIGHT,"SE":LEFT+DOWN,"SW":LEFT+UP,"NW":UP+RIGHT}
        labels_shift = {"N":RIGHT, "S":RIGHT, "W":UP, "E":UP, "NE":DOWN+RIGHT, "SE":UP+RIGHT, "SW":UP+LEFT, "NW":DOWN+LEFT}
        self.tail_lines_dict = {}
        for cardinal in tail_squares:
            if tail_squares[cardinal] == None:
                continue
            T = tail_squares[cardinal]
            if cardinal in ["N","W", "S","E"]:
                padding = self.render_scale * 0.2
            else:
                padding = self.render_scale * 0.15
            green_line = Line(h.get_center(), T.get_center(), buff = padding, stroke_color = GREEN, stroke_width = 10*SCALE, stroke_opacity = 0.5)
            green_line.shift(line_shift[cardinal]*self.render_scale*0.1)
            tail_lines.add(green_line)
            
            label = Tex(cardinal)
            label.set_height(0.35*self.render_scale)
            label.move_to(green_line.get_center())
            label.shift(labels_shift[cardinal]*SCALE/2.5)
            tail_lines.add(label)
            self.tail_lines_dict[cardinal] = green_line

        return tail_lines



        self.play(edge_animation, layer_animation, *added_anims)

