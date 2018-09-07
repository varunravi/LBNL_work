'''
ANDREW PILON

Initializes csv files necessary for download_fits_cutouts.py; csv files are created in the same folder as program.
object information is appended to the end of the files with each call of download_fits_cutouts.py

'''

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import wget
import re
import csv
import urllib.request

def main(csvfile, objectcsvfile):
	print('initializing empty classifications csv file...')
	with open(csvfile+'.csv', 'w') as myFile:  
		myFields = ["ID","is_lens","Einstein_area","numb_pix_lensed_image","flux_lensed_image_in_sigma"]
		writer = csv.DictWriter(myFile, fieldnames=myFields)    
		writer.writeheader()
	print('done.')

	print('initializing empty object info csv file...')
	with open(objectcsvfile+'.csv', 'w') as oFile:
		# omitting 'image' bc it's a lot to put in the csv file and we already have it
		oFields = ['filename','brickname','objid','ra','dec','flux_g','flux_r','flux_z','mag_g','mag_r','mag_z','nobs_g','nobs_r','nobs_z', 'mtype']
		writer = csv.DictWriter(oFile, fieldnames=oFields)    
		writer.writeheader()
	print('done.')

if __name__ == '__main__':
	main('/Users/mac/Desktop/LBNL/DR7/classifications_dr7_NONLENS_CANDIDATES', '/Users/mac/Desktop/LBNL/DR7/objectinfo_dr7_NONLENS_CANDIDATES')