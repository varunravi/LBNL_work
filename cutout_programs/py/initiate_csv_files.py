'''
ANDREW PILON

Initializes csv files necessary for download_fits_cutouts.py; csv files are created in the same folder as program.
object information is appended to the end of the files with each call of download_fits_cutouts.py

'''

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import re
import csv
import os
import urllib.request


def main(csvfile, objectcsvfile, outfile, outstart):
    print('initializing empty classifications csv file...')
    with open(csvfile+'.csv', 'w') as myFile:
        myFields = ["ID", "is_lens", "Einstein_area",
                    "numb_pix_lensed_image", "flux_lensed_image_in_sigma"]
        writer = csv.DictWriter(myFile, fieldnames=myFields)
        writer.writeheader()
    print('done.')

    print('initializing empty object info csv file...')
    with open(objectcsvfile+'.csv', 'w') as oFile:
        # omitting 'image' bc it's a lot to put in the csv file and we already have it
        oFields = ['filename', 'brickname', 'objid', 'ra', 'dec', 'flux_g', 'flux_r',
                   'flux_z', 'mag_g', 'mag_r', 'mag_z', 'nobs_g', 'nobs_r', 'nobs_z', 'mtype']
        writer = csv.DictWriter(oFile, fieldnames=oFields)
        writer.writeheader()
    print('done.')

    print('initializing outfile...')
    with open(outfile+'.txt', 'w') as outFile:
        file, objid, c, t_folder = outstart
        outFile.write('{},{},{},{}'.format(file, objid, c, t_folder))
    print('done.')


if __name__ == '__main__':

    # file, objid, c, t_folder --  for outfile
    outstart = ('tractor-0010p292.fits', '0', '0', '001')

    DR = int(input('DR: '))
    path = str(input('path: '))
    os.makedirs('{}cutouts/'.format(path))
    csvfile = '{}classifications_dr{}'.format(path, DR)
    objectfile = '{}objectinfo_dr{}'.format(path, DR)
    outfile = '{}outfile_dr{}'.format(path, DR)
    main(csvfile, objectfile, outfile, outstart)
