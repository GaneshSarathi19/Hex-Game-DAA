import pygame as pg
import sys
from os import path
from math import sqrt
from consts import *
from funcs import *
from Button import *

class Game:
    def __init__(self, size):
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((W, H))
        self.clock = pg.time.Clock()
        self.size = size
        self.setTileSize()
        self.state = [[0 for _ in range(self.size)] for __ in range(self.size)]
        self.origin = Point(W/2 - (H/2-50)/sqrt(3), 50)
        self.move = 1
        self.started = False
        self.sound_state = True
        self.bg_color = BLACK

    def loadData(self):
        '''load all the data (images, files, etc)'''
        game_folder = path.dirname(__file__)
        img_folder = path.join(game_folder, 'img')
        doc_folder = path.join(game_folder, 'docs')
        #------------------IMAGES------------------
        # image for tiles (optional)
        #self.tile_img = pg.image.load(path.join(img_folder, TILE_IMG)).convert_alpha()
        #self.tile_img = pg.transform.scale(self.tile_img, (2*self.tile_size+1, int(self.tile_size*sqrt(3))+1))

        self.pause_img = pg.image.load(path.join(img_folder, PAUSE_IMG)).convert_alpha()
        self.back_img = pg.image.load(path.join(img_folder, BACK_IMG)).convert_alpha()

        #------------------SOUNDS--------------------
        self.click_sound = pg.mixer.Sound(path.join(doc_folder, CLICK_SOUND))
        self.click_sound_channel = pg.mixer.Channel(2)

        #-----------------TEXT--------------------
        with open(path.join(doc_folder, RULES), 'r') as f:
            self.rules_text = ''.join(f.readlines())

    def setTileSize(self):
        self.tile_size = 4*(H/2-50)/3/sqrt(3)/(self.size-1)

    def coords(self, r, c):
        '''translates grid coordinates to real coordinates'''
        x = self.origin.x + c*3/2*self.tile_size
        y = self.origin.y + (c+2*r)*self.tile_size*sqrt(3)/2
        return int(x), int(y)

    def tick(self, pos):
        '''is called if mouse pressed, changes the state of the game (only for human player 1)'''
        # Only allow human to move when it's player 1's turn (Green)
        if self.move != 1:
            return
        
        for r in range(self.size):
            for c in range(self.size):
                x, y = self.coords(r, c)
                if inHex(pos, x, y, self.tile_size) and self.state[r][c] != 2\
                                                    and self.state[r][c] != 1:
                    if self.sound_state:
                        self.click_sound_channel.play(self.click_sound)
                    self.state[r][c] = self.move
                    self.move = 3-self.move

    def highlight(self, pos):
        '''highlights the hexagon that is under the mouse'''
        for r in range(self.size):
            for c in range(self.size):
                x, y = self.coords(r, c)
                if self.state[r][c] == 0 and inHex(pos, x, y, self.tile_size):
                    self.state[r][c] = self.move + 2
                elif self.state[r][c] > 2 and not inHex(pos, x, y, self.tile_size):
                    self.state[r][c] = 0

    def showGrid(self):
        '''shows hexagonal grid as well as players moves and destination sides'''
        # draw bounds
        A = (self.origin.x-self.tile_size, self.origin.y-self.tile_size*sqrt(3))
        B = (self.origin.x-self.tile_size/2*(1-3*self.size),\
             self.origin.y+self.tile_size*sqrt(3)/2*(self.size-2)+self.tile_size*sqrt(3)/6)
        C = (self.origin.x-self.tile_size/2*(1-3*self.size), self.origin.y+self.tile_size*sqrt(3)/2*(2*self.size+self.size-1))
        D = (self.origin.x-self.tile_size, self.origin.y+self.tile_size*sqrt(3)*(self.size-1/2)-self.tile_size*sqrt(3)/6)
        M = ((A[0]+B[0])/2, (B[1]+C[1])/2)
        pg.draw.polygon(self.screen, GREEN, [A, B, M])
        pg.draw.polygon(self.screen, GREEN, [C, D, M])
        pg.draw.polygon(self.screen, BLUE, [B, C, M])
        pg.draw.polygon(self.screen, BLUE, [D, A, M])
        for r in range(self.size):
            for c in range(self.size):
                x, y = self.coords(r, c)
                # draw a tile
                #self.screen.blit(self.tile_img, (x-self.tile_size, y-self.tile_size))
                # draw players
                if self.state[r][c] == 1:
                    drawHex(self.screen, GREEN, LIGHTYELLOW, (x, y), self.tile_size)
                elif self.state[r][c] == 2:
                    drawHex(self.screen, BLUE, LIGHTYELLOW, (x, y), self.tile_size)
                elif self.state[r][c] == 3:
                    drawHex(self.screen, LIGHTGREEN, LIGHTYELLOW, (x, y), self.tile_size)
                elif self.state[r][c] == 4:
                    drawHex(self.screen, LIGHTBLUE, LIGHTYELLOW, (x, y), self.tile_size)
                else:
                    drawHex(self.screen, DARKRED, LIGHTYELLOW, (x, y), self.tile_size)