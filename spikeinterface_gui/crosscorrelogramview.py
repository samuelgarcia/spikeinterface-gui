from .view_base import ViewBase



class CrossCorrelogramView(ViewBase):
    _supported_backend = ['qt']
    _settings = [
                      {'name': 'window_ms', 'type': 'float', 'value' : 50. },
                      {'name': 'bin_ms', 'type': 'float', 'value' : 1.0 },
                      {'name': 'display_axis', 'type': 'bool', 'value' : True },
                      {'name': 'max_visible', 'type': 'int', 'value' : 8 },
        ]
    
    _need_compute = True

    def __init__(self, controller=None, parent=None, backend="qt"):
        ViewBase.__init__(self, controller=controller, parent=parent,  backend=backend)

        self.ccg, self.bins = self.controller.get_correlograms()


    def _qt_make_layout(self):
        from .myqt import QT
        import pyqtgraph as pg

        self.layout = QT.QVBoxLayout()
        # self.setLayout(self.layout)
        
        h = QT.QHBoxLayout()
        self.layout.addLayout(h)

        self.grid = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.grid)

    def _panel_make_layout(self):
        raise NotImplementedError
    
    def _on_settings_changed(self):
        self.ccg = None
        self.refresh()

    def compute(self):
        self.ccg, self.bins = self.controller.compute_correlograms(
                self.settings['window_ms'],  self.settings['bin_ms'])
        self.refresh()

    def _qt_refresh(self):
        import pyqtgraph as pg

        self.grid.clear()
        
        if self.ccg is None:
            return
        
        visible_unit_ids = [ ]
        for unit_id in self.controller.unit_ids:
            if self.controller.unit_visible_dict[unit_id]:
                visible_unit_ids.append(unit_id)

        visible_unit_ids = visible_unit_ids[:self.settings['max_visible']]
        
        n = len(visible_unit_ids)
        
        unit_ids = list(self.controller.unit_ids)
        
        for r in range(n):
            for c in range(r, n):
                
                i = unit_ids.index(visible_unit_ids[r])
                j = unit_ids.index(visible_unit_ids[c])
                
                count = self.ccg[i, j, :]
                
                plot = pg.PlotItem()
                if not self.settings['display_axis']:
                    plot.hideAxis('bottom')
                    plot.hideAxis('left')
                
                if r==c:
                    unit_id = visible_unit_ids[r]
                    color = self.get_unit_color(unit_id)
                else:
                    color = (120,120,120,120)
                
                curve = pg.PlotCurveItem(self.bins, count, stepMode='center', fillLevel=0, brush=color, pen=color)
                plot.addItem(curve)
                self.grid.addItem(plot, row=r, col=c)

    def _panel_refresh(self):
        raise(NotImplementedError)


CrossCorrelogramView._gui_help_txt = """Crosscorrelogram of units/autocorrelogram of one unit
Shows only the selected unit(s).
Settings control the bin size in ms.
Right mouse : zoom
Left mouse : drags the correlograms"""



# ####################

# class MyViewBox(pg.ViewBox):
#     doubleclicked = QT.pyqtSignal()
#     def mouseDoubleClickEvent(self, ev):
#         self.doubleclicked.emit()
#         ev.accept()
#     def raiseContextMenu(self, ev):
#         #for some reasons enableMenu=False is not taken (bug ????)
#         pass



# class CrossCorrelogramView(WidgetBase):
#     _settings = [
#                       {'name': 'window_ms', 'type': 'float', 'value' : 50. },
#                       {'name': 'bin_ms', 'type': 'float', 'value' : 1.0 },
#                       #~ {'name': 'symmetrize', 'type': 'bool', 'value' : True },
#                       {'name': 'display_axis', 'type': 'bool', 'value' : True },
#                       {'name': 'max_visible', 'type': 'int', 'value' : 8 },
#                       #~ {'name': 'check_sorted', 'type': 'bool', 'value' : False },
#         ]
    
#     _need_compute = True
#     def __init__(self, controller=None, parent=None):
#         WidgetBase.__init__(self, parent=parent, controller=controller)
        
#         self.layout = QT.QVBoxLayout()
#         self.setLayout(self.layout)
        
#         h = QT.QHBoxLayout()
#         self.layout.addLayout(h)

#         self.grid = pg.GraphicsLayoutWidget()
#         self.layout.addWidget(self.grid)
        
#         self.ccg, self.bins = self.controller.get_correlograms()

#     def on_params_changed(self):
#         self.ccg = None
#         self.refresh()
    
#     def compute(self):
#         self.ccg, self.bins = self.controller.compute_correlograms(
#                 self.settings['window_ms'],  self.settings['bin_ms'])
#         self.refresh()

#     def _refresh(self):
#         self.grid.clear()
        
#         if self.ccg is None:
#             return
        
#         visible_unit_ids = [ ]
#         for unit_id in self.controller.unit_ids:
#             if self.controller.unit_visible_dict[unit_id]:
#                 visible_unit_ids.append(unit_id)

#         visible_unit_ids = visible_unit_ids[:self.settings['max_visible']]
        
#         n = len(visible_unit_ids)
        
#         unit_ids = list(self.controller.unit_ids)
        
#         for r in range(n):
#             for c in range(r, n):
                
#                 i = unit_ids.index(visible_unit_ids[r])
#                 j = unit_ids.index(visible_unit_ids[c])
                
#                 count = self.ccg[i, j, :]
                
#                 plot = pg.PlotItem()
#                 if not self.settings['display_axis']:
#                     plot.hideAxis('bottom')
#                     plot.hideAxis('left')
                
#                 if r==c:
#                     unit_id = visible_unit_ids[r]
#                     color = self.controller.qcolors[unit_id]
#                 else:
#                     color = (120,120,120,120)
                
#                 curve = pg.PlotCurveItem(self.bins, count, stepMode='center', fillLevel=0, brush=color, pen=color)
#                 plot.addItem(curve)
#                 self.grid.addItem(plot, row=r, col=c)


# CrossCorrelogramView._gui_help_txt = """Crosscorrelogram of units/autocorrelogram of one unit
# Shows only the selected unit(s).
# Settings control the bin size in ms.
# Right mouse : zoom
# Left mouse : drags the correlograms"""
