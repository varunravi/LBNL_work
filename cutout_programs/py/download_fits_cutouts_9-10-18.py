'''
ANDREW PILON

REQUIRES:

    1. if first run of generating new data set: first run "initiate_csv_files.py" with specified file path/names

    2. 

Use this to get data sets from Legacy Surveys.

Specifies files from Tractor to download, pulls info on objects, gets fits cutouts from skyviewer using coordinates, writes csv file
to have the same format as the training classifications.csv, writes objectinfo csvfile containing object info from Tractor. Returns
object dictionaries and last file opened.

NOTE: The directories 'tractor_folders', 'tractor_fits' and 'fits_cutouts' must exist in the same folder as this notebook to run.

!!! MORE IMPORTANT NOTE:    I haven't yet figured out the issue of only being able to get certain amounts of cutouts from the viewer
                            before one fails, which causes the rest to fail. For this reason, this program is a workaround that currently
                            just gets 200 cutouts at a time (max was 247 from terminal, 192 from notebook). Last file opeend is returned so
                            that it can start from the next one, as well as a counter to not overwrite filenames but keep appending to the
                            cutout folder.

Run using: python3 download_fits_cutouts.py -f tractor-0003m002.fits -c 4600 -t 000
                                            *startfile              *counter  *t_folder

                                            OUTDATED^^^: just run with program now (python3 download_fits_cutouts.py). works with outfile

'''

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import wget
import re
import csv
import urllib.request
import argparse
import sys
import os
import time

def fluxToMag(f):
    return (-2.5 * (np.log(f)/np.log(10.) - 9))

def download_Tractor2(csvfile, objectcsvfile, t_folder='000', n_objects='all', min_passes=2, counter_init=0, startfile=False, startobject=False):
    
    # download folder within tractor catalog from nersc portal, get html of folder webpage
    DR = 7
    print('downloading Tractor files from DR{}...'.format(DR))
    if DR == 7:
        t_url = 'http://portal.nersc.gov/project/cosmo/data/legacysurvey/dr{}/tractor/{}/'.format(DR, t_folder) # DR7
        foldername = '/Users/mac/Desktop/LBNL/DR{}/tractor_folders/tractor_{}'.format(DR, t_folder) # DR7
    elif DR == 6:
        t_url = 'http://portal.nersc.gov/project/cosmo/data/legacysurvey/dr{}/tractor/{}/'.format(DR, t_folder) # DR6
        foldername = '/Users/mac/Desktop/LBNL/DR{}/tractor_folders/tractor_{}'.format(DR, t_folder) # DR6
    print('t_folder:', t_folder, '  type=', type(t_folder))
    print('t_url = ', t_url)
    print('foldername = ', foldername)
    t_folder_file = wget.download(t_url, foldername) #, foldername
    with open(t_folder_file) as wgetfile:
        wgetdata = wgetfile.read()
    os.remove(foldername)

    # search html code for filenames 
    prog = re.compile('(?<=\.fits">).{21}')
    result = prog.findall(wgetdata)
    
    # create dictionaries for each object containing image, ra/dec, flux (mag), nobs (exposures)
    objects = [] # list of object dictionaries
    counter = counter_init
    total_fails = 0
    
    # start where you left off (if specified)
    firstfile_idx = 0
    next_start_file = False
    if startfile != False:
        for i, r in enumerate(result):
            if startfile == r:
                firstfile_idx = i # + 1
                break

    # iterate through tractor filenames found
    folder_done = False
    f_idx = firstfile_idx
    for f in result[firstfile_idx:]:
        
        # open the file, get object info
        print('opening file {}...'.format(f))
        filelink = t_url + f
        t_file = wget.download(filelink, '/Users/mac/Desktop/LBNL/DR{}/tractor_fits/'.format(DR))
        with fits.open(t_file) as fit:
            filedata = fit[1].data

        goodobj = 0
        # update where to begin within the start file, using startobject
        if startobject == False:
            startobject = 0

        # go through objects in file
        for i in range(startobject, filedata.shape[0]):

            same_file = False
            
            # check if enough objects have already been added to the list
            if len(objects) == n_objects:
                last_object = i # this IS the next object to get because it won't be read in this iteration (break)
                if last_object == (filedata.shape[0] - 1): # check if it happened to be the alst object in the file so that
                    last_object = 0                            # the next file can start on objid: 0
                break
            #  break out of loop and go to next file if it gets stalled after a failure and can't continue to get fits
            if total_fails == 15:
                print('!!! failed to get cutout 15 times - quitting early with recovered objects !!!')
                break
            
            # PERFORM DATA CUTS (nobs, mag, type, etc.)
            if DR == 7:
                nobs_g = filedata[i][104] # DR7
                nobs_r = filedata[i][105]
                nobs_z = filedata[i][107]
                mtype = filedata[i][6]
            elif DR == 6:
                nobs_g = filedata[i][65] # DR6
                nobs_r = filedata[i][66]
                nobs_z = filedata[i][68]

            if nobs_g >= min_passes and nobs_r >= min_passes and nobs_z >= min_passes:

                # now see if we can get it from the viewer cutout
                if DR == 7:
                    ra = filedata[i][7] #DR7
                    dec = filedata[i][8]
                    objid = filedata[i][3]
                elif DR == 6:
                    ra = filedata[i][6] #DR6
                    dec = filedata[i][7]
                    objid = filedata[i][3]
                print('\t [{}] attempting to get cutout for object {} at {} {}'.format(goodobj,objid,ra,dec))
                if DR == 7:
                    url = 'http://legacysurvey.org/viewer/fits-cutout?ra={}&dec={}&size=101&layer=decals-dr7&pixscale=0.262&bands=grz'.format(ra, dec) # DR5 -> DR7
                elif DR == 6:
                    url = 'http://legacysurvey.org/viewer/fits-cutout?ra={}&dec={}&size=101&layer=mzls+bass-dr6&pixscale=0.262&bands=grz'.format(ra, dec) # DR6
                
                failed_attempts = 0
                failed = False
                retrieved = False
                while failed == False and retrieved == False:
                    # checks how many attempts have been made, moves onto next object if too many
                    if failed_attempts == 50:
                        failed = True
                    try:
                        if DR == 7:
                            filename = wget.download(url, '/Users/mac/Desktop/LBNL/DR{}/fits_cutouts_dr{}_NONLENS_CANDIDATES/cutout_{:06d}.fits'.format(DR, DR, counter)) # DR7
                        elif DR == 6:
                            filename = wget.download(url, '/Users/mac/Desktop/LBNL/DR{}/fits_cutouts_dr{}_NONLENS_CANDIDATES/cutout_{:06d}.fits'.format(DR, DR, counter)) # DR6
                        
                        # EXIT IF DOWNLOADING FITS WITH SAME NAME
                        if '(1)' in filename:
                            same_file = True
                            print(filename)
                            print('\nthat file already exist, go figure out what you messed up. saving parameters and exiting program...')
                            break

                        with fits.open(filename) as fit:
                            image = fit[0].data
                        retrieved = True
                    except:
                        failed_attempts += 1
                        if failed_attempts % 10 == 0:
                            print('\t\tfailed attempt {}'.format(failed_attempts))
                        pass
   
                if failed:
                    # don't update object list or counter
                    total_fails += 1
                    print('\t\tfailed to retrieve cutout for object - moving on to next object...')
                
                if retrieved:
                    # get all remaining values needed for dictionary, update object list and counter
                    if DR == 7:
                        filename = 'cutout_{:06d}'.format(counter)
                        brickname = filedata[i][2]
                        flux_g = filedata[i][44] # DR7
                        mag_g = 0
                        if flux_g != 0:
                            mag_g = fluxToMag(flux_g)
                        flux_r = filedata[i][45] # DR7
                        mag_r = 0
                        if flux_r != 0:
                            mag_r = fluxToMag(flux_r)
                        flux_z = filedata[i][47] # DR7
                        mag_z = 0
                        if flux_z != 0:
                            mag_z = fluxToMag(flux_z)
                    elif DR == 6:
                        filename = 'cutout_{:06d}'.format(counter)
                        brickname = filedata[i][2]
                        flux_g = filedata[i][17] # DR6
                        mag_g = 0
                        if flux_g != 0:
                            mag_g = fluxToMag(flux_g)
                        flux_r = filedata[i][18] # DR6
                        mag_r = 0
                        if flux_r != 0:
                            mag_r = fluxToMag(flux_r)
                        flux_z = filedata[i][20] # DR6
                        mag_z = 0
                        if flux_z != 0:
                            mag_z = fluxToMag(flux_z)

                    object_dict = {'image':image,'brickname':brickname,'objid':objid,'filename':filename,'ra':ra,'dec':dec,'flux_g':flux_g,'flux_r':flux_r,'flux_z':flux_z,'mag_g':mag_g,'mag_r':mag_r,'mag_z':mag_z,'nobs_g':nobs_g,'nobs_r':nobs_r,'nobs_z':nobs_z, 'mtype':mtype}
                    objects.append(object_dict)
                    counter += 1
                    goodobj += 1
                    
        print('\ngot {} good objects from {}'.format(goodobj, f))

        if len(objects) == n_objects:
            print('enough objects gathered.')
            next_start_file = f # return the current file name
            next_start_object = last_object # return the index for the next object in the current file
            next_c = counter
            # os.remove(t_file)
            break
        # check if file is finished but need to move onto next file. Then reset objid to 0 again
        if (i == filedata.shape[0] - 1) and (len(objects) < n_objects):
            print('not enough objects from {}  ---  moving on to next file...'.format(f))
            startobject = 0
            next_start_object = 0
            next_c = counter
        if total_fails == 15:
            break

        if same_file == True:
            print('repeat file detected. continuing to exit...')
            break

        # UPDATE TRACTOR FOLDER IF EXHAUSTED FILES WITHIN
        f_idx += 1
        if f_idx == len(result) - 1:
            print('\ntractor folder {} has been exhausted.\n'.format(t_folder))
            folder_done = True
            break


    
    # check to make sure there were enough objects found in the folder of files
    if len(objects) < n_objects:
        print('\tonly able to retrieve {} good objects from folder {}'.format(len(objects), t_folder))


    # now create csv file to match fits file images, imitating the lensfinder challenge format
    print('appending files to classification csv file...')
    with open(csvfile+'.csv', 'a') as myFile:
        myFields = ["ID","is_lens","Einstein_area","numb_pix_lensed_image","flux_lensed_image_in_sigma"]
        writer = csv.DictWriter(myFile, fieldnames=myFields) 
        counter=counter_init
        for i in range(len(objects)):
            # might want to change the ID for the training process if it makes it easier to iterate
            ID = '{:06d}'.format(counter)
            counter+=1
            writer.writerow({"ID":ID,"is_lens":0,"Einstein_area":'nan',"numb_pix_lensed_image":'nan',"flux_lensed_image_in_sigma":'nan'})

            
    # write csv file to contain information from object dictionaries
    print('appending files to object info csv file...')
    with open(objectcsvfile+'.csv', 'a') as oFile:
        # omitting 'image' bc it's a lot to put in the csv file and we already have it
        oFields = ['filename','brickname','objid','ra','dec','flux_g','flux_r','flux_z','mag_g','mag_r','mag_z','nobs_g','nobs_r','nobs_z', 'mtype']
        writer = csv.DictWriter(oFile, fieldnames=oFields)
        for o in objects:
            writer.writerow({'filename':o['filename'],'brickname':o['brickname'],'objid':o['objid'],'ra':o['ra'],'dec':o['dec'],'flux_g':o['flux_g'],'flux_r':o['flux_r'],'flux_z':o['flux_z'],'mag_g':o['mag_g'],'mag_r':o['mag_r'],'mag_z':o['mag_z'],'nobs_g':o['nobs_g'],'nobs_r':o['nobs_r'],'nobs_z':o['nobs_z'], 'mtype':o['mtype']})    
    
    if folder_done:
        objects = False

    return objects, next_start_file, next_start_object, next_c

def main(startfile=False, startobject=False, c=0, t_folder='000'):

    csvfilee = '/Users/mac/Desktop/LBNL/DR7/classifications_dr7_NONLENS_CANDIDATES'
    objectinfoo = '/Users/mac/Desktop/LBNL/DR7/objectinfo_dr7_NONLENS_CANDIDATES'
    ret_objects, next_start_file, next_start_object, next_c = download_Tractor2(csvfile=csvfilee, objectcsvfile=objectinfoo, t_folder=t_folder, n_objects=200, min_passes=3, counter_init=c, startfile=startfile, startobject=startobject)
    
    # check if you need to continue getting files from the next folder
    if ret_objects == False:
        new_t_folder = '{:03d}'.format(int(t_folder)+1)
        # call main again, starting with the first object of the first file in the next tractor folder
        ret_objects, next_start_file, next_start_object, next_c = main(startfile=False, startobject=False, c=next_c, t_folder=new_t_folder)

    print('\ndone.')
    return ret_objects, next_start_file, next_start_object, next_c

if __name__ == "__main__":


    # # to input tractor folder, starting file within folder, and counter to update file names.
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-o', type = str)
    # parser.add_argument('-f', type = str)
    # parser.add_argument('-c', type = int)
    # parser.add_argument('-t', type = str)
    # args = parser.parse_args()
    # startobject = args.o # object index within file
    # startfile = args.f # file name of last opened file
    # c = args.c # counter
    # t_folder = args.t # tractor folder

    # # # running program with output file, which makes command line arguments unnecessary: # # #

    # get parameters from outfile generated from previous program run
    
    DR = 7
    output_filename = '/Users/mac/Desktop/LBNL/DR{}/outfile_dr{}_NONLENS_CANDIDATES.txt'.format(DR, DR)
    print('\n\nloading in parameters from {}'.format(output_filename))
    with open(output_filename, 'r') as output_file:
        outdata = output_file.readlines()
    startfile, startobject, c, t_folder = str(outdata[-1].split(',')[0]), int(outdata[-1].split(',')[1]), int(outdata[-1].split(',')[2]), str(outdata[-1].split(',')[3])
    # run main
    start_time = time.time()
    ret_objects, next_start_file, next_start_object, next_c = main(startfile, startobject, c, t_folder)
    # write new parameters to outfile
    print('\t- - - completed downloads in {} seconds'.format(time.time() - start_time))
    print('writing parameters for next run to outfile')
    with open(output_filename, 'a') as output_file:
        output_file.write('\n{},{},{},{}'.format(next_start_file, next_start_object, next_c, t_folder))



    # print('\nTractor folder used: {}'.format('tractor_' + t_folder))
    # print('begin next download with c: {}'.format(c + 200))
    # print('begin next download with startfile: {}'.format(next_start_file))
    # print('begin next download with startobject: {}'.format(next_start_object))

