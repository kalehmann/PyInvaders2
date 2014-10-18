#!/usr/bin/env python

#PyInvaders2 (c) 2014 by Karsten Lehmann

###############################################################################
#                                                                             #
#    This file is a part of PyInvaders2                                       #
#                                                                             #
#    PyInvaders2 is free software: you can redistribute it and/or modify      #
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
import Tkinter
import tkMessageBox
import keys
import surfacesequence as surfseq

__author__ = "Karsten Lehmann"
__copyright__ = "Copyright 2014, Karsten Lehmann"
__license__ = "GPLv3"
__version__ = "2.0"
__maintainer__ = "Karsten Lehmann"


#Global Properties:
#INVADER_LIST     List-object, handles and manages all invaders
#LEVEL_LIST       List-object, handles and manages all levels
#MISSILE_LIST     List-object, handles and manages all missiles
#EXPLOSION_LIST   List-object, handles and manages all explosions
#HIGHSCORE        List-object, contains five highest scores
#GAME_OVER        Boolean-property, prepares for leaving
#BREAK_GAME       Boolean-property, if true the game will be leaved
#BREAK_DELAY      Integer-property, if zero then return to the main menu
#CURRENT_LEVEL    Integer-property, current level
#EVENT_LIST       List with all pygame.events
#PLAYER           Spaceship-object
#SCORE            Integer-property, current score
#LIVE_BAR         Livebar-object, shows current lives

def messagebox(message):
    """Opens a simple window with the message"""
    window = Tkinter.Tk()
    window.wm_withdraw()
    tkMessageBox.showinfo("Info", message)
    window.destroy()

def load_sound(sound_file):
    """checks whether the file exists and loads it"""
    if os.path.isfile(sound_file):
        return pygame.mixer.Sound(sound_file)
    else:
        messagebox("Error , couldn't load %s" % sound_file)
        sys.exit()

class Button(object):
    """A simple button for menus, use it with ButtonGroup"""
    def __init__(self, position):
        self.position = position
        self.type = None
        self.active_surface = None
        self.passive_surface = None

    def add_text(self, font, text, colour_passive, colour_active):
        """Add a text to this button

           Args: font          -> path to an font-file               (string)
                 text          -> text on the button                 (string)
                 colour_passive -> colour of the button in idle mode   (tuple)
                 colour_active  -> colour of the button, when selected (tuple)
        """
        self.type = 'text'
        self.active_surface = font.render(text, 8, colour_active)
        self.passive_surface = font.render(text, 8, colour_passive)

    def add_images(self, active_image, passive_image):
        """Add a surface to this buttons

           Args: active_image -> image of the button, when selected (string)
                 passive_image -> image of the button in idle mode   (string)
        """
        self.type = 'image'
        self.active_surface = surfseq.SurfaceSequence()
        self.active_surface.open_images(active_image)
        self.passive_surface = surfseq.SurfaceSequence()
        self.passive_surface.open_images(passive_image)

    def handle(self, state):
        """Render the current state of the button"""
        if state == 'passive':
            if self.type == 'text':
                SCREEN.blit(self.passive_surface, self.position)
            elif self.type == 'image':
                SCREEN.blit(self.passive_surface.handle(), self.position)
        elif state == 'active':
            if self.type == 'text':
                SCREEN.blit(self.active_surface, self.position)
            elif self.type == 'image':
                SCREEN.blit(self.active_surface.handle(), self.position)


class ButtonGroup(object):
    """Handle buttons in an menu

       You can add buttons to a buttongroup an switch between them with keys.
       If return_key get pressed, handle() will return the current button number
    """

    def __init__(self):
        self.current_button = 1
        self.button_list = []
        self.down_key = keys.KeyCheck(pygame.K_DOWN, 10)
        self.up_key = keys.KeyCheck(pygame.K_UP, 10)

    def add_buttons(self, *buttons):
        """add buttons to this group"""
        for button in buttons:
            self.button_list.append(button)

    def get_current_button(self):
        """get and handle keyboard inputs"""
        if self.down_key.check(EVENT_LIST):
            if GAME_SOUND:
                KLICK_SOUND.play()
            if self.current_button == len(self.button_list):
                self.current_button = 1
            else:
                self.current_button += 1
        elif self.up_key.check(EVENT_LIST):
            if GAME_SOUND:
                KLICK_SOUND.play()
            if self.current_button == 1:
                self.current_button = len(self.button_list)
            else:
                self.current_button -= 1

    def handle(self):
        """manage the buttons, returns button-number, when return gets
           pressed"""
        self.get_current_button()

        for button in self.button_list:
            if self.button_list.index(button) == self.current_button - 1:
                button.handle('active')
            else:
                button.handle('passive')

        if keys.check_for_keydown(pygame.K_RETURN, EVENT_LIST):
            if GAME_SOUND:
                KLICK_SOUND.play()
            return self.current_button

class Delay(object):
    """A simple object, that helps to manage time in loops

       Args: ticks -> number of rounds in the loop
    """
    def __init__(self, ticks):
        self.ticks = ticks

    def handle(self):
        """Wait the number of ticks and then return True"""
        if not self.ticks:
            return True
        else:
            self.ticks -= 1
            return False

class Spaceship(object):
    """A spaceship in a game, which can move and shot

    The spaceship moves on the x-axis in a given range, and fires missiles to
    the invaders

    Attributes: surface        -> the surface of the spaceship (SurfaceSequence)
                live           -> number of lives, (integer, >= 0)
                position       -> current position in game and render position
                _shoot_counter -> time to wait between shots
    """
    def __init__(self):
        self.surface = surfseq.SurfaceSequence()
        self.surface.open_images("textures/spaceship.png", (64, 64))
        self.live = 6
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
                MISSILE_LIST.shoot(shot_position, 'up')
                self._shoot_counter = 10
        else:
            self._shoot_counter -= 1

    def handle(self):
        """Move the spaceship and fire missiles"""
        if self.live > 0:
            self.shoot()
            self.move()
            SCREEN.blit(self.surface.handle(), self.position)

    def hit(self):
        """delete one livepoint and check if the ship is still alive"""
        self.live -= 1
        if self.live == 0:
            EXPLOSION_LIST.add_explosion(self.position)
            global GAME_OVER
            GAME_OVER = True


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
        if not Invader.surface:
            Invader.surface = surfseq.SurfaceSequence()
            Invader.surface.open_images("textures/invader.png", (32, 32))
        self.current_surface = random.randint(0, self.surface.surface_number)
        self.position = list(position)
        self._shot_counter = random.randint(0, 250)

    def move(self, ymove, direction):
        """move the invaders

           Args: ymove     -> distance to move on the y-axis
                 direction -> direction to move on the x-axis
        """
        if direction == 'LEFT':
            self.position[0] -= 2
        elif direction == 'RIGHT':
            self.position[0] += 2
        self.position[1] += ymove

    def shot(self):
        """fires a missile

           checks if there is a chance of friendly fire(a missile hit an other
           invader) and if not fire a missile
        """
        if self._shot_counter == 0:
            position = self.position[0], self.position[1] + 32
            friendly_fire = False
            self_range = range(self.position[0] - 32, self.position[0] + 32)
            for invader in INVADER_LIST:
                if (invader.position[0] in self_range and
                    invader.position[1] > self.position[1]):
                    friendly_fire = True
            if not friendly_fire:
                MISSILE_LIST.shoot(position, 'down')
            self._shot_counter = random.randint(150, 250)
        elif self._shot_counter > 0:
            self._shot_counter -= 1

    def handle(self, ymove, direction):
        """move the invader, fires missiles and render it"""
        self.move(ymove, direction)
        self.shot()
        if not self.current_surface == self.surface.surface_number:
            self.current_surface += 1
        else:
            self.current_surface = 1
        SCREEN.blit(self.surface.handle(self.current_surface - 1),
                    self.position)

    def hit(self):
        """Add an explosion to the current position of the invader"""
        EXPLOSION_LIST.add_explosion(self.position)


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
        self.position = position
        self.direction = direction
        self.current_surface = 1
        if not Missile.surface_up:
            Missile.surface_up = surfseq.SurfaceSequence()
            Missile.surface_up.open_images("textures/missile.png", (32, 32))
            Missile.surface_down = surfseq.SurfaceSequence()
            Missile.surface_down.open_images("textures/missile.png", (32, 32),
                                             (False, True))
    def move(self):
        """move the missile"""
        if self.direction == 'up':
            self.position[1] -= 15
            SCREEN.blit(self.surface_up.handle(self.current_surface - 1),
                        self.position)
        elif self.direction == 'down':
            self.position[1] += 9
            SCREEN.blit(self.surface_down.handle(self.current_surface - 1),
                        self.position)


    def handle(self):
        """Render and move the missile """
        if not self.current_surface == self.surface_up.surface_number:
            self.current_surface += 1
        else:
            self.current_surface = 1
        self.move()

class Explosion(object):
    """a simple fireball"""
    surface = None
    def __init__(self, position):
        self.current_surface = 0
        self.position = position
        if not Explosion.surface:
            Explosion.surface = surfseq.SurfaceSequence()
            Explosion.surface.open_images("textures/explosion.png", (64, 64))

    def handle(self):
        """render the explosion"""
        SCREEN.blit(self.surface.handle(self.current_surface), self.position)
        self.current_surface += 1


class StaticObject(object):
    """a image/font, which is displayed at a static position"""
    def __init__(self, position):
        self.surface = None
        self.position = position
        self.type = None

    def add_images(self, image_path, scaling):
        """add an image"""
        self.type = 'image'
        self.surface = surfseq.SurfaceSequence()
        self.surface.open_images(image_path, scaling)

    def add_font(self, font, size, text, colour):
        """add a text"""
        self.type = 'font'
        font = pygame.font.Font(font, size)
        self.surface = font.render(text, 8, colour)

    def handle(self):
        """render the font/image"""
        if self.type == 'image':
            SCREEN.blit(self.surface.handle(), self.position)
        elif self.type == 'font':
            SCREEN.blit(self.surface, self.position)


class LiveBar(object):
    """Displays the number of lives remaining"""
    def __init__(self):
        self.position = 540, 20
        self.surface = surfseq.SurfaceSequence()
        self.surface.open_images("textures/livebar.png", (32, 32))
        self._current_surface = 0

    def handle(self):
        """render the livebar"""
        surface = self.surface.handle()
        for i in range(PLAYER.live):
            position = self.position[0] - (i * 32), self.position[1]
            SCREEN.blit(surface, position)


class Score(object):
    """a simple font, in the top-left corner of the window """
    def __init__(self):
        self.font = pygame.font.Font(GAME_FONT, 36)
        self.score = 0

    def add_score(self):
        """add a score point"""
        self.score += 1

    def handle(self):
        """render the score-font"""
        surface = self.font.render(str(self.score), 8, (200, 100, 0))
        SCREEN.blit(surface, (600, 20))

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
            for letter, number in zip(line, range(21)):
                if letter == '#':
                    position = number * 32 + 32, line_number * 32 + 16
                    self.invader_positions.append(position)
        level_file.close()

    def set_invaders(self):
        """add the invaders of the level to the game"""
        for position in self.invader_positions:
            INVADER_LIST.append(Invader(position))


class MissileList(list):
    """A list with all missiles"""
    def shoot(self, position, direction):
        """fire a missile"""
        if GAME_SOUND:
            SHOT_SOUND.play()
        self.append(Missile(list(position), direction))

    def handle(self):
        """Check if a missile
               - is out off the window
               - hit's an invader
               - hit's the player
        """
        player_radius = (range(PLAYER.position[0] - 8, PLAYER.position[0] + 72),
                         range(PLAYER.position[1] - 8, PLAYER.position[1] + 72))
        for shot in self:
            shot.handle()
            if not 0 < shot.position[1] < 480:
                #missile is out off the window
                self.remove(shot)

            elif (shot.position[0] in player_radius[0] and
                  shot.position[1] in player_radius[1]):
                #missile hit player'''
                self.remove(shot)
                PLAYER.hit()

            else:
                #missile hit invader'''
                for invader in INVADER_LIST:
                    invader_radius = (range(invader.position[0] - 8,
                                      invader.position[0] + 40),
                                      range(invader.position[1] - 8,
                                      invader.position[1] + 40))
                    if (shot.position[0] in invader_radius[0] and
                        shot.position[1] in invader_radius[1]):
                        self.remove(shot)
                        invader.hit()
                        SCORE.add_score()
                        INVADER_LIST.remove(invader)
                        break

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
            messagebox("No level-file found!")
            sys.exit()

    def handle(self):
        """if necessary change to next level"""
        if INVADER_LIST == []:
            global CURRENT_LEVEL
            if CURRENT_LEVEL == len(self) + 1:
                print "Reached max. level, EXIT"
                sys.exit()
            self[CURRENT_LEVEL -1].set_invaders()
            CURRENT_LEVEL += 1


class InvaderList(list):
    """A list with all invaders

       Attributes: move_direction -> the current direction to move
                   move_counter   -> time to wait before the invaders move one
                                     row down
    """
    def __init__(self):
        list.__init__(self)
        self.move_direction = random.choice(('LEFT', 'RIGHT'))
        self.move_counter = 100

    def handle(self):
        """move the invaders"""
        global BREAK_GAME, NEXT
        direction = self.move_direction
        if self.move_counter:
            self.move_counter -= 1
            down_move = 0
        else:
            self.move_counter = 100
            down_move = 32

        player_radius = (range(PLAYER.position[0] - 8, PLAYER.position[0] + 72),
                         range(PLAYER.position[1] - 8, PLAYER.position[1] + 72))
        for invader in self:
            invader.handle(down_move, direction)
            if invader.position[0] <= 10:
                self.move_direction = 'RIGHT'
            elif invader.position[0] >= 598:
                self.move_direction = 'LEFT'
            if invader.position[1] >= 460:
                BREAK_GAME = True
                NEXT = 'gameover'
            if (invader.position[0] in player_radius[0] and
                invader.position[1] in player_radius[1]):
                BREAK_GAME = True
                NEXT = 'gameover'

class ExplosionList(list):
    """A list of all explosions"""
    def add_explosion(self, position):
        """add an explosion"""
        if GAME_SOUND:
            EXPLOSION_SOUND.play()
        self.append(Explosion(position))

    def handle(self):
        """render all explosions"""
        for explosion in self:
            explosion.handle()
            if (explosion.current_surface ==
                explosion.surface.surface_number -1):
                self.remove(explosion)

def check_highscore(score):
    """Check if the score exceeds any highscore and replace it"""
    global HIGHSCORE
    if not score in HIGHSCORE:
        for value in HIGHSCORE:
            if score > value:
                HIGHSCORE.append(score)
                HIGHSCORE.sort()
                HIGHSCORE.reverse()
                del HIGHSCORE[5]
                write_highscores()
                break

def write_highscores():
    """write all highscores to the file .score """
    score_file = open(".score", "w")
    for score in HIGHSCORE:
        score_file.write("%d " % score + "\n")
    score_file.close()

def read_highscores():
    """read all highscores from the file .score"""
    global HIGHSCORE
    HIGHSCORE = []
    if os.path.isfile(".score"):
        score_file = open(".score", "r")
        for line in score_file:
            if len(HIGHSCORE) == 5:
                break
            HIGHSCORE.append(int(line))
        score_file.close()
        HIGHSCORE.sort()
        HIGHSCORE.reverse()
        if len(HIGHSCORE) != 5:
            messagebox("Corrupted .score file!")
            HIGHSCORE = [0, 0, 0, 0, 0]
            write_highscores()
    else:
        HIGHSCORE = [0, 0, 0, 0, 0]
        write_highscores()

def check_for_exit(events):
    """test if the window gets closed and exit the game"""
    for event in events:
        if event.type == pygame.QUIT:
            print 'EXIT'
            sys.exit()

def check_for_gameover():
    """test if the var GAME_OVER is set to True and leave the game"""
    global BREAK_GAME, NEXT
    if GAME_OVER:
        if BREAK_DELAY.handle():
            NEXT = 'gameover'
            BREAK_GAME = True


def paused():
    """pause the game and give the choice to continue or leave"""
    global NEXT, BREAK_GAME, EVENT_LIST
    screenshot = copy.copy(pygame.display.get_surface())
    paused_surface = StaticObject((0, 0))
    paused_surface.add_images('textures/paused.png', (640, 480))
    font_paused = StaticObject((160, 20))
    font_paused.add_font(GAME_FONT, 100, 'paused', (255, 150, 0))
    font_continue = StaticObject((40, 150))
    font_continue.add_font(GAME_FONT, 35, 'Press return to continue, ' \
                           'escape to quit', (255, 150, 0))

    while True:
        EVENT_LIST = pygame.event.get()
        check_for_exit(EVENT_LIST)

        if keys.check_for_keydown(pygame.K_RETURN, EVENT_LIST):
            if GAME_SOUND:
                KLICK_SOUND.play()
            break
        elif keys.check_for_keydown(pygame.K_ESCAPE, EVENT_LIST):
            if GAME_SOUND:
                KLICK_SOUND.play()
            BREAK_GAME = True
            NEXT = 'menu'
            break
        SCREEN.blit(screenshot, (0, 0))
        paused_surface.handle()
        font_paused.handle()
        font_continue.handle()

        pygame.display.update()
        FPS_CLOCK.tick(FPS)



def game():
    """The main game"""
    global INVADER_LIST, CURRENT_LEVEL, LEVEL_LIST, MISSILE_LIST, PLAYER, \
           EXPLOSION_LIST, SCORE, LIVE_BAR, GAME_OVER, BREAK_GAME, \
           BREAK_DELAY, EVENT_LIST
    GAME_OVER = False
    BREAK_GAME = False
    BREAK_DELAY = Delay(40)
    CURRENT_LEVEL = 1
    INVADER_LIST = InvaderList()
    LEVEL_LIST = LevelList('levels/')
    MISSILE_LIST = MissileList()
    EXPLOSION_LIST = ExplosionList()
    SCORE = Score()
    LIVE_BAR = LiveBar()
    PLAYER = Spaceship()
    background = StaticObject((0, 0))
    background.add_images('textures/background.png', (640, 480))
    while True:
        EVENT_LIST = pygame.event.get()
        check_for_exit(EVENT_LIST)
        check_for_gameover()

        if not GAME_SOUND:
            SOUNDTRACK.stop()

        if keys.check_for_keydown(pygame.K_ESCAPE, EVENT_LIST):
            if GAME_SOUND:
                KLICK_SOUND.play()
            paused()

        background.handle()
        LEVEL_LIST.handle()
        MISSILE_LIST.handle()
        INVADER_LIST.handle()
        EXPLOSION_LIST.handle()
        PLAYER.handle()

        SCORE.handle()
        LIVE_BAR.handle()

        if BREAK_GAME:
            check_highscore(SCORE.score)
            break

        pygame.display.update()
        FPS_CLOCK.tick(FPS)


def gameover():
    """Simple image, exit to the main menu after 5 seconds"""
    global NEXT, EVENT_LIST
    NEXT = 'menu'
    gameover_image = StaticObject((0, 0))
    gameover_image.add_images('textures/gameover.png', (640, 480))
    time_to_continue = 150
    while time_to_continue:
        EVENT_LIST = pygame.event.get()
        check_for_exit(EVENT_LIST)
        gameover_image.handle()

        if keys.check_for_keydown(pygame.K_ESCAPE, EVENT_LIST):
            break

        pygame.display.update()
        FPS_CLOCK.tick(FPS)

        time_to_continue -= 1

def score_menu():
    """menu, list all highscores"""
    global NEXT, EVENT_LIST
    NEXT = 'menu'
    score_fonts = []
    font_highscore = StaticObject((160, 20))
    font_highscore.add_font(GAME_FONT, 80, 'Highscores', (55, 225, 0))

    for score, number in zip(HIGHSCORE, range(5)):
        font_object = StaticObject((100, number * 60 + 120))
        font_object.add_font(GAME_FONT, 50, str(score), (255, 150, 0))
        score_fonts.append(font_object)

    menu_background = StaticObject((0, 0))
    menu_background.add_images('textures/menu_background.png', (640, 480))
    while True:
        EVENT_LIST = pygame.event.get()
        check_for_exit(EVENT_LIST)
        if keys.check_for_keydown(pygame.K_ESCAPE, EVENT_LIST):
            break
        menu_background.handle()
        font_highscore.handle()
        for font in score_fonts:
            font.handle()

        pygame.display.update()
        FPS_CLOCK.tick(FPS)

def main_menu():
    """Main menu, start game, list highscores, enable/disable sound, leave"""
    global NEXT, EVENT_LIST, GAME_SOUND
    menu_font = pygame.font.Font(GAME_FONT, 70)
    colour_active = (255, 150, 0)
    colour_passive = (100, 60, 0)

    font_pyinvaders = StaticObject((160, 20))
    font_pyinvaders.add_font(GAME_FONT, 80, 'PyInvaders2', (55, 225, 0))
    button_play = Button((125, 110))
    button_play.add_text(menu_font, 'Play', colour_passive, colour_active)

    button_highscores = Button((125, 190))
    button_highscores.add_text(menu_font, 'Highscores', colour_passive,
                               colour_active)

    font_sound = StaticObject((125, 270))
    font_sound.add_font(GAME_FONT, 70, 'Sound', colour_passive)

    button_sound = Button((325, 270))
    button_sound.add_text(menu_font, 'Yes', colour_passive, colour_active)

    button_exit = Button((125, 350))
    button_exit.add_text(menu_font, 'Exit', colour_passive, colour_active)

    menu_background = StaticObject((0, 0))
    menu_background.add_images('textures/menu_background.png', (640, 480))

    menu_buttons = ButtonGroup()
    menu_buttons.add_buttons(button_play, button_highscores, button_sound,
                             button_exit)
    while True:
        EVENT_LIST = pygame.event.get()
        check_for_exit(EVENT_LIST)

        menu_background.handle()
        font_sound.handle()
        font_pyinvaders.handle()

        action = menu_buttons.handle()
        if action == 1:
            NEXT = 'game'
            break
        elif action == 2:
            NEXT = 'scores'
            break
        elif action == 3:
            if GAME_SOUND:
                menu_buttons.button_list[2].add_text(menu_font, 'No',
                                                     colour_passive,
                                                     colour_active)
                GAME_SOUND = False
                SOUNDTRACK.stop()
            else:
                menu_buttons.button_list[2].add_text(menu_font, 'Yes',
                                                     colour_passive,
                                                     colour_active)
                GAME_SOUND = True
                SOUNDTRACK.play(loops=-1)
        elif action == 4:
            sys.exit()

        pygame.display.update()
        FPS_CLOCK.tick(FPS)


if __name__ == "__main__":
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()

    SCREEN_SIZE = 640, 480
    SCREEN = pygame.display.set_mode(SCREEN_SIZE)
    GAME_FONT = "textures/Game_font.ttf"
    GAME_SOUND = True
    FPS = 30
    FPS_CLOCK = pygame.time.Clock()
    NEXT = 'menu'
    if not os.path.isfile("icon.png"):
        messagebox("couldn't load icon.png")
        sys.exit()
    SCREEN_ICON = pygame.image.load("icon.png").convert_alpha()
    SCREEN_ICON = pygame.transform.scale(SCREEN_ICON, (32, 32))
    pygame.display.set_icon(SCREEN_ICON)
    pygame.display.set_caption("PyInvaders2")
    read_highscores()

    #Sounds
    SOUNDTRACK = load_sound("sound/soundtrack.ogg")
    KLICK_SOUND = load_sound("sound/klick.ogg")
    EXPLOSION_SOUND = load_sound("sound/explosion.ogg")
    SHOT_SOUND = load_sound("sound/shot.ogg")

    SOUNDTRACK.play(loops=-1)

    while True:
        if NEXT == 'game':
            game()
        elif NEXT == 'gameover':
            gameover()
        elif NEXT == 'menu':
            main_menu()
        elif NEXT == 'scores':
            score_menu()


