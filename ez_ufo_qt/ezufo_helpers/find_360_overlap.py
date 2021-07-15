#!/usr/bin/env python2

'''
This script takes as input a CT scan that has been collected in "half-acquisition" mode 
and produces a series of reconstructed slices, each of which are generated by cropping and
concatenating opposing projections together over a range of "overlap" values (i.e. the pixel column
at which the images are cropped and concatenated).
The objective is to review this series of images to determine the pixel column at which the axis of rotation
is located (much like the axis search function commonly used in reconstruction software).
'''


import os
import shutil
import numpy as np
import argparse
import tifffile
from util import read_image

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--input', type=str, help='Input directory')
    parser.add_argument('--tmpdir', default='/data/tmp-stitch_search/', type=str, help='Temporary directory for intermediate steps')
    parser.add_argument('--output', type=str, help='Output directory')

    parser.add_argument('--row', default=200, type=int, help='Pixel row to be used for sinogram')
    parser.add_argument('--min', default=100, type=int, help='Lower limit of stitch/axis search range')
    parser.add_argument('--max', default=200, type=int, help='Upper limit of stitch/axis search range')
    parser.add_argument('--step', default=2, type=int, help='Value by which to increment through search range')
    parser.add_argument('--axis_on_left', default=True, type=bool, help='Is the rotation axis on the left-hand side of the image?')


    return parser.parse_args()



def open_tif_sequence(dir_name, row):

    sequence = []
    filenames = os.listdir(dir_name)
    filenames.sort()

    for filename in filenames:
        if '.tif' in filename:
            tif_img = read_image(os.path.join(dir_name, filename)).astype(np.uint16)
            sequence.append(np.array(tif_img)[(row-10):(row+10),:])
    return np.array(sequence)


def main():

    # assign parsed command line arguments to variables
    args = parse_args()

    root = args.input
    proc = args.tmpdir
    output =  args.output
    row_num = args.row
    overlap_min = args.min
    overlap_max = args.max
    overlap_increment = args.step
    axis_on_left = args.axis_on_left

    # recursively create output temporary directory if it doesn't exist
    if os.path.exists(os.path.join(proc)):
        shutil.rmtree(proc)
        os.makedirs(os.path.join(proc, 'sinos'))
    else:
        os.makedirs(os.path.join(proc, 'sinos'))



    # concatenate images end-to-end and generate a sinogram
    print('opening half-acquisition image sequence...')
    tomo = open_tif_sequence(os.path.join(root,'tomo'), row_num)

    #open flats and darks and average them
    flat = np.mean(open_tif_sequence(os.path.join(root,'flats'), row_num)/65535.0, axis=0)
    flat2 = np.mean(open_tif_sequence(os.path.join(root,'flats2'), row_num)/65535.0, axis=0)
    dark = np.mean(open_tif_sequence(os.path.join(root,'darks'), row_num)/65535.0, axis=0)

    tomo_single_row = tomo[:,tomo.shape[1]//2,:]/65535.0
    dark_single_row = np.tile(dark[tomo.shape[1]//2,:], (tomo.shape[0],1))
    flat_single_row = np.zeros((tomo.shape[0], tomo.shape[2]))
    img_height = tomo.shape[0]
    img_width = tomo.shape[1]

    del tomo

    #create interpolated sinogram of flats on the same row as we use for the projections, then carry out flat/dark correction
    print('creating stitched sinograms...')
    for i in range(0, img_height):
        flat_single_row[i,:] = (flat[img_width//2,:]*(float(i)/float(img_height))+flat2[img_width//2,:]*(1.0 - float(i)/float(img_height)))

    tomo_sino_corr = (tomo_single_row - dark_single_row) / (flat_single_row - dark_single_row)
    max_gray_value = tomo_sino_corr.max()
    tomo_sino_corr = tomo_sino_corr/max_gray_value

    tomo_first_half = tomo_sino_corr[:int(tomo_sino_corr.shape[0]/2),:]
    tomo_second_half = tomo_sino_corr[int(tomo_sino_corr.shape[0]/2):tomo_sino_corr.shape[0],:]

    tomo_first_half = -1.0*np.log(tomo_first_half)
    tomo_second_half = -1.0*np.log(tomo_second_half)

    #flip half of corrected unstitched sinos (depending on right- or left-hand axis) and produce stitched sinos at regular increments TODO: fix code for right-hand axis case
    if axis_on_left:
        tomo_second_half_flipped = np.fliplr(tomo_second_half)

        for axis in range(overlap_min, overlap_max, overlap_increment):
            sino_halves = []
            sino_halves.append(tomo_second_half_flipped[:,:tomo_second_half_flipped.shape[1] - axis])
            sino_halves.append(tomo_first_half[:,axis:])
            stitched_sino = np.concatenate(sino_halves, axis=1)

            output_img = (stitched_sino)

            tifffile.imsave(os.path.join(proc, 'sinos', 'axis-'+str(axis).zfill(4)+'.tif'), output_img.astype(np.float32))

    # else:
    #     tomo_first_half_flipped = np.flip(tomo_second_half, 1)

    #     for axis in range(overlap_min, overlap_max, overlap_increment):
    #         stitched_sino = np.concatenate(tomo_second_half[:,:tomo_second_half.shape[0] - axis], tomo_first_half_flipped[:,axis:], axis=1)
    #         io.imsave(os.path.join(output, 'axis-'+str(axis)+'.tif'), stitched_sino)


    # perform reconstructions for each sinogram and save to output folder
    print('reconstructing stitched sinograms:')

    for filename in os.listdir(os.path.join(proc,'sinos')):
        if '.tif' in filename:
            
            current_img = np.array(read_image(os.path.join(proc,'sinos',filename)))
            axis = current_img.shape[1]/2

            recon_cmd = 'tofu tomo  --output-bytes-per-file 0 --sinograms '+os.path.join(proc,'sinos', filename)+' --output '+os.path.join(output, filename)+' --axis '+str(axis)
            os.system(recon_cmd)
    
    shutil.rmtree(proc)

if __name__ == '__main__':
    main()
