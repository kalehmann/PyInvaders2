#! /usr/bin/env python

#PyInvaders2 (c) 2018 by Karsten Lehmann

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
This software allows you to create level for PyInvaders2
"""

import pygame
import sys
import tkinter as tk
from tkinter import filedialog as tkFileDialog
from tkinter import messagebox as tkMessageBox

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

def mouse_down(events):
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return True
def mouse_over(x_vals, y_vals, mouse_pos):
    if (x_vals[0] <= mouse_pos[0] <= x_vals[1] and
        y_vals[0] <= mouse_pos[1] <= y_vals[1] and
        pygame.mouse.get_focused()):
        return True

class Button(object):
    def __init__(self, image_p, image_a, position):
        self.surface_p = pygame.image.load(image_p)
        self.surface_p.convert_alpha()
        self.surface_a = pygame.image.load(image_a)
        self.surface_a.convert_alpha()
        self.size = self.surface_a.get_size()
        self.position = position
        self.screen = pygame.display.get_surface()
        self.range = ((self.position[0], self.position[0] + self.size[0]),
                      (self.position[1], self.position[1] + self.size[1]))

    def add_text(self, text, font, colour):
        font = font.render(text, 8, colour)
        font_position = (int(self.size[0] * 0.5 - font.get_size()[0] / 2),
                         int(self.size[1] * 0.5 - font.get_size()[1] / 2))
        self.surface_a.blit(font, font_position)
        self.surface_p.blit(font, font_position)

    def handle(self, events, mouse_pos):
        if mouse_over(self.range[0], self.range[1], mouse_pos):
            self.screen.blit(self.surface_a, self.position)
            if mouse_down(events):
                return True
        else:
            self.screen.blit(self.surface_p, self.position)

class LevelCreator(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 400))
        self.fps_clock = pygame.time.Clock()
        self.fps = 30
        self.font = pygame.font.Font(
            game_dir + "/textures/game_font.ttf", 50
        )

    def main(self):
        self.selection_screen()

    def selection_screen(self):
        pygame.mouse.set_visible(True)

        button_create = Button(
            game_dir + "/gfx/button_p.png",
            game_dir + "/gfx/button_a.png",
            (25, 25)
        )
        button_create.add_text("Create Level", self.font, (0, 0, 0))

        button_load = Button(
            game_dir + "/gfx/button_p.png",
            game_dir + "/gfx/button_a.png",
            (425, 25)
        )
        button_load.add_text("Load Level", self.font, (0, 0, 0))

        while True:
            mouse_position = pygame.mouse.get_pos()
            event_list = pygame.event.get()
            self.check_for_exit(event_list)
            self.screen.fill((55, 55, 55))

            if button_create.handle(event_list, mouse_position):
                self.edit_screen()
            if button_load.handle(event_list, mouse_position):
                lines = self.open_file()
                self.edit_screen(lines)

            pygame.display.update()
            self.fps_clock.tick(self.fps)

    def edit_screen(self, lines=None):
        button_back = Button(
            game_dir + "/gfx/button_flat_p.png",
            game_dir + "/gfx/button_flat_a.png",
            (25, 275)
        )
        button_back.add_text("Back", self.font, (0, 0, 0))
        button_save = Button(
            game_dir + "/gfx/button_flat_p.png",
            game_dir + "/gfx/button_flat_a.png",
            (425, 275)
        )
        button_save.add_text("Save", self.font, (0, 0, 0))


        surface_empty = pygame.image.load(game_dir + "/gfx/empty.png")
        surface_invader = pygame.image.load(game_dir + "/gfx/invader.png")

        if lines is None:
            lines = [[], [], [], [], []]
            for i in range(5):
                for j in range(19):
                    lines[i].append(False)
        else:
            pass
        while True:
            mouse_position = pygame.mouse.get_pos()
            event_list = pygame.event.get()
            self.check_for_exit(event_list)
            self.screen.fill((55, 55, 55))
            for i in range(5):
                for j in range(19):
                    position = 38 * j + 39, 38 * i + 55
                    if lines[i][j]:
                        self.screen.blit(surface_invader, position)
                    else:
                        self.screen.blit(surface_empty, position)
            if mouse_down(event_list):
               line = int(round((mouse_position[1] - 71) / 38.0))
               number = int(round((mouse_position[0] - 55) / 38.0))
               if number < 19 and line < 5:
                   lines[line][number] = not lines[line][number]

            if button_back.handle(event_list, mouse_position):
                break
            if button_save.handle(event_list, mouse_position):
                self.save_file(lines)

            pygame.display.update()
            self.fps_clock.tick(self.fps)

    def check_for_exit(self, events):
        """test if the window gets closed and exit the game"""
        for event in events:
            if event.type == pygame.QUIT:
                print('EXIT')
                sys.exit()

    def open_file(self):
        window = tk.Tk()       #setup main_window
        window.wm_withdraw()   #set main_window to invisible
        level_file = tkFileDialog.askopenfilename()
        window.destroy()       #close main_window

        if level_file == '':
            return None

        lines = [[], [], [], [], []]
        num_lines = sum(1 for line in open(level_file))
        if num_lines != 5:
            self.messagebox("Invalid level_file")
            sys.exit()
        level_file = open(level_file, 'r')
        for line, line_number in zip(level_file, range(5)):
            for letter, number in zip(line, range(19)):
                if letter == '#':
                    lines[line_number].append(True)
                else:
                    lines[line_number].append(False)
        level_file.close()
        return lines

    def save_file(self, lines):
        window = tk.Tk()       #setup main_window
        window.wm_withdraw()   #set main_window to invisible
        file_name = tkFileDialog.asksaveasfilename()
        window.destroy()       #close main_window
        if file_name == '':
            return None
        level_file = open(file_name, "w")
        for line in lines:
            for place in line:
                if place:
                    level_file.write("#")
                else:
                    level_file.write("0")
            level_file.write('\n')

    def messagebox(self, message):
        """Opens a simple window with the message"""
        window = tk.Tk()  #setup main_window
        window.wm_withdraw()   #set main_window to invisible
        tkMessageBox.showinfo("Info", message)
        window.destroy()       #close main_window
