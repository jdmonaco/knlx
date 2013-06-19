# encoding: utf-8

"""
knlx.py -- Library of functions for reading Neuralynx files for events (.Nev), 
    position tracking (Pos.p), and continuous records (.Ncs)

Requires: numpy, bitstring

Copyright (c) 2011-2013 Johns Hopkins University. All rights reserved.

This software is provided AS IS under the terms of the Open Source MIT License. 
See http://www.opensource.org/licenses/mit-license.php.
"""

import os
import sys
import numpy as np
import numpy.core.records as rec

try:
    import bitstring as bstr
except ImportError:
    sys.stderr.write('scanr: bitstring must be installed to read Neuralynx files\n')

# Constants
DEBUG = True
NCS_SAMPLE_RATE = 1001.0

# File parameters
HDR_SIZE = 8 * 16384
EVENT_STR_LEN = 8 * 128
NCS_DATA_POINTS = 512

# Record descriptions
NCS_RECORD = dict(  timestamp = 'uintle:64',
                    channel = 'uintle:32',
                    Fs = 'uintle:32',
                    valid = 'uintle:32',
                    samples = 'intle:16'    )
                    
POS_RECORD = dict(  timestamp = 'floatle:64',
                    pos = 'floatle:32'  )
                    
NEV_RECORD = dict(  byte = 'intle:16',
                    timestamp = 'uintle:64',
                    extra = 'intle:32'  )


def read_event_file(fn):
    """Load event record data from Neuralynx .Nev file fn
    
    Returns (timestamp, event_string) tuple where timestamp is an array of
    timestamp values and event_string is a corresponding list of event strings.
    """
    if fn is None or not (os.path.exists(fn) and fn.endswith('.Nev')):
        raise ValueError, 'invalid Nev file specified: %s' % fn
        
    out = sys.stdout.write
    out('Loading %s...\n' % fn)
    
    bits = bstr.ConstBitStream(filename=fn)
    bits.read(HDR_SIZE) # skip 16k header
    
    timestamp_list = []
    string_list = []
    
    while True:
        try:
            bits.read(NEV_RECORD['byte'])   # nstx
            bits.read(NEV_RECORD['byte'])   # npkt_id
            bits.read(NEV_RECORD['byte'])   # npkt_data_size
            
            timestamp_list.append(bits.read(NEV_RECORD['timestamp']))
            
            bits.read(NEV_RECORD['byte'])   # nevent_id
            bits.read(NEV_RECORD['byte'])   # nttl
            bits.read(NEV_RECORD['byte'])   # ncrc
            bits.read(NEV_RECORD['byte'])   # ndummy1
            bits.read(NEV_RECORD['byte'])   # ndummy2
            
            bits.readlist([NEV_RECORD['extra']] * 8)  # dnExtra (length 8 array)
            
            # Read out the event string, truncate it, and advance the read position
            evstr = bits[bits.pos:bits.pos + EVENT_STR_LEN].tobytes()
            evstr = evstr[:evstr.find('\x00')]
            string_list.append(evstr)
            bits.pos += EVENT_STR_LEN
            
            if DEBUG:
                out('At T=%d: %s\n' % (timestamp_list[-1], evstr))
            
        except bstr.ReadError:
            if DEBUG:
                out('Reached EOF\n')
            break
    
    return np.array(timestamp_list), string_list

def read_position_file(fn):
    """Load position record data from Neuralynx Pos.p file fn
    
    Returns (timestamp, x, y, dir) tuple where timestamp is an array of
    timestamp values, x and y are position arrays, and dir is head direction.
    """
    if fn is None or not (os.path.exists(fn) and fn.endswith('.p')):
        raise ValueError, 'invalid position file specified: %s' % fn
        
    out = sys.stdout.write
    out('Loading %s...\n' % fn)
    bits = bstr.ConstBitStream(filename=fn)
    bits.pos = position_data_index(fn)
    
    timestamp_list = []
    x_list = []
    y_list = []
    dir_list = []
    
    every = 1000
    while True:
        try:
            timestamp_list.append(bits.read(POS_RECORD['timestamp']))
            x_list.append(bits.read(POS_RECORD['pos']))
            y_list.append(bits.read(POS_RECORD['pos']))
            dir_list.append(bits.read(POS_RECORD['pos']))
            
            if len(timestamp_list) % every == 0:
                out('At T=%d: %.3f, %.3f\n' % (timestamp_list[-1], x_list[-1], 
                    y_list[-1]))
            
        except bstr.ReadError:
            if DEBUG:
                out('Reached EOF\n')
            break
    
    return np.array(timestamp_list, long), np.array(x_list, float), \
        np.array(y_list, float), np.array(dir_list, float)

def write_position_ascii_file(fn='Pos.p'):
    """Write out a Pos.p.ascii file for the given Pos.p binary file
    """
    # Get the data
    ts, x, y, hd = read_position_file(fn)
    
    # Get the header
    bits = bstr.ConstBitStream(filename=fn)
    header = bits[:position_data_index(fn)].tobytes()
    
    # Write out ascii file
    ascii_fn = os.path.join(os.path.split(fn)[0], 'Pos.p.ascii')
    fd = file(ascii_fn, 'w')
    
    fd.write(header)
    for i in xrange(len(ts)):
        fd.write('%d,%.4f,%.4f,%d\n'%(ts[i], x[i], y[i], int(hd[i])))
    fd.close()
    
    sys.stdout.write('Wrote %s.\n' % ascii_fn)    
    
def position_data_index(fn):
    """Given the filename of a position file, return the bit index of the first
    data record past the header.
    """
    hdr_end = "%%ENDHEADER\r\n"
    token = bstr.ConstBitArray(bytearray(hdr_end))
    bits = bstr.ConstBitStream(filename=fn)
    bits.find(token)
    bits.read('bytes:%d'%len(hdr_end))
    return bits.pos

def read_ncs_file(fn, verbose=True):
    """Load continuous record data from Neuralynx .Ncs file fn
    
    Returns (timestamp, sample) tuple of data arrays.
    """
    if fn is None or not (os.path.exists(fn) and fn.endswith('.Ncs')):
        raise ValueError, 'invalid Ncs file specified: %s' % fn
    
    if verbose:
        out = sys.stdout.write
        out('Loading %s...\n' % fn)
    
    bits = bstr.ConstBitStream(filename=fn)
    bits.read(HDR_SIZE) # skip 16k header
    
    sample_read_str = [NCS_RECORD['samples']] * NCS_DATA_POINTS
    timestamp_list = []
    sample_list = []
    prev_rec_ts = 0L
    prev_rec_valid = 0
    Fs_list = []
    
    while True:
        try:
            rec_ts = bits.read(NCS_RECORD['timestamp'])
            
            if verbose:
                out('Reading record starting at timestamp %d:\n' % rec_ts)
            
            rec_ch = bits.read(NCS_RECORD['channel'])
            rec_fs = float(bits.read(NCS_RECORD['Fs']))
            rec_valid = bits.read(NCS_RECORD['valid'])
            
            if rec_fs not in Fs_list:
                Fs_list.append(rec_fs)
            if rec_valid != NCS_DATA_POINTS:
                if verbose:
                    out('Found %d valid samples instead of %d.\n' % (rec_valid, 
                        NCS_DATA_POINTS))
            
            # Load samples, truncate to valid if necessary
            samples = bits.readlist(sample_read_str)
            sample_list.append(samples)
            N_samples = len(samples)
            
            if verbose:
                out('Ch: %d, Fs: %.1f Hz, Nvalid = %d\n' % (rec_ch, rec_fs, rec_valid))
            
            # Interpolate new timestamps
            if prev_rec_ts:
                delta = long(float(rec_ts - prev_rec_ts) / prev_rec_valid)
                timestamp_list.append(
                    np.cumsum(
                        np.r_[long(prev_rec_ts), 
                            np.repeat(delta, prev_rec_valid-1)]))

            prev_rec_ts = rec_ts
            prev_rec_valid = N_samples
            
        except bstr.ReadError:
            if verbose:
                out('Reached EOF\n')
            break

    # Interpolate timestamps for last valid sample block before EOF
    if len(timestamp_list):
        timestamp_list.append(
            np.linspace(
                prev_rec_ts, 
                    prev_rec_ts + prev_rec_valid*(np.diff(timestamp_list[-1][-2:])), 
                        prev_rec_valid, endpoint=False).astype('i8'))
    else:
        return np.array([], dtype='i8'), array([], dtype='i2')
    
    if verbose:
        if len(Fs_list) > 1:
            out('Found multiple sample frequencies: %s\n' % str(Fs_list)[1:-1])
        elif len(Fs_list) == 1 and Fs_list[0] != NCS_SAMPLE_RATE:
            out('Found non-standard sample rate: %.1f Hz\n' % Fs_list[0])

    return np.concatenate(timestamp_list).astype('i8'), \
            np.concatenate(sample_list).astype('i2')
