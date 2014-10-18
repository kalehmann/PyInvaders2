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
This module contains tools to handle keyboard inputs
"""

import pygame

__author__ = "Karsten Lehmann"
__copyright__ = "Copyright 2014, Karsten Lehmann"
__license__ = "GPLv3"
__version__ = "1.0"
__maintainer__ = "Karsten Lehmann"

def check_for_keydown(key, event_list):
    """Return True once, if the key was pressed down"""
    for event in event_list:
        if event.type == pygame.KEYDOWN:
            if event.key == key:
                return True
    return False

def check_for_keyup(key, event_list):
    """Return True once, if the key goes up"""
    for event in event_list:
        if event.type == pygame.KEYUP:
            if event.key == key:
                return True
    return False

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


