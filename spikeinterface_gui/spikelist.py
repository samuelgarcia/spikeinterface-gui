import numpy as np


from .view_base import ViewBase


_columns = ['num', 'unit_id', 'segment', 'sample_index', 'channel_index', 'rand_selected']


# class SpikeModel(QT.QAbstractItemModel):

#     def __init__(self, parent =None, controller=None):
#         QT.QAbstractItemModel.__init__(self,parent)
#         self.controller = controller
#         self.refresh_colors()
        
#         self.visible_ind = self.controller.get_indices_spike_visible()
    
#     def columnCount(self , parentIndex):
#         return len(_columns)
    
#     def rowCount(self, parentIndex):
#         if not parentIndex.isValid():
#             return int(self.visible_ind.size)
#         else :
#             return 0
    
#     def index(self, row, column, parentIndex):
#         if not parentIndex.isValid():
#             return self.createIndex(row, column, None)
#         else:
#             return QT.QModelIndex()

#     def parent(self, index):
#         return QT.QModelIndex()
    
#     def data(self, index, role):
        
#         if not index.isValid():
#             return None
        
#         if role not in (QT.Qt.DisplayRole, QT.Qt.DecorationRole):
#             return
        
#         col = index.column()
#         row = index.row()
        
#         abs_ind = self.visible_ind[row]
#         spike = self.controller.spikes[abs_ind]
#         unit_id = self.controller.unit_ids[spike['unit_index']]
        
#         if role ==QT.Qt.DisplayRole :
#             if col == 0:
#                 return '{}'.format(abs_ind)
#             elif col == 1:
#                 return '{}'.format(unit_id)
#             elif col == 2:
#                 return '{}'.format(spike['segment_index'])
#             elif col == 3:
#                 return '{}'.format(spike['sample_index'])
#             elif col == 4:
#                 return '{}'.format(spike['channel_index'])
#             elif col == 5:
#                 return '{}'.format(spike['rand_selected'])
#             else:
#                 return None
#         elif role == QT.Qt.DecorationRole :
#             if col != 0:
#                 return None
#             if unit_id in self.icons:
#                 return self.icons[unit_id]
#             else:
#                 return None
#         else :
#             return None
        
    
#     def flags(self, index):
#         if not index.isValid():
#             return QT.Qt.NoItemFlags
#         return QT.Qt.ItemIsEnabled | QT.Qt.ItemIsSelectable #| Qt.ItemIsDragEnabled

#     def headerData(self, section, orientation, role):
#         if orientation == QT.Qt.Horizontal and role == QT.Qt.DisplayRole:
#             return  _columns[section]
#         return

#     def refresh_colors(self):
#         self.icons = { }
#         for unit_id, qcolor in self.controller.qcolors.items():
#             pix = QT.QPixmap(10,10 )
#             pix.fill(qcolor)
#             self.icons[unit_id] = QT.QIcon(pix)
    
#     def refresh(self):
#         self.visible_ind = self.controller.get_indices_spike_visible()
#         self.layoutChanged.emit()

#     def clear(self):
#         self.visible_ind = np.array([])
#         self.layoutChanged.emit()


class SpikeListView(ViewBase):
    _supported_backend = ['qt']
    _settings = [
            {'name': 'select_change_channel_visibility', 'type': 'bool', 'value': False},
        ]    
    
    
    def __init__(self, controller=None, parent=None, backend="qt"):
        ViewBase.__init__(self, controller=controller, parent=parent,  backend=backend)

    def _qt_make_layout(self):
        from .myqt import QT

        # this getter is to protect import QT
        SpikeModel = get_qt_spike_model()
        
        self.layout = QT.QVBoxLayout()
        
        h = QT.QHBoxLayout()
        self.layout.addLayout(h)
        
        self.label = QT.QLabel('') 
        h.addWidget(self.label)
        
        h.addStretch()

        but = QT.QPushButton('↻ spikes')
        h.addWidget(but)
        but.clicked.connect(self.refresh)
        
        self.tree = QT.QTreeView(minimumWidth = 100, uniformRowHeights = True,
                    selectionMode= QT.QAbstractItemView.ExtendedSelection, selectionBehavior = QT.QTreeView.SelectRows,
                    contextMenuPolicy = QT.Qt.CustomContextMenu,)

        
        self.layout.addWidget(self.tree)
        
        self.model = SpikeModel(controller=self.controller, columns=_columns)
        qcolors = {unit_id:self.get_unit_color(unit_id) for unit_id in self.controller.unit_ids}
        self.model.refresh_colors(qcolors)

        self.tree.setModel(self.model)
        self.tree.selectionModel().selectionChanged.connect(self.on_tree_selection)

        for i in range(self.model.columnCount(None)):
            self.tree.resizeColumnToContents(i)
        self.tree.setColumnWidth(0,80)
        
    
    def refresh_label(self):
        n1 = self.controller.spikes.size
        n2 = self.controller.get_indices_spike_visible().size
        n3 = self.controller.get_indices_spike_selected().size
        txt = f'<b>All spikes</b> : {n1} - <b>visible</b> : {n2} - <b>selected</b> : {n3}'
        self.label.setText(txt)
   
    def _refresh(self):
        self.refresh_label()
        self.model.refresh()
    
    def on_tree_selection(self):
        inds = []
        for index in self.tree.selectedIndexes():
            if index.column() == 0:
                ind = self.model.visible_ind[index.row()]
                inds.append(ind)
        self.controller.set_indices_spike_selected(inds)
        self.notify_spike_selection_changed()
        if len(inds) == 1 and self.settings['select_change_channel_visibility']:
            # also change channel for centering trace view.
            sparsity_mask = self.controller.get_sparsity_mask()
            unit_index = self.controller.spikes[inds[0]]['unit_index']
            visible_channel_inds, = np.nonzero(sparsity_mask[unit_index, :])

            # check ifchannel visibility must be changed
            if not np.all(np.isin(visible_channel_inds, self.controller.visible_channel_inds)):
                self.controller.set_channel_visibility(visible_channel_inds)
                self.channel_visibility_changed.emit()
        
        self.refresh_label()
    
    def _qt_on_unit_visibility_changed(self):
        # we cannot refresh this list in real time whil moving channel/unit visibility
        # it is too slow.
        self.refresh_label()
        self.model.clear()

    def _qt_on_spike_selection_changed(self):
        from .myqt import QT
        self.tree.selectionModel().selectionChanged.disconnect(self.on_tree_selection)
        
        selected_inds  = self.controller.get_indices_spike_selected()
        visible_inds = self.controller.get_indices_spike_visible()
        row_selected,  = np.nonzero(np.isin(visible_inds, selected_inds))
        
        
        if row_selected.size>100:#otherwise this is verry slow
            row_selected = row_selected[:10]
        
        # change selection
        self.tree.selectionModel().clearSelection()
        flags = QT.QItemSelectionModel.Select #| QItemSelectionModel.Rows
        itemsSelection = QT.QItemSelection()
        for r in row_selected:
            for c in range(2):
                index = self.tree.model().index(r,c,QT.QModelIndex())
                ir = QT.QItemSelectionRange( index )
                itemsSelection.append(ir)
        self.tree.selectionModel().select(itemsSelection , flags)

        # set selection visible
        if len(row_selected)>=1:
            index = self.tree.model().index(row_selected[0],0,QT.QModelIndex())
            self.tree.scrollTo(index)

        self.tree.selectionModel().selectionChanged.connect(self.on_tree_selection)
        
        self.refresh_label()


SpikeListView._gui_help_txt = """Spike list view
Show all spikes of the visible units.
When on spike is selected then:
  * the trace scroll to it
  * ndscatter shows it (if included_in_pc=True)"""





def get_qt_spike_model():
    # this getter is to protect import QT when using panel

    from .myqt import QT

    class SpikeModel(QT.QAbstractItemModel):

        def __init__(self, parent =None, controller=None, columns=[]):
            QT.QAbstractItemModel.__init__(self,parent)
            self.controller = controller
            self.columns = columns
            # self.refresh_colors()
            
            self.visible_ind = self.controller.get_indices_spike_visible()
        
        def columnCount(self , parentIndex):
            return len(self.columns)
        
        def rowCount(self, parentIndex):
            if not parentIndex.isValid():
                return int(self.visible_ind.size)
            else :
                return 0
        
        def index(self, row, column, parentIndex):
            if not parentIndex.isValid():
                return self.createIndex(row, column, None)
            else:
                return QT.QModelIndex()

        def parent(self, index):
            return QT.QModelIndex()
        
        def data(self, index, role):
            
            if not index.isValid():
                return None
            
            if role not in (QT.Qt.DisplayRole, QT.Qt.DecorationRole):
                return
            
            col = index.column()
            row = index.row()
            
            abs_ind = self.visible_ind[row]
            spike = self.controller.spikes[abs_ind]
            unit_id = self.controller.unit_ids[spike['unit_index']]
            
            if role ==QT.Qt.DisplayRole :
                if col == 0:
                    return '{}'.format(abs_ind)
                elif col == 1:
                    return '{}'.format(unit_id)
                elif col == 2:
                    return '{}'.format(spike['segment_index'])
                elif col == 3:
                    return '{}'.format(spike['sample_index'])
                elif col == 4:
                    return '{}'.format(spike['channel_index'])
                elif col == 5:
                    return '{}'.format(spike['rand_selected'])
                else:
                    return None
            elif role == QT.Qt.DecorationRole :
                if col != 0:
                    return None
                if unit_id in self.icons:
                    return self.icons[unit_id]
                else:
                    return None
            else :
                return None
            
        
        def flags(self, index):
            if not index.isValid():
                return QT.Qt.NoItemFlags
            return QT.Qt.ItemIsEnabled | QT.Qt.ItemIsSelectable #| Qt.ItemIsDragEnabled

        def headerData(self, section, orientation, role):
            if orientation == QT.Qt.Horizontal and role == QT.Qt.DisplayRole:
                return  self.columns[section]
            return

        def refresh_colors(self, qcolors):
            self.icons = { }
            for unit_id, qcolor in qcolors.items():
                pix = QT.QPixmap(10,10 )
                pix.fill(qcolor)
                self.icons[unit_id] = QT.QIcon(pix)
        
        def refresh(self):
            self.visible_ind = self.controller.get_indices_spike_visible()
            self.layoutChanged.emit()

        def clear(self):
            self.visible_ind = np.array([])
            self.layoutChanged.emit()


    return SpikeModel