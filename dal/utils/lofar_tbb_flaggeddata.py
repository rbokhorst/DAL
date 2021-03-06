#!/usr/bin/env python
#
# lofar_tbb_flaggeddata.py
# Python script that searches for frame payload sized sequences of zeros in TBB transient data in LOFAR HDF5 files.
#
# File:         lofar_tbb_flaggeddata
# Author:       Alexander S. van Amesfoort (amesfoort_at_astron.nl)
# Date:         2012-06-11
# Last change:  2012-08-15

import sys
import numpy
import dal

def get_lost_frame_nrs(data, block_len):
	lost_frame_nrs = [ ]

	offset = 0
	nr_zeros_seen = 0
	while offset < len(data):
		if data[offset] != 0:
			offset += block_len - nr_zeros_seen
			nr_zeros_seen = 0
		else:
			nr_zeros_seen += 1
			if nr_zeros_seen == block_len:
				lost_frame_nrs.append(offset / block_len)
				nr_zeros_seen = 0
			offset += 1

	return lost_frame_nrs

def print_lost_frame_nrs(filename):
	fh = dal.TBB_File(filename)

	datasets_found = False
	total_frames = 0
	total_lost = 0

	station_groups = fh.stations();
	for st in station_groups:
		dipole_datasets = st.dipoles();
		for dp in dipole_datasets:
			datasets_found = True
			data_len = dp.dims1D() # actual data len; should be equal to dp.dataLength().get()
			data = numpy.zeros((data_len, ), dtype=dp.dtype)
			#data = numpy.array(dp, dtype=dp.dtype) # only works if Python binding of TBB_DipoleDataset exposes the array interface, __array__ returns an array or any (nested) sequence.
			start_idx = 0
			dp.get1D(start_idx, data)

			# Not always available when this program was written, but will be always there.
			# Use .get() instead of .value to have an exc raised instead of None returned.
			block_len = dp.samplesPerFrame().value
			if block_len is None:
				block_len = 1024 # the TBBs always send 1024 samples/frame for transient data
			total_frames += (data_len + block_len-1) // block_len # add rounded up #frames
			dp_lost_frame_nrs = get_lost_frame_nrs(data, block_len)
			if dp_lost_frame_nrs: # Does not account for missing frames at the end. We'd have to max(<len(any dipole datasets)>) and even then we could miss the true max.
				total_lost += len(dp_lost_frame_nrs)
				print 'Station', st.stationName().value, 'rsp', str(dp.rspID().value), 'rcu', str(dp.rcuID().value) + ':', 'numbers of zeroed frames of', str(block_len), 'values each:'
				for frame_nr in dp_lost_frame_nrs:
					print frame_nr,
				print

	if not datasets_found:
		print 'Warning: no dipole datasets found in filename', filename
		print

	if total_lost:
		print 'Total data loss in filename', filename + ':', total_lost, '/', total_frames, '(' + str(100.0 * total_lost / total_frames) + ' %)'
		print

def print_usage():
	print 'Search for and print frame payload sized sequences of zeros in TBB transient data in LOFAR HDF5 files.'
	print 'Usage:', sys.argv[0], 'L12345_xxx_tbb.h5 ...'

def main():
	if len(sys.argv) == 1:
		print_usage()
		return 2

	filenames = sys.argv[1 : ]
	try:
		for filename in filenames:
			print_lost_frame_nrs(filename)
	except KeyboardInterrupt as exc:
		return 1
	except Exception as exc:
		sys.stderr.write('Error: ' + str(exc) + '\n')
		return 1

	return 0

if __name__ == '__main__':
	sys.exit(main())

