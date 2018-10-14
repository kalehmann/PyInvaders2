#!/usr/bin/env python

#PyInvaders2 (c) 2014 by Karsten Lehmann

###############################################################################
#                                                                             #
#    This file is a part of PyInvaders2                                       #
#                                                                             #
#    PyInvaders2 is free software: you can redistribute it and/or modify      #
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
PyInvaders is a simple, python-based clone of the popular game Space Invaders
"""

import sys
import pygame
import copy
import os
import time
import random
import gametools as gt
import data

__author__ = "Karsten Lehmann"
__copyright__ = "Copyright 2014, Karsten Lehmann"
__license__ = "GPLv3"
__version__ = "2.0"
__maintainer__ = "Karsten Lehmann"


def check_for_exit(events):
    """test if the window gets closed and exit the game

       Args: events -> pygame.event.get()
    """
    for event in events:
        if event.type == pygame.QUIT:
            print 'EXIT'
            sys.exit()

def scene_basics():
    """Update the screen, scale it and manage the fps"""
    upscaler.handle()
    pygame.display.update()
    fps_clock.tick(Constants.fps)


def paused():
    """pause the game and give the choice to continue or leave"""
    screenshot = copy.copy(pygame.display.get_surface()) #copy the screen
    surface = pygame.Surface((640, 480), (pygame.SRCALPHA))
    surface.fill((0, 0, 0, 200))
    screenshot.blit(surface, (0, 0))
    background = gt.SurfaceSequence()
    background.add_surface(screenshot)
    menu = gt.Menu(Constants.menu_font, background, Constants.colour_active,
                   Constants.colour_passive, klick_sound)
    menu.add_text("Paused", (160, 30), Constants.colour_headline)
    menu.add_button("Return", (100, 140))
    menu.add_button("Quit", (100, 220))
    while True:
        event_list = pygame.event.get()
        check_for_exit(event_list)
        action = menu.handle(event_list, Constants.game_sound)
        if action == 1:
            break
        elif action == 2:
            return True
        scene_basics()

class Game(object):
    """the main game"""
    def __init__(self):
        self.player = data.Spaceship((320, 440))
        self.background = data.StaticObject((0, 0))
        self.background.add_images("textures/background.png", (640, 480))
        self.level_list = data.LevelList("levels/")
        self.live_bar = data.LiveBar((370, 20))
        self.score = data.Score(Constants.game_font, (580, 20))
        self.invaders = []
        self.missiles = []
        self.trackers = []
        self.explosions = []
        self.level = 0
        self.game_over = False
        self.go_delay = gt.Delay(45)
        self.iv_down = gt.Delay(100)
        self.iv_direction = random.choice(('LEFT', 'RIGHT'))
        self.screen = pygame.display.get_surface()

    def add_explosion(self, position):
        """add an explosion to the given rect/position"""
        if Constants.game_sound:
           explosion_sound.play()
        self.explosions.append(data.Explosion(position[:2]))

    def add_missile(self, position, direction):
        """add a missile to the given rect/position"""
        if Constants.game_sound:
           shot_sound.play()
        self.missiles.append(data.Missile(position[:2], direction))

    def handle_missiles(self):
        """render all missiles and check for hits"""
        for missile in self.missiles:
            missile.move()
            if (missile.rect.colliderect(self.player.rect) and
                missile.direction == 'down'):
                player_surface = self.player.surface.handle(copy=True)
                player_surface = pygame.transform.scale(player_surface,
                                                        (32, 32))
                self.missiles.remove(missile)
                self.trackers.append(data.Tracker(player_surface,
                                                self.player.rect,
                                                self.live_bar.left_pos))
            for invader in self.invaders:
                if (missile.rect.colliderect(invader.rect) and
                    missile.direction == 'up'):
                    self.missiles.remove(missile)
                    self.invaders.remove(invader)
                    self.add_explosion(invader.rect.center)
                    self.trackers.append(data.Tracker(invader.surface.handle(),
                                                    invader.rect,
                                                    self.score.position))
                    break
            self.screen.blit(*missile.get_data())

    def handle_invaders(self):
        """move and render all invaders"""
        direction = self.iv_direction
        if self.iv_down.handle():
            self.iv_down = gt.Delay(100)
            iv_ymove = 32
        else:
            iv_ymove = 0
        for invader in self.invaders:
            invader.move(iv_ymove, direction)
            if invader.rect.center[0] < 40:
                self.iv_direction = 'RIGHT'
            elif invader.rect.center[0] > 600:
                self.iv_direction = 'LEFT'
            if invader.shoot(self.invaders):
                missile_position = list(invader.rect.center)
                missile_position[1] += 16
                self.add_missile(missile_position, 'down')
            if (invader.rect.colliderect(self.player.rect) or
                invader.rect[1] > 460):
                self.game_over = True
                self.go_delay = gt.Delay(0)
            self.screen.blit(*invader.get_data())

    def handle_explosions(self):
        """render all explosions"""
        for explosion in self.explosions:
            if explosion.finished():
                self.explosions.remove(explosion)
            self.screen.blit(*explosion.get_data())

    def handle_trackers(self):
        """render all trackers"""
        for tracker in self.trackers:
            self.screen.blit(*tracker.get_data())
            if tracker.dest_reached():
                if tracker.destination == self.live_bar.left_pos:
                    if self.live_bar.deduct():
                        self.game_over = True
                        self.add_explosion(self.player.rect.center)
                elif tracker.destination == self.score.position:
                    self.score.add_score()
                self.trackers.remove(tracker)

    def handle_player(self):
        """move and render the player"""
        if not self.game_over:
            self.player.move((50, 590))
            if self.player.shoot():
                missile_position = list(self.player.rect.center)
                missile_position[1] -= 32
                self.add_missile(missile_position, 'up')
            self.screen.blit(*self.player.get_data())

    def main(self):
        """the game"""
        self.__init__()
        while True:
            event_list = pygame.event.get()
            check_for_exit(event_list)

            if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
                if paused():
                    highscore.check_highscore(self.score.score)
                    break

            if self.game_over:
                if self.go_delay.handle():
                    gameover()
                    highscore.check_highscore(self.score.score)
                    break

            if self.invaders == []:
                if self.level_list.exist_level(self.level):
                    self.invaders = self.level_list[self.level].get_invaders()
                    self.level += 1
                else:
                    highscore.check_highscore(self.score.score)
                    break

            self.screen.blit(*self.background.get_data())
            self.handle_invaders()
            self.handle_missiles()
            self.handle_explosions()
            self.handle_player()
            self.screen.blit(*self.live_bar.get_data())
            self.screen.blit(*self.score.get_data())
            self.handle_trackers()

            scene_basics()

def gameover():
    """Simple image, exit to the main menu after 5 seconds"""
    gameover_image = data.StaticObject((0, 0))
    gameover_image.add_images('textures/gameover.png', (640, 480))
    time_to_continue = 150
    while time_to_continue:
        event_list = pygame.event.get()
        check_for_exit(event_list)
        Constants.screen.blit(*gameover_image.get_data())

        if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
            break

        time_to_continue -= 1
        scene_basics()


def options_menu():
    """menu, with various options"""
    resolution_string = "%d*%d" % Constants.screen_size
    menu = gt.Menu(Constants.menu_font, Constants.menu_background,
                   Constants.colour_active, Constants.colour_passive,
                   klick_sound)
    menu.add_text("Options", (160, 20), Constants.colour_headline)
    menu.add_text("Sound", (100, 110))
    menu.add_text("Size", (100, 190))
    menu.add_text("Blur", (100, 270))
    menu.add_button(str(Constants.game_sound), (350, 110))
    menu.add_button(resolution_string, (350, 190))
    menu.add_button(str(Constants.smooth_scaling), (350, 270))
    while True:
        event_list = pygame.event.get()
        check_for_exit(event_list)

        action = menu.handle(event_list, Constants.game_sound)
        if action == 1:
            if Constants.game_sound:
                soundtrack.stop()
            else:
                soundtrack.play(loops=-1)
            Constants.game_sound = not Constants.game_sound
            menu.change_button(str(Constants.game_sound), (350, 110), 1)

        elif action == 2:
            resolutions = ((640, 480), (800, 600), (1024, 768), (1280, 960))
            reso_index = resolutions.index(Constants.screen_size)
            if reso_index == 0:
                Constants.screen_scaling = True
                upscaler.set_size((800, 600))
            elif 0 < reso_index < 3:
                upscaler.set_size(resolutions[reso_index + 1])
            elif reso_index == 3:
                Constants.screen_scaling = False
                upscaler.set_size((640, 480))
            resolution_string = "%d*%d" % Constants.screen_size
            menu.change_button(resolution_string, (350, 190), 2)

        elif action == 3:
            Constants.smooth_scaling = not Constants.smooth_scaling
            menu.change_button(str(Constants.smooth_scaling), (350, 270), 3)

        if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
            break

        scene_basics()


def score_menu():
    """menu, lists all highscores"""
    menu = gt.Menu(Constants.menu_font, Constants.menu_background,
                   Constants.colour_active, Constants.colour_passive,
                   klick_sound)
    menu.add_text("Highscores", (160, 20), Constants.colour_headline)
    for score, number in zip(highscore.scores, range(5)):
        menu.add_text(str(score), (120, number * 65 + 100))
    while True:
        event_list = pygame.event.get()
        check_for_exit(event_list)
        menu.handle(event_list, Constants.game_sound)
        if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
            break
        scene_basics()


def main_menu():
    """main menu of the game"""
    menu = gt.Menu(Constants.menu_font, Constants.menu_background,
                   Constants.colour_active, Constants.colour_passive,
                   klick_sound)
    menu.add_text("PyInvaders2", (160, 20), Constants.colour_headline)
    menu.add_button("Play", (125, 110))
    menu.add_button("Highscores", (125, 190))
    menu.add_button("Options", (125, 270))
    menu.add_button("Exit", (125, 350))
    while True:
        event_list = pygame.event.get()
        check_for_exit(event_list)
        action = menu.handle(event_list, Constants.game_sound)

        if action == 1:
            game.main()
        elif action == 2:
            score_menu()
        elif action == 3:
            options_menu()
        elif action == 4:
            break
        scene_basics()


class ScreenScaling(object):
    """Experimental up- or downscaling of the screen"""
    def __init__(self):
        self.size = 640, 480
        self.scaling = (self.size[0] / Constants.screen_size[0],
                        self.size[1] / Constants.screen_size[1])
        self.frame_times = []
        self.fps_check = gt.Delay(30)

    def get_fps(self):
        """prints the average fps-rate of the last second"""
        if self.fps_check.handle():
            self.frame_times.append(time.time())
            if len(self.frame_times) > 2:
                del self.frame_times[0]
                fps = 30 / (self.frame_times[-1:][0] -
                            self.frame_times[-2:-1][0])
                print "%f FPS" % fps
            self.fps_check = gt.Delay(30)

    def set_size(self, size):
        """set new screen-size"""
        self.size = size
        self.scaling = (size[0] / 640.0,
                        size[1] / 480.0)
        Constants.screen_size = size
        Constants.screen = pygame.display.set_mode(size)

    def handle(self):
        """scale the screen"""
        if Constants.screen_scaling:
            screenshot = copy.copy(pygame.display.get_surface())
            surf_size = (int(self.size[0] * self.scaling[0]),
                         int(self.size[1] * self.scaling[1]))
            if Constants.smooth_scaling:
                screenshot = pygame.transform.smoothscale(screenshot, surf_size)
            else:
                screenshot = pygame.transform.scale(screenshot, surf_size)
            screenshot.set_clip((0, 0, self.size[0], self.size[1]))
            Constants.screen.blit(screenshot, (0, 0))
        self.get_fps()

if __name__ == "__main__":
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()

    class Constants(object): pass

    Constants.screen_size = 640, 480
    Constants.screen = pygame.display.set_mode(Constants.screen_size)
    Constants.screen_scaling = True
    Constants.smooth_scaling = False
    if not os.path.isfile("textures/Game_font.ttf"):
        gt.messagebox("couldn't load textures/Game_font.ttf")
        sys.exit()
    Constants.game_font = "textures/Game_font.ttf"
    Constants.game_sound = False
    Constants.fps = 30

    if not os.path.isfile("icon.png"):
        gt.messagebox("couldn't load icon.png")
        sys.exit()
    screen_icon = pygame.image.load("icon.png").convert_alpha()
    screen_icon = pygame.transform.scale(screen_icon, (32, 32))
    pygame.display.set_icon(screen_icon)
    pygame.display.set_caption("PyInvaders2")
    #Sounds
    soundtrack = gt.load_sound("sound/soundtrack.ogg")
    klick_sound = gt.load_sound("sound/klick.ogg")
    explosion_sound = gt.load_sound("sound/explosion.ogg")
    shot_sound = gt.load_sound("sound/shot.ogg")
    #colours
    Constants.colour_headline = (55, 225, 0)
    Constants.colour_active = (255, 150, 0)
    Constants.colour_passive = (100, 60, 0)
    #Fonts
    Constants.menu_font = pygame.font.Font(Constants.game_font, 70)
    #background of the menus
    Constants.menu_background = gt.SurfaceSequence()
    Constants.menu_background.open_images("textures/menu_background.png",
                                          (640, 480))
    highscore = data.Highscore()
    game = Game()
    upscaler = ScreenScaling()
    fps_clock = pygame.time.Clock()

    main_menu()
