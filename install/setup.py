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

import os
import sys
import py2exe
from distutils.core import setup

#include .dll files for font and mixer modules
#thanks to :
#http://www.pygame.org/wiki/Pygame2exe
origIsSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
    dlls = ("libfreetype-6.dll", "libogg-0.dll", "sdl_ttf.dll")
    if os.path.basename(pathname).lower() in dlls:
        return 0
    return origIsSystemDLL(pathname)
py2exe.build_exe.isSystemDLL = isSystemDLL

setup(author = "Karsten Lehmann",
      version = '2.0',
      windows = [{'script': "PyInvader2.py",
                  'icon_resources': [(0, "pyin.ico")],
                  '#copyright': "Copyright (c) 2014 by Karsten Lehmann"}])
