#!/usr/bin/env python

###############################################################################
# This files is a part of PyInvaders                                          #
#                                                                             #
#    PyInvaders is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    any later version.                                      		          #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
###############################################################################

"""
PyInvaders is a simple, python-based clone of the popular game Space Invaders
"""

import sys
import pygame
import random
import copy
import os
import surfacesequence as surfseq

__author__ = "Karsten Lehmann"
__copyright__ = "Copyright 2014, Karsten Lehmann"
__license__ = "GPLv3"
__version__ = "2.0"
__maintainer__ = "Karsten Lehmann"

pygame.mixer.pre_init()
pygame.init()

SCREEN_SIZE = 640, 480
SCREEN = pygame.display.set_mode(SCREEN_SIZE)
ScreenIcon = pygame.image.load("icon.png").convert_alpha()
ScreenIcon = pygame.transform.scale(ScreenIcon, (32,32))
pygame.display.set_icon(ScreenIcon)
pygame.display.set_caption("PyInvader")
GameFont = "textures/Game_font.ttf"
GAME_SOUND = True
FPS = 30
fpsClock = pygame.time.Clock()


class spaceship(object):
    """A spaceship in a game, which can move and shot

    The spaceship moves on the x-axis in a given range, and fires shots to
    the invaders

    Attributes: surface        -> the surface of the spaceship (surfacesequence)
                life           -> number of lifes, (integer, >= 0)
                position       -> current position in game and render position
                _shoot_counter -> time to wait between shots
    """
    def __init__(self):
        self.surface = surfseq.surfacesequence()
        self.surface.open_images("textures/spaceship.png", (64, 64)) 
        self.life = 6
        self.position = [320, 400]   
        self._shoot_counter = 0

    def move(self):
        """Check if the key A,D,LEFT,RIGHT were pressed and moves the
           Spaceship """
        pressed_keys = pygame.key.get_pressed()
        keys_left = pygame.K_a, pygame.K_LEFT
        keys_right = pygame.K_d, pygame.K_RIGHT
        for key in keys_left:
            if pressed_keys[key] and self.position[0] > 10:
                self.position[0] -= 7
        for key in keys_right:
            if pressed_keys[key] and self.position[0] < 566:        
                self.position[0] += 7

    def shoot(self):
        """check if spacebar is pressed and fires a missile"""
        pressed_keys = pygame.key.get_pressed()
        if self._shoot_counter == 0:
            if pressed_keys[pygame.K_SPACE]:
                shot_position = self.position[0] + 16, self.position[1] - 35
                missile_list.shoot(shot_position, 'up') 
                self._shoot_counter = 10
        else:
            self._shoot_counter -= 1      

    def handle(self):
        if self.life >= 0:
            self.shoot()
            self.move()
            SCREEN.blit(self.surface.handle(), self.position)

    def hit(self):
        """delete one lifepoint and check if the ship is still alive"""
        self.life -= 1
        if self.life == 0:
            explosion_list.add_explosion(self.position)


class invader(object):
    """the evil invaders try to destroy the earth

       Attributes: current_surface -> There is on single surfacesequence for
                                      all invaders, this attribute handles the 
                                      single invaders
                   position        -> the renderposition and current position
                                      in the game
                   _shoot_counter  -> time to wait between shots
    """
    surface = surfseq.surfacesequence()
    surface.open_images("textures/invader.png", (32, 32))

    def __init__(self, position):
        self.current_surface = random.randint(0, self.surface.surface_number)
        self.position = list(position)
        self._shot_counter = random.randint(0,250)
        
    def move(self, ymove, direction):
        if direction == 'LEFT':
            self.position[0] -= 2
        elif direction == 'RIGHT':
            self.position[0] += 2
        self.position[1] += ymove

    def shot(self):
        """fires a missile 
          
           checks if there is a chance of firendly fire(a missile hit an other 
           invader) and if not fire a missile
        """
        if not self._shot_counter:
            position = self.position[0], self.position[1] + 32
            friendly_fire = False
            self_range = range(self.position[0] - 32, self.position[0] + 32)
            for invader in invader_list:
                if (invader.position[0] in self_range and 
                    invader.position[1] > self.position[1]):
                    friendly_fire = True
            if not friendly_fire:   
                missile_list.shoot(position, 'down')
            self._shot_counter = random.randint(150,250)
        else:
            self._shot_counter -= 1 

    def handle(self, ymove, direction):
        self.move(ymove, direction)
        self.shot()
        if not self.current_surface == self.surface.surface_number:
            self.current_surface += 1
        else:
            self.current_surface = 1
        SCREEN.blit(self.surface.handle(self.current_surface - 1), 
                    self.position)

    def hit(self):
        explosion_list.add_explosion(self.position)


class missile(object):
    """A simple object, that moves until it hits something

       Attributes: surface_up and surface_down
                             -> the missiles got also on single surfacesequence,
                                but every one has an different "current_surface"
                   direction -> direction where to move, spaceship-missiles 
                                move upwards and invader-missiles downwards
                   
    """
    surface_up = surfseq.surfacesequence()
    surface_up.open_images("textures/missile.png", (32, 32))
    surface_down = surfseq.surfacesequence()
    surface_down.open_images("textures/missile.png", (32, 32), (False, True))

    def __init__(self, position, direction):
        self.position = position
        self.direction = direction
        self.current_surface = 1

    def handle(self):
        if not self.current_surface == self.surface_up.surface_number:
            self.current_surface += 1
        else:
            self.current_surface = 1

        if self.direction == 'up':
            self.position[1] -= 15
            SCREEN.blit(self.surface_up.handle(self.current_surface - 1), 
                        self.position)
        elif self.direction == 'down':
            self.position[1] += 9
            SCREEN.blit(self.surface_down.handle(self.current_surface - 1), 
                        self.position)


class explosion(object):
    """a simple fireball"""
    surface = surfseq.surfacesequence()
    surface.open_images("textures/explosion.png", (64, 64))
    def __init__(self, position):
        self._current_surface = 0
        self.position = position

    def handle(self):
        SCREEN.blit(self.surface.handle(self._current_surface), self.position)
        self._current_surface += 1


class background(object):

    def __init__(self):
        self.surface = surfseq.surfacesequence() 
        self.surface.open_images("textures/background.png", (640, 480))

    def handle(self):
        SCREEN.blit(self.surface.handle(), (0, 0))


class life_bar(object):

    def __init__(self):
        self.position = 540, 20
        self.surface = surfseq.surfacesequence()
        self.surface.open_images("textures/lifebar.png", (32, 32))

    def handle(self):
        for i in range(player.life):
            position = self.position[0] - (i * 32), self.position[1]
            SCREEN.blit(self.surface.handle(), position)


class score(object):
    """a simple font, in the top-left corner of the window """
    def __init__(self):
        self.font = pygame.font.Font(GameFont, 36)
        self.score = 0

    def add_score(self):
        self.score += 1
 
    def handle(self):
        surface = self.font.render(str(self.score),8,(200,100,0))
        SCREEN.blit(surface, (600, 20))

class level(object):
    """Contains Informations about invaderpositions in each level 

       Attributes: number            -> number of the level
                   invader_positions -> list with the starting positions
                                        of the invaders in this level                     
    """
    def __init__(self, file_path):
        self.invader_positions = []
        level_file = open(file_path,'r')
        for line, linenumber in zip(level_file, range(5)):
            for letter, number in zip(line, range(21)):
                if letter =='#':
                    position = number * 32 + 32,linenumber * 32 + 16
                    self.invader_positions.append(position) 
        level_file.close()

    def set_invaders(self):
        for position in self.invader_positions:
            invader_list.append(invader(position))


class missile_list(list):
    """A list with all missies""" 
    def shoot(self, position, direction):
        self.append(missile(list(position), direction)) 

    def handle(self):
        """Check if a missile
               - is out off the window
               - hit's an invader
               - hit's the player            
        """
        player_radius = (range(player.position[0], player.position[0] + 64),
                         range(player.position[1], player.position[1] + 64))
        for shot in self:
            shot.handle()
            '''missile is out off the window'''
            if not 10 < shot.position[1] < 470:
                self.remove(shot)
            '''missile hit invader'''
            for invader in invader_list:
                invader_radius = (range(invader.position[0], 
                                  invader.position[0] + 32),
                                  range(invader.position[1], 
                                  invader.position[1] + 32))
                if (shot.position[0] in invader_radius[0] and
                    shot.position[1] in invader_radius[1]):
                    self.remove(shot)
                    invader.hit()
                    score.add_score()
                    invader_list.remove(invader)
            '''missile hit player'''
            if (shot.position[0] in player_radius[0] and 
                shot.position[1] in player_radius[1]):
                self.remove(shot)
                player.hit()


class level_list(list):
    """A list with all levels"""
    def __init__(self, path):
        filelist = os.listdir(path)
        filelist.sort()
        for level_file in filelist:
            self.append(level(path + level_file))
            print("Found levelfie at %s"% path +level_file)

    def handle(self):
        if invader_list == []:
            global current_level
            if current_level == len(self) + 1:
                print("Reached max. level, EXIT")
                sys.exit()
            self[current_level -1].set_invaders()
            current_level += 1


class invader_list(list):
    """A list with all invaders

       Attributes: move_direction -> the current direction to move
                   move_counter   -> time to wait before the invaders move one
                                     row down
    """
    def __init__(self):
        self.move_direction = random.choice(('LEFT', 'RIGHT'))
        self.move_counter = 100

    def handle(self):
        direction = self.move_direction
        if self.move_counter:
            self.move_counter -= 1
            down_move = 0
        else: 
            self.move_counter = 100
            down_move = 32
        for invader in self:
            invader.handle(down_move, direction)
            if invader.position[0] <= 10:
                self.move_direction = 'RIGHT'
            elif invader.position[0] >= 598:
                self.move_direction = 'LEFT'


class explosion_list(list):
    """A list of all explosions"""
    def add_explosion(self, position):
        self.append(explosion(position))              

    def handle(self):
        for explosion in self:
            explosion.handle()
            if (explosion._current_surface == 
                explosion.surface.surface_number -1):
                self.remove(explosion)


def check_for_exit(events):
    for event in events:
        if event.type == pygame.QUIT:
            print('EXIT')
            sys.exit()

def game(): 
    global invader_list, current_level, level_list, missile_list, player, \
           background, explosion_list, score, life_bar
    current_level = 1
    invader_list = invader_list()
    level_list = level_list('levels/')
    missile_list = missile_list()
    explosion_list = explosion_list()
    score = score()
    life_bar = life_bar()
    player = spaceship()
    background = background() 
    while True:
        EVENT_LIST = pygame.event.get()
        check_for_exit(EVENT_LIST)

        background.handle()        
        level_list.handle()
        missile_list.handle()
        invader_list.handle() 
        explosion_list.handle()          
        player.handle()

        score.handle()
        life_bar.handle() 

        pygame.display.update()
        fpsClock.tick(FPS)


if __name__ == "__main__":
    game() 

