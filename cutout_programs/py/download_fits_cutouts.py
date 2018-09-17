'''
ANDREW PILON


Use this to get data sets from Legacy Surveys.

 - If first run, generates 'cutouts' folder as well as classifications_dr#.csv, objectinfo_dr#.csv, and outfile_dr#.txt within path.

Specifies files from Tractor to download, pulls info on objects, gets fits cutouts from skyviewer using coordinates, writes csv file
to have the same format as the training classifications.csv, writes Tractor catalog information to objectinfo_dr#.csv. Appends outfile
with next run parameters. Returns object dictionaries and parameters for next run.

!!! IMPORTANT NOTE:    I haven't yet figured out the issue of only being able to get certain amounts of cutouts from the viewer
                            before one fails, which causes the rest to fail. For this reason, this program is a workaround that currently
                            just gets 200 cutouts at a time (max was 247 from terminal, 192 from notebook). Outfile regulates this to keep
                            program running.

                            -- AJP try using time.sleep() to slow down program, may be overloading server with requests?

Run using: python3 download_fits_cutouts.py

'''

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import re
import csv
import urllib.request
import argparse
import sys
import os
import time
import urllib.request
import shutil
from numbers import Number
from pathlib import Path

def fluxToMag(f):
    return (-2.5 * (np.log(f)/np.log(10.) - 9))

def download_file(url, file_name):
    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def parse_tractor_dir(dir_path = '/global/cscratch1/sd/mdomingo/data/legacysurvey/dr7/tractor'):
    # recursively goes through and files
    p = Path(dir_path)
    for dir_name, sub_dirs, files in os.walk(p):
        print('Found directory: %s' % dir_name)
        for fname in files:
            print('\t%s' % fname)
    #TODO: hook up to parse_tractor_file


def parse_tractor_dir_flat(dir_path = '/global/cscratch1/sd/mdomingo/data/legacysurvey/dr7/tractor/250'):
    # goes through that directory and finds all the paths in the file. Does NOT go through subdirectory
    p = Path(dir_path)
    folders = []
    files = []

    for entry in os.scandir(p):
        if entry.is_dir():
            folders.append(entry)
        elif entry.is_file():
            files.append(entry)
    #TODO: hook up to parse_tractor_file

    print("Folders - {}".format(folders))
    print("Files - {}".format(files))

# checks if the dictionary cutout_values has values nobs_g, nobs_r and nobs_z greater then or equal to min_passes
def has_valid_nobs_values(cutout_values, min_passes):
    check_values = ['nobs_g', 'nobs_r', 'nobz_z']
    for check_value in check_values:
        if not _valid_pass(cutout_values, min_passes, check_value):
            return False
    return True

# checks if the dictionary cutout_values's key is a number and has a value greater then or equal to min_passes
def _valid_pass(cutout_values, min_passes, key):
    return cutout_values['nobs_g'].isinstance(n, Number) and cutout_values['nobs_g'] >= min_passes

# intakes a .fits file and returns a list of the valid cutouts from the tractor file in the form of a dictionary containing nobs_g, nobs_r, nobs_z, mtype, ra, dec and objid
def parse_tractor_file(file_path='/global/cscratch1/sd/mdomingo/data/legacysurvey/dr7/tractor/250/tractor-2501p320.fits'):
    #TODO: put these into the constructor
    DR = 7
    n_objects = 'all'
    min_passes = 3

    #TODO: what are these for?
    startfile = False
    startobject = False

    cutout_list = []
    p = Path(file_path)
    # check if file is a fits file
    if p.is_file and p.suffix == 'fits':
        print("File - {}".format(p.name))
        # update where to begin within the start file, using startobject
        if startobject == False:
            startobject = 0

        # go through objects in file
        for i in range(startobject, filedata.shape[0]):

<<<<<<< HEAD
def download_Tractor2(path, csvfile, objectcsvfile, DR=7, t_folder='000', n_objects='all', min_passes=2, counter_init=0, startfile=False, startobject=False):
=======
            same_file = False
            
            # check if enough objects have already been added to the list
            if len(objects) == n_objects:
                #TODO: what is this?
                last_object = i # this IS the next object to get because it won't be read in this iteration (break)
                if last_object == (filedata.shape[0] - 1): # check if it happened to be the alst object in the file so that
                    last_object = 0                            # the next file can start on objid: 0
                break
            
            cutout_values = {}

            # obtain values of nobs_g, nobs_r, nobs_z, mtype, ra, dec and objid values
            if DR == 7:
                cutout_values['dr'] = 7
                cutout_values['nobs_g'] = filedata[i][104] # DR7
                cutout_values['nobs_r'] = filedata[i][105]
                cutout_values['nobs_z'] = filedata[i][107]
                cutout_values['ra'] = filedata[i][7]
                cutout_values['dec'] = filedata[i][8]
                cutout_values['objid'] = filedata[i][3]
                cutout_values['mtype'] = filedata[i][6]
            elif DR == 6:
                cutout_values['dr'] = 6
                cutout_values['nobs_g'] = filedata[i][65] # DR6
                cutout_values['nobs_r'] = filedata[i][66]
                cutout_values['nobs_z'] = filedata[i][68]
                cutout_values['ra'] = filedata[i][6]
                cutout_values['dec'] = filedata[i][7]
                cutout_values['objid'] = filedata[i][3]
                # does not have an mtype
            else:
                continue
            # check if the nobs values are valid, if so add that to the cutout list
            if has_valid_nobs_values(cutout_values, min_passes):
                cutout_list.append(cutout_values)
    return cutout_list

# takes in a list of cutouts and creates tries to download the ra and dec values
def download_cutouts(cutout_list):
    necessary_values = ['nobs_g', 'nobs_r', 'nobz_z', 'ra', 'dec', 'objid', 'dr']
    # todo: parse through set of cutouts
    # create url for cutout
    for count, cutout in enumerate(cutout_list):
        for necessary_value in necessary_values:
            if necessary_value not in cutout:
                print('Warning: A cutout #{} does not contain the necessary value {}. Skipping that cutout'.format(count, necessary_value))
                continue
        
        objid = cutout['objid']
        ra = cutout['ra']
        dec = cutout['dec']

        url = ''
        print('\t [{}] attempting to get cutout for object {} at {} {}'.format(count, objid, ra,dec))
        if DR == 7:
            url = 'http://legacysurvey.org/viewer/fits-cutout?ra={}&dec={}&size=101&layer=decals-dr7&pixscale=0.262&bands=grz'.format(ra, dec) # DR5 -> DR7
        elif DR == 6:
            url = 'http://legacysurvey.org/viewer/fits-cutout?ra={}&dec={}&size=101&layer=mzls+bass-dr6&pixscale=0.262&bands=grz'.format(ra, dec) # DR6

        # TODO: uncomment these and figure out what to keep
        # while failed == False and retrieved == False:
        #     # checks how many attempts have been made, moves onto next object if too many
        #     if failed_attempts == 50:
        #         failed = True
        #     try:
        #         filename = wget.download(url, '{}cutouts/cutout_{:06d}.fits'.format(path, counter)) # DR7
                
        #         # EXIT IF DOWNLOADING FITS WITH SAME NAME
        #         if '(1)' in filename:
        #             same_file = True
        #             print(filename)
        #             print('\nthat file already exist, go figure out what you messed up. saving parameters and exiting program...')
        #             break

        #         with fits.open(filename) as fit:
        #             image = fit[0].data
        #         retrieved = True
        #     except:
        #         failed_attempts += 1
        #         if failed_attempts % 10 == 0:
        #             print('\t\tfailed attempt {}'.format(failed_attempts))
        #         pass

        # if failed:
        #     # don't update object list or counter
        #     total_fails += 1
        #     print('\t\tfailed to retrieve cutout for object - moving on to next object...')
        
        # if retrieved:
        #     # get all remaining values needed for dictionary, update object list and counter
        #     if DR == 7:
        #         filename = 'cutout_{:06d}'.format(counter)
        #         brickname = filedata[i][2]
        #         flux_g = filedata[i][44] # DR7
        #         mag_g = 0
        #         if flux_g != 0:
        #             mag_g = fluxToMag(flux_g)
        #         flux_r = filedata[i][45] # DR7
        #         mag_r = 0
        #         if flux_r != 0:
        #             mag_r = fluxToMag(flux_r)
        #         flux_z = filedata[i][47] # DR7
        #         mag_z = 0
        #         if flux_z != 0:
        #             mag_z = fluxToMag(flux_z)
        #     elif DR == 6:
        #         filename = 'cutout_{:06d}'.format(counter)
        #         brickname = filedata[i][2]
        #         flux_g = filedata[i][17] # DR6
        #         mag_g = 0
        #         if flux_g != 0:
        #             mag_g = fluxToMag(flux_g)
        #         flux_r = filedata[i][18] # DR6
        #         mag_r = 0
        #         if flux_r != 0:
        #             mag_r = fluxToMag(flux_r)
        #         flux_z = filedata[i][20] # DR6
        #         mag_z = 0
        #         if flux_z != 0:
        #             mag_z = fluxToMag(flux_z)

def download_Tractor2(path, csvfile, objectcsvfile, DR=7, t_folder='000', n_objects='all', min_passes=3, counter_init=0, startfile=False, startobject=False):
>>>>>>> f33af0c4c7eeb50dc53c68555f0e1e225db060f5
    # download folder within tractor catalog from nersc portal, get html of folder webpage, remove file
    print('downloading Tractor files from DR{} Tractor folder {}...'.format(DR, t_folder))
    t_url = 'http://portal.nersc.gov/project/cosmo/data/legacysurvey/dr{}/tractor/{}/'.format(DR, t_folder)
    foldername = '{}tractor_{}'.format(path, t_folder)
    t_folder_file = wget.download(t_url, foldername)
    with open(t_folder_file) as wgetfile:
        wgetdata = wgetfile.read()
    os.remove(foldername)

    # search html code for filenames 
    prog = re.compile('(?<=\.fits">).{21}')
    result = prog.findall(wgetdata)
    
    # create dictionaries for each object containing: image, ra/dec, flux (mag), nobs (exposures), etc.
    objects = [] # list of object dictionaries
    counter = counter_init
    total_fails = 0
    
    # start where you left off (if specified; otherwise set to 0 to start on first file in folder)
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
        
        # open the file, get object info, remove file
        print('opening file {}...'.format(f))
        filelink = t_url + f
        t_file = wget.download(filelink, path)
        with fits.open(t_file) as fit:
            filedata = fit[1].data
        os.remove(t_file)

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
                # creating url for good cut
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
                        filename = wget.download(url, '{}cutouts/cutout_{:06d}.fits'.format(path, counter)) # DR7
                        
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
            row = {field:o[field] for field in oFields}
            writer.writerow(row)
    if folder_done:
        objects = False

    return objects, next_start_file, next_start_object, next_c

def initiate_download_files(path, DR, outstart=('tractor-0010p292.fits','0','0','001')):
    '''
    If first run of program (i.e. not resuming), this creates the necessary files and folders for program to work
    '''
    os.makedirs('{}cutouts/'.format(path))
    csvfile = '{}classifications_dr{}'.format(path, DR)
    objectfile = '{}objectinfo_dr{}'.format(path, DR)
    outfile = '{}outfile_dr{}'.format(path, DR)

    print('initializing empty classifications csv file...')
    with open(csvfile+'.csv', 'w') as myFile:  
        myFields = ["ID","is_lens","Einstein_area","numb_pix_lensed_image","flux_lensed_image_in_sigma"]
        writer = csv.DictWriter(myFile, fieldnames=myFields)    
        writer.writeheader()
    print('done.')

    print('initializing empty object info csv file...')
    with open(objectfile+'.csv', 'w') as oFile:
        # omitting 'image' bc it's a lot to put in the csv file and we already have it
        oFields = ['filename','brickname','objid','ra','dec','flux_g','flux_r','flux_z','mag_g','mag_r','mag_z','nobs_g','nobs_r','nobs_z', 'mtype']
        writer = csv.DictWriter(oFile, fieldnames=oFields)    
        writer.writeheader()
    print('done.')

    print('initializing outfile...')
    with open(outfile+'.txt', 'w') as outFile:
        file, objid, c, t_folder = outstart
        outFile.write('{},{},{},{}'.format(file, objid, c, t_folder))
    print('done.\n')

    return

def main(path, outfile, csvfile, objectinfo, DR=7, startfile=False, startobject=False, c=0, t_folder='000'):

    ret_objects, next_start_file, next_start_object, next_c = download_Tractor2(path=path, csvfile=csvfile, objectcsvfile=objectinfo, DR=DR, t_folder=t_folder, n_objects=200, min_passes=3, counter_init=c, startfile=startfile, startobject=startobject)
    
    # check if you need to continue getting files from the next folder
    if ret_objects == False:
        new_t_folder = '{:03d}'.format(int(t_folder)+1)
        # call main again, starting with the first object of the first file in the next tractor folder
        ret_objects, next_start_file, next_start_object, next_c = main(path, outfile, csvfile, objectinfo, DR=7, startfile=False, startobject=False, c=next_c, t_folder=new_t_folder)

    print('\ndone.')
    return ret_objects, next_start_file, next_start_object, next_c

if __name__ == "__main__":

    # REQUIRED PARAMETERS
    # -- NOTE: MUST RUN "INITIATE_CSV_FILES.PY" BEFORE FIRST TIME RUNNING THIS
    DR = 7
    path = '/Users/mac/Desktop/LBNL/cutouts/tester_folder/' # <-- this needs to end in '/'

    # check if first run
    if not os.path.isdir('{}cutouts'.format(path)):
        initiate_download_files(path, DR)

    output_filename = '{}outfile_dr{}.txt'.format(path, DR)
    csvfile = '{}classifications_dr{}'.format(path, DR)
    objectinfo = '{}objectinfo_dr{}'.format(path, DR)


    print('\nloading in parameters from {}'.format(output_filename)) # get the parameters to run the function with from outfile
    with open(output_filename, 'r') as output_file:
        outdata = output_file.readlines()
    startfile, startobject, c, t_folder = str(outdata[-1].split(',')[0]), int(outdata[-1].split(',')[1]), int(outdata[-1].split(',')[2]), str(outdata[-1].split(',')[3])
    # run main
    start_time = time.time()
    ret_objects, next_start_file, next_start_object, next_c = main(path, output_filename, csvfile, objectinfo, DR, startfile, startobject, c, t_folder)
    # write new parameters to outfile
    print('\t- - - completed downloads in {} seconds - - -'.format(time.time() - start_time))
    print('writing parameters for next run to outfile...')
    with open(output_filename, 'a') as output_file:
        output_file.write('\n{},{},{},{}'.format(next_start_file, next_start_object, next_c, t_folder))
    print('done.\n')

