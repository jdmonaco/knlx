
KNlx README
-----------

----------------------

**Description** A quick Python module for easily reading a subset of Neuralynx binary data files.
	
**Author** Joe Monaco

**Organization** Zanvyl Krieger Mind/Brain Institute, Johns Hopkins University, Baltimore, MD, USA

----------------------

Installation
------------

This module requires Python (obviously), numpy, and bitstring. Numpy is very common, especially in any scientific distribution of Python; see [SciPy.org](http://scipy.org/) for installation instructions. The bitstring library can be installed easily via `easy_install` or `pip` or [downloaded from PyPI](https://pypi.python.org/pypi/bitstring/) for a `distutils` install. Then:

    $ tar xzf knlx-0.01.tar.gz
    $ cd knlx-0.01/
    $ sudo python setup.py install

to install `knlx` into your current Python environment.

Library Functions
-----------------

In your own code, `knlx` can be imported by

    import knlx

The library provides functions for reading the binary files created by Neuralynx data acquisition devices. Note that `knlx` was created to read files from place cell experiments, so capabilities are currently limited to experimental events (`.Nev`), video position-tracking (`.p`, with `timestamp`, `x`, `y`, and `direction` columns), and continuous records (`.Ncs`, usually for LFP/EEG recordings). The formats are based on the [specifications (pdf)](http://neuralynx.com/software/NeuralynxDataFileFormats.pdf) provided by Neuralynx. The functions are

* `read_event_file`
* `read_position_file`
* `write_position_ascii_file` 
* `read_ncs_file`

and they take the path to the Neuralynx file you want to read as the only argument. Obviously, more functionality could be added here (including allowing for more flexible data-format configurations), but these functions at least demonstrate a generalizable method for using bitstring to read out the binary formats of Neuralynx files into usable numpy arrays. 
