# spikeinterface-gui

GUI for spikeinterface objects without data copy.

This is a cross platform interactive viewer to inspect the final results
and quality of any spike sorter supported by spikeinterface 
(kilosort, spykingcircus, tridesclous, moutainssort, yass, ironclust, herdinspikes, hdsort, klusta...)

This interactive GUI offer several views that dynamically refresh other views.
This allows us to very quickly check the strengths and weaknesses of any sorter output.

Contrary to other viewers (like  phy), this viewer skips the tedious and long step of
copying and reformating the entire dataset (filtered signal + waveform + PCA) to a particular
format or folder organisation. This gui is built on top of spikeinterface objects
(Recording, Sorting, WaveformExtractor)
These objects are "lazy" and retrieve data on the fly (no copy!).
And contrary to phy, this is a view only tool : no manual curation at the moment (split/merge/trash have to be done outside).

This viewer internally use Qt (with PySide6, PyQT6 or PyQt5) and pyqtgraph.
And so, this viewer is a local desktop app (old school!!).
There is a web based viewer work-in-progress [here](https://github.com/magland/sortingview).

![screenshot](screenshot.png)

## Launch

In order to use this viewer you will need to know a bit of [spikeinterface](https://spikeinterface.readthedocs.io/)

### Step 1 : extract waveforms

You first need to "extract waveform" with spikeinterface
See help [here](https://spikeinterface.readthedocs.io/en/latest/modules/core/plot_4_waveform_extractor.html#sphx-glr-modules-core-plot-4-waveform-extractor-py)

Note that:
  * not all waveform snipets are extracted (See `max_spikes_per_unit`) only some of them
  * this step is cached to a folder (and can be reloaded)
  * this step can be run in parallel (and so is quite fast)
  * optionally PCA can be computed and displayed

  
Example:

```python
import spikeinterface.full as si
recording = si.read_XXXX('/path/to/my/recording')
recording_filtered = si.bandpass_filter(recording)
sorting = si.run_sorter('YYYYY', recording_filtered)
waveform_folder = '/path/for/my/waveforms'
we = si.extract_waveforms(
    recording_filtered, sorting, waveform_folder,
    max_spikes_per_unit=500,
    ms_before=1.5, ms_after=2.5,
    n_jobs=10, total_memory='500M',
    progress_bar=True,
)
# and optionally compute principal component
pc = si.compute_principal_components(we,
    n_components=5,
    mode='by_channel_local',
    whiten=True)
```

### Step 2 : open the GUI

With python:

```python
import spikeinterface_gui
# This creates a Qt app
app = spikeinterface_gui.mkQApp() 
# reload the waveform folder
we = si.WaveformExtractor.load_from_folder(waveform_folder)
# create the mainwindow and show
win = spikeinterface_gui.MainWindow(we)
win.show()
# run the main Qt6 loop
app.exec_()
```

With the command line

```
sigui /path/for/my/waveforms
```


## Install

You need first to install one of these 3 packages (by order of preference):
  * `pip install PySide6`
  * `pip install PyQt6`
  * `pip install PyQt5`


From pypi:

```bash
pip install spikeinterface-gui
```

From sources:

```bash
git clone https://github.com/SpikeInterface/spikeinterface-gui.git
cd spikeinterface-gui
pip install .
```

## Author

Samuel Garcia, CNRS, Lyon, France

This work is a port of the old `tridesclous.gui` submodule of top of
[spikeinterface](https://github.com/SpikeInterface/spikeinterface).
