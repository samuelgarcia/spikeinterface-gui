import numpy as np
from matplotlib.path import Path as mpl_path

from .view_base import ViewBase


# TODO sam : handle segment idnex
# TODO alessio : handle lasso


class SpikeAmplitudeView(ViewBase):
    _supported_backend = ['qt', 'panel']
    _depend_on = ['spike_amplitudes']
    _settings = [
            {'name': 'alpha', 'type': 'float', 'value' : 0.7, 'limits':(0, 1.), 'step':0.05 },
            {'name': 'scatter_size', 'type': 'float', 'value' : 4., 'step':0.5 },
            {'name': 'num_bins', 'type': 'int', 'value' : 400, 'step': 1 },
            {'name': 'noise_level', 'type': 'bool', 'value' : True },
            {'name': 'noise_factor', 'type': 'int', 'value' : 5 },
        ]
    _need_compute = False
    
    def __init__(self, controller=None, parent=None, backend="qt"):
        
        # compute_amplitude_bounds
        self._amp_min = np.min(controller.spike_amplitudes)
        self._amp_max = np.max(controller.spike_amplitudes)
        eps = (self._amp_max - self._amp_min) / 100.0
        self._amp_max += eps

        ViewBase.__init__(self, controller=controller, parent=parent,  backend=backend)


    def get_unit_data(self, unit_id, seg_index=0):
        # TODO sam : handle segment idnex

        inds = self.controller.get_spike_indices(unit_id, seg_index=seg_index)
        spike_times = self.controller.spikes["sample_index"][inds] / self.controller.sampling_frequency
        spike_amps = self.controller.spike_amplitudes[inds]

        hist_count, hist_bins = np.histogram(spike_amps, bins=np.linspace(self._amp_min, self._amp_max, self.settings['num_bins']))

        return spike_times, spike_amps, hist_count, hist_bins

    def get_selected_spikes_data(self, seg_index=0):
        # TODO sam : handle segment idnex

        sl = self.controller.segment_slices[seg_index]
        spikes_in_seg = self.controller.spikes[sl]
        selected_indices = self.controller.get_indices_spike_selected()
        mask = np.isin(sl.start + np.arange(len(spikes_in_seg)), selected_indices)
        selected_spikes = spikes_in_seg[mask]
        spike_times = selected_spikes['sample_index'] / self.controller.sampling_frequency
        amps = self.controller.spike_amplitudes[sl][mask]
        return (spike_times, amps)





    ## QT zone ##

    def _qt_make_layout(self):
        from .myqt import QT
        import pyqtgraph as pg

        self.layout = QT.QVBoxLayout()
        # self.setLayout(self.layout)

        h = QT.QHBoxLayout()
        self.layout.addLayout(h)
        self.combo_seg = QT.QComboBox()
        h.addWidget(self.combo_seg)
        self.combo_seg.addItems([ f'Segment {seg_index}' for seg_index in range(self.controller.num_segments) ])
        self.combo_seg.currentIndexChanged.connect(self.refresh)
        self.lasso_but = but = QT.QPushButton("select", checkable = True)
        self.lasso_but.setMaximumWidth(50)
        h.addWidget(self.lasso_but)
        self.lasso_but.clicked.connect(self.enable_disable_lasso)

        
        h = QT.QHBoxLayout()
        self.layout.addLayout(h)
        
        self.graphicsview = pg.GraphicsView()
        #~ self.graphicsview.setHorizontalStretch(3)
        #~ self.layout.addWidget(self.graphicsview)
        h.addWidget(self.graphicsview, 3)

        self.graphicsview2 = pg.GraphicsView()
        #~ self.layout.addWidget(self.graphicsview2)
        h.addWidget(self.graphicsview2, 1)
        #~ self.graphicsview2.setHorizontalStretch(1)


        self.initialize_plot()
        
        # Add lasso curve
        self.lasso = pg.PlotCurveItem(pen='#7FFF00')
        self.plot.addItem(self.lasso)
        
        # Add selection scatter
        brush = QT.QColor('white')
        brush.setAlpha(200)
        self.scatter_select = pg.ScatterPlotItem(pen=pg.mkPen(None), brush=brush, size=11, pxMode=True)
        self.plot.addItem(self.scatter_select)
        self.scatter_select.setZValue(1000)


    
    def initialize_plot(self):
        import pyqtgraph as pg
        from .utils_qt import ViewBoxHandlingLasso

        self.viewBox = ViewBoxHandlingLasso()
        # self.viewBox.doubleclicked.connect(self.open_settings)
        self.viewBox.lasso_drawing.connect(self.on_lasso_drawing)
        self.viewBox.lasso_finished.connect(self.on_lasso_finished)
        self.viewBox.disableAutoRange()
        self.plot = pg.PlotItem(viewBox=self.viewBox)
        self.graphicsview.setCentralItem(self.plot)
        self.plot.hideButtons()
    
        self.viewBox2 = ViewBoxHandlingLasso()
        # self.viewBox2.doubleclicked.connect(self.open_settings)
        self.viewBox2.disableAutoRange()
        self.plot2 = pg.PlotItem(viewBox=self.viewBox2)
        self.graphicsview2.setCentralItem(self.plot2)
        self.plot2.hideButtons()
        self.plot2.setYLink(self.plot)

        
        self.scatter = pg.ScatterPlotItem(size=self.settings['scatter_size'], pxMode = True)
        self.plot.addItem(self.scatter)
        
        self._text_items = []
        
        self.plot.setYRange(self._amp_min,self._amp_max, padding = 0.0)

    def on_spike_selection_changed(self):
        self.refresh()

    def _qt_refresh(self):
        from .myqt import QT
        import pyqtgraph as pg
        
        self.scatter.clear()
        self.plot2.clear()
        self.scatter_select.clear()
        
        if self.controller.spike_amplitudes is None:
            return

        max_count = 1
        for unit_id in self.controller.unit_ids:
            if not self.controller.unit_visible_dict[unit_id]:
                continue

            spike_times, spike_amps, hist_count, hist_bins = self.get_unit_data(unit_id)

            # make a copy of the color
            color = QT.QColor(self.get_unit_color(unit_id))
            color.setAlpha(int(self.settings['alpha']*255))
            self.scatter.addPoints(x=spike_times, y=spike_amps,  pen=pg.mkPen(None), brush=color)

            color = self.get_unit_color(unit_id)
            curve = pg.PlotCurveItem(hist_count, hist_bins[:-1], fillLevel=None, fillOutline=True, brush=color, pen=color)
            self.plot2.addItem(curve)

            max_count = max(max_count, np.max(hist_count))

        # average noise across channels
        if self.settings["noise_level"]:
            n = self.settings["noise_factor"]
            noise = np.mean(self.controller.noise_levels)
            alpha_factor = 50 / n
            for i in range(1, n + 1):
                self.plot2.addItem(
                    pg.LinearRegionItem(values=(-i * noise, i * noise), orientation="horizontal",
                                        brush=(255, 255, 255, int(i * alpha_factor)), pen=(0, 0, 0, 0))
                )
        
        # TODO sam  seg_index
        seg_index = 0
        time_max = self.controller.get_num_samples(seg_index) / self.controller.sampling_frequency

        self.plot.setXRange( 0., time_max, padding = 0.0)
        self.plot2.setXRange(0,max_count, padding = 0.0)
        
        spike_times, amps = self.get_selected_spikes_data()
        self.scatter_select.setData(spike_times, amps)

    def enable_disable_lasso(self, checked):
        self.viewBox.lasso_active = checked

    def on_lasso_drawing(self, points):
        points = np.array(points)
        self.lasso.setData(points[:, 0], points[:, 1])
    
    def on_lasso_finished(self, points):
        self.lasso.setData([], [])
        vertices = np.array(points)
        
        seg_index = self.combo_seg.currentIndex()
        sl = self.controller.segment_slices[seg_index]
        spikes_in_seg = self.controller.spikes[sl]
        fs = self.controller.sampling_frequency
        
        # Create mask for visible units
        visible_mask = np.zeros(len(spikes_in_seg), dtype=bool)
        for unit_index, unit_id in enumerate(self.controller.unit_ids):
            if self.controller.unit_visible_dict[unit_id]:
                visible_mask |= (spikes_in_seg['unit_index'] == unit_index)
        
        # Only consider spikes from visible units
        visible_spikes = spikes_in_seg[visible_mask]
        if len(visible_spikes) == 0:
            # Clear selection if no visible spikes
            self.controller.set_indices_spike_selected([])
            self.refresh()
            self.notify_spike_selection_changed()
            return
            
        spike_times = visible_spikes['sample_index'] / fs
        amps = self.controller.spike_amplitudes[sl][visible_mask]
        
        points = np.column_stack((spike_times, amps))
        inside = mpl_path(vertices).contains_points(points)
        
        # Clear selection if no spikes inside lasso
        if not np.any(inside):
            self.controller.set_indices_spike_selected([])
            self.refresh()
            self.notify_spike_selection_changed()
            return
            
        # Map back to original indices
        visible_indices = np.nonzero(visible_mask)[0]
        selected_indices = sl.start + visible_indices[inside]
        self.controller.set_indices_spike_selected(selected_indices)
        self.refresh()
        self.notify_spike_selection_changed()



    ## Panel zone ##
    def _panel_make_layout(self):
        import panel as pn
        from .utils_panel import _bg_color
        import bokeh.plotting as bpl

        self.scatter_fig = bpl.figure(
            sizing_mode="stretch_both",
            tools="pan,box_zoom,reset,wheel_zoom,lasso_select",
            background_fill_color=_bg_color,
            border_fill_color=_bg_color,
            outline_line_color="white",
            styles={"flex": "1"}
        )
        self.scatter_fig.xaxis.axis_label = "Time (s)"
        self.scatter_fig.yaxis.axis_label = "Amplitude"

        self.hist_fig = bpl.figure(
            tools="pan,box_zoom,reset,wheel_zoom",
            sizing_mode="stretch_both",
            background_fill_color=_bg_color,
            border_fill_color=_bg_color,
            outline_line_color="white",
            styles={"flex": "1"}  # Make histogram narrower than scatter plot
        )
        self.hist_fig.yaxis.axis_label = "Amplitude"
        self.hist_fig.xaxis.axis_label = "Count"

        self.layout = pn.Row(
            pn.Column(
                self.scatter_fig,
                styles={"flex": "1"},
                sizing_mode="stretch_both"
            ),
            pn.Column(
                self.hist_fig,
                styles={"flex": "0.3"},
                sizing_mode="stretch_both"
            ),
        )

        self.scatter = None
        self.hist_lines = {}
        self.noise_harea = []


    def _panel_refresh(self):
        from bokeh.models import ColumnDataSource, HoverTool

        # clear figures
        self.hist_fig.renderers = []
        self.scatter_fig.renderers = []
        self.scatter = None
        self.hist_lines = {}
        self.noise_harea = []

        max_count = 1
        scatter_data = {"x": [], "y": [], "color": []}
        for unit_id in self.controller.unit_ids:
            if not self.controller.unit_visible_dict[unit_id]:
                continue

            spike_times, spike_amps, hist_count, hist_bins = self.get_unit_data(unit_id)
            color = self.get_unit_color(unit_id)
            scatter_data["x"].extend(spike_times)
            scatter_data["y"].extend(spike_amps)
            scatter_data["color"].extend([color] * len(spike_times))

            self.hist_lines[unit_id] = self.hist_fig.line(
                "x",
                "y",
                source=ColumnDataSource(
                    {"x":hist_count,
                     "y":hist_bins[:-1],
                     }
                ),
                line_color=color,
                line_width=2,
            )
            max_count = max(max_count, np.max(hist_count))

        # Add scatter plot with correct alpha parameter
        self.scatter = self.scatter_fig.scatter(
            "x",
            "y",
            source=scatter_data,
            size=self.settings['scatter_size'],
            color="color",
            fill_alpha=self.settings['alpha'],
        )


        if self.settings['noise_level']:
            noise = np.mean(self.controller.noise_levels)
            n = self.settings['noise_factor']
            alpha_factor = 50 / n
            for i in range(1, n + 1):
                
                h = self.hist_fig.harea(
                    y="y",
                    x1="x1",
                    x2="x2",
                    source={
                        "y": [-i * noise, i * noise],
                        "x1": [0, 0],
                        "x2": [max_count, max_count],
                    },
                    alpha=int(i * alpha_factor) / 255,  # Match Qt alpha scaling
                    color="lightgray",
                )
                self.noise_harea.append(h)

        # Set axis ranges
        # TODO sam  seg_index
        seg_index = 0
        time_max = self.controller.get_num_samples(seg_index) / self.controller.sampling_frequency
        self.scatter_fig.x_range.start = 0.
        self.scatter_fig.x_range.end = time_max
        self.scatter_fig.y_range.start = self._amp_min
        self.scatter_fig.y_range.end = self._amp_max
        self.hist_fig.x_range.start = 0
        self.hist_fig.x_range.end = max_count




SpikeAmplitudeView._gui_help_txt = """Spike Amplitude view
Check amplitudes of spikes across the recording time or in a histogram
comparing the distribution of ampltidues to the noise levels
Mouse click : change scaling
Left click drag : draw lasso to select spikes"""
