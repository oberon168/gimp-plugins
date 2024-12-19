#!/usr/bin/env python
#   Copyright (C) 2015 Oberon Leung

from gimpfu import *

def makeAdjoint(m):
	m00p = m[1][1] * m[2][2] - m[1][2] * m[2][1]
	m01p = m[1][2] * m[2][0] - m[1][0] * m[2][2] 
	m02p = m[1][0] * m[2][1] - m[1][1] * m[2][0]
	m10p = m[0][2] * m[2][1] - m[0][1] * m[2][2] 
	m11p = m[0][0] * m[2][2] - m[0][2] * m[2][0]
	m12p = m[0][1] * m[2][0] - m[0][0] * m[2][1] 
	m20p = m[0][1] * m[1][2] - m[0][2] * m[1][1]
	m21p = m[0][2] * m[1][0] - m[0][0] * m[1][2] 
	m22p = m[0][0] * m[1][1] - m[0][1] * m[1][0]
# Transpose and copy sub-determinants
	m[0][0] = m00p
	m[0][1] = m10p
	m[0][2] = m20p
	m[1][0] = m01p
	m[1][1] = m11p
	m[1][2] = m21p
	m[2][0] = m02p
	m[2][1] = m12p
	m[2][2] = m22p

def concatenate(mx,my):
	m00p = mx[0][0] * my[0][0] + mx[1][0] * my[0][1] + mx[2][0] * my[0][2]
	m10p = mx[0][0] * my[1][0] + mx[1][0] * my[1][1] + mx[2][0] * my[1][2]
	m20p = mx[0][0] * my[2][0] + mx[1][0] * my[2][1] + mx[2][0] * my[2][2]
	m01p = mx[0][1] * my[0][0] + mx[1][1] * my[0][1] + mx[2][1] * my[0][2]
	m11p = mx[0][1] * my[1][0] + mx[1][1] * my[1][1] + mx[2][1] * my[1][2]
	m21p = mx[0][1] * my[2][0] + mx[1][1] * my[2][1] + mx[2][1] * my[2][2]
	m02p = mx[0][2] * my[0][0] + mx[1][2] * my[0][1] + mx[2][2] * my[0][2]
	m12p = mx[0][2] * my[1][0] + mx[1][2] * my[1][1] + mx[2][2] * my[1][2]
	m22p = mx[0][2] * my[2][0] + mx[1][2] * my[2][1] + mx[2][2] * my[2][2]
	mx[0][0] = m00p
	mx[1][0] = m10p
	mx[2][0] = m20p
	mx[0][1] = m01p
	mx[1][1] = m11p
	mx[2][1] = m21p
	mx[0][2] = m02p
	mx[1][2] = m12p
	mx[2][2] = m22p
	
def normalize(m):
	invscale = 1.0 / m[2][2]
	m[0][0] *= invscale
	m[0][1] *= invscale
	m[0][2] *= invscale
	m[1][0] *= invscale
	m[1][1] *= invscale
	m[1][2] *= invscale
	m[2][0] *= invscale
	m[2][1] *= invscale
	m[2][2] = 1.0

def quadToSquare(xy,m):
	squareToQuad(xy,m)
	makeAdjoint(m)
	
def squareToQuad(xy,m):
	dx3 = xy[0][0] - xy[0][1] + xy[0][2] - xy[0][3]
	dy3 = xy[1][0] - xy[1][1] + xy[1][2] - xy[1][3]
	m[2][2] = 1.0
	if ((dx3 == 0.0) and (dy3 == 0.0)):
		m[0][0] = xy[0][1] - xy[0][0]
		m[0][1] = xy[0][2] - xy[0][1]
		m[0][2] = xy[0][0]
		m[1][0] = xy[1][1] - xy[1][0]
		m[1][1] = xy[1][2] - xy[1][1]
		m[1][2] = xy[1][0]
		m[2][0] = 0.0
		m[2][1] = 0.0
	else:
		dx1 = xy[0][1] - xy[0][2]
		dy1 = xy[1][1] - xy[1][2]
		dx2 = xy[0][3] - xy[0][2]
		dy2 = xy[1][3] - xy[1][2]
		invdet = 1.0 / (dx1 * dy2 - dx2 * dy1)
		m[2][0] = (dx3 * dy2 - dx2 * dy3) * invdet
		m[2][1] = (dx1 * dy3 - dx3 * dy1) * invdet
		m[0][0] = (xy[0][1] - xy[0][0]) + (m[2][0] * xy[0][1])
		m[0][1] = (xy[0][3] - xy[0][0]) + (m[2][1] * xy[0][3])
		m[0][2] = xy[0][0]
		m[1][0] = (xy[1][1] - xy[1][0]) + (m[2][0] * xy[1][1])
		m[1][1] = (xy[1][3] - xy[1][0]) + (m[2][1] * xy[1][3])
		m[1][2] = xy[1][0]

def quadToQuad(xx,yy,m):
	my = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
	quadToSquare(xx,m)
	squareToQuad(yy,my)
	concatenate(m,my)
	normalize(m) 

def pointsFromStroke(stroke):
#	Takes a list of stroke coordinates and extracts the anchors as (x,y) tuples
	p,c=stroke.points
	return ([tuple(p[i:i+2]) for i in range(2,len(p),6)],c)	
	
def transform(x, y, m):
	w = (m[2][0] * x) + (m[2][1] * y) + m[2][2]
	xx = (int) (((m[0][0] * x) + (m[0][1] * y) + m[0][2]) / w)
	yy = (int) (((m[1][0] * x) + (m[1][1] * y) + m[1][2]) / w)
	return (xx, yy)	

def python_ob_align(img, layer, acpath, rfpath, clip) :
# Set up an undo group, so the operation will be undone in one step.
	pdb.gimp_undo_push_group_start(img)
# console
# img = gimp.image_list()[0]
# layer = pdb.gimp_image_get_active_layer(img)

	inv = [[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0]]
	outv = [[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0]]
	txm = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
	
	j = 0
	for stroke in acpath.strokes:
		points,closed = pointsFromStroke(stroke)
		for i in range(len(points)):
#			pdb.gimp_message('R(%d,%3.1f,%3.1f)' % (i,points[i-1][0],points[i-1][1]))
			inv[0][j] = points[i-1][0]
			inv[1][j] = points[i-1][1]
#			pdb.gimp_message('A(%d,%3.1f,%3.1f)' % (j,inv[0][j],inv[1][j]))
			if (j >= 3): 
				break
			j = j + 1
	if (j < 3):
		raise Exception('%s need at least 4 points' % acpath.name)
	j = 0
	for stroke in rfpath.strokes:
		points,closed = pointsFromStroke(stroke)
		for i in range(len(points)):
#			pdb.gimp_message('R(%d,%3.1f,%3.1f)' % (i,points[i-1][0],points[i-1][1]))
			outv[0][j] = points[i-1][0]
			outv[1][j] = points[i-1][1]
#			pdb.gimp_message('R(%d,%3.1f,%3.1f)' % (j,outv[0][j],outv[1][j]))
			if (j >= 3): 
				break
			j = j + 1

	if (j < 3):
		raise Exception('%s need at least 4 points' % rfpath.name)
	quadToQuad(inv, outv, txm)
	height = pdb.gimp_image_height(img)
	width = pdb.gimp_image_width(img)
	x0, y0 = transform(0, 0, txm)
	x1, y1 = transform(width, 0, txm)
	x2, y2 = transform(0, height, txm)
	x3, y3 = transform(width, height, txm)	
	pdb.gimp_drawable_transform_perspective_default(layer,x0,y0,x1,y1,x2,y2,x3,y3,TRUE,clip)

# Close the undo group.
	pdb.gimp_undo_push_group_end(img)

register(
	"python_fu_ob_align",
	"Perspective align to path",
	"affine transform defined between 2 paths",
	"Oberon Leung",
	"Oberon Leung",
	"June 2015",
	"<Image>/Filters/Distorts/Align to path",
	"*",
	[
	(PF_VECTORS, "acpath", "Active path", None),
	(PF_VECTORS, "rfpath", "Reference path", None),
	(PF_OPTION, "clip", "Clip Results", 0, ["Adjust","Clip","Crop","Crop Aspect"] )
	],
	[],
	python_ob_align)

main()
