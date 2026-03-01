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
        elif self.ai_mode == 'Backtracking':
            self._cpuMoveBacktracking()
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

    def _cpuMoveBacktracking(self):
        '''
        FULL logical backtracking for CPU (player 2, Blue).
        CPU connects LEFT → RIGHT, human TOP → BOTTOM.

        For each candidate CPU move M:
            For every human reply H:
                CPU must have at least one counter C (adjacent to H)
                such that, after C, the human has NO immediate winning move.
            If ANY human reply lacks such a CPU counter, M is rejected.

        If we find a move M that survives all human replies, we play it
        immediately. If none exist, fall back to a simple delaying move.
        '''
        board = self.state
        n = self.size

        def neighbors(r, c):
            for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n:
                    yield nr, nc

        def human_wins():
            return self.checkWin() == 1

        def cpu_wins():
            return self.checkWin() == 2

        def cpu_connectivity_score(local_board):
            """
            Approximate LEFT→RIGHT connectivity for CPU (player 2).
            Lower score is better: smaller remaining horizontal gap.
            """
            cols = [c for r in range(n) for c in range(n) if local_board[r][c] == 2]
            if not cols:
                return n - 1
            min_col = min(cols)
            max_col = max(cols)
            span = max_col - min_col
            gap = (n - 1) - span
            return gap

        def human_immediate_wins():
            """
            True if human has any immediate winning move from
            the CURRENT board by playing on an empty cell adjacent
            to at least one human stone.
            """
            candidates = set()
            for r in range(n):
                for c in range(n):
                    if board[r][c] == 1:
                        for nr, nc in neighbors(r, c):
                            if board[nr][nc] == 0:
                                candidates.add((nr, nc))
            if not candidates:
                return False

            for r, c in candidates:
                if board[r][c] != 0:
                    continue
                board[r][c] = 1
                if human_wins():
                    board[r][c] = 0
                    return True
                board[r][c] = 0
            return False
        def get_player_groups(player):
            """Return list of connected components (groups) for given player."""
            visited = [[False] * n for _ in range(n)]
            groups = []
            for r in range(n):
                for c in range(n):
                    if board[r][c] == player and not visited[r][c]:
                        stack = [(r, c)]
                        visited[r][c] = True
                        group = [(r, c)]
                        while stack:
                            cr, cc = stack.pop()
                            for nr, nc in neighbors(cr, cc):
                                if board[nr][nc] == player and not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    stack.append((nr, nc))
                                    group.append((nr, nc))
                        groups.append(group)
            return groups

        def detectVirtualConnections(player):
            """
            Lightweight virtual connection detector.

            For the given player:
            - Find connected groups of stones.
            - For each pair of groups, and for human also group+goal-edge,
              find empty carrier cells that are adjacent to both structures.
            - A virtual connection exists for that pair if there are >= 2
              distinct carrier cells.

            Returns: list of lists of carrier cells [(r, c), ...].
            """
            groups = get_player_groups(player)
            if len(groups) < 1:
                return []

            empties = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 0]
            connections = []

            # Group–group virtual connections
            for i in range(len(groups)):
                g1 = set(groups[i])
                for j in range(i + 1, len(groups)):
                    g2 = set(groups[j])
                    carriers = []
                    for er, ec in empties:
                        touches_g1 = False
                        touches_g2 = False
                        for nr, nc in neighbors(er, ec):
                            if (nr, nc) in g1:
                                touches_g1 = True
                            if (nr, nc) in g2:
                                touches_g2 = True
                            if touches_g1 and touches_g2:
                                carriers.append((er, ec))
                                break
                    if len(carriers) >= 2:
                        connections.append(carriers)

            # For human (player 1), also consider group + goal edge (TOP/BOTTOM)
            if player == 1:
                for g in groups:
                    gset = set(g)

                    # Top edge: empties in row 0 adjacent to group
                    top_carriers = []
                    for er, ec in empties:
                        if er != 0:
                            continue
                        if any((nr, nc) in gset for nr, nc in neighbors(er, ec)):
                            top_carriers.append((er, ec))
                    if len(top_carriers) >= 2:
                        connections.append(top_carriers)

                    # Bottom edge: empties in last row adjacent to group
                    bottom_carriers = []
                    for er, ec in empties:
                        if er != n - 1:
                            continue
                        if any((nr, nc) in gset for nr, nc in neighbors(er, ec)):
                            bottom_carriers.append((er, ec))
                    if len(bottom_carriers) >= 2:
                        connections.append(bottom_carriers)

            return connections
            
        def cpu_has_response_after(h_r, h_c):
            """
            Given human has just played at (h_r, h_c),
            check whether CPU has ANY counter move C adjacent to H
            such that, after C, the human has NO immediate winning move.
            """
            responses = []
            for nr, nc in neighbors(h_r, h_c):
                if board[nr][nc] == 0:
                    responses.append((nr, nc))

            if not responses:
                return False

            # Connectivity baseline after H is already on board
            base_conn = cpu_connectivity_score(board)

            for cr, cc in responses:
                if board[cr][cc] != 0:
                    continue
                board[cr][cc] = 2

                # Reject counters that worsen CPU LEFT→RIGHT connectivity
                if cpu_connectivity_score(board) > base_conn:
                    board[cr][cc] = 0
                    continue

                # Accept if after C the human has no immediate winning move
                if not human_immediate_wins():
                    board[cr][cc] = 0
                    return True

                board[cr][cc] = 0

            return False

        # STEP 1: Generate CPU candidate moves
        candidates = set()
        for r in range(n):
            for c in range(n):
                if board[r][c] == 2:
                    for nr, nc in neighbors(r, c):
                        if board[nr][nc] == 0:
                            candidates.add((nr, nc))

        if not candidates:
            # No neighbors: try center
            center_r, center_c = n // 2, n // 2
            if board[center_r][center_c] == 0:
                candidates.add((center_r, center_c))
            else:
                for r in range(n):
                    for c in range(n):
                        if board[r][c] == 0:
                            candidates.add((r, c))
                            break
                    if candidates:
                        break

        if not candidates:
            return

        candidates = list(candidates)

        # Baseline CPU LEFT→RIGHT connectivity before any move
        base_conn_before = cpu_connectivity_score(board)

        # STEP 2: Try each candidate M with full logical backtracking
        best_safe_move = None
        best_safe_improvement = -1  # higher is better

        for mr, mc in candidates:
            if board[mr][mc] != 0:
                continue

            # CPU plays M
            board[mr][mc] = 2

            # Enforce connectivity invariant: do not worsen LEFT→RIGHT potential
            conn_after_M = cpu_connectivity_score(board)
            if conn_after_M > base_conn_before:
                board[mr][mc] = 0
                continue

            # Immediate CPU win
            if cpu_wins():
                self.move = 1
                return



    def _dcSolve(self, rowStart, rowEnd, colStart, colEnd):
        """
        Simple D&C - unchanged.
        """
        height = rowEnd - rowStart + 1
        width = colEnd - colStart + 1
        
        # BASE CASE
        if width <= 4 or height <= 4:
            best_r, best_c, best_score = None, None, float('-inf')
            for r in range(rowStart, rowEnd + 1):
                for c in range(colStart, colEnd + 1):
                    if self.state[r][c] == 0:
                        score = self._dcScoreCell(r, c, colStart, colEnd)
                        if score > best_score:
                            best_score = score
                            best_r, best_c = r, c
            return (best_r, best_c, best_score)
        
        # DIVIDE
        mid_col = colStart + width // 2
        
        if mid_col <= colStart or mid_col > colEnd:
            best_r, best_c, best_score = None, None, float('-inf')
            for r in range(rowStart, rowEnd + 1):
                for c in range(colStart, colEnd + 1):
                    if self.state[r][c] == 0:
                        score = self._dcScoreCell(r, c, colStart, colEnd)
                        if score > best_score:
                            best_score = score
                            best_r, best_c = r, c
            return (best_r, best_c, best_score)
        
        # CONQUER
        left_result = self._dcSolve(rowStart, rowEnd, colStart, mid_col - 1)
        right_result = self._dcSolve(rowStart, rowEnd, mid_col, colEnd)
        
        r_left, c_left, score_left = left_result
        r_right, c_right, score_right = right_result
        
        # COMBINE
        has_left = any(self.state[r][c] == 2 
                    for r in range(self.size) 
                    for c in range(colStart, min(mid_col, self.size)))
        
        has_right = any(self.state[r][c] == 2 
                        for r in range(self.size) 
                        for c in range(max(mid_col, 0), min(colEnd + 1, self.size)))
        
        if not has_left and not has_right:
            return right_result if score_right > score_left else left_result
        elif has_left and not has_right:
            return right_result if r_right is not None else left_result
        elif has_right and not has_left:
            return left_result if r_left is not None else right_result
        else:
            return right_result if score_right > score_left else left_result


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
        Pure DP Table Solution using bidirectional shortest path.
        
        DP Tables:
        1. dp_left[r][c] = minimum cost to reach (r,c) from LEFT edge
        2. dp_right[r][c] = minimum cost from (r,c) to RIGHT edge
        3. Combine: Pick empty cell that minimizes total path length
        
        Complexity: O(n²)
        '''
        n = self.size
        INF = 10 ** 9
        
        
        # DP TABLE 1: dp_left[r][c] - Distance from LEFT to (r,c)
        
        
        dp_left = [[INF] * n for _ in range(n)]
        
        # Base case: LEFT edge (column 0)
        for r in range(n):
            if self.state[r][0] == 2:
                dp_left[r][0] = 0  # Our stone - free
            elif self.state[r][0] == 0:
                dp_left[r][0] = 1  # Empty - costs 1
            else:
                dp_left[r][0] = INF  # Opponent - blocked
        
        # Fill table column by column (left to right)
        for c in range(1, n):
            for r in range(n):
                # Skip opponent cells
                if self.state[r][c] == 1:
                    continue
                
                # Cost of current cell
                if self.state[r][c] == 2:
                    cell_cost = 0
                else:
                    cell_cost = 1
                
                # Find minimum cost from previous positions
                # Hexagonal neighbors that could lead to (r,c)
                min_prev = INF
                for dr, dc in [(-1, -1), (-1, 0), (0, -1), (1, -1), (1, 0)]:
                    pr = r + dr
                    pc = c + dc
                    if 0 <= pr < n and 0 <= pc < n:
                        min_prev = min(min_prev, dp_left[pr][pc])
                
                # DP recurrence
                if min_prev < INF:
                    dp_left[r][c] = min_prev + cell_cost
        
        
        # DP TABLE 2: dp_right[r][c] - Distance from (r,c) to RIGHT
        
        
        dp_right = [[INF] * n for _ in range(n)]
        
        # Base case: RIGHT edge (column n-1)
        for r in range(n):
            if self.state[r][n-1] == 2:
                dp_right[r][n-1] = 0
            elif self.state[r][n-1] == 0:
                dp_right[r][n-1] = 1
            else:
                dp_right[r][n-1] = INF
        
        # Fill table column by column (right to left)
        for c in range(n - 2, -1, -1):
            for r in range(n):
                # Skip opponent cells
                if self.state[r][c] == 1:
                    continue
                
                # Cost of current cell
                if self.state[r][c] == 2:
                    cell_cost = 0
                else:
                    cell_cost = 1
                
                # Find minimum cost to next positions
                # Hexagonal neighbors that (r,c) can reach
                min_next = INF
                for dr, dc in [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, 1)]:
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        min_next = min(min_next, dp_right[nr][nc])
                
                # DP recurrence
                if min_next < INF:
                    dp_right[r][c] = min_next + cell_cost
        
        
        # DECISION: Find best empty cell to play
        
        
        best_r, best_c = None, None
        best_total = INF
        
        for r in range(n):
            for c in range(n):
                if self.state[r][c] != 0:
                    continue  # Not empty
                
                
                # Path = (LEFT → this cell) + (this cell → RIGHT)
                
                
                # Best distance TO this cell (from left neighbors)
                dist_to = INF
                for dr, dc in [(-1, -1), (-1, 0), (0, -1), (1, -1), (1, 0)]:
                    pr = r + dr
                    pc = c + dc
                    if 0 <= pr < n and 0 <= pc < n:
                        dist_to = min(dist_to, dp_left[pr][pc])
                
                # Special case: if this is in column 0
                if c == 0:
                    dist_to = 0
                
                # Best distance FROM this cell (to right neighbors)
                dist_from = INF
                for dr, dc in [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, 1)]:
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        dist_from = min(dist_from, dp_right[nr][nc])
                
                # Special case: if this is in column n-1
                if c == n - 1:
                    dist_from = 0
                
                # Total path length if we play here (this cell = 0 cost)
                total = dist_to + 0 + dist_from
                
                # Track minimum
                if total < best_total:
                    best_total = total
                    best_r, best_c = r, c
        
        # Make the move
        if best_r is not None:
            self.state[best_r][best_c] = 2
            self.move = 1
            return
        
        # Fallback: no valid move found (shouldn't happen)
        for r in range(n):
            for c in range(n):
                if self.state[r][c] == 0:
                    self.state[r][c] = 2
                    self.move = 1
                    return

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
        # Strategy options (centered, balanced)
        grid_center_x = W / 2
        strategy_y = 220
        strategy_y2 = 290
        btn_size = 42
        btn_spacing = 140  # Spacing between buttons

        greedy_btn = Button((grid_center_x - btn_spacing, strategy_y), btn_size, 'Greedy', col=GREEN)
        dnc_btn = Button((grid_center_x, strategy_y), btn_size, 'D&C', col=LIGHTBLUE)
        dp_btn = Button((grid_center_x + btn_spacing, strategy_y), btn_size, 'DP', col=YELLOW)
        backtracking_btn = Button((grid_center_x, strategy_y2), btn_size, 'Backtracking', col=ORANGE)
        mode_buttons = [greedy_btn, dnc_btn, dp_btn, backtracking_btn]

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
                    elif backtracking_btn.triggered():
                        selected_ai_mode = 'Backtracking'
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
                'Backtracking': (grid_center_x, strategy_y2),
            }
            strategy_colors = {'Greedy': GREEN, 'D&C': LIGHTBLUE, 'DP': YELLOW, 'Backtracking': ORANGE}
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
