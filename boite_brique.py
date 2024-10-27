#!/usr/bin/env/python
'''
Copyright (C)2011 Mark Schafer <neon.mark(a)gmaildotcom>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This    program    is    distributed in the    hope    that    it    will    be    useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
'''

# Build a tabbed box for lasercutting with tight fit, and minimal material use options.
# User defines:
# - internal or external dimensions,
# - number of tabs,
# - amount lost to laser (kerf),
# - include corner cubes or not,
# - dimples, or perfect fit (accounting for kerf).
# - If zero kerf it will be perfectly packed for minimal laser cuts and material size.

### Todo
#  add option to pack multiple boxes (if zero kerf) - new tab maybe?
#  add option for little circles at sharp corners for acrylic
#  annotations: - add overlap value as markup - Ponoko annotation color
#  choose colours from a dictionary

### Versions
#  0.6  Suppression des unittoouu, 
#       Renommage des variables et rationalisation des commentaires,
#       Changement des couleurs,
#       Changement du versionning.
#  0.5 Modify tab for adjust kerf (increase tab size)
#  0.4 Add option for lid or not
# [Frank SAURET - ^^^^ depuis 2018 ^^^^]
#  0.3 Option to avoid half-sized tabs at corners. <juergen@fabmail.org>
#  0.2 changes to unittouu for Inkscape 0.91
#  0.1 February 2011 - basic lasercut box with dimples etc





__version__ = "2024.01"

#from math import *
import sys
import inkex
from simplepath import *
from lxml import etree

class LasercutBox(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        # * Onglet "Dimensions"
        self.arg_parser.add_argument("-C", "--aveccouvercle",
                type=inkex.Boolean,
                dest="aveccouvercle", default=True,
                help="Box is closed or not")
        self.arg_parser.add_argument("-i", "--external_dimensions",
                        type=inkex.Boolean,
                        dest="external_dimensions", default=False,
                        help="Are the Dimensions for External (True) or Internal (False) sizing.")
        self.arg_parser.add_argument("-u", "--units",
                        type=str,
                        dest="units", default="mm",
                        help="The unit of the box dimensions")        
        self.arg_parser.add_argument("-x", "--width",
                        type=float,
                        dest="width", default=30.0,
                        help="The Box Width - in the X dimension")
        self.arg_parser.add_argument("-y", "--length",
                        type=float,
                        dest="length", default=50.0,
                        help="The Box length - in the Y dimension")
        self.arg_parser.add_argument("-z", "--height",
                        type=float,
                        dest="height", default=20.0,
                        help="The Box height - in the Z dimension")
        self.arg_parser.add_argument("-t", "--thickness",
                        type=float,
                        dest="thickness", default=3.0,
                        help="Material Thickness")
        self.arg_parser.add_argument("-p", "--num_tab_Width",
                        type=int,
                        dest="num_tab_Width", default=3,
                        help="Number of tabs in Width")        
        self.arg_parser.add_argument("-q", "--num_tab_Length",
                        type=int,
                        dest="num_tab_Length", default=3,
                        help="Number of tabs in length")        
        self.arg_parser.add_argument("-r", "--num_tab_Height",
                        type=int,
                        dest="num_tab_Height", default=3,
                        help="Number of tabs in height")
        self.arg_parser.add_argument("-c", "--corners",
                        type=inkex.Boolean,
                        dest="corners", default=True,
                        help="The corner cubes can be removed for a different look")
        self.arg_parser.add_argument("-H", "--halftabs",
                        type=inkex.Boolean,
                        dest="halftabs", default=True,
                        help="Start/End with half-sized tabs - Avoid with very small tabs")
        # * Onglet "trait de coupe"
        self.arg_parser.add_argument("-b", "--bymaterial",
                        type=inkex.Boolean,
                        dest="bymaterial", default=True,
                        help="Are kerf define by material")
        self.arg_parser.add_argument("-o", "--materiaux",
                        type=float,
                        dest="materiaux", default=1, #**********************************************
                        help="Kerf size define by material")
        self.arg_parser.add_argument("-k", "--kerf_size",
                        type=float,
                        dest="kerf_size", default=0.0,
                        help="Kerf size - amount lost to laser for this material. 0 = loose fit")
        self.arg_parser.add_argument("-g", "--linewidth",
                        type=inkex.Boolean,
                        dest="linewidth", default=True,
                        help="Use the kerf value as the drawn line width")        
        self.arg_parser.add_argument("-f", "--forcingseparation",
                        type=inkex.Boolean,
                        dest="forcingseparation", default=False,
                        help="Forcing the separation of the panels")
        # * Onglet "Bosses"
        self.arg_parser.add_argument("-d", "--dimples",
                        type=inkex.Boolean,
                        dest="dimples", default=False,
                        help="Add dimples for press fitting wooden materials")
        self.arg_parser.add_argument("-s", "--dstyle",
                        type=inkex.Boolean,
                        dest="dstyle", default=False,
                        help="Dimples can be triangles(cheaper) or half rounds(better)")
        self.arg_parser.add_argument("--tab",
                        type=str, 
                        dest="tab", 
                        default="use",
                        help="The selected UI-tab when OK was pressed")
        #internal useful variables
        self.stroke_width  = 0.1 #default for visibility
        self.external_line_style = {'stroke':          '#660066', # Violet
                           'fill':            'none',
                           'stroke-width':    self.stroke_width,
                           'stroke-linecap':  'butt',
                           'stroke-linejoin': 'miter'}
        self.internal_line_style = {'stroke':          '#006633', # Vert foncé
                           'fill':            'none',
                           'stroke-width':    self.stroke_width,
                           'stroke-linecap':  'butt',
                           'stroke-linejoin': 'miter'}
    
    def annotation(self, x, y, text):
        """ Draw text at this location
         - change to path
         - use annotation color        """
        pass
            
    def thickness_line(self, dimple, vert_horiz, pos_neg):
        """ Trace les lignes des onglets dans l'épaisseur du matériaux. Avec ou sans bosses.
             - pos_neg is 1, -1 for direction
             - vert_horiz is v or h                """
        if dimple and self.kerf > 0.0: # we need a dimple
            # size is radius = kerf
            # short line, half circle, short line
            #[ 'C', [x1,y1, x2,y2, x,y] ]  x1 is first handle, x2 is second
            self.decalage_dimple0=0
            self.decalage_dimple1=self.decalage
            self.decalage_dimple2=2*self.decalage
            self.decalage_dimple3=3*self.decalage            
            lines = []
            radius = self.kerf
            if self.materialThickness - 2 * radius < 0.2:  # correct for large dimples(kerf) on small thicknesses
                radius = (self.materialThickness - 0.2) / 2
                short = 0.1
            else:
                short = self.materialThickness/2 - radius
            if vert_horiz == 'v': # § vertical line
                # first short line
                lines.append(['v', [pos_neg*short]])
                # half circle
                if pos_neg == 1: # only the DH_sides need reversed tabs to interlock
                    if self.BossesTriangulaires:
                        lines.append(['l', [radius, pos_neg*radius]])
                        lines.append(['l', [-radius, pos_neg*radius]])
                    else:
                        lines.append(['c', [radius, 0, radius, pos_neg*2*radius, 0, pos_neg*2*radius]])                
                else:
                    if self.BossesTriangulaires:
                        lines.append(['l', [-radius, pos_neg*radius]])
                        lines.append(['l', [radius, pos_neg*radius]])
                    else:
                        lines.append(['c', [-radius, 0, -radius, pos_neg*2*radius, 0, pos_neg*2*radius]])
                # last short line
                lines.append(['v', [pos_neg*short]])
            else: # § horizontal line
                # first short line
                lines.append(['h', [pos_neg*short]])
                # half circle
                if self.BossesTriangulaires:
                    lines.append(['l', [pos_neg*radius, radius]])
                    lines.append(['l', [pos_neg*radius, -radius]])
                else:
                    lines.append(['c', [0, radius, pos_neg*2*radius, radius, pos_neg*2*radius, 0]])
                # last short line
                lines.append(['h', [pos_neg*short]])
            return lines
        
        # No dimple - so much easier
        else: # return a straight v or h line same as thickness
            self.decalage_dimple0=self.decalage
            self.decalage_dimple1=2 * self.decalage
            self.decalage_dimple2=self.decalage
            self.decalage_dimple3=2*self.decalage            
            if vert_horiz == 'v':
                return [ ['v', [pos_neg*self.materialThickness]] ]
            else:
                return [ ['h', [pos_neg*self.materialThickness]] ]


    def draw_top_bottom(self, startx, starty, boxCover, boxSide, masktop=False):
        """ Return an SVG path for the top or bottom of box
        """
        line_path = []
        line_path.append(['M', [startx, starty]])
        
        # * Trace le dessus de la boite sans languettes
        if boxSide in "Top" and not boxCover:
            line_path.append(['m', [-self.materialThickness, -self.materialThickness]])
            line_path.append(['h', [self.boxWidth+self.materialThickness*2]])
            line_path.append(['v', [self.boxLength+self.materialThickness*2]])
            line_path.append(['h', [-self.boxWidth-self.materialThickness*2]])
            line_path.append(['v', [-self.boxLength-self.materialThickness*2-self.kerf/2]])
        else:
            # $ top row of tabs 
            if masktop and self.kerf ==0.0 and not self.forcing_separation: # don't draw top for packing with no extra cuts
                line_path.append(['m', [self.boxWidth,0]])
            else:
                if not self.half_tabs: 
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/4]])
                for i in range(int(self.num_tab_W)):
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/4-self.decalage_dimple0]])#1> 0
                    for l in self.thickness_line(self.dimple, 'v', -1):
                        line_path.append(l)
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/2 +self.decalage_dimple1]])#2>1
                    line_path.append(['v', [self.materialThickness]])
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/4-self.decalage]])
                if not self.half_tabs: line_path.append(['h', [self.boxWidth/self.num_tab_W/4]])
            # $ right hand vertical drop
            if not self.half_tabs: line_path.append(['v', [self.boxLength/self.num_tab_L/4 ]])
            for i in range(int(self.num_tab_L)):
                line_path.append(['v', [self.boxLength/self.num_tab_L/4 - self.decalage]])
                line_path.append(['h', [self.materialThickness]])
                line_path.append(['v', [self.boxLength/self.num_tab_L/2 + self.decalage_dimple1]])#2>1
                for l in self.thickness_line(self.dimple, 'h', -1):
                    line_path.append(l)
                line_path.append(['v', [self.boxLength/self.num_tab_L/4 - self.decalage_dimple0]])#1>0
            if not self.half_tabs: line_path.append(['v', [self.boxLength/self.num_tab_L/4 ]])
            # $ bottom row (in reverse)
            if not self.half_tabs: line_path.append(['h', [-self.boxWidth/self.num_tab_W/4]])
            for i in range(int(self.num_tab_W)):
                line_path.append(['h', [-self.boxWidth/self.num_tab_W/4+self.decalage ]])
                line_path.append(['v', [self.materialThickness]])
                line_path.append(['h', [-self.boxWidth/self.num_tab_W/2 -self.decalage_dimple1]])#2>1
                for l in self.thickness_line(self.dimple, 'v', -1):
                    line_path.append(l)
                line_path.append(['h', [-self.boxWidth/self.num_tab_W/4+self.decalage_dimple0]])#1>0
            if not self.half_tabs: line_path.append(['h', [-self.boxWidth/self.num_tab_W/4]])
            # $ up the left hand side
            if not self.half_tabs: line_path.append(['v', [-self.boxLength/self.num_tab_L/4 ]])
            for i in range(int(self.num_tab_L)):
                line_path.append(['v', [-self.boxLength/self.num_tab_L/4 +self.decalage_dimple0]])#1>0
                for l in self.thickness_line(self.dimple, 'h', -1):
                    line_path.append(l)
                line_path.append(['v', [-self.boxLength/self.num_tab_L/2 -self.decalage_dimple1]])#2>1
                line_path.append(['h', [self.materialThickness]])
                line_path.append(['v', [-self.boxLength/self.num_tab_L/4+self.decalage ]])
            line_path.append(['v', [-self.kerf_PF/2 ]])   #line_path.append(['v', [-self.kerf_PF/2 ]]) 
            if not self.half_tabs: line_path.append(['v', [-self.boxLength/self.num_tab_L/4 ]])
        
        
        return line_path


    def draw_short_side(self, startx, starty, boxCover, boxSide, mask=False, corners=True):
        """ Return an SVG path for the short side of box
        """
        # Draw side of the box (placed below the lid)
        line_path = []
        # $ top row of tabs
        if corners:
            line_path.append(['M', [startx - self.materialThickness, starty]])
            line_path.append(['v', [-self.materialThickness]])
            line_path.append(['h', [self.materialThickness]])
        else:
            line_path.append(['M', [startx, starty]])
            line_path.append(['v', [-self.materialThickness]])
        #
        # if fit perfectly - don't draw double line  modify by Frank SAURET 12-12-2018
        if boxSide in "Back" and not boxCover:
            if self.kerf == 0.0 and not self.forcing_separation:
                if corners:
                    line_path.append(['m', [self.boxWidth+self.materialThickness,0]])
                else:
                    line_path.append(['m', [self.boxWidth,0]])
            else:       
                if corners:
                    line_path.append(['h', [self.boxWidth+self.materialThickness]])
                else:
                    line_path.append(['h', [self.boxWidth]])
        else:
            if self.kerf > 0.0 or self.forcing_separation:
                if not self.half_tabs: line_path.append(['h', [self.boxWidth/self.num_tab_W/4]])          
                for i in range(int(self.num_tab_W)):
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/4 + self.decalage]])
                    line_path.append(['v', [self.materialThickness]])
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/2 - self.decalage_dimple1]])
                    for l in self.thickness_line(self.dimple, 'v', -1):
                        line_path.append(l)
                    line_path.append(['h', [self.boxWidth/self.num_tab_W/4 + self.decalage_dimple0 ]])
                if not self.half_tabs: line_path.append(['h', [self.boxWidth/self.num_tab_W/4]])
                if corners: line_path.append(['h', [self.materialThickness]])
            else: # move to skipped drawn lines
                if corners:    
                    line_path.append(['m', [self.boxWidth + self.materialThickness, 0]])
                else:
                    line_path.append(['m', [self.boxWidth, 0]])
        #
        line_path.append(['v', [self.materialThickness]])
        if not corners: line_path.append(['h', [self.materialThickness]])
        # $ Tight hand side
        if not self.half_tabs: line_path.append(['v', [self.boxHeight/self.num_tab_H/4]])
        for i in range(int(self.num_tab_H)):
            line_path.append(['v', [self.boxHeight/self.num_tab_H/4 + self.decalage_dimple0]])
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [self.boxHeight/self.num_tab_H/2 - self.decalage_dimple1 ]])
            line_path.append(['h', [self.materialThickness]])
            line_path.append(['v', [self.boxHeight/self.num_tab_H/4 + self.decalage]])
        if not self.half_tabs: line_path.append(['v', [self.boxHeight/self.num_tab_H/4 ]])
        #
        if corners:
            line_path.append(['v', [self.materialThickness]])
            line_path.append(['h', [-self.materialThickness]])
        else:
            line_path.append(['h', [-self.materialThickness]])
            line_path.append(['v', [self.materialThickness]])
        # $ Bottom row of tabs
        if boxSide in "Front" and not boxCover:
            if corners:
                line_path.append(['h', [-self.boxWidth]])
            else:
                line_path.append(['h', [-self.boxWidth]])
        else:
            if not self.half_tabs: line_path.append(['h', [-self.boxWidth/self.num_tab_W/4]])
            for i in range(int(self.num_tab_W)):
                line_path.append(['h', [-self.boxWidth/self.num_tab_W/4 -self.decalage_dimple0]])
                for l in self.thickness_line(self.dimple, 'v', -1):
                    line_path.append(l)
                line_path.append(['h', [-self.boxWidth/self.num_tab_W/2+self.decalage_dimple1]])
                line_path.append(['v', [self.materialThickness]])
                line_path.append(['h', [-self.boxWidth/self.num_tab_W/4-self.decalage ]])
            if not self.half_tabs: line_path.append(['h', [-self.boxWidth/self.num_tab_W/4]])
        #
        if corners:
            line_path.append(['h', [-self.materialThickness]])
            line_path.append(['v', [-self.materialThickness]])
        else:
            line_path.append(['v', [-self.materialThickness]])
            line_path.append(['h', [-self.materialThickness]])
        # $ Left hand side
        if not self.half_tabs: line_path.append(['v', [-self.boxHeight/self.num_tab_H/4 ]])
        for i in range(int(self.num_tab_H)):
            line_path.append(['v', [-self.boxHeight/self.num_tab_H/4 -self.decalage]])
            line_path.append(['h', [self.materialThickness]])
            line_path.append(['v', [-self.boxHeight/self.num_tab_H/2+self.decalage_dimple1 ]])
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [-self.boxHeight/self.num_tab_H/4-self.decalage_dimple0]])
        if not self.half_tabs: line_path.append(['v', [-self.boxHeight/self.num_tab_H/4]])
        #
        line_path.append(['h', [self.kerf_PF/2 ]])
        if not corners: line_path.append(['h', [self.materialThickness]])
        return line_path


    def draw_long_side(self, startx, starty, boxCover, boxSide, corners, mask=False):
        """ Return an SVG path for the long side of box
        """
        line_path = []
        # $ top row of tabs
        line_path.append(['M', [startx, starty]])
        line_path.append(['h', [self.materialThickness]])
        if not self.half_tabs: line_path.append(['h', [self.boxHeight/self.num_tab_H/4]])
        for i in range(int(self.num_tab_H)):
            line_path.append(['h', [self.boxHeight/self.num_tab_H/4-self.decalage ]])
            line_path.append(['v', [-self.materialThickness]])
            line_path.append(['h', [self.boxHeight/self.num_tab_H/2+self.decalage_dimple1 ]])
            for l in self.thickness_line(self.dimple, 'v', 1):
                line_path.append(l)
            line_path.append(['h', [self.boxHeight/self.num_tab_H/4 -self.decalage_dimple0]])
        if not self.half_tabs: line_path.append(['h', [self.boxHeight/self.num_tab_H/4]])
        line_path.append(['h', [self.materialThickness]])
        # $ Right row of tabs or line
        if not self.half_tabs: line_path.append(['v', [self.boxLength/self.num_tab_L/4 ]])
        if boxSide in "Right" and not boxCover:
            if self.half_tabs:
                line_path.append(['v', [self.boxLength]])
            else:
                line_path.append(['v', [self.boxLength-self.boxLength/self.num_tab_L/4]])
            line_path.append(['h', [-self.materialThickness]])
            
        else:
            for i in range(int(self.num_tab_L)):
                line_path.append(['v', [self.boxLength/self.num_tab_L/4 + self.decalage_dimple0]])
                for l in self.thickness_line(self.dimple, 'h', -1):
                    line_path.append(l)
                line_path.append(['v', [self.boxLength/self.num_tab_L/2 - self.decalage_dimple1 ]])
                line_path.append(['h', [self.materialThickness]])
                line_path.append(['v', [self.boxLength/self.num_tab_L/4 + self.decalage]])
            if not self.half_tabs: line_path.append(['v', [self.boxLength/self.num_tab_L/4 ]])    
            line_path.append(['h', [-self.materialThickness]])
        # $ Bottom row of tab
        if not self.half_tabs: line_path.append(['h', [-self.boxHeight/self.num_tab_H/4]])
        for i in range(int(self.num_tab_H)):
            line_path.append(['h', [-self.boxHeight/self.num_tab_H/4 -self.decalage_dimple2]])#1>2
            for l in self.thickness_line(self.dimple, 'v', 1):  # this is the weird +1 instead of -1 dimple
                line_path.append(l)
            line_path.append(['h', [-self.boxHeight/self.num_tab_H/2+self.decalage_dimple3 ]])#2>3
            line_path.append(['v', [-self.materialThickness]])
            line_path.append(['h', [-self.boxHeight/self.num_tab_H/4-self.decalage]])
        if not self.half_tabs: line_path.append(['h', [-self.boxHeight/self.num_tab_H/4]])
        line_path.append(['h', [-self.materialThickness]])
        # $ Left hand
        # if fit perfectly - don't draw double line modify by Frank SAURET 12-12-2018
        if (self.kerf > 0.0 or self.forcing_separation) and (boxCover or boxSide in "Right"):
            if not self.half_tabs: line_path.append(['v', [-self.boxLength/self.num_tab_L/4 ]])
            for i in range(int(self.num_tab_L)):
                line_path.append(['v', [-self.boxLength/self.num_tab_L/4-self.decalage]])
                line_path.append(['h', [self.materialThickness]])
                line_path.append(['v', [-self.boxLength/self.num_tab_L/2+self.decalage_dimple1 ]])
                for l in self.thickness_line(self.dimple, 'h', -1):
                    line_path.append(l)
                line_path.append(['v', [-self.boxLength/self.num_tab_L/4-self.decalage_dimple0 ]])
            line_path.append(['v', [-self.kerf_PF/2 ]])    
            if not self.half_tabs: line_path.append(['v', [-self.boxLength/self.num_tab_L/4 ]])
        # si pas de couvercle trace une ligne sans languette
        elif boxSide in "Left" and not boxCover and (self.kerf > 0.0 or self.forcing_separation):
            line_path.append(['v', [-self.boxLength-self.kerf/2]])
                
        return line_path

    ###--------------------------------------------
    ### The    main function    called    by    the    inkscape    UI
    def effect(self):
        # extract fields from UI
        self.boxWidth  = self.options.width
        self.boxLength  = self.options.length
        self.boxHeight  = self.options.height
        self.materialThickness = self.options.thickness
        self.kerf  = self.options.kerf_size
        #  Added by Frank SAURET 12-12-2018 
        materiaux  = self.options.materiaux
        bymaterial=self.options.bymaterial
        if bymaterial: 
            self.kerf = materiaux
        self.aveccouvercle=self.options.aveccouvercle
        #  05-05-2021
        self.decalage = self.kerf/4 # Pour un ajustement serré si le kerf est réel
        self.decalage_dimple0 = 0 # Augmentation du jeu si utilisation de dimple
        self.decalage_dimple1 = 0 # Augmentation du jeu si utilisation de dimple
        self.decalage_dimple2 = 0 # Augmentation du jeu si utilisation de dimple
        self.decalage_dimple3 = 0 # Augmentation du jeu si utilisation de dimple        
        #  deddA by Frank SAURET 12-12-2018
        if self.kerf < 0.01: self.kerf = 0.0  # snap to 0 for UI error when setting spinner to 0.0
        self.num_tab_W  = self.options.num_tab_Width
        self.num_tab_L  = self.options.num_tab_Length
        self.num_tab_H  = self.options.num_tab_Height
        self.dimple = self.options.dimples
        line_width  = self.options.linewidth
        #  Added by Frank SAURET 12-12-2018
        self.forcing_separation=self.options.forcingseparation
        #  deddA by Frank SAURET 12-12-2018
        corners  = self.options.corners
        self.BossesTriangulaires = self.options.dstyle
        # self.annotation = self.options.annotation
        self.half_tabs  = self.options.halftabs
        if not self.half_tabs:
            self.num_tab_W += 0.5
            self.num_tab_L += 0.5
            self.num_tab_H += 0.5                                
        # Correct for thickness in dimensions
        if self.options.external_dimensions: # external donc enlève l'épaisseur
            self.boxWidth -= self.materialThickness*2
            self.boxLength -= self.materialThickness*2
            self.boxHeight -= self.materialThickness*2
        # adjust for laser kerf (precise measurement)
        self.boxWidth += self.kerf
        self.boxLength += self.kerf
        self.boxHeight += self.kerf

        # Precise fit or dimples (if kerf > 0.0)
        if self.dimple == False: # and kerf > 0.0:
            self.kerf_PF = self.kerf
        else:
            self.kerf_PF = 0.0
            
        # set the stroke width and line style
        sw = self.kerf
        if self.kerf == 0.0: sw = self.stroke_width
        ls = self.external_line_style
        if line_width: # user wants drawn line width to be same as kerf size
            ls['stroke-width'] = sw
        external_line_style = str(inkex.Style(ls))

        ###--------------------------- 
        ### create the inkscape object
        box_id = self.svg.get_unique_id('box')
        self.box = g = etree.SubElement(self.svg.get_current_layer(), 'g', {'id':box_id})

        #Set local position for drawing the box
        lower_pos = 0
        left_pos  = 0
        # §Draw top (using SVG path definitions)
        line_path = self.draw_top_bottom(left_pos, lower_pos, self.aveccouvercle,'Top', False)
        # Add to scene
        line_atts = { 'style':external_line_style, 'id':box_id+'-lid', 'd':str(Path(line_path)) }
        etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # §draw the short side 1 of the box directly below modify by Frank SAURET 12-12-2018
        if self.kerf > 0.0 or self.forcing_separation:
            lower_pos += self.boxLength + (3*self.materialThickness)
        else:  # kerf = 0 so don't draw extra lines and fit perfectly
            if self.aveccouvercle:
                lower_pos += self.boxLength + self.materialThickness  # at lower edge of lid
            else:
                lower_pos += self.boxLength+ self.materialThickness *2   # at lower edge of lid
        left_pos += 0
        # Draw side of the box (placed below the top)
        line_path = self.draw_short_side(left_pos, lower_pos, self.aveccouvercle,'Back', False, corners=corners)
        # Add to scene
        line_atts = { 'style':external_line_style, 'id':box_id+'-longside1', 'd':str(Path(line_path)) }
        etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # §draw the bottom of the box directly below modify by Frank SAURET 12-12-2018
        if self.kerf > 0.0 or self.forcing_separation:
            lower_pos += self.boxHeight + (3*self.materialThickness)
        else:  # kerf = 0 so don't draw extra lines and fit perfectly
            lower_pos += self.boxHeight + self.materialThickness # at lower edge
        left_pos += 0
        line_path = self.draw_top_bottom(left_pos, lower_pos, self.aveccouvercle,'Bot', True)
        # Add to scene
        line_atts = { 'style':external_line_style, 'id':box_id+'-base', 'd':str(Path(line_path)) }
        etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # §  draw the second short side 2 of the box directly below modify by Frank SAURET 12-12-2018
        if self.kerf > 0.0 or self.forcing_separation:
            lower_pos += self.boxLength + (3*self.materialThickness)
        else:  # kerf = 0 so don't draw extra lines and fit perfectly
            lower_pos += self.boxLength + self.materialThickness  # at lower edge of lid
        left_pos += 0
        # Draw side of the box (placed below the bottom)
        line_path = self.draw_short_side(left_pos, lower_pos, self.aveccouvercle, 'Front', False, corners=corners)
        # Add to scene
        line_atts = { 'style':external_line_style, 'id':box_id+'-longside2', 'd':str(Path(line_path)) }
        etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # § draw long side 1 next to top by Frank SAURET 12-12-2018
        if self.kerf > 0.0 or self.forcing_separation:

            left_pos += self.boxWidth + (2*self.materialThickness) # adequate space (could be a param for separation when kerf > 0)
        else:
            if self.aveccouvercle:
                left_pos += self.boxWidth  # right at right edge of lid
            else:
                left_pos += self.boxWidth + (self.materialThickness)
        lower_pos = 0
        # Side of the box (placed next to the top)
        line_path = self.draw_long_side(left_pos, lower_pos, self.aveccouvercle,'Left', corners, False)
        # Add to scene
        line_atts = { 'style':external_line_style, 'id':box_id+'-endface2', 'd':str(Path(line_path)) }
        etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # § draw long side 2 next to bottom by Frank SAURET 12-12-2018
        if self.kerf > 0.0 or self.forcing_separation:
            lower_pos += self.boxLength + self.boxHeight + 6*self.materialThickness
        else:
            if self.aveccouvercle:
                lower_pos += self.boxLength +self.boxHeight + 2*self.materialThickness
            else:
                lower_pos += self.boxLength +self.boxHeight + 3*self.materialThickness
                left_pos-=self.materialThickness
        # Side of the box (placed next to the lid)
        line_path = self.draw_long_side(left_pos, lower_pos, self.aveccouvercle,'Right', corners, True)
        # Add to scene
        line_atts = { 'style':external_line_style, 'id':box_id+'-endface1', 'd':str(Path(line_path)) }
        etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        ###----------------------------------------
        
        # Transform entire drawing to center of doc
        #lower_pos += self.boxLength*2 + self.boxHeight*2 + 2*self.materialThickness
        #left_pos += self.boxLength + 2*self.materialThickness
        #g.set( 'transform', 'translate(%f,%f)' % ( (docW-left_pos)/2, (docH-lower_pos)/2))
        # § Transform entire drawing to uper left corner
        g.set( 'transform', 'translate(%f,%f)' % ( 2*self.materialThickness+self.kerf/2,2*self.materialThickness+self.kerf/2))

###
# if __name__ == '__main__':
#     LasercutBox().run()
    
#Pour débugger dans VSCode et en lançant InkScape    
if __name__ == '__main__':
    filename='H:\\OneDrive\\TestBoiteBrique.svg'
    if 'inkscape' in sys.argv[0]:
        # Dans VSCode
        input_file = filename
        output_file = input_file
        LasercutBox().run([input_file, '--output=' + output_file])
    else:
        LasercutBox().run()