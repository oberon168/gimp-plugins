#!/usr/bin/env python
# -*- coding: utf-8 -*-

# version 1.4 12/12/2013
# Copyright (c) 2013 Oberon Leung
# released under GNU General Public License v3
# for license information see: https://www.gnu.org/licenses/

from gimpfu import *

def python_ob_jobs(img, mlayer, gamma, toggle) :

	pname = "JOBS Colors"
	ptable = [ 0x161213, 0xbb619e, 0x1493c0, 0x249d3c, 0xeb4f43, 0xf06e41, 0xf57940, 0xf38e40, 0xf7aa40, 0xd1c8b9 ]
#	ptable = [ 0x0a0a0b, 0x021f64, 0x171e12, 0x7e7621, 0x94781f, 0x59090b, 0x913728, 0xd98207, 0xafb19b ]
#	ptable = [ 0x0c0c0a, 0xb45b95, 0x1798c2, 0x229b3a, 0xe93429, 0xea5044, 0xf58e41, 0xf5a840, 0xdcd4c7 ]
	
# Set up an undo group, so the operation will be undone in one step.
	pdb.gimp_undo_push_group_start(img)
	oname = pdb.gimp_context_get_palette()

	palette = pdb.gimp_palette_new(pname)
	for color_number in range(len(ptable)):
		color = ptable[color_number]
		r = color >> 16
		g = (color >> 8) & 0xff
		b = color & 0xff
		pdb.gimp_palette_add_entry(palette, "Index " + str(color_number), (r,g,b))
		
	if toggle:
		pdb.gimp_equalize(mlayer, FALSE)
		
	gamma = math.pow(10.0,gamma)
	if gamma != 1.0:
		pdb.gimp_levels(mlayer, HISTOGRAM_VALUE, 0, 255, gamma, 5, 250)
	pdb.gimp_context_set_palette(palette)
	pdb.plug_in_palettemap(img, mlayer)
	pdb.gimp_palette_delete(palette)
	pdb.gimp_context_set_palette(oname)	
	
# Close the undo group.
	pdb.gimp_undo_push_group_end(img)

register(
	"python_fu_ob_jobs",
	"Produce JOBS effect",
	"Produce JOBS effect",
	"Oberon Leung",
	"Oberon Leung",
	"2013",
	"<Image>/Filters/Artistic/JOBS effect",
	"*",
	[
	(PF_SLIDER, "gamma", "Gamma(-1.0 - 1.0)", 0.0, (-1.0,1.0,0.01,0.5,0.5)),
	(PF_BOOL, "equalize", "Equalize", FALSE)
	],
	[],
	python_ob_jobs)

main()
