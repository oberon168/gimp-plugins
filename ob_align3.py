#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2015-2026 Oberon Leung
# GIMP 3 conversion

import sys
import gi

gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gegl', '0.4')

from gi.repository import Gimp
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import GimpUi


# ------------------------------------------------------------
# Matrix helpers
# ------------------------------------------------------------

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


def concatenate(mx, my):
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


def quadToSquare(xy, m):
    squareToQuad(xy, m)
    makeAdjoint(m)



def squareToQuad(xy, m):
    dx3 = xy[0][0] - xy[0][1] + xy[0][2] - xy[0][3]
    dy3 = xy[1][0] - xy[1][1] + xy[1][2] - xy[1][3]

    m[2][2] = 1.0

    if (dx3 == 0.0) and (dy3 == 0.0):
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



def quadToQuad(xx, yy, m):
    my = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]

    quadToSquare(xx, m)
    squareToQuad(yy, my)
    concatenate(m, my)
    normalize(m)



def transform(x, y, m):
    w = (m[2][0] * x) + (m[2][1] * y) + m[2][2]

    xx = int(((m[0][0] * x) + (m[0][1] * y) + m[0][2]) / w)
    yy = int(((m[1][0] * x) + (m[1][1] * y) + m[1][2]) / w)

    return (xx, yy)


# ------------------------------------------------------------
# Main processing
# ------------------------------------------------------------

def ob_align_run(procedure, run_mode, image, drawables, config, data):

    if len(drawables) < 1:
        return procedure.new_return_values(
            Gimp.PDBStatusType.CALLING_ERROR,
            GLib.Error()
        )

    layer = drawables[0]

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init("python-fu-ob-align")
        dialog = GimpUi.ProcedureDialog.new(
            procedure,
            config
        )
        dialog.fill(['acpath', 'rfpath'])
        response = dialog.run()
        dialog.destroy()
        if not response:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CANCEL,
                GLib.Error()
            )
    acpath = config.get_property('acpath')
    rfpath = config.get_property('rfpath')
    image.undo_group_start()

    try:
        inv = [[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0]]
        outv = [[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0]]
        txm = [[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]

        strokes = acpath.get_strokes()
        print(len(strokes))
        j = 0
        for stroke_id in acpath.get_strokes():
            dtype, points, closed = acpath.stroke_get_points(stroke_id)
            for i in range(0, len(points), 6):
                inv[0][j] = points[i+2]
                inv[1][j] = points[i+3]

                if j >= 3:
                    break

                j += 1

        if j < 3:
            raise Exception(f'{acpath.get_name()} needs at least 4 points')

        j = 0

        for stroke_id in rfpath.get_strokes():
            type, points, closed = rfpath.stroke_get_points(stroke_id)
            for i in range(0, len(points), 6):
                outv[0][j] = points[i+2]
                outv[1][j] = points[i+3]

                if j >= 3:
                    break

                j += 1

        if j < 3:
            raise Exception(f'{rfpath.get_name()} needs at least 4 points')

        quadToQuad(inv, outv, txm)

        height = image.get_height()
        width = image.get_width()

        x0, y0 = transform(0, 0, txm)
        x1, y1 = transform(width, 0, txm)
        x2, y2 = transform(0, height, txm)
        x3, y3 = transform(width, height, txm)

        pdb = Gimp.get_pdb()
        proc = pdb.lookup_procedure('gimp-item-transform-perspective')

        if proc is None:
            raise Exception('Could not find gimp-item-transform-perspective')

        cfg = proc.create_config()

        cfg.set_property('item', layer)
        cfg.set_property('x0', float(x0))
        cfg.set_property('y0', float(y0))
        cfg.set_property('x1', float(x1))
        cfg.set_property('y1', float(y1))
        cfg.set_property('x2', float(x2))
        cfg.set_property('y2', float(y2))
        cfg.set_property('x3', float(x3))
        cfg.set_property('y3', float(y3))

        proc.run(cfg)

    except Exception as e:
        image.undo_group_end()

        return procedure.new_return_values(
            Gimp.PDBStatusType.EXECUTION_ERROR,
            GLib.Error.new_literal(
                Gimp.PlugIn.error_quark(),
                str(e),
                0
            )
        )

    image.undo_group_end()

    return procedure.new_return_values(
        Gimp.PDBStatusType.SUCCESS,
        GLib.Error()
    )


# ------------------------------------------------------------
# Plugin class
# ------------------------------------------------------------

class ObAlignPlugin(Gimp.PlugIn):

    def do_set_i18n(self, procname):
        return False

    def do_query_procedures(self):
        return ['python-fu-ob-align']


    def do_create_procedure(self, name):

        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            ob_align_run,
            None
        )

        procedure.set_image_types('*')

        procedure.set_menu_label('Align to path')

        procedure.add_menu_path('<Image>/Filters/Distorts')

        procedure.set_documentation(
            'Perspective align to path',
            'Affine transform defined between 2 paths',
            name
        )

        procedure.set_attribution(
            'Oberon Leung',
            'Oberon Leung',
            '2015-2026'
        )

        procedure.add_path_argument(
            'acpath',
            '_Initial path',
            'Select original path',
            False,
            GObject.ParamFlags.READWRITE
        )

        procedure.add_path_argument(
            'rfpath',
            '_New path',
            'Select desired path',
            False,
            GObject.ParamFlags.READWRITE
        )

        # procedure.add_int_argument(
        #     'clip',
        #     'Clip Results',
        #     '0=Adjust, 1=Clip, 2=Crop, 3=Crop Aspect',
        #     0,
        #     3,
        #     0,
        #     GObject.ParamFlags.READWRITE
        # )

        return procedure


Gimp.main(ObAlignPlugin.__gtype__, sys.argv)