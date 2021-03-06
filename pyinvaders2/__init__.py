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
from . import gametools as gt
from . import data
from .level_creator import LevelCreator

from os.path import dirname, abspath
import inspect

__author__ = "Karsten Lehmann"
__copyright__ = "Copyright 2018, Karsten Lehmann"
__license__ = "GPLv3"
__version__ = "2.1"
__maintainer__ = "Karsten Lehmann"

game_dir = dirname(
    abspath(inspect.getfile(inspect.currentframe()))
)
FONT_GAME = "/textures/game_font.ttf"
IMG_ICON = "/icon.png"

class Constants(object): pass

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
                print("{} FPS".format(fps))
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

class Scene(object):
    upscaler = None
    fps_clock = None
    menu_background = None

    def __init__(self):
        if Scene.upscaler is None:
            Scene.upscaler = ScreenScaling()
        if Scene.fps_clock is None:
            Scene.fps_clock = pygame.time.Clock()
        if Scene.menu_background is None:
            Scene.menu_background = gt.SurfaceSequence()
            Scene.menu_background.open_images(
                game_dir + "/textures/menu_background.png", (640, 480)
            )

    def check_for_exit(self, events):
        """test if the window gets closed and exit the game

           Args: events -> pygame.event.get()
        """
        for event in events:
            if event.type == pygame.QUIT:
                print('EXIT')
                sys.exit()

    def scene_basics(self):
        """Update the screen, scale it and manage the fps"""
        self.upscaler.handle()
        pygame.display.update()
        self.fps_clock.tick(Constants.fps)

class PauseMenu(Scene):
    def main(self):
        """pause the game and give the choice to continue or leave"""
        screenshot = copy.copy(pygame.display.get_surface()) #copy the screen
        surface = pygame.Surface((640, 480), (pygame.SRCALPHA))
        surface.fill((0, 0, 0, 200))
        screenshot.blit(surface, (0, 0))
        background = gt.SurfaceSequence()
        background.add_surface(screenshot)
        menu = gt.Menu(Constants.menu_font, background, Constants.colour_active,
                       Constants.colour_passive)
        menu.add_text("Paused", (160, 30), Constants.colour_headline)
        menu.add_button("Return", (100, 140))
        menu.add_button("Quit", (100, 220))
        while True:
            event_list = pygame.event.get()
            self.check_for_exit(event_list)
            action = menu.handle(event_list, Constants.game_sound)
            if action == 1:
                break
            elif action == 2:
                return True
            self.scene_basics()

class Game(Scene):
    """the main game"""
    EXPLOSION_SOUND = None
    SHOT_SOUND = None

    def __init__(self):
        super().__init__()
        if Game.EXPLOSION_SOUND is None:
            Game.EXPLOSION_SOUND = gt.load_sound(
                game_dir + "/sound/explosion.ogg"
            )
        if Game.SHOT_SOUND is None:
            Game.SHOT_SOUND = gt.load_sound(
                game_dir + "/sound/shot.ogg"
            )
        self.player = data.Spaceship((320, 440))
        self.background = data.StaticObject((0, 0))
        self.background.add_images(
            game_dir + "/textures/background.png", (640, 480)
        )
        self.level_list = data.LevelList()
        self.live_bar = data.LiveBar((370, 20))
        self.score = data.Score((580, 20))
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
           self.EXPLOSION_SOUND.play()
        self.explosions.append(data.Explosion(position[:2]))

    def add_missile(self, position, direction):
        """add a missile to the given rect/position"""
        if Constants.game_sound:
           self.SHOT_SOUND.play()
        self.missiles.append(data.Missile(position[:2], direction))

    def handle_missile(self, missile):
        missile.move()
        if (missile.rect.colliderect(self.player.rect) and
            missile.direction == 'down'):
            player_surface = self.player.surface.handle(copy=True)
            player_surface = pygame.transform.scale(player_surface,
                                                    (32, 32))
            self.trackers.append(data.Tracker(player_surface,
                                            self.player.rect,
                                            self.live_bar.left_pos))
            return False

        for invader in self.invaders:
            if (missile.rect.colliderect(invader.rect) and
                missile.direction == 'up'):
                self.invaders.remove(invader)
                self.add_explosion(invader.rect.center)
                self.trackers.append(data.Tracker(invader.surface.handle(),
                                                invader.rect,
                                                self.score.position))
                return False

        if missile.rect.y < 0 or missile.rect.y > 480:
            return False

        self.screen.blit(*missile.get_data())

        return True

    def handle_missiles(self):
        """render all missiles and check for hits"""
        self.missiles[:] = [missile for missile in self.missiles
                if self.handle_missile(missile)]

    def get_invader_direction(self):
        stuck_left = False
        stuck_right = False
        for invader in self.invaders:
            if invader.rect.center[0] < 40:
                stuck_left = True
            elif invader.rect.center[0] > 600:
                stuck_right = True
        if stuck_left and stuck_right:
            return 'STUCK'
        if stuck_left:
            self.iv_direction = 'RIGHT'
            return 'RIGHT'
        if stuck_right:
            self.iv_direction = 'LEFT'
            return 'LEFT'
        return self.iv_direction

    def handle_invaders(self):
        """move and render all invaders"""
        direction = self.get_invader_direction()
        if self.iv_down.handle():
            self.iv_down = gt.Delay(100)
            iv_ymove = 32
        else:
            iv_ymove = 0

        for invader in self.invaders:
            invader.move(iv_ymove, direction)
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
        while True:
            event_list = pygame.event.get()
            self.check_for_exit(event_list)

            if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
                if PauseMenu().main():
                    data.Highscore().check_highscore(self.score.score)
                    break

            if self.game_over:
                if self.go_delay.handle():
                    GameOver().main()
                    data.Highscore().check_highscore(self.score.score)
                    break

            if self.invaders == []:
                if self.level_list.exist_level(self.level):
                    self.invaders = self.level_list[self.level].get_invaders()
                    self.level += 1
                else:
                    data.Highscore().check_highscore(self.score.score)
                    break

            self.screen.blit(*self.background.get_data())
            self.handle_invaders()
            self.handle_missiles()
            self.handle_explosions()
            self.handle_player()
            self.screen.blit(*self.live_bar.get_data())
            self.screen.blit(*self.score.get_data())
            self.handle_trackers()

            self.scene_basics()

class GameOver(Scene):
    def main(self):
        """Simple image, exit to the main menu after 5 seconds"""
        gameover_image = data.StaticObject((0, 0))
        gameover_image.add_images(game_dir + '/textures/gameover.png', (640, 480))
        time_to_continue = 150
        while time_to_continue:
            event_list = pygame.event.get()
            self.check_for_exit(event_list)
            Constants.screen.blit(*gameover_image.get_data())

            if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
                break

            time_to_continue -= 1
            self.scene_basics()

class OptionsMenu(Scene):

    SOUND_TRACK = None

    def __init__(self):
        super().__init__()
        if OptionsMenu.SOUND_TRACK is None:
            OptionsMenu.SOUND_TRACK = gt.load_sound(
                game_dir + "/sound/soundtrack.ogg"
            )

    def main(self):
        """menu, with various options"""
        resolution_string = "%d*%d" % Constants.screen_size
        menu = gt.Menu(Constants.menu_font, self.menu_background,
                       Constants.colour_active, Constants.colour_passive)
        menu.add_text("Options", (160, 20), Constants.colour_headline)
        menu.add_text("Sound", (100, 110))
        menu.add_text("Size", (100, 190))
        menu.add_text("Blur", (100, 270))
        menu.add_button(str(Constants.game_sound), (350, 110))
        menu.add_button(resolution_string, (350, 190))
        menu.add_button(str(Constants.smooth_scaling), (350, 270))
        while True:
            event_list = pygame.event.get()
            self.check_for_exit(event_list)

            action = menu.handle(event_list, Constants.game_sound)
            if action == 1:
                if Constants.game_sound:
                    self.SOUND_TRACK.stop()
                else:
                    self.SOUND_TRACK.play(loops=-1)
                Constants.game_sound = not Constants.game_sound
                menu.change_button(str(Constants.game_sound), (350, 110), 1)

            elif action == 2:
                resolutions = ((640, 480), (800, 600), (1024, 768), (1280, 960))
                reso_index = resolutions.index(Constants.screen_size)
                if reso_index == 0:
                    Constants.screen_scaling = True
                    self.upscaler.set_size((800, 600))
                elif 0 < reso_index < 3:
                    self.upscaler.set_size(resolutions[reso_index + 1])
                elif reso_index == 3:
                    Constants.screen_scaling = False
                    self.upscaler.set_size((640, 480))
                resolution_string = "%d*%d" % Constants.screen_size
                menu.change_button(resolution_string, (350, 190), 2)

            elif action == 3:
                Constants.smooth_scaling = not Constants.smooth_scaling
                menu.change_button(str(Constants.smooth_scaling), (350, 270), 3)

            if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
                break

            self.scene_basics()

class ScoreMenu(Scene):
    def main(self):
        """menu, lists all highscores"""
        menu = gt.Menu(Constants.menu_font, self.menu_background,
                       Constants.colour_active, Constants.colour_passive)
        menu.add_text("Highscores", (160, 20), Constants.colour_headline)
        for score, number in zip(data.Highscore().scores, range(5)):
            menu.add_text(str(score), (120, number * 65 + 100))
        while True:
            event_list = pygame.event.get()
            self.check_for_exit(event_list)
            menu.handle(event_list, Constants.game_sound)
            if gt.check_for_keydown(pygame.K_ESCAPE, event_list):
                break
            self.scene_basics()

class MainMenu(Scene):
    def main(self):
        """main menu of the game"""
        menu = gt.Menu(Constants.menu_font, self.menu_background,
                       Constants.colour_active, Constants.colour_passive)
        menu.add_text("PyInvaders2", (160, 20), Constants.colour_headline)
        menu.add_button("Play", (125, 110))
        menu.add_button("Highscores", (125, 190))
        menu.add_button("Options", (125, 270))
        menu.add_button("Exit", (125, 350))
        while True:
            event_list = pygame.event.get()
            self.check_for_exit(event_list)
            action = menu.handle(event_list, Constants.game_sound)

            if action == 1:
                Game().main()
            elif action == 2:
                ScoreMenu().main()
            elif action == 3:
                OptionsMenu().main()
            elif action == 4:
                break
            self.scene_basics()

class PyInvaders2(object):
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()

        Constants.screen_size = 640, 480
        Constants.screen = pygame.display.set_mode(Constants.screen_size)
        Constants.screen_scaling = True
        Constants.smooth_scaling = False
        Constants.font_path = game_dir + FONT_GAME
        if not os.path.isfile(Constants.font_path):
            gt.messagebox("couldn't load {}".format(FONT_GAME))
            sys.exit()
        Constants.game_sound = False
        Constants.fps = 30

        icon_path = game_dir + IMG_ICON
        if not os.path.isfile(icon_path):
            gt.messagebox("couldn't load {}".format(IMG_ICON))
            sys.exit()
        screen_icon = pygame.image.load(icon_path).convert_alpha()
        screen_icon = pygame.transform.scale(screen_icon, (32, 32))
        pygame.display.set_icon(screen_icon)
        pygame.display.set_caption("PyInvaders2")
        #colours
        Constants.colour_headline = (55, 225, 0)
        Constants.colour_active = (255, 150, 0)
        Constants.colour_passive = (100, 60, 0)
        #Fonts
        Constants.menu_font = pygame.font.Font(Constants.font_path, 70)

    def main(self):
        main_menu = MainMenu()
        main_menu.main()

def levelcreator():
    LevelCreator().main()

def game():
    PyInvaders2().main()

if __name__ == "__main__":
    game()
