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
from concert.storage import read_image
from tofu.util import get_filenames, read_image
from ez_ufo_qt.ufo_cmd_gen import fmt_in_out_path
from ez_ufo_qt.evaluate_sharpness import process as process_metrics
from ez_ufo_qt.util import enquote

class tofu_cmds(object):
    '''
    Generates partially formatted ufo-launch and tofu commands
    Parameters are included in the string; pathnames must be added
    '''
    def __init__(self, fol):
        self._fdt_names = fol

    def make_inpaths(self,lvl0, flats2):
        indir = []
        for i in self._fdt_names[:3]:
            indir.append( os.path.join(lvl0, i) )
        if flats2-3:
            indir.append( os.path.join(lvl0, self._fdt_names[3]) )
        return indir

    def check_8bit(self, cmd, gray256, bit, hmin, hmax):
        if gray256:
            cmd += " --output-bitdepth {}".format(bit)
            cmd += " --output-minimum \" {}\" --output-maximum \" {}\""\
                    .format(hmin, hmax)
        return cmd

    def check_vcrop(self, cmd, vcrop, y, yheight, ystep, ori_height):
        if vcrop:
            cmd += " --y {} --height {} --y-step {}"\
                    .format(y, yheight, ystep)
        else:
            cmd += ' --height {}'.format(ori_height)
        return cmd

    def check_bigtif(self, cmd, swi):
        if not swi:
            cmd += " --output-bytes-per-file 0"
        return cmd

    def get_1step_ct_cmd(self, ctset, out_pattern, ax, args, nviews, WH):
        #direct CT reconstruction from input dir to output dir;
        #or CT reconstruction after preprocessing only
        indir = self.make_inpaths(ctset[0], ctset[1])
        #correct location of proj folder in case if prepro was done
        in_proj_dir, quatsch = fmt_in_out_path(args.tmpdir,ctset[0], self._fdt_names[2], False)
        indir[2]=os.path.join(os.path.split(indir[2])[0], os.path.split(in_proj_dir)[1])
        #format command
        cmd = 'tofu tomo --absorptivity --fix-nan-and-inf'
        cmd += ' --darks {} --flats {} --projections {}'.format(indir[0],indir[1],indir[2])
        if ctset[1]==4: #must be equivalent to len(indir)>3
            cmd += ' --flats2 {}'.format(indir[3])
        cmd += ' --output {}'.format(out_pattern)
        cmd += ' --axis {}'.format(ax)
        cmd += ' --offset {}'.format(args.a0)
        cmd += ' --number {}'.format(nviews)
        if args.step>0.0:
            cmd += ' --angle {}'.format(args.step)
        cmd = self.check_vcrop(cmd, args.vcrop, args.y, args.yheight, args.ystep, WH[0])
        cmd = self.check_8bit(cmd, args.gray256, args.bit, args.hmin, args.hmax)
        cmd = self.check_bigtif(cmd, args.bigtif_sli)
        return cmd

    def get_ct_proj_cmd(self, out_pattern,ax, args, nviews, WH):
        #CT reconstruction from pre-processed and flat-corrected projections
        in_proj_dir, quatsch = fmt_in_out_path(args.tmpdir,'obsolete;if-you-need-fix-it', self._fdt_names[2], False)
        cmd = 'tofu tomo --projections {}'.format( in_proj_dir)
        cmd += ' --output {}'.format(out_pattern)
        cmd += ' --axis {}'.format(ax)
        cmd += ' --offset {}'.format(args.a0)
        cmd += ' --number {}'.format(nviews)
        if args.step>0.0:
            cmd += ' --angle {}'.format(args.step)
        cmd = self.check_vcrop(cmd, args.vcrop, args.y, args.yheight, args.ystep, WH[0])
        cmd = self.check_8bit(cmd, args.gray256, args.bit, args.hmin, args.hmax)
        cmd = self.check_bigtif(cmd, args.bigtif_sli)
        return cmd

    def get_ct_sin_cmd(self, out_pattern,ax, args, nviews, WH):
        sinos_dir = os.path.join( args.tmpdir,'sinos-filt' )
        cmd = 'tofu tomo --sinograms {}'.format(sinos_dir)
        cmd += ' --output {}'.format(out_pattern)
        cmd += ' --axis {}'.format(ax)
        cmd += ' --offset {}'.format(args.a0)
        if args.vcrop:
            cmd += ' --number {}'.format(int(args.yheight/args.ystep))
        else:
            cmd += ' --number {}'.format(WH[0])
        cmd += ' --height {}'.format(nviews)
        if args.step>0.0:
            cmd += ' --angle {}'.format(args.step)
        cmd = self.check_8bit(cmd, args.gray256, args.bit, args.hmin, args.hmax)
        cmd = self.check_bigtif(cmd, args.bigtif_sli)
        return cmd

    def get_sinos_ffc_cmd(self,ctset, tmpdir,args, nviews, WH):
        indir = self.make_inpaths(ctset[0], ctset[1])
        in_proj_dir, out_pattern = fmt_in_out_path(args.tmpdir,ctset[0], self._fdt_names[2], False)
        cmd = 'tofu sinos --absorptivity --fix-nan-and-inf'
        cmd += ' --darks {} --flats {} '.format(indir[0],indir[1])
        if ctset[1]==4:
            cmd += ' --flats2 {}'.format(indir[3])
        cmd += ' --projections {}'.format(in_proj_dir)
        cmd += ' --output {}'.format( os.path.join(tmpdir,'sinos/sin-%04i.tif') )
        cmd += ' --number {}'.format(nviews)
        cmd = self.check_vcrop(cmd, args.vcrop, args.y, args.yheight, args.ystep, WH[0])
        if not args.RR_ufo:
        # because second RR algorithm does not know how to work with multipage tiffs
            cmd += " --output-bytes-per-file 0"
        return cmd

    def get_sinos_noffc_cmd(self, ctsetpath, tmpdir, args, nviews, WH):
        in_proj_dir, out_pattern = fmt_in_out_path(args.tmpdir, ctsetpath, self._fdt_names[2], False)
        cmd = 'tofu sinos'
        cmd += ' --projections {}'.format(in_proj_dir)
        cmd += ' --output {}'.format( os.path.join(tmpdir,'sinos/sin-%04i.tif') )
        cmd += ' --number {}'.format(nviews)
        cmd = self.check_vcrop(cmd, args.vcrop, args.y, args.yheight, args.ystep, WH[0])
        if not args.RR_ufo:
        # because second RR algorithm does not know how to work with multipage tiffs
            cmd += " --output-bytes-per-file 0"
        return cmd

    def get_sinos2proj_cmd(self,args, proj_height):
        quatsch, out_pattern = fmt_in_out_path(args.tmpdir,'quatsch', self._fdt_names[2], True)
        cmd = 'tofu sinos'
        cmd += ' --projections {}'.format(os.path.join(args.tmpdir,'sinos-filt'))
        cmd += ' --output {}'.format( out_pattern )
        if not args.vcrop:
            cmd += ' --number {}'.format(proj_height)
        else:
            cmd += ' --number {}'.format(int(args.yheight/args.ystep))#(np.ceil(args.yheight/args.ystep))
        return cmd

    def get_sinFFC_cmd(self, ctset, args, nviews, n):
        indir = self.make_inpaths(ctset[0], ctset[1])
        in_proj_dir, out_pattern = fmt_in_out_path(args.tmpdir, ctset[0], self._fdt_names[2])
        cmd = 'bmit_sin --fix-nan'
        cmd += ' --darks {} --flats {} --projections {}'.format(indir[0], indir[1], in_proj_dir)
        if ctset[1] == 4:
            cmd += ' --flats2 {}'.format(indir[3])
        cmd += ' --output {}'.format(os.path.dirname(out_pattern))
        cmd += ' --eigen-pco-repetitions {}'.format(args.sinFFCEigenReps)
        cmd += ' --eigen-pco-downsample {}'.format(args.sinFFCEigenDowns)
        cmd += ' --downsample {}'.format(args.sinFFCDowns)
        return cmd

    def get_pr_sinFFC_cmd(self, ctset, args, nviews, n):
        indir = self.make_inpaths(ctset[0], ctset[1])
        in_proj_dir, out_pattern = fmt_in_out_path(args.tmpdir, ctset[0], self._fdt_names[2])
        cmd = 'bmit_sin --fix-nan'
        cmd += ' --darks {} --flats {} --projections {}'.format(indir[0], indir[1], in_proj_dir)
        if ctset[1] == 4:
            cmd += ' --flats2 {}'.format(indir[3])
        cmd += ' --output {}'.format(os.path.dirname(out_pattern))
        #cmd += ' --absorptivity'
        cmd += ' --multiprocessing'
        #cmd += ' --eigen-pco-repetitions {}'.format(args.sinFFCEigenReps)
        #cmd += ' --eigen-pco-downsample {}'.format(args.sinFFCEigenDowns)
        #cmd += ' --downsample {}'.format(args.sinFFCDowns)
        return cmd

    def get_pr_tofu_cmd_sinFFC(self, ctset, args, nviews, WH):
        # indir will format paths to flats darks and tomo2 correctly even if they were
        # pre-processed, however path to the input directory with projections
        # cannot be formatted with that command correctly
        #indir = self.make_inpaths(ctset[0], ctset[1])
        # so we need a separate "universal" command which considers all previous steps
        in_proj_dir, out_pattern = fmt_in_out_path(args.tmpdir, ctset[0], self._fdt_names[2])
        # Phase retrieval
        cmd = 'tofu preprocess --delta 1e-6'
        cmd += ' --energy {} --propagation-distance {}' \
               ' --pixel-size {} --regularization-rate {:0.2f}' \
            .format(args.energy, args.z, args.pixel, args.log10db)
        #cmd += ' --width {}'.format(WH[0])
        #cmd += ' --height {}'.format(WH[1])
        cmd += ' --projections {}'.format(in_proj_dir)
        #cmd += ' --projections {}'.format(os.path.join(in_proj_dir, 'proj-%04i.tif'))
        cmd += ' --output {}'.format(out_pattern)
        #cmd += ' --projection-crop-after'
        return cmd

    def get_pr_tofu_cmd(self, ctset, args, nviews, WH):
        # indir will format paths to flats darks and tomo2 correctly even if they were
        # pre-processed, however path to the input directory with projections
        # cannot be formatted with that command correctly
        indir = self.make_inpaths(ctset[0], ctset[1])
        # so we need a separate "universal" command which considers all previous steps
        in_proj_dir, out_pattern = fmt_in_out_path(args.tmpdir, ctset[0], self._fdt_names[2])
        cmd = 'tofu preprocess --fix-nan-and-inf --projection-filter none --delta 1e-6'
        cmd += ' --darks {} --flats {} --projections {}'.format(indir[0], indir[1], in_proj_dir)
        if ctset[1] == 4:
            cmd += ' --flats2 {}'.format(indir[3])
        cmd += ' --output {}'.format(out_pattern)
        cmd += ' --energy {} --propagation-distance {}' \
               ' --pixel-size {} --regularization-rate {:0.2f}' \
            .format(args.energy, args.z, args.pixel, args.log10db)
        return cmd

    def get_reco_cmd(self, ctset, out_pattern, ax, args, nviews, WH, ffc, PR):
        #direct CT reconstruction from input dir to output dir;
        #or CT reconstruction after preprocessing only
        indir = self.make_inpaths(ctset[0], ctset[1])
        #correct location of proj folder in case if prepro was done
        in_proj_dir, quatsch = fmt_in_out_path(args.tmpdir, ctset[0], self._fdt_names[2], False)
        #in_proj_dir, quatsch = fmt_in_out_path(args.tmpdir,args.indir, self._fdt_names[2], False)
        #indir[2]=os.path.join(os.path.split(indir[2])[0], os.path.split(in_proj_dir)[1])
        #format command
        cmd = 'tofu reco --overall-angle 180'
        #cmd += '  --projections {}'.format(indir[2])
        cmd += '  --projections {}'.format(in_proj_dir)
        cmd += ' --output {}'.format(out_pattern)
        if ffc:
            cmd += ' --fix-nan-and-inf'
            cmd += ' --darks {} --flats {}'.format(indir[0],indir[1])
            if ctset[1]==4: #must be equivalent to len(indir)>3
                cmd += ' --flats2 {}'.format(indir[3])
            if not PR:
                cmd += ' --absorptivity'
        if PR:
            cmd += ' --delta 1e-6'\
                   ' --energy {} --propagation-distance {}'\
                   ' --pixel-size {} --regularization-rate {:0.2f}'\
                   .format(args.energy, args.z, args.pixel, args.log10db)
        cmd += ' --center-position-x {}'.format(ax)
        #if args.nviews==0:
        cmd += ' --number {}'.format(nviews)
        #elif args.nviews>0:
        #    cmd += ' --number {}'.format(args.nviews)
        cmd += ' --volume-angle-z {:0.5f}'.format(args.a0)
        # rows-slices to be reconstructed
        # full ROI
        b = int(np.ceil(WH[0]/2.0))
        a = -int(WH[0]/2.0)
        c = 1
        if args.vcrop:
            if args.RR:
                h2 = args.yheight/args.ystep/2.0
                b = np.ceil(h2)
                a = -int(h2)
            else:
                h2 = int(WH[0]/2.0)
                a = args.y - h2
                b = args.y+args.yheight - h2
                c = args.ystep
        cmd += ' --region={},{},{}'.format(a,b,c)
        # crop of reconstructed slice in the axial plane
        b = WH[1]/2
        if args.crop:
            cmd += ' --x-region={},{},{}'.format(args.x0-b,args.x0+args.dx-b,1)
            cmd += ' --y-region={},{},{}'.format(args.y0-b,args.y0+args.dy-b,1)
        #cmd = self.check_vcrop(cmd, args.vcrop, args.y, args.yheight, args.ystep, WH[0])
        cmd = self.check_8bit(cmd, args.gray256, args.bit, args.hmin, args.hmax)
        cmd = self.check_bigtif(cmd, args.bigtif_sli)
        cmd += ' --slice-memory-coeff=0.5'
        return cmd


    def get_reco_cmd_sinFFC(self, ctset, out_pattern, ax, args, nviews, WH, ffc, PR):
        #direct CT reconstruction from input dir to output dir;
        #or CT reconstruction after preprocessing only
        indir = self.make_inpaths(ctset[0], ctset[1])
        #correct location of proj folder in case if prepro was done
        in_proj_dir, quatsch = fmt_in_out_path(args.tmpdir, ctset[0], self._fdt_names[2], False)
        #in_proj_dir, quatsch = fmt_in_out_path(args.tmpdir,args.indir, self._fdt_names[2], False)
        #indir[2]=os.path.join(os.path.split(indir[2])[0], os.path.split(in_proj_dir)[1])
        #format command
        cmd = 'tofu reco --overall-angle 180'
        #cmd += '  --projections {}'.format(indir[2])
        cmd += '  --projections {}'.format(in_proj_dir)
        cmd += ' --output {}'.format(out_pattern)
        if PR:
            cmd += ' --disable-projection-crop'\
                   ' --delta 1e-6'\
                   ' --energy {} --propagation-distance {}'\
                   ' --pixel-size {} --regularization-rate {:0.2f}'\
                   .format(args.energy, args.z, args.pixel, args.log10db)
        cmd += ' --center-position-x {}'.format(ax)
        #if args.nviews==0:
        cmd += ' --number {}'.format(nviews)
        #elif args.nviews>0:
        #    cmd += ' --number {}'.format(args.nviews)
        cmd += ' --volume-angle-z {:0.5f}'.format(args.a0)
        # rows-slices to be reconstructed
        # full ROI
        b = int(np.ceil(WH[0]/2.0))
        a = -int(WH[0]/2.0)
        c = 1
        if args.vcrop:
            if args.RR:
                h2 = args.yheight/args.ystep/2.0
                b = np.ceil(h2)
                a = -int(h2)
            else:
                h2 = int(WH[0]/2.0)
                a = args.y - h2
                b = args.y+args.yheight - h2
                c = args.ystep
        cmd += ' --region={},{},{}'.format(a,b,c)
        # crop of reconstructed slice in the axial plane
        b = WH[1]/2
        if args.crop:
            cmd += ' --x-region={},{},{}'.format(args.x0-b,args.x0+args.dx-b,1)
            cmd += ' --y-region={},{},{}'.format(args.y0-b,args.y0+args.dy-b,1)
        #cmd = self.check_vcrop(cmd, args.vcrop, args.y, args.yheight, args.ystep, WH[0])
        cmd = self.check_8bit(cmd, args.gray256, args.bit, args.hmin, args.hmax)
        cmd = self.check_bigtif(cmd, args.bigtif_sli)
        cmd += ' --slice-memory-coeff=0.5'
        return cmd