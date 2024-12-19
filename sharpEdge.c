#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>

typedef struct
{
	gint	 radius;
	gint     threshold;
	gboolean preview;
} MyParaVals;

static void query(void);
static void run(const gchar      *name,
	gint              nparams,
	const GimpParam  *param,
	gint             *nreturn_vals,
	GimpParam       **return_vals);

static void sharpEdge(GimpDrawable     *drawable,
	GimpPreview      *preview);

static void init_mem(guchar         ***row,

	gint              num_bytes);

static void process_row(guchar          **row,

	gint              width,
	gint              height,
	gint              channels);

static void shuffle(GimpPixelRgn     *rgn_in,
	guchar          **row,

	gint              x1,
	gint              y1,
	gint              width,

	gint              ypos);

static gboolean sharpEdge_dialog(GimpDrawable *drawable);

/* Set up default values for options */
static MyParaVals bvals =
{
	4,	/* radius */
	20,  /* threshold */
	1   /* preview */
};

GimpPlugInInfo PLUG_IN_INFO =
{
	NULL,
	NULL,
	query,
	run
};

MAIN()

static void
query(void)
{
	static GimpParamDef args[] =
	{
		{
			GIMP_PDB_INT32,
			"run-mode",
			"Run mode"
		},
		{
			GIMP_PDB_IMAGE,
			"image",
			"Input image"
		},
		{
			GIMP_PDB_DRAWABLE,
			"drawable",
			"Input drawable"
		},
		{
			GIMP_PDB_INT32,
			"radius",
			"Radius"
		},
		{
			GIMP_PDB_INT32,
				"threshold",
				"Threshold"
		}
	};

	gimp_install_procedure(
		"plug-in-sharpEdge",
		"Sharp Edge (preview)",
		"Sharp the image Edge",
		"Oberon Leung",
		"Copyright Oberon Leung",
		"Oct 2014",
		"Sharp Edge (preview)",
		"RGB*, GRAY*",
		GIMP_PLUGIN,
		G_N_ELEMENTS(args), 0,
		args, NULL);

	gimp_plugin_menu_register("plug-in-sharpEdge",
		"<Image>/Filters/Enhance");
}

static void
run(const gchar      *name,
gint              nparams,
const GimpParam  *param,
gint             *nreturn_vals,
GimpParam       **return_vals)
{
	static GimpParam  values[1];
	GimpPDBStatusType status = GIMP_PDB_SUCCESS;
	GimpRunMode       run_mode;
	GimpDrawable     *drawable;

	/* Setting mandatory output values */
	*nreturn_vals = 1;
	*return_vals = values;

	values[0].type = GIMP_PDB_STATUS;
	values[0].data.d_status = status;

	/* Getting run_mode - we won't display a dialog if
	* we are in NONINTERACTIVE mode */
	run_mode = param[0].data.d_int32;

	/*  Get the specified drawable  */
	drawable = gimp_drawable_get(param[2].data.d_drawable);

	switch (run_mode)
	{
	case GIMP_RUN_INTERACTIVE:
		/* Get options last values if needed */
		gimp_get_data("plug-in-sharpEdge", &bvals);

		/* Display the dialog */
		if (!sharpEdge_dialog(drawable))
			return;
		break;

	case GIMP_RUN_NONINTERACTIVE:
		if (nparams != 5)
			status = GIMP_PDB_CALLING_ERROR;
		if (status == GIMP_PDB_SUCCESS) {
			bvals.radius = param[3].data.d_int32;
			bvals.threshold = param[4].data.d_int32;
		}
		break;

	case GIMP_RUN_WITH_LAST_VALS:
		/*  Get options last values if needed  */
		gimp_get_data("plug-in-sharpEdge", &bvals);
		break;

	default:
		break;
	}

	sharpEdge(drawable, NULL);

	gimp_displays_flush();
	gimp_drawable_detach(drawable);

	/*  Finally, set options in the core  */
	if (run_mode == GIMP_RUN_INTERACTIVE)
		gimp_set_data("plug-in-sharpEdge", &bvals, sizeof(MyParaVals));

	return;
}

static void
sharpEdge(GimpDrawable *drawable,
GimpPreview  *preview)
{
	gint         i, ii, channels;
	gint         x1, y1, x2, y2;
	GimpPixelRgn rgn_in, rgn_out;
	guchar     **row;

	gint         width, height;

	if (!preview)
		gimp_progress_init("Sharp Edge...");

	/* Gets upper left and lower right coordinates,
	* and layers number in the image */
	if (preview)
	{
		gimp_preview_get_position(preview, &x1, &y1);
		gimp_preview_get_size(preview, &width, &height);
		x2 = x1 + width;
		y2 = y1 + height;
	}
	else
	{
		gimp_drawable_mask_bounds(drawable->drawable_id,
			&x1, &y1,
			&x2, &y2);
		width = x2 - x1;
		height = y2 - y1;
	}

	channels = gimp_drawable_bpp(drawable->drawable_id);

	/* Allocate a big enough tile cache */
	gimp_tile_cache_ntiles(bvals.radius * (drawable->width / gimp_tile_width() + 1));

	/* Initialises two PixelRgns, one to read original data,
	* and the other to write output data. That second one will
	* be merged at the end by the call to
	* gimp_drawable_merge_shadow() */
	gimp_pixel_rgn_init(&rgn_in,
		drawable,
		x1, y1,
		width, height,
		FALSE, FALSE);
	gimp_pixel_rgn_init(&rgn_out,
		drawable,
		x1, y1,
		width, height,
		preview == NULL, TRUE);

	/* Allocate memory for input and output tile rows */
	init_mem(&row, width * channels);

	for (ii = 0; ii < bvals.radius; ii++)
	{
		gimp_pixel_rgn_get_row(&rgn_in,
			row[ii],
			x1, y1 + ii,
			width);
	}


	for (i = 0; i < height-bvals.radius+1; i++)	{
		/* To be done for each tile row */
		process_row(row, width, height,	channels);
		gimp_pixel_rgn_set_row(&rgn_out,row[0],	x1, y1 + i,	width);
		/* shift tile rows to insert the new one at the end */
		shuffle(&rgn_in, row, x1, y1, width, i);

		if (!preview && i % 16 == 0)
			gimp_progress_update((gdouble)i / (gdouble)height);
	}
	for (ii=0; i < height; i++)	{
		gimp_pixel_rgn_set_row(&rgn_out,row[ii++],x1, y1 + i,width);
	}

	/* We could also put that in a separate function but it's
	* rather simple */
	for (ii = 0; ii < bvals.radius; ii++) {
		g_free(row[ii]);
	}
	g_free(row);

	/*  Update the modified region */
	if (preview) {
		gimp_drawable_preview_draw_region(GIMP_DRAWABLE_PREVIEW(preview),&rgn_out);
	}
	else {
		gimp_drawable_flush(drawable);
		gimp_drawable_merge_shadow(drawable->drawable_id, TRUE);
		gimp_drawable_update(drawable->drawable_id,	x1, y1,	width, height);
	}
}

static void
init_mem(guchar ***row,

gint      num_bytes)
{
	gint i;

	/* Allocate enough memory for row */
	*row = g_new(guchar *, bvals.radius);

	for (i = 0; i < bvals.radius; i++) {
		(*row)[i] = g_new(guchar, num_bytes);
	}
}

static void
process_row(guchar **row,

gint     width,
gint     height,
gint     channels
)
{
	gint j, pos = 0;
	gint lastp;

	lastp = bvals.radius - 1;
#if 1
	for (j = 0; j < width- lastp; j++)
	{
		gint k;

		for (k = 0; k < channels; k++)
		{
			gint dif, lfc, rgc;
			gint sign;

			dif = (0xff & row[0][pos + k]) - (0xff & row[lastp][pos + k]);
			if (dif >= bvals.threshold || -dif >= bvals.threshold) {
				gint lp, rp;

				/* is mono direction */
				for (lp = 1; lp < bvals.radius; ++lp) {
					if (dif > 0 && (0xff & row[lp-1][pos + k]) < (0xff & row[lp][pos + k]))
						break;
					if (dif < 0 && (0xff & row[lp - 1][pos + k]) > (0xff & row[lp][pos + k]))
						break;
				}
				if (lp >= bvals.radius) {
					if (dif > 0) {
						sign = 1;
					}
					else {
						sign = -1;
					}
					
					lp = 1;
					rp = bvals.radius - 1;
					while (lp < rp-1) {
						lfc = ((0xff & row[lp - 1][pos + k]) - (0xff & row[lp][pos + k])) * sign;
						rgc = ((0xff & row[rp - 1][pos + k]) - (0xff & row[rp][pos + k])) * sign;
						if (lfc >= rgc) {
							row[rp - 1][pos + k] = (row[rp - 1][pos + k] & 0xff) - rgc * sign;
							row[lp][pos + k] = (row[lp][pos + k] & 0xff) + rgc * sign;
							--rp;
							if (lfc == rgc)
								++lp;
						}
						else {
							row[lp][pos + k] = (row[lp][pos + k] & 0xff) + lfc * sign;
							row[rp-1][pos + k] = (row[rp-1][pos + k] & 0xff) - lfc * sign;
							++lp;
						}
					}
				}
			}
		}
		pos += channels;
	}
#endif
#if 1
	pos = 0;
	for (j = 0; j < width-lastp; j++)
	{
		gint k;

		for (k = 0; k < channels; k++)
		{
			gint dif, lfc, rgc;
			gint sign;
		
			dif = (0xff & row[0][pos + k]) - (0xff & row[0][pos + k+channels*3]);
			if (dif >= bvals.threshold || -dif >= bvals.threshold) {
				gint lp, rp;

				/* is mono direction */
				for (lp = 1; lp < bvals.radius; ++lp) {
					if (dif > 0 && (0xff & row[0][pos + k+channels*(lp-1)]) < (0xff & row[0][pos + k+channels*lp]))
						break;
					if (dif < 0 && (0xff & row[0][pos + k+channels*(lp-1)]) >(0xff & row[0][pos + k + channels*lp]))
						break;
				}
				if (lp >= bvals.radius) {
					if (dif > 0) {
						sign = 1;
					}
					else {
						sign = -1;
					}

					lp = 1;
					rp = bvals.radius - 1;
					while (lp < rp - 1) {
						lfc = ((0xff & row[0][pos + k+channels*(lp-1)]) - (0xff & row[0][pos + k+channels*(lp)])) * sign;
						rgc = ((0xff & row[0][pos + k+channels*(rp-1)]) - (0xff & row[0][pos + k+channels*(rp)])) * sign;
						if (lfc >= rgc) {
							row[0][pos + k+channels*(lp)] = (row[0][pos + k+channels*(lp)] & 0xff) + rgc * sign;
							row[0][pos + k+channels*(rp-1)] = (row[0][pos + k+channels*(rp-1)] & 0xff) - rgc * sign;
							--rp;
						}
						else {
							row[0][pos + k+channels*(lp)] = (row[0][pos + k+channels*lp] & 0xff) + lfc * sign;
							row[0][pos + k+channels*(rp-1)] = (row[0][pos + k+channels*(rp-1)] & 0xff) - lfc * sign;
							++lp;
						}
					}
				}
			}
		}
		pos += channels;
	}
#endif
}

static void
shuffle(GimpPixelRgn *rgn_in,
guchar      **row,
gint          x1,
gint          y1,
gint          width,
gint          ypos)
{
	guchar *tmp_row1;
	gint ir;
	/* Get tile row (i + threshold + 1) into row[0] */
	gimp_pixel_rgn_get_row(rgn_in,row[0],x1, ypos + y1 + bvals.radius,width);

	tmp_row1 = row[0];
	for (ir = 1; ir < bvals.radius; ++ir) {
		row[ir-1] = row[ir];
	}
	row[bvals.radius-1] = tmp_row1;
}

static gboolean
sharpEdge_dialog(GimpDrawable *drawable)
{
	GtkWidget *dialog;
	GtkWidget *main_vbox;
	GtkWidget *main_hbox;
	GtkWidget *preview;
	GtkWidget *frame;
	GtkWidget *threshold_label;
	GtkWidget *radius_label;
	GtkWidget *alignment;
	GtkWidget *spinbutton;
	GtkObject *spinbutton1_adj;
	GtkWidget *spinbutton1;
	GtkObject *spinbutton_adj;
	GtkWidget *frame_label;
	gboolean   run;

	gimp_ui_init("Sharp Edge", FALSE);

	dialog = gimp_dialog_new("Sharp Edge", "sharpEdge",
		NULL, 0,
		gimp_standard_help_func, "plug-in-sharpEdge",

		GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL,
		GTK_STOCK_OK, GTK_RESPONSE_OK,

		NULL);

	main_vbox = gtk_vbox_new(FALSE, 6);
	gtk_container_add(GTK_CONTAINER(GTK_DIALOG(dialog)->vbox), main_vbox);
	gtk_widget_show(main_vbox);

	preview = gimp_drawable_preview_new(drawable, &bvals.preview);
	gtk_box_pack_start(GTK_BOX(main_vbox), preview, TRUE, TRUE, 0);
	gtk_widget_show(preview);

	frame = gtk_frame_new(NULL);
	gtk_widget_show(frame);
	gtk_box_pack_start(GTK_BOX(main_vbox), frame, TRUE, TRUE, 0);
	gtk_container_set_border_width(GTK_CONTAINER(frame), 6);

	alignment = gtk_alignment_new(0.5, 0.5, 1, 1);
	gtk_widget_show(alignment);
	gtk_container_add(GTK_CONTAINER(frame), alignment);
	gtk_alignment_set_padding(GTK_ALIGNMENT(alignment), 6, 6, 6, 6);

	main_hbox = gtk_hbox_new(FALSE, 0);
	gtk_widget_show(main_hbox);
	gtk_container_add(GTK_CONTAINER(alignment), main_hbox);
	/* radius */
	radius_label = gtk_label_new_with_mnemonic("_radius:");
	gtk_widget_show(radius_label);
	gtk_box_pack_start(GTK_BOX(main_hbox), radius_label, FALSE, FALSE, 6);
	gtk_label_set_justify(GTK_LABEL(radius_label), GTK_JUSTIFY_RIGHT);
	/* spin button*/
	spinbutton1 = gimp_spin_button_new(&spinbutton1_adj, bvals.radius,
		4, 20, 1, 1, 1, 1, 0);
	gtk_box_pack_start(GTK_BOX(main_hbox), spinbutton1, FALSE, FALSE, 0);
	gtk_widget_show(spinbutton1);
	/* threshold */
	threshold_label = gtk_label_new_with_mnemonic("_threshold:");
	gtk_widget_show(threshold_label);
	gtk_box_pack_start(GTK_BOX(main_hbox), threshold_label, FALSE, FALSE, 6);
	gtk_label_set_justify(GTK_LABEL(threshold_label), GTK_JUSTIFY_RIGHT);
	/* spin button */
	spinbutton = gimp_spin_button_new(&spinbutton_adj, bvals.threshold,
		1, 128, 5, 1, 1, 5, 0);
	gtk_box_pack_start(GTK_BOX(main_hbox), spinbutton, FALSE, FALSE, 0);
	gtk_widget_show(spinbutton);

	frame_label = gtk_label_new("<b>Modify parameters</b>");
	gtk_widget_show(frame_label);
	gtk_frame_set_label_widget(GTK_FRAME(frame), frame_label);
	gtk_label_set_use_markup(GTK_LABEL(frame_label), TRUE);

	g_signal_connect_swapped(preview, "invalidated",
		G_CALLBACK(sharpEdge),
		drawable);
	g_signal_connect_swapped(spinbutton_adj, "value_changed",
		G_CALLBACK(gimp_preview_invalidate),
		preview);

	sharpEdge(drawable, GIMP_PREVIEW(preview));

	g_signal_connect(spinbutton_adj, "value_changed",
		G_CALLBACK(gimp_int_adjustment_update),
		&bvals.threshold);
	g_signal_connect(spinbutton1_adj, "value_changed",
		G_CALLBACK(gimp_int_adjustment_update),
		&bvals.radius);
	gtk_widget_show(dialog);

	run = (gimp_dialog_run(GIMP_DIALOG(dialog)) == GTK_RESPONSE_OK);

	gtk_widget_destroy(dialog);

	return run;
}