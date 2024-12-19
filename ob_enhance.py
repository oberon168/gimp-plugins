#!/usr/bin/env python
#   Copyright (C) 2015 Oberon Leung
from gimpfu import *

def python_ob_enhance(img, layer) :

# Set up an undo group, so the operation will be undone in one step.
	pdb.gimp_undo_push_group_start(img)

# console
# img = gimp.image_list()[0]
# layer = pdb.gimp_image_get_active_layer(img)
	
#luminosity
	mlayer = pdb.gimp_layer_copy(layer, False)
	pdb.gimp_image_insert_layer(img, mlayer, None, -1)
	pdb.gimp_desaturate_full(mlayer, DESATURATE_LUMINOSITY)
	pdb.gimp_layer_set_mode(mlayer,GRAIN_EXTRACT_MODE)
	pdb.gimp_item_set_name(mlayer, "shadow")
#color
	clayer = pdb.gimp_layer_new_from_visible(img, img, "shadow")
	pdb.gimp_image_insert_layer(img, clayer, None, -1)
	pdb.gimp_item_set_name(clayer, "color")
	pdb.gimp_layer_set_mode(clayer,GRAIN_MERGE_MODE)
	pdb.gimp_layer_set_opacity(clayer, 20)
	pdb.gimp_item_set_visible(clayer, FALSE)
#shadow
	pdb.gimp_invert(mlayer)
	mask = pdb.gimp_layer_create_mask(mlayer, ADD_COPY_MASK)
	pdb.gimp_layer_add_mask(mlayer, mask)
	pdb.gimp_layer_set_mode(mlayer,OVERLAY_MODE)
	pdb.gimp_layer_set_opacity(mlayer, 50)
	pdb.gimp_item_set_visible(mlayer, FALSE)
#brightness
	blayer = pdb.gimp_layer_copy(mlayer, False)
	pdb.gimp_image_insert_layer(img, blayer, None, -1)
#	mask = pdb.gimp_layer_create_mask(blayer, ADD_COPY_MASK)
#	pdb.gimp_layer_add_mask(blayer, mask)
	mask = pdb.gimp_layer_get_mask(blayer)
	pdb.gimp_invert(mask)
	pdb.gimp_layer_set_mode(blayer,OVERLAY_MODE)
	pdb.gimp_item_set_name(blayer, "brightness")
	pdb.gimp_layer_set_opacity(blayer, 20)
	pdb.gimp_item_set_visible(blayer, FALSE)
#sharpness
	pdb.gimp_image_set_active_layer(img, layer)
#	pdb.python_fu_ob_us2m(img, layer, 4.0)
	pdb.python_fu_ob_usmlayer(img, layer, 4.0)
	tlayer = pdb.gimp_image_get_active_layer(img)
	pdb.gimp_item_set_name(tlayer, "sharpness")
	pdb.gimp_layer_set_opacity(tlayer, 50)
	pdb.gimp_item_set_visible(tlayer, FALSE)
#contrast	
	pdb.gimp_image_set_active_layer(img, layer)	
#	pdb.python_fu_ob_us2m(img, layer, 50.0)
	pdb.python_fu_ob_usmlayer(img, layer, 50.0)
	llayer = pdb.gimp_image_get_active_layer(img)
	pdb.gimp_item_set_name(llayer, "contrast")
	pdb.gimp_layer_set_opacity(llayer, 20)
	pdb.gimp_item_set_visible(clayer, TRUE)
	pdb.gimp_item_set_visible(mlayer, TRUE)
	pdb.gimp_item_set_visible(tlayer, TRUE)
	pdb.gimp_item_set_visible(blayer, TRUE)
	
# Close the undo group.
	pdb.gimp_undo_push_group_end(img)

register(
	"python_fu_ob_enhance",
	"enhance color, contrast, shadow and sharpness",
	"create adjustment layers of color, contrast, shadow/brightness and sharpness",
	"Oberon Leung",
	"Oberon Leung",
	"24-05-2015",
	"<Image>/Filters/Enhance/Enhance CCSS",
	"RGB*",
	[
	],
	[],
	python_ob_enhance)

main()
