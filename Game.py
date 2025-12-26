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

    def checkWin(self):
        '''checks if any of the players have won using Dijkstra's algorithm'''
        from funcs import dijkstra_check_win
        
        # Check if player 2 (Blue) has won - connects left to right
        if dijkstra_check_win(self.state, 2):
            return 2
        
        # Check if player 1 (Green) has won - connects top to bottom
        if dijkstra_check_win(self.state, 1):
            return 1
        
        return 0

    def estimateWinningDistance(self):
        '''
        Uses Dijkstra's algorithm to estimate which player is closer to winning.
        Models the game as a graph where each hex cell is a node.
        Returns tuple (player1_distance, player2_distance) where:
        - player1_distance: minimum moves needed for Green to connect top to bottom
        - player2_distance: minimum moves needed for Blue to connect left to right
        Lower distance means closer to winning.
        '''
        from funcs import estimate_winning_chance
        return estimate_winning_chance(self.state)

    def cpuMove(self):
        '''
        CPU (Player 2, Blue) makes a move using Dijkstra-based logic.
        Strategy: 
        1. If CPU can win immediately, do it
        2. If human is close to winning, prioritize blocking
        3. Otherwise, balance winning and blocking
        '''
        # Find all empty cells
        empty_cells = []
        for r in range(self.size):
            for c in range(self.size):
                if self.state[r][c] == 0:
                    empty_cells.append((r, c))
        
        # If no empty cells, return
        if not empty_cells:
            return
        
        # Get current distances before CPU move using Dijkstra
        human_dist_before, cpu_dist_before = self.estimateWinningDistance()
        
        best_move = None
        best_score = float('-inf')
        
        # Try each empty cell to find the best move
        for r, c in empty_cells:
            # Temporarily place CPU's move here
            self.state[r][c] = 2
            
            # Calculate distances after this move using Dijkstra
            human_dist_after, cpu_dist_after = self.estimateWinningDistance()
            
            # Check if this move makes CPU win immediately
            if cpu_dist_after == 0:
                # CPU wins! This is the best move
                self.state[r][c] = 0  # Undo temporary move
                best_move = (r, c)
                break
            
            # Calculate improvements
            cpu_improvement = cpu_dist_before - cpu_dist_after  # How much closer CPU gets to winning
            human_block = human_dist_after - human_dist_before  # How much further human is from winning
            
            # Determine threat level: how close is human to winning?
            human_threat_level = human_dist_before
            
            # Dynamic scoring based on threat level
            if human_threat_level <= 2:
                # Human is very close to winning - prioritize blocking heavily
                score = (5 * human_block) + cpu_improvement
            elif human_threat_level <= 4:
                # Human is moderately close - balance but favor blocking
                score = (2.5 * human_block) + cpu_improvement
            else:
                # Human is not immediately threatening - balance both strategies
                score = (1.5 * human_block) + cpu_improvement
            
            # Undo the temporary move
            self.state[r][c] = 0
            
            # Keep track of best move
            if score > best_score:
                best_score = score
                best_move = (r, c)
        
        # Make the best move
        if best_move:
            r, c = best_move
            self.state[r][c] = 2
            if self.sound_state:
                self.click_sound_channel.play(self.click_sound)
            self.move = 1  # Switch back to human player

    def shadow(self):
        shadow = pg.Surface((W, H))
        shadow.set_alpha(200)
        self.screen.blit(shadow, (0, 0))

    def startScreen(self):
        '''shows start screen, returns True if the game has started'''
        start = True
        # initializing buttons
        play = Button((W/2, 2*H/3), 80, 'Play')
        rules = Button((W-100, H-75), 50, 'Rules')
        buttons = [play, rules]
        while start:
            # sticking to fps
            self.clock.tick(FPS)
            # --------------------EVENTS---------------------
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    # if exit button is pressed
                    return False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    # if mouse is pressed check button overlapping
                    if play.triggered(channel=self.click_sound_channel,
                                      sound=self.click_sound,
                                      playing=self.sound_state):
                        self.__init__(self.size)
                        self.started = True
                        return True
                    if rules.triggered(channel=self.click_sound_channel,
                                       sound=self.click_sound,
                                       playing=self.sound_state):
                        start = self.rulesScreen()
            # highlight buttons
            for button in buttons:
                button.highlighted()
            # --------------------STUFF-----------------------
            self.screen.fill(self.bg_color)
            textOut(self.screen, 'HEX', 200, ORANGE, (W/2, H/3))
            # show buttons
            for button in buttons:
                button.show(self.screen)
            # double processing
            pg.display.flip()

    def rulesScreen(self):
        '''shows the rules of the game, returns True if the "back" button was hit'''
        start = True
        # initializing buttons
        back = Button((30, 30), 50, img=self.back_img)
        buttons = [back]
        while start:
            # sticking to fps
            self.clock.tick(FPS)
            # --------------------EVENTS---------------------
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    # if exit button is pressed
                    return False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    # if mouse is pressed check button overlapping
                    if back.triggered(channel=self.click_sound_channel,
                                      sound=self.click_sound,
                                      playing=self.sound_state):
                        return True
            # highlight buttons
            for button in buttons:
                button.highlighted()
            # --------------------STUFF-----------------------
            self.screen.fill(self.bg_color)
            textOut(self.screen, 'Rules', 100, ORANGE, (W/2, H/3))
            textOutMultiline(self.screen, self.rules_text, 30, WHITE, (W/2, H/3))
            # show buttons
            for button in buttons:
                button.show(self.screen)
            # double processing
            pg.display.flip()

    def pauseScreen(self):
        '''shows pause screen, returns True if the game was resumed'''
        start = True
        # initializing buttons
        resume = Button((W/2, H/3), 80, 'Resume', col=ORANGE)
        home = Button((W/2, H/2), 50, 'Home', col=WHITE)
        buttons = [home, resume]
        while start:
            # sticking to fps
            self.clock.tick(FPS)
            # --------------------EVENTS---------------------
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    # if exit button is pressed
                    return False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    # if mouse is pressed check button overlapping
                    if home.triggered(channel=self.click_sound_channel,
                                      sound=self.click_sound,
                                      playing=self.sound_state):
                        self.started = False
                        return True
                    if resume.triggered(channel=self.click_sound_channel,
                                        sound=self.click_sound,
                                        playing=self.sound_state):
                        return True
            # highlight buttons
            for button in buttons:
                button.highlighted()
            # --------------------STUFF-----------------------
            # show buttons
            self.screen.fill(self.bg_color)
            self.showGrid()
            self.shadow()
            for button in buttons:
                button.show(self.screen)
            # double processing
            pg.display.flip()

    def GOScreen(self, winner):
        '''shows game over screen, returns True if any key is hit'''
        go = True
        home = Button((W/2, 2*H/3), 50, 'Home', col=WHITE)
        while go:
            # sticking to fps
            self.clock.tick(FPS)
            # --------------------EVENTS---------------------
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    # if exit button is pressed
                    return False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    # if mouse is pressed check button overlapping
                    if home.triggered(channel=self.click_sound_channel,
                                      sound=self.click_sound,
                                      playing=self.sound_state):
                        self.started = False
                        return True
            home.highlighted()
            # --------------------STUFF-----------------------
            self.screen.fill(self.bg_color)
            self.showGrid()
            self.shadow()
            textOut(self.screen, 'GAME OVER', 80, ORANGE, (W/2, H/3))
            if winner == 2:
                textOut(self.screen, 'Blue won', 60, BLUE, (W/2, H/2))
            else:
                textOut(self.screen, 'Green won', 60, GREEN, (W/2, H/2))
            home.show(self.screen)
            # double processing
            pg.display.flip()
