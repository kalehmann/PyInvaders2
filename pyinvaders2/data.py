#PyInvaders2 (c) 2014 by Karsten Lehmann

###############################################################################
#                                                                             #
#    This file is a part of PyInvaders2                                       #
#                                                                             #
#    PyInvaders2 is free software you can redistribute it and/or modify       #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    any later version.                                                       #
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
This module contains objects for the game PyInvaders2
"""

import pygame
import os
import random
import copy
import sys
import gametools as gt

__author__ = "Karsten Lehmann"
__copyright__ = "Copyright 2014, Karsten Lehmann"
__license__ = "GPLv3"
__version__ = "2.0"
__maintainer__ = "Karsten Lehmann"

class Spaceship(pygame.sprite.Sprite):
    """A spaceship in a game, which can move and fire missiles

    The spaceship moves on the x-axis in a given range, and fires missiles to
    the invaders

    Attributes: surface        -> the surface of the spaceship (SurfaceSequence)
                live           -> number of lives, (integer, >= 0)
                position       -> current position in game and render position
                _shoot_counter -> time to wait between shots
    """
    surface = None

    def __init__(self, position):
        self.size = 64, 64
        if not Spaceship.surface:
            #create surface
            Spaceship.surface = gt.SurfaceSequence()
            Spaceship.surface.open_images("textures/spaceship.png", (64, 64))
        self.rect = pygame.Rect(0, 0, *self.size)
        self.rect.center = position
        self.shoot_delay = gt.Delay(0)

    def move(self, area):
        """Check if the key A,D,LEFT,RIGHT were pressed and moves the
           Spaceship """
        pressed_keys = pygame.key.get_pressed()
        keys_left = pygame.K_a, pygame.K_LEFT
        keys_right = pygame.K_d, pygame.K_RIGHT
        for key in keys_left:
            if pressed_keys[key] and self.rect.center[0] > area[0]:
                self.rect[0] -= 9
        for key in keys_right:
            if pressed_keys[key] and self.rect.center[0] < area[1]:
                self.rect[0] += 9

    def shoot(self):
        """check if spacebar is pressed and fires a missile"""
        pressed_keys = pygame.key.get_pressed()
        if self.shoot_delay.handle():
            if pressed_keys[pygame.K_SPACE]:
                self.shoot_delay = gt.Delay(10)
                return True

    def get_data(self):
        """Move the spaceship and fire missiles"""
        return self.surface.handle(), self.rect

class Invader(object):
    """the evil invaders try to destroy the earth

       Attributes: current_surface -> There is on single SurfaceSequence for
                                      all invaders, this attribute handles the
                                      single invaders
                   position        -> the current position in the game
                   _shoot_counter  -> time to wait between shots
    """
    surface = None

    def __init__(self, position):
        self.size = 32, 32
        if not Invader.surface:
            Invader.surface = gt.SurfaceSequence()
            Invader.surface.open_images("textures/invader.png", self.size)
        self.rect = pygame.Rect(0, 0, *self.size)
        self.rect.center = position
        self.surface = Invader.surface.private_handler()
        self.surface.set_random()
        self.shoot_delay = gt.Delay(random.randint(0, 250))

    def move(self, ymove, direction):
        """move the invaders

           Args: ymove     -> distance to move on the y-axis
                 direction -> direction to move on the x-axis
        """
        if direction == 'LEFT':
            self.rect[0] -= 2
        elif direction == 'RIGHT':
            self.rect[0] += 2
        self.rect[1] += ymove

    def shoot(self, iv_list):
        """fires a missile

           checks if there is a chance of friendly fire(a missile hit an other
           invader) and if not fire a missile
        """
        if self.shoot_delay.handle():
            friendly_fire = False
            for invader in iv_list:
                if (self.rect.center[0] - 32 <= invader.rect.center[0] <=
                    self.rect.center[0] + 32 and
                    self.rect.center[1] < invader.rect.center[1]):
                    friendly_fire = True
            if not friendly_fire:
                self.shoot_delay = gt.Delay(random.randint(300, 450))
                return True

    def get_data(self):
        """return surface and rect"""
        return self.surface.handle(), self.rect

class Missile(object):
    """A simple object, that moves until it hits something

       Attributes: surface_up and surface_down
                             -> the missiles got also on single SurfaceSequence,
                                but every one has an different "current_surface"
                   direction -> direction where to move, spaceship-missiles
                                move upwards and invader-missiles downwards
    """
    surface_up = None
    surface_down = None

    def __init__(self, position, direction):
        self.size = 32, 32
        self.rect = pygame.Rect(0, 0, *self.size)
        self.rect.center = position
        self.direction = direction
        if not Missile.surface_up:
            Missile.surface_up = gt.SurfaceSequence()
            Missile.surface_up.open_images("textures/missile.png", self.size)
            Missile.surface_down = gt.SurfaceSequence()
            Missile.surface_down.open_images("textures/missile.png", self.size,
                                             (False, True))
        if direction == 'up':
            self.surface = Missile.surface_up.private_handler()
        elif direction == 'down':
            self.surface = Missile.surface_down.private_handler()

    def move(self):
        """changes the position of the missile"""
        if self.direction == 'up':
            self.rect[1] -= 18
        elif self.direction == 'down':
            self.rect[1] += 9

    def get_data(self):
        """returns: surface and rect"""
        return self.surface.handle(), self.rect

class Explosion(object):
    """a simple fireball"""
    surface = None
    def __init__(self, position):
        self.size = 64, 64
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = position
        self.current_surface = -1
        if not Explosion.surface:
            Explosion.surface = gt.SurfaceSequence()
            Explosion.surface.open_images("textures/explosion.png", (64, 64))

    def finished(self):
        """check if the explosion is gone"""
        if self.current_surface == self.surface.surface_number - 2:
            return True

    def get_data(self):
        """render the explosion"""
        self.current_surface += 1
        return self.surface.handle(self.current_surface), self.rect


class StaticObject(object):
    """a image/font, which is displayed at a static position"""
    def __init__(self, position):
        self.surface = None
        self.position = position
        self.type = None

    def add_images(self, image_path, scaling):
        """add an image"""
        self.type = 'image'
        self.surface = gt.SurfaceSequence()
        self.surface.open_images(image_path, scaling)

    def add_font(self, font, size, text, colour):
        """add a text"""
        self.type = 'font'
        font = pygame.font.Font(font, size)
        self.surface = font.render(text, 8, colour)

    def get_data(self):
        """render the font/image"""
        if self.type == 'image':
            return self.surface.handle(), self.position
        elif self.type == 'font':
            return self.surface, self.position

class Level(object):
    """Contains Informations about invader positions in each level

       Attributes: number            -> number of the level
                   invader_positions -> list with the starting positions
                                        of the invaders in this level
    """
    def __init__(self, file_path):
        self.invader_positions = []
        level_file = open(file_path, 'r')
        for line, line_number in zip(level_file, range(5)):
            for letter, number in zip(line, range(19)):
                if letter == '#':
                    position = number * 32 + 32, line_number * 32 + 32
                    self.invader_positions.append(position)
        level_file.close()

    def get_invaders(self):
        """add the invaders of the level to the game"""
        invaders = []
        for position in self.invader_positions:
            invaders.append(Invader(position))
        return invaders

class LevelList(list):
    """A list with all levels"""
    def __init__(self, path):
        list.__init__(self)
        filelist = os.listdir(path)
        filelist.sort()
        for level_file in filelist:
            self.append(Level(path + level_file))
            print "Found levelfie at %s"% path +level_file
        if self == []:
            gt.messagebox("No level-file found!")
            sys.exit()

    def exist_level(self, level):
        """if necessary change to next level"""
        if level == len(self):
            gt.messagebox("You've reached the max. level!")
        else:
            return True

class LiveBar(object):
    """Displays the number of lives remaining"""
    surface = None
    def __init__(self, position):
        self.lives = 6
        self.position = position
        self.left_pos = self.position[0] + 192, self.position[1]
        if not LiveBar.surface:
            LiveBar.surface = gt.SurfaceSequence()
            LiveBar.surface.open_images("textures/livebar.png", (32, 32))

    def deduct(self):
        """delete one livepoint and check if the spaceship is still alive"""
        self.lives -= 1
        if self.lives == 0:
            return True

    def get_data(self):
        """render the livebar"""
        live_surface = self.surface.handle()
        surface = pygame.surface.Surface((192, 32), pygame.SRCALPHA)
        for i in range(self.lives):
            surface.blit(live_surface, (160 - 32 * i, 0))
        return surface, self.position

class Score(object):
    """a simple font, in the top-left corner of the window """
    def __init__(self, font, position):
        self.font = pygame.font.Font(font, 36)
        self.score = 0
        self.position = position

    def add_score(self):
        """add a score point"""
        self.score += 1

    def get_data(self):
        """render the score-font"""
        surface = self.font.render(str(self.score), 8, (200, 100, 0))
        return surface, self.position

class Tracker(object):
    """Moves semi transparent surface over the screen"""
    def __init__(self, surface, position, destination):
        self.surface = copy.copy(surface)
        self.surface = self.surface.convert_alpha()
        alpha_array = pygame.surfarray.array_alpha(self.surface)
        pygame.surfarray.pixels_alpha(self.surface)[:] = alpha_array * 0.5
        self.position = list(position)
        self.destination = destination
        self.speed = (self.position[0] - float(self.destination[0])) / 15, \
                     (self.position[1] - float(self.destination[1])) / 15
        self.wait = gt.Delay(15)

    def dest_reached(self):
        """check if the tracker reached his destination"""
        if self.wait.handle():
            return True

    def get_data(self):
        """Render the surface"""
        self.position[0] -= self.speed[0]
        self.position[1] -= self.speed[1]
        return self.surface, self.position

class Highscore(object):
    """A list with the five highest scores, reached in this game"""
    def __init__(self):
        self.scores = []
        self.read_highscores()

    def check_highscore(self, score):
        """Check if the score exceeds any highscore and replace it"""
        if not score in self.scores:
            for value in self.scores:
                if score > value:
                    self.scores.append(score)
                    self.scores.sort()
                    self.scores.reverse()
                    del self.scores[5]
                    self.write_highscores()
                    break

    def write_highscores(self):
        """write all highscores to the file .score """
        score_file = open(".score", "w")
        for score in self.scores:
            score_file.write("%d " % score + "\n")
        score_file.close()

    def read_highscores(self):
        """read all highscores from the file .score"""
        self.scores = []
        if os.path.isfile(".score"):
            score_file = open(".score", "r")
            for line in score_file:
                if len(self.scores) == 5:
                    break
                self.scores.append(int(line))
            score_file.close()
            self.scores.sort()
            self.scores.reverse()
            if len(self.scores) != 5:
                self.scores = [0, 0, 0, 0, 0]
                self.write_highscores()
                gt.messagebox("Corrupted .score file!")
        else:
            self.scores = [0, 0, 0, 0, 0]
            self.write_highscores()
