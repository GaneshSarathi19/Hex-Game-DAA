import pygame as pg
from math import sqrt, hypot
from collections import deque
import heapq

class Point:
    def __init__(self, *pos):
        if len(pos) == 1:
            self.x, self.y = pos[0]
            self.X, self.Y = list(map(int, pos[0]))
        else:
            self.x, self.y = pos
            self.X, self.Y = list(map(int, pos))

    def dist(self, other):
        return hypot(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __str__(self):
        return '[x:{x}, y:{y}]'.format(x=self.x, y=self.y)

    def __iter__(self):
        '''for unpacking'''
        return (x for x in (self.x, self.y))


from consts import *

def triangleS(A, B, C):
    '''retrun the surface of a triangle'''
    a = C.dist(B)
    b = A.dist(C)
    c = A.dist(B)
    p = (a+b+c)/2
    return sqrt(p*(p-a)*(p-b)*(p-c))

def inHex(pos, x, y, a):
    '''checks if a point is in a hexagon'''
    P = Point(pos)
    points = [(x+a, y), (x+a/2, y+a*sqrt(3)/2),
              (x-a/2, y+a*sqrt(3)/2), (x-a, y),
              (x-a/2, y-a*sqrt(3)/2), (x+a/2, y-a*sqrt(3)/2)]
    points = list(map(Point, points))
    sum = 0
    for i in range(-1, 5):
        sum += triangleS(points[i], points[i+1], P)
    S = a*a*3*sqrt(3)/2
    return abs(S-sum) < EPS

def inRect(pos, x, y, w, h):
    '''checks if a point is in a rectangle'''
    return (pos.x > x and pos.x < x + w and\
           pos.y > y and pos.y < y + h)

def drawHex(surface, colIn, colOut, pos, a):
    x, y = pos
    points = [(x-a/2, y-a*sqrt(3)/2),
              (x+a/2, y-a*sqrt(3)/2),
              (x+a, y),
              (x+a/2, y+a*sqrt(3)/2),
              (x-a/2, y+a*sqrt(3)/2),
              (x-a, y)]
    pg.draw.polygon(surface, colIn, points)
    pg.draw.polygon(surface, colOut, points, 4)

def inBounds(v, w, h):
    return (v.X >= 0 and v.X < h and\
            v.Y >= 0 and v.Y < w)

def textRect(txt, size):
    font = pg.font.SysFont('Verdana', size)
    text = font.render(txt, False, BLACK)
    return text.get_rect()

def textOut(surface, data, size, col, pos):
    txt = str(data)
    font = pg.font.SysFont('Verdana', size)
    text = font.render(txt, False, col)
    rect = text.get_rect(center=pos)
    surface.blit(text, rect)

def textOutMultiline(surface, txt, size, col, pos):
    font = pg.font.SysFont('Verdana', size)
    for y, line in enumerate(txt.split('\n')):
        text = font.render(line, False, col)
        rect = text.get_rect(center=(pos[0], pos[1]+(y+5)*size))
        surface.blit(text, rect)

def dijkstra_check_win(grid, player):
    '''
    Uses Dijkstra's algorithm to check if a player has won.
    A player wins if they have a path from one side to the opposite side using only their pieces.
    Returns True if player has won, False otherwise.
    '''
    size = len(grid)
    INF = float('inf')
    
    # Initialize distance matrix
    dist = [[INF for _ in range(size)] for __ in range(size)]
    
    # Priority queue: (distance, row, col)
    pq = []
    
    if player == 1:  # Green: connect top (row 0) to bottom (row size-1)
        # Initialize all cells in top row that belong to player
        for col in range(size):
            if grid[0][col] == player:
                dist[0][col] = 0
                heapq.heappush(pq, (0, 0, col))
    else:  # Player 2 (Blue): connect left (col 0) to right (col size-1)
        # Initialize all cells in left column that belong to player
        for row in range(size):
            if grid[row][0] == player:
                dist[row][0] = 0
                heapq.heappush(pq, (0, row, 0))
    
    # Dijkstra's algorithm - only traverse through player's own pieces
    while pq:
        d, r, c = heapq.heappop(pq)
        
        # If we've already found a better path, skip
        if d > dist[r][c]:
            continue
        
        # Check if we've reached the target side
        if player == 1 and r == size - 1:  # Green reached bottom
            return True
        elif player == 2 and c == size - 1:  # Blue reached right
            return True
        
        # Explore neighbors (hexagonal adjacency) - only through player's pieces
        for move in moves:
            nr, nc = r + move.X, c + move.Y
            
            if not (0 <= nr < size and 0 <= nc < size):
                continue
            
            # Only traverse through player's own pieces (weight 0)
            if grid[nr][nc] == player:
                weight = 0
            else:
                continue  # Skip opponent's cells and empty cells
            
            # Relax edge
            new_dist = dist[r][c] + weight
            if new_dist < dist[nr][nc]:
                dist[nr][nc] = new_dist
                heapq.heappush(pq, (new_dist, nr, nc))
    
    # No path found to target side
    return False