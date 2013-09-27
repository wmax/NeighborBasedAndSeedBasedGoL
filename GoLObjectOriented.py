#!/usr/bin/env python

import time as tm
import pygame as pg
import random as rnd
import os
import sys
from pygame.locals import *
import threading
import threadpool
#import multiprocessing as mp

class NeighbourBasedGoL(object):
    """
    speed   :=  fps
    size    :=  count of rows and cols
    chance  :=  ... to spawn living cells
    zoom    :=  'zoom * x, zoom * y' is the size of a cell in the gui
    glider  :=  decision wether we like to spawn a glider or not
    """
    def __init__(self, size=30, speed=3, chance=0.3, zoom=15, threadCount=1, glider=True, withGui=True):

        self.withGui = withGui
        self.size = size        
        self.gameSpeed = speed  
        self.chance = chance    
        self.factor = zoom      
        self.threadCount = threadCount
        self.spawnGlider = glider
        
        self.pool = threadpool.ThreadPool(threadCount)
        
        alive, dead = 9, 0
        self.alive, self.dead = alive, dead
        
        # create a two-dimensional grid of cells
        # which may or may not be alive depending
        # on a chance(percentage) in the config
        self.grid = [
            [alive if rnd.random() < chance else dead for x in range(self.size)]
            for y in range(self.size)
        ]
        
        # a grid which will be used to count neighbours for every cell
        self.nbs = [[0 for x in range(self.size)] for y in range(self.size)]

        
    def countLivingNeighbours(self, grid, x, y, alive):
        neighbours = 0
        for nx in range(x - 1, x + 2):
            for ny in range(y - 1, y + 2):
                if nx >= 0 and nx < len(grid[y]) and ny >= 0 and ny < len(grid):
                    if grid[ny][nx] == alive:
                        neighbours += 1

        return neighbours - 1 if grid[y][x] == alive else neighbours

    def countAllNeighbours(self, firstRow=0, lastRow=0):
        for x in range(firstRow, self.size if lastRow == 0 else lastRow):
            for y in range(self.size):
                self.nbs[y][x] = self.countLivingNeighbours(self.grid, x, y, self.alive)

                
    def simulateLifeAndDeath(self, firstRow=0, lastRow=0):
        for x in range(firstRow, self.size if lastRow == 0 else lastRow):
            for y in range(self.size):

                if self.grid[y][x] == self.alive:
                    if self.nbs[y][x] < 2 or self.nbs[y][x] > 3:
                        self.grid[y][x] = self.dead

                elif self.nbs[y][x] == 3:
                    self.grid[y][x] = self.alive

    def simulateStep(self):
        tc = self.threadCount

        kwargs = [([], {'firstRow': self.size/tc * x, 'lastRow': self.size/tc * x + self.size/tc}) for x in range(tc)]
      
        [self.pool.putRequest(req) for req in threadpool.makeRequests(self.countAllNeighbours, kwargs)]
        self.pool.wait()
      
        [self.pool.putRequest(req) for req in threadpool.makeRequests(self.simulateLifeAndDeath, kwargs)]
        self.pool.wait()

    def _spawnGlider(self):
        grid = self.grid
        grid[2][1] = self.alive
        grid[2][2] = self.alive
        grid[2][0] = self.alive
        grid[1][2] = self.alive
        grid[0][1] = self.alive

    def drawGui(self, window):
        window.fill(pg.Color(0, 0, 0))

        for x in range(self.size):
            for y in range(self.size):
         #       
                if self.grid[y][x] == self.alive:
         #           print 'X',
         #       print ' ',
         #   print "\n"
                    pg.draw.rect(
                        window,
                        pg.Color(150, 150, 150),
                        pg.Rect(x*self.factor, y*self.factor, self.factor, self.factor)
                    )
    def play(self):
        pg.init()
        clock = pg.time.Clock()
        window = pg.display.set_mode((self.size * self.factor, self.size * self.factor))
        #window = 0
        if self.spawnGlider:
            self._spawnGlider()
        
        while True:

            pg.display.update()

            startS = tm.time()
            self.simulateStep()
            endS = tm.time()

            if self.withGui:
                self.drawGui(window)
            print "simulated step in:\t" + str((endS - startS) * 100) + "ms"
            #tm.sleep(self.gameSpeed)
            # handle events
            for ev in pg.event.get():
                if ev.type == QUIT:
                    pg.quit()
                    sys.exit()

            clock.tick(self.gameSpeed)


class SeedBasedGoL(NeighbourBasedGoL):
    
    """
    increments every neighbor by 1 for every living cell.
    overlapping increments are intended by the way.
    """ 
    def plantSeeds(self, x, y):
        grid = self.grid
        
        grid[y][x] -= 1
        for nx in range(x - 1, x + 2):
            for ny in range(y - 1, y + 2):
                if nx >= 0 and nx < len(grid[y]) and ny >= 0 and ny < len(grid):
                    grid[ny][nx] += 1

    """
    lastRow == 0    tells the script to iterate till the last item was reached
    """
    def simulateStep(self, firstRow=0, lastRow=0):
        grid = self.grid

        for x in range(firstRow, self.size if lastRow == 0 else lastRow):
            for y in range(self.size):
                if grid[y][x] >= self.alive:
                    self.plantSeeds(x, y)

        for x in range(firstRow, self.size if lastRow == 0 else lastRow):
            for y in range(self.size):
                cell = grid[y][x]
                
                if cell >= self.alive:
                    if cell > self.alive + 3 or cell < self.alive + 2:
                        grid[y][x] = self.dead
                    else:
                        grid[y][x] = self.alive

                else:
                    grid[y][x] = self.alive if grid[y][x] == 3 else self.dead
                    
if __name__ == '__main__':
  #  gol = SeedBasedGoL(chance=0.33, speed=5, zoom=3, size=300, withGui=True)
    gol = NeighbourBasedGoL(chance=0.33, speed=0.5, zoom=3, size=300, threadCount=10, withGui=True)
    gol.play()
