#! /usr/bin/python

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

import os
import sys
import pygame

def create_surface(image_path, surface_scaling,
                   surface_flipping = (False, False)):
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


class surfacesequence(object):
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
        self._current_surface = 1

    def open_images(self, image_path, surface_scaling, 
                    surface_flipping = (False, False)):
        """Open images, convert them to surfaces, scale and flip them"""
        print("Load image(s) from %s . . . " % image_path),
        if os.path.isfile(image_path):
            surface = create_surface(image_path, surface_scaling, 
                                     surface_flipping)
            self.surface_list.append(surface)
        else:
            for path in read_multiple_images(image_path):
                surface = create_surface(path, surface_scaling, 
                                         surface_flipping)  
                self.surface_list.append(surface)
            self.surface_number = len(self.surface_list)
        


        if not self.surface_list == []:
            print("DONE") 
        else:
            print("Error, couldn't load %s" % image_path) 
            sys.exit()              

    def handle(self):
        """returns the current surface from the sequence """
        if not self._current_surface == self.surface_number:
            self._current_surface += 1
            return self.surface_list[self.current_surface - 2]
        else:
            self._current_surface = 1
            return self.surface_list[self.surface_number - 1]  
