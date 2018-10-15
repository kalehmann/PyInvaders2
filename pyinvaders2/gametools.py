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
This module contains tools for building menus, handling keyboard inputs, manage
time in loops, show messageboxes and load soundfiles
"""

import pygame
import os
import tkinter as tk
from tkinter import messagebox as tkMessageBox
import random
import sys

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

def messagebox(message):
    """Opens a simple window with the message

       Args: message -> string, displayed in the messagebox
    """
    window = tk.Tk()  #setup main_window
    window.wm_withdraw()   #set main_window to invisible
    tkMessageBox.showinfo("Info", message)
    window.destroy()       #close main_window

def load_sound(sound_file):
    """checks whether the file exists and loads it

       Args: sound_file -> string, path to the sound file
    """
    if os.path.isfile(sound_file):
        return pygame.mixer.Sound(sound_file)
    else:
        messagebox("Error , couldn't load %s" % sound_file)
        sys.exit()


def check_for_keydown(key, event_list):
    """Return True once, if the key was pressed down

       Args: key        -> int, number of the key (pygame.K_KEY)
             event_list -> pygame.event.get()
    """
    for event in event_list:
        if event.type == pygame.KEYDOWN:
            if event.key == key:
                return True
    return False

def check_for_keyup(key, event_list):
    """Return True once, if the key goes up

       Args: key        -> int, number of the key (pygame.K_KEY)
             event_list -> pygame.event.get()
    """
    for event in event_list:
        if event.type == pygame.KEYUP:
            if event.key == key:
                return True
    return False


def create_surface(image_path, surface_scaling,
                   surface_flipping=(False, False)):
    """creates a surface from a image, scale the surface and
       if necessary flip it

       Args: image_path      -> the path to the image (str)
             surface_scaling -> the new scaling of the surface (tuple/list)
    """
    surface = pygame.image.load(image_path)
    surface.convert_alpha()
    surface = pygame.transform.scale(surface, surface_scaling)
    surface = pygame.transform.flip(surface, surface_flipping[0],
                                    surface_flipping[1])
    return surface

def read_multiple_images(image_path):
    """load multiple numerated images

       This function loads images from a path, which are numerated like
       image000.png

       Returns a list with all the image_paths
    """
    splitted_path = image_path.rpartition("/")
    splitted_file = splitted_path[2].partition(".")
    path_list = []
    for counter in range(1000):
        path_to_test = splitted_path[0] + "/" + splitted_file[0] + "/" \
                       + splitted_file[0] + "%03d"%counter + "." \
                       + splitted_file[2]
        if os.path.isfile(path_to_test):
            path_list.append(path_to_test)
        else:
            break
    return path_list

class Button(object):
    """A simple button for menus, use it with ButtonGroup

       Args: position -> Position of the button on the screen
    """
    def __init__(self, position):
        self.position = position
        self.type = None
        self.active_surface = None
        self.passive_surface = None
        self.screen = pygame.display.get_surface()

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
        """Add a image(sequence) to this buttons

           Args: active_image -> image of the button, when selected (string)
                 passive_image -> image of the button in idle mode   (string)
        """
        self.type = 'image'
        self.active_surface = SurfaceSequence()
        self.active_surface.open_images(active_image)
        self.passive_surface = SurfaceSequence()
        self.passive_surface.open_images(passive_image)

    def handle(self, state):
        """Render the current state of the button

           Args: state -> string, could be 'active' or 'passive'
        """
        if state == 'passive':
            if self.type == 'text':
                self.screen.blit(self.passive_surface, self.position)
            elif self.type == 'image':
                self.screen.blit(self.passive_surface.handle(),
                                      self.position)
        elif state == 'active':
            if self.type == 'text':
                self.screen.blit(self.active_surface, self.position)
            elif self.type == 'image':
                self.screen.blit(self.active_surface.handle(),
                                      self.position)


class ButtonGroup(object):
    """Handle buttons in an menu

       You can add buttons to a buttongroup an switch between them with keys.
       If return_key get pressed, handle() will return the current button number

       Args: sound -> pygame.mixer.Sound, played when button is pressed or
                      changed
    """
    CLICK_SOUND = None

    def __init__(self, sound = None):
        if ButtonGroup.CLICK_SOUND is None:
            ButtonGroup.CLICK_SOUND = load_sound(game_dir + "/sound/click.ogg")
        self.current_button = 1
        self.button_list = []
        if sound is None:
            sound = self.CLICK_SOUND
        self.button_sound = sound
        self.down_key = KeyCheck(pygame.K_DOWN, 10)
        self.up_key = KeyCheck(pygame.K_UP, 10)
        self.screen = pygame.display.get_surface()

    def add_buttons(self, *buttons):
        """add buttons to this group

           Args: *buttons -> Button
        """
        for button in buttons:
            self.button_list.append(button)

    def get_current_button(self, event_list, sound):
        """get and handle keyboard inputs

           Args: event_list -> pygame.event.get()
                 sound      -> boolean
        """
        if self.down_key.check(event_list):
            if sound:
                self.button_sound.play()
            if self.current_button == len(self.button_list):
                self.current_button = 1
            else:
                self.current_button += 1
        elif self.up_key.check(event_list):
            if sound:
                self.button_sound.play()
            if self.current_button == 1:
                self.current_button = len(self.button_list)
            else:
                self.current_button -= 1

    def handle(self, events, sound):
        """manage the buttons, returns button-number, when return gets
           pressed"""
        self.get_current_button(events, sound)

        for button in self.button_list:
            if self.button_list.index(button) == self.current_button - 1:
                button.handle('active')
            else:
                button.handle('passive')

        if check_for_keydown(pygame.K_RETURN, events):
            if sound:
                self.button_sound.play()
            return self.current_button


class Menu(object):
    """Menu in a game, contains button, a background and fonts

       Args: font               -> pygame.font.Font
             background_surfseq -> SurfaceSequence, displayed in the background
             colour_active      -> tuple, colour of all active objects
             colour_passive     -> tuple, colour of all passive objects
             klick_sound        -> pygame.mixer.Sound, played when button is
                                   pressed or changed
    """
    def __init__(self, font, background_surfseq, colour_active, colour_passive,
                 click_sound = None):
        self.screen = pygame.display.get_surface()
        self.font = font
        self.colour_active = colour_active
        self.colour_passive = colour_passive
        self.background = background_surfseq
        self.button_group = ButtonGroup(click_sound)
        self.fonts = []

    def add_text(self, text, position, colour=None):
        """add a static font to the menu

           Args: text     -> string, displayed text
                 position -> tuple/list, position of the text on the screen
                 colour   -> tuple, colour of the text
        """
        if not colour:
            font = self.font.render(text, 8, self.colour_passive)
        else:
            font = self.font.render(text, 8, colour)
        self.fonts.append((font, position))

    def add_button(self, text, position):
        """add a text button to the menu

           Args: text     -> string, text of the button
                 position -> position of the button on the screen
        """
        button = Button(position)
        button.add_text(self.font, text, self.colour_passive,
                        self.colour_active)
        self.button_group.add_buttons(button)

    def change_button(self, text, position, number):
        """Modify a button of the menu

           Args: text     -> string, new text of the button
                 position -> tuple, new position of the button
                 number   -> number of the button in the button_list of the
                             menu object(number, the button was added)
        """
        button = Button(position)
        button.add_text(self.font, text, self.colour_passive,
                        self.colour_active)
        self.button_group.button_list[number - 1] = button

    def handle(self, events, sound):
        """render all buttons, fonts and the background

           Returns: number of the pressed button

           Args: events -> pygame.event.get()
                 sound  -> boolean
        """
        self.screen.blit(self.background.handle(), (0, 0))
        for font in self.fonts:
            self.screen.blit(font[0], font[1])

        pressed_button = self.button_group.handle(events, sound)
        return pressed_button

class KeyCheck(object):
    """advanced handle of keyboard input

       Normaly, a key get pressed and the program got an input one time.
    """
    def __init__(self, key, delay):
        self.key = key
        self.delay = delay
        self.current_value = 0
        self.key_down = False
        self.ticks = 2
        self.current_ticks = 2

    def check(self, event_list):
        """test if key pressed, return true after a defined time"""
        pressed_keys = pygame.key.get_pressed()
        if not self.key_down:
            if check_for_keydown(self.key, event_list):
                self.key_down = True
                return True
            return False
        elif self.key_down:
            if self.current_value == self.delay:
                if check_for_keyup(self.key, event_list):
                    self.key_down = False
                    self.current_value = 0
                if self.ticks == self.current_ticks:
                    self.current_ticks = 0
                    return True
                else:
                    self.current_ticks += 1
                    return False
            else:
                if (check_for_keyup(self.key, event_list) or
                    not pressed_keys[self.key]):
                    self.key_down = False
                    self.current_value = 0
                else:
                    self.current_value += 1
                return False

class Delay(object):
    """A simple object, that helps to manage time in loops

       Args: ticks -> number of loops to wait
    """
    def __init__(self, ticks):
        self.ticks = ticks

    def set_value(self, value):
        """Update the time to wait

           Args: value -> overwrite the number of loops to wait
        """
        self.ticks = value

    def handle(self):
        """Wait the number of ticks and then return True"""
        if not self.ticks:
            return True
        else:
            self.ticks -= 1
            return False

class PrivateHandler(object):
    """Allows multiple objects to use the same surfacesequence

       Args: surface_sequence -> an instance of the surfacesequence to use
    """
    def __init__(self, surface_sequence):
        self.surf_seq = surface_sequence
        self._current_surface = 1

    def set_random(self):
        """switches to random surface"""
        self._current_surface = random.randint(0, self.surf_seq.surface_number)

    def handle(self):
        """returns the current surface from the sequence"""
        if not self._current_surface == self.surf_seq.surface_number:
            self._current_surface += 1
        else:
            self._current_surface = 1
        return self.surf_seq.surface_list[self._current_surface - 1]


class SurfaceSequence(object):
    """Allows to handle multiple images as a sequence

    This class load images and checks automaticaly if it is a single image
    or multiple images. All images were converted to surfaces. This class
    also handle imagesequences automatically

    Attributes: surface_list     -> a list of all surfaces in this sequence
                surface_number   -> the number of all surfaces in this sequence
                _current_surface -> the current surface in this sequence
    """
    def __init__(self):
        self.surface_list = []
        self.surface_number = 1
        self.current_surface = 1

    def open_images(self, image_path, surface_scaling,
                    surface_flipping=(False, False)):
        """Open images, convert them to surfaces, scale and flip them

           Args: image_path       -> the path to the image
                                    (string, 'folder/file.png')
                 surface_scaling  -> size of the new surface(s) (tuple)
                 surface_flipping -> flip the new surface on the x- or y- axis
                                     (tuple)
        """
        print("Load image(s) from {} . . . ".format(image_path), end="")
        #check if there is a single image
        if os.path.isfile(image_path):
            surface = create_surface(image_path, surface_scaling,
                                     surface_flipping)
            self.surface_list.append(surface)
        #or an imagesequence
        else:
            for path in read_multiple_images(image_path):
                surface = create_surface(path, surface_scaling,
                                         surface_flipping)
                self.surface_list.append(surface)
            self.surface_number = len(self.surface_list)

        if not self.surface_list == []:
            print("DONE")
        else:
            messagebox("Error, couldn't load %s" % image_path)
            sys.exit()

    def add_surface(self, surface):
        """Add a surface to the sequence

           Args: surface -> pygame.Surface
        """
        self.surface_list.append(surface)
        self.surface_number = len(self.surface_list)

    def private_handler(self):
        """Returns a object, which allows multiple other objects to use
           this SurfaceSequence
        """
        return PrivateHandler(self)

    def handle(self, number=None, copy=False):
        """returns the current surface from the sequence

           Args: number -> number of the surface to return
                 copy   -> boolean, if true, the current surface won't be
                           changed
        """
        if number:
            return self.surface_list[number]

        #self._current_surface counts continual from 0 to the number of
        #surfaces in the list
        if not copy:
            if not self.current_surface == self.surface_number:
                self.current_surface += 1
            else:
                self.current_surface = 1
        return self.surface_list[self.current_surface - 1]
