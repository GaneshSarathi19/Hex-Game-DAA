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
        self.screen = pg.display.set_mode((W, H))
        self.clock = pg.time.Clock()
        self.size = size
        self.setTileSize()
        self.state = [[0 for _ in range(self.size)] for __ in range(self.size)]
        self.origin = Point(W/2 - (H/2-50)/sqrt(3), 50)
        self.move = 1
        self.started = False
        self.bg_color = BLACK
        self.ai_mode = 'Greedy'  # Default AI mode: 'Greedy', 'D&C', or 'DP'

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
        CPU (Player 2, Blue) makes a move using the selected AI strategy.
        '''
        if self.ai_mode == 'Greedy':
            self._cpuMoveGreedy()
        elif self.ai_mode == 'D&C':
            self._cpuMoveDivideConquer()
        elif self.ai_mode == 'DP':
            self._cpuMoveDynamicProgramming()
        else:  # Default fallback to Greedy
            self._cpuMoveGreedy()
    
    def _cpuMoveGreedy(self):
        '''
        Greedy AI: Uses Dijkstra's algorithm (a greedy algorithm) to find optimal moves.
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
            self.move = 1  # Switch back to human player
    
    def _dcScoreCell(self, r, c, colStart, colEnd):
        """
        SIMPLE scoring: Favor HORIZONTAL neighbors, discourage VERTICAL.
        """
        if self.state[r][c] != 0:
            return float('-inf')
        
        # Count neighbors by direction
        horizontal_neighbors = 0  # Left/right connections (good!)
        vertical_neighbors = 0    # Up/down connections (bad for horizontal path!)
        
        for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                if self.state[nr][nc] == 2:
                    if dc != 0:
                        # Column changes = horizontal neighbor
                        horizontal_neighbors += 1
                    else:
                        # Only row changes = vertical neighbor
                        vertical_neighbors += 1
        
        # Scoring: Horizontal good, vertical bad
        score = horizontal_neighbors * 10.0  # Reward horizontal
        score -= vertical_neighbors * 5.0     # Penalize vertical
        
        # If no neighbors, prefer center columns
        if horizontal_neighbors == 0 and vertical_neighbors == 0:
            center_col = self.size // 2
            score = 5.0 - abs(c - center_col) * 0.1
        
        return score


        #---------main D&C logic------------
    
    def _cpuMoveDivideConquer(self):
        """
        Main entry point.
        """
        result = self._dcSolve(0, self.size - 1, 0, self.size - 1)
        r, c, _ = result
        if r is not None and c is not None and self.state[r][c] == 0:
            self.state[r][c] = 2
            self.move = 1
            return
        
        for ri in range(self.size):
            for cj in range(self.size):
                if self.state[ri][cj] == 0:
                    self.state[ri][cj] = 2
                    self.move = 1
                    return
    
    def _cpuMoveDynamicProgramming(self):
        '''
        Dynamic Programming AI: Placeholder for future implementation.
        Currently does nothing.
        '''
        # TODO: Implement Dynamic Programming algorithm
        pass

    def shadow(self):
        shadow = pg.Surface((W, H))
        shadow.set_alpha(200)
        self.screen.blit(shadow, (0, 0))

    def startScreen(self):
        '''Home screen: title, strategy options only, Start and Rules. Fits 600x600.'''
        start = True
        selected_ai_mode = 'Greedy'

        # Layout: fit 600x600 with even spacing and margins
        margin = 50
        title_y = 70
        # Strategy options in a single row (centered, balanced)
        grid_center_x = W / 2
        strategy_y = 220
        btn_size = 42
        btn_spacing = 140  # Spacing between buttons

        greedy_btn = Button((grid_center_x - btn_spacing, strategy_y), btn_size, 'Greedy', col=GREEN)
        dnc_btn = Button((grid_center_x, strategy_y), btn_size, 'D&C', col=LIGHTBLUE)
        dp_btn = Button((grid_center_x + btn_spacing, strategy_y), btn_size, 'DP', col=YELLOW)
        mode_buttons = [greedy_btn, dnc_btn, dp_btn]

        play_y = 400
        rules_y = 480
        play = Button((grid_center_x, play_y), 52, 'Start Game', col=GREEN)
        rules = Button((grid_center_x, rules_y), 44, 'Rules', col=WHITE)
        buttons = [play, rules] + mode_buttons

        while start:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if greedy_btn.triggered():
                        selected_ai_mode = 'Greedy'
                    elif dnc_btn.triggered():
                        selected_ai_mode = 'D&C'
                    elif dp_btn.triggered():
                        selected_ai_mode = 'DP'
                    if play.triggered():
                        self.__init__(self.size)
                        self.ai_mode = selected_ai_mode
                        self.started = True
                        return True
                    if rules.triggered():
                        start = self.rulesScreen()

            for button in buttons:
                button.highlighted()

            self.screen.fill(self.bg_color)

            # Title only
            textOut(self.screen, 'HEX GAME', 72, ORANGE, (grid_center_x, title_y))

            # Optional: thin line under title for separation
            pg.draw.line(self.screen, (70, 70, 70), (margin, title_y + 50), (W - margin, title_y + 50), 1)

            # Selection indicator: draw border on selected strategy button area
            strategy_pos = {
                'Greedy': (grid_center_x - btn_spacing, strategy_y),
                'D&C': (grid_center_x, strategy_y),
                'DP': (grid_center_x + btn_spacing, strategy_y),
            }
            strategy_colors = {'Greedy': GREEN, 'D&C': LIGHTBLUE, 'DP': YELLOW}
            sx, sy = strategy_pos[selected_ai_mode]
            pg.draw.rect(self.screen, strategy_colors[selected_ai_mode],
                         (sx - 62, sy - 22, 124, 44), 2)

            for button in buttons:
                button.show(self.screen)

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
                    if back.triggered():
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
                    if home.triggered():
                        self.started = False
                        return True
                    if resume.triggered():
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
                    if home.triggered():
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
