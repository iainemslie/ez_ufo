#!/bin/python
'''
Created on Apr 6, 2018

@author: gasilos
'''
import glob
import os
import argparse
import sys
import numpy as np
from ez_ufo_qt.evaluate_sharpness import process as process_metrics
from ez_ufo_qt.util import enquote
from tofu.util import (get_filenames, read_image, determine_shape)
import tifffile


class findCOR_cmds(object):
    '''
    Generates commands to find the axis of rotation
    '''
    def __init__(self, fol):
        self._fdt_names = fol

    def make_inpaths(self, lvl0, flats2, args):
        """
        Creates a list of paths to flats/darks/tomo directories
        :param lvl0: Root of directory containing flats/darks/tomo
        :param flats2: The type of directory: 3 contains flats/darks/tomo 4 contains flats/darks/tomo/flats2
        :return: List of paths to the directories containing darks/flats/tomo and flats2 (if used)
        """
        indir = []
        # If using flats/darks/flats2 in same dir as tomo
        if not args.common_darks_flats:
            for i in self._fdt_names[:3]:
                indir.append(os.path.join(lvl0, i))
            if flats2 - 3:
                indir.append(os.path.join(lvl0, self._fdt_names[3]))
            return indir
        # If using common flats/darks/flats2 across multiple reconstructions
        elif args.common_darks_flats:
            indir.append(args.common_darks)
            indir.append(args.common_flats)
            indir.append(os.path.join(lvl0, self._fdt_names[2]))
            if args.use_common_flats2:
                indir.append(args.common_flats2)
            return indir

    def find_axis_std(self, ctset, tmpdir, ax_range, p_width, search_row, nviews, args, WH):
        indir = self.make_inpaths(ctset[0], ctset[1], args)
        image = read_image(get_filenames(indir[2])[0])
        cmd =  'tofu reco --absorptivity --fix-nan-and-inf --overall-angle 180'\
               ' --axis-angle-x 0'
        cmd += ' --darks {} --flats {} --projections {}'.\
                    format(indir[0], indir[1], enquote(indir[2]))
        cmd += ' --number {}'.format(nviews)
        #cmd += ' --angle {:0.5f}'.format( np.radians(180.0/float(nviews)) )
        if ctset[1]==4:
            cmd += ' --flats2 {}'.format(indir[3])
        out_pattern = os.path.join(tmpdir,"axis-search/sli")
        cmd += ' --output {}'.format(enquote(out_pattern))
        cmd += ' --x-region={},{},{}'.format(int(-p_width / 2), int(p_width / 2), 1)
        cmd += ' --y-region={},{},{}'.format(int(-p_width / 2), int(p_width / 2), 1)
        #cmd += ' --y {} --height 2'.format(search_row)
        image_width = WH[1]
        #search_row_shifted = int(search_row) - int(image_width/2)
        #search_row_string = str(search_row_shifted) + "," + str(search_row_shifted+1) + "," + str(1)
        #cmd += ' --region={}'.format(search_row_string)
        cmd += ' --z-parameter center-position-x'
        #Split ax_range by commas
        ax_range_list = ax_range.split(",")
        #Subtract imagewidth/2 from range_min
        range_min = ax_range_list[0]
        range_min_shifted = int(range_min) - int(image_width/2)
        #Subtract imagewidth/2 from range_max
        range_max = ax_range_list[1]
        range_max_shifted = int(range_max) - int(image_width/2)
        #Create string from range_min, range_max and step separated by commas
        range_string = str(range_min_shifted) + ',' + str(range_max_shifted) + ',' + str(ax_range_list[2])
        cmd += ' --region={}'.format(range_string)
        #cmd += ' --z 0'
        res = [float(num) for num in ax_range.split(',')]
        #cmd += ' --axis {},{}'.format( (res[0]+res[1])/2., 1.0) #middle of ax search range?
        cmd += " --output-bytes-per-file 0"
        # cmd += ' --delete-slice-dir'
        print(cmd)
        os.system(cmd)
        points, maximum = evaluate_images_simp(out_pattern + '*.tif', "msag")
        print(points)
        print(maximum)
        return res[0] + res[2] * maximum
        

    def find_axis_corr(self, ctset, vcrop, y, height, multipage, args):
        indir = self.make_inpaths(ctset[0], ctset[1], args)
        """Use correlation to estimate center of rotation for tomography."""
        from scipy.signal import fftconvolve
        def flat_correct(flat, radio):
            nonzero = np.where(radio != 0)
            result = np.zeros_like(radio)
            result[nonzero] = flat[nonzero] / radio[nonzero]
            # log(1) = 0
            result[result <= 0] = 1

            return np.log(result)

        if multipage:
            with tifffile.TiffFile(get_filenames(indir[2])[0]) as tif:
                first = tif.pages[0].asarray().astype(np.float)
            with tifffile.TiffFile(get_filenames(indir[2])[-1]) as tif:
                last = tif.pages[-1].asarray().astype(np.float)
            with tifffile.TiffFile(get_filenames(indir[0])[-1]) as tif:
                dark = tif.pages[-1].asarray().astype(np.float)
            with tifffile.TiffFile(get_filenames(indir[1])[0]) as tif:
                flat1 = tif.pages[-1].asarray().astype(np.float) - dark
        else:
            first = read_image(get_filenames(indir[2])[0]).astype(np.float)
            last = read_image(get_filenames(indir[2])[-1]).astype(np.float)
            dark = read_image(get_filenames(indir[0])[-1]).astype(np.float)
            flat1 = read_image(get_filenames(indir[1])[-1]) - dark

        first = flat_correct(flat1, first - dark)

        if ctset[1] == 4:
            if multipage:
                with tifffile.TiffFile(get_filenames(indir[3])[0]) as tif:
                    flat2 = tif.pages[-1].asarray().astype(np.float) - dark
            else:
                flat2 = read_image(get_filenames(indir[3])[-1]) - dark
            last = flat_correct(flat2, last - dark)
        else:
            last = flat_correct(flat1, last - dark)

        if vcrop:
            y_region = slice(y, min(y + height, first.shape[0]), 1)
            first = first[y_region, :]
            last = last[y_region, :]

        width = first.shape[1]
        first = first - first.mean()
        last = last - last.mean()

        conv = fftconvolve(first, last[::-1, :], mode='same')
        center = np.unravel_index(conv.argmax(), conv.shape)[1]

        return (width / 2.0 + center) / 2.0

    #Find midpoint width of image and return its value
    def find_axis_image_midpoint(self, ctset, multipage, height_width):
        return height_width[1] / 2


def evaluate_images_simp(input_pattern, metric, num_images_for_stats=0, out_prefix=None, fwhm=None,
                blur_fwhm=None, verbose=False):
    #simplified version of original evaluate_images function
    #from Tomas's optimize_parameters script
    names = sorted(glob.glob(input_pattern))
    res = process_metrics(names, num_images_for_stats=num_images_for_stats,
                          metric_names=(metric,), out_prefix=out_prefix,
                          fwhm=fwhm, blur_fwhm=blur_fwhm)[metric]
    return res, np.argmax(res)



    
    
    
    
    
    
    
    
        
