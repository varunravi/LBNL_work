"""
ANDREW PILON


Use this to get data sets from Legacy Surveys.

 # .csv, objectinfo_dr#.csv, and outfile_dr#.txt within path.
 - If first run, generates 'cutouts' folder as well as classifications_dr

Specifies files from Tractor to download, pulls info on objects, gets fits cutouts from skyviewer using coordinates, writes csv file
to have the same format as the training classifications.csv, writes Tractor catalog information to objectinfo_dr#.csv. Appends outfile
with next run parameters. Returns object dictionaries and parameters for next run.

!!! IMPORTANT NOTE:    I haven't yet figured out the issue of only being able to get certain amounts of cutouts from the viewer
                            before one fails, which causes the rest to fail. For this reason, this program is a workaround that currently
                            just gets 200 cutouts at a time (max was 247 from terminal, 192 from notebook). Outfile regulates this to keep
                            program running.

                            -- AJP try using time.sleep() to slow down program, may be overloading server with requests?

Run using: python3 download_fits_cutouts.py

"""

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import re
import csv
import wget
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
    return -2.5 * (np.log(f) / np.log(10.) - 9)


def download_Tractor2(
    path,
    csvfile,
    objectcsvfile,
    DR=7,
    t_folder="000",
    n_objects="all",
    min_passes=3,
    counter_init=0,
    startfile=False,
    startobject=False,
):
    # download folder within tractor catalog from nersc portal, get html of folder webpage, remove file
    print(
        "downloading Tractor files from DR{} Tractor folder {}...".format(DR, t_folder)
    )
    t_url = "http://portal.nersc.gov/project/cosmo/data/legacysurvey/dr{}/tractor/{}/".format(
        DR, t_folder
    )
    foldername = "{}tractor_{}".format(path, t_folder)
    t_folder_file = wget.download(t_url, foldername)
    with open(t_folder_file) as wgetfile:
        wgetdata = wgetfile.read()
    os.remove(foldername)
    # search html code for filenames
    prog = re.compile('(?<=\.fits">).{21}')
    result = prog.findall(wgetdata)

    # create dictionaries for each object containing: image, ra/dec, flux (mag), nobs (exposures), etc.
    objects = []  # list of object dictionaries
    counter = counter_init
    total_fails = 0

    # start where you left off (if specified; otherwise set to 0 to start on first file in folder)
    firstfile_idx = 0
    next_start_file = False
    if startfile != False:
        for i, r in enumerate(result):
            if startfile == r:
                firstfile_idx = i  # + 1
                break

    # iterate through tractor filenames found
    folder_done = False
    f_idx = firstfile_idx
    for f in result[firstfile_idx:]:

        # open the file, get object info, remove file
        print("opening file {}...".format(f))
        filelink = t_url + f
        t_file = wget.download(filelink, path)
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
                # this IS the next object to get because it won't be read in this iteration (break)
                last_object = i
                # check if it happened to be the alst object in the file so that
                if last_object == (filedata.shape[0] - 1):
                    last_object = 0  # the next file can start on objid: 0
                break
            #  break out of loop and go to next file if it gets stalled after a failure and can't continue to get fits
            if total_fails == 15:
                print(
                    "!!! failed to get cutout 15 times - quitting early with recovered objects !!!"
                )
                break

            filename = "cutout_{:06d}".format(counter)

            mag_g = 0
            mag_r = 0
            mag_z = 0
            flux_g = 0
            flux_r = 0
            flux_z = 0
            brickname = None
            ra = None
            dec = None
            objid = None
            url = None
            # Extracting information from the huge filedata array.
            if DR == 7:
                nobs_g = filedata[i][104]
                nobs_r = filedata[i][105]
                nobs_z = filedata[i][107]
                mtype = filedata[i][6]
                brickname = filedata[i][2]
                flux_g = filedata[i][44]
                flux_r = filedata[i][45]
                flux_z = filedata[i][47]
                ra = filedata[i][7]
                dec = filedata[i][8]
                objid = filedata[i][3]
                url = "http://legacysurvey.org/viewer/fits-cutout?ra={}&dec={}&size=101&layer=decals-dr7&pixscale=0.262&bands=grz".format(
                    ra, dec
                )
            elif DR == 6:
                nobs_g = filedata[i][65]
                nobs_r = filedata[i][66]
                nobs_z = filedata[i][68]
                brickname = filedata[i][2]
                flux_g = filedata[i][17]
                flux_r = filedata[i][18]
                flux_z = filedata[i][20]
                ra = filedata[i][6]
                dec = filedata[i][7]
                objid = filedata[i][3]
                url = "http://legacysurvey.org/viewer/fits-cutout?ra={}&dec={}&size=101&layer=mzls+bass-dr6&pixscale=0.262&bands=grz".format(
                    ra, dec
                )
            else:
                continue
            # DATA CUT SECTION
            if nobs_g < min_passes or nobs_r < min_passes or nobs_z < min_passes:
                print("\nFailed min_passes check")
                continue
            # if not (mtype == 'COMP' or mtype == 'DEV' or mtype == 'EXP'):
            #     print('\nFailed mtype check. mtype=' + mtype)
            #     continue
            if flux_g <= 0 or flux_r <= 0 or flux_z <= 0:
                print("\nFailed positive flux check")
                continue
            mag_g = fluxToMag(flux_g)
            mag_r = fluxToMag(flux_r)
            mag_z = fluxToMag(flux_z)
            # if mag_z < 2:
            # print('\nFailed check: mag_z=' + str(mag_z) + " flux_z=" +
            #       str(flux_z))
            # continue
            print(
                "\t [{}] attempting to get cutout for object {} at {} {}".format(
                    goodobj, objid, ra, dec
                )
            )

            failed_attempts = 0
            failed = False
            retrieved = False
            while failed == False and retrieved == False:
                # checks how many attempts have been made, moves onto next object if too many
                if failed_attempts == 50:
                    failed = True
                try:
                    filename = wget.download(
                        url, "{}cutouts/cutout_{:06d}.fits".format(path, counter)
                    )

                    # EXIT IF DOWNLOADING FITS WITH SAME NAME
                    if "(1)" in filename:
                        same_file = True
                        print(filename)
                        print(
                            "\nthat file already exist, go figure out what you messed up. saving parameters and exiting program..."
                        )
                        return
                    with fits.open(filename) as fit:
                        image = fit[0].data
                    retrieved = True
                except:
                    failed_attempts += 1
                    if failed_attempts % 10 == 0:
                        print("\t\tfailed attempt {}".format(failed_attempts))
                    pass

            if failed:
                # don't update object list or counter
                total_fails += 1
                print(
                    "\t\tfailed to retrieve cutout for object - moving on to next object..."
                )
                continue
            object_dict = {
                "image": image,
                "brickname": brickname,
                "objid": objid,
                "filename": filename,
                "ra": ra,
                "dec": dec,
                "flux_g": flux_g,
                "flux_r": flux_r,
                "flux_z": flux_z,
                "mag_g": mag_g,
                "mag_r": mag_r,
                "mag_z": mag_z,
                "nobs_g": nobs_g,
                "nobs_r": nobs_r,
                "nobs_z": nobs_z,
                "mtype": mtype,
            }
            objects.append(object_dict)
            counter += 1
            goodobj += 1

        print("\ngot {} good objects from {}".format(goodobj, f))

        if len(objects) == n_objects:
            print("enough objects gathered.")
            next_start_file = f  # return the current file name
            # return the index for the next object in the current file
            next_start_object = last_object
            next_c = counter
            # os.remove(t_file)
            break
        # check if file is finished but need to move onto next file. Then reset objid to 0 again
        if (i == filedata.shape[0] - 1) and (len(objects) < n_objects):
            print(
                "not enough objects from {}  ---  moving on to next file...".format(f)
            )
            startobject = 0
            next_start_object = 0
            next_c = counter
        if total_fails == 15:
            break

        if same_file == True:
            print("repeat file detected. continuing to exit...")
            break

        # UPDATE TRACTOR FOLDER IF EXHAUSTED FILES WITHIN
        f_idx += 1
        if f_idx == len(result) - 1:
            print("\ntractor folder {} has been exhausted.\n".format(t_folder))
            folder_done = True
            break

    # check to make sure there were enough objects found in the folder of files
    if len(objects) < n_objects:
        print(
            "\tonly able to retrieve {} good objects from folder {}".format(
                len(objects), t_folder
            )
        )

    # now create csv file to match fits file images, imitating the lensfinder challenge format
    print("appending files to classification csv file...")
    with open(csvfile + ".csv", "a") as myFile:
        myFields = [
            "ID",
            "is_lens",
            "Einstein_area",
            "numb_pix_lensed_image",
            "flux_lensed_image_in_sigma",
        ]
        writer = csv.DictWriter(myFile, fieldnames=myFields)
        counter = counter_init
        for i in range(len(objects)):
            # might want to change the ID for the training process if it makes it easier to iterate
            ID = "{:06d}".format(counter)
            counter += 1
            writer.writerow(
                {
                    "ID": ID,
                    "is_lens": 0,
                    "Einstein_area": "nan",
                    "numb_pix_lensed_image": "nan",
                    "flux_lensed_image_in_sigma": "nan",
                }
            )

    # write csv file to contain information from object dictionaries
    print("appending files to object info csv file...")
    with open(objectcsvfile + ".csv", "ab") as oFile:
        # omitting 'image' bc it's a lot to put in the csv file and we already have it
        oFields = [
            "filename",
            "brickname",
            "objid",
            "ra",
            "dec",
            "flux_g",
            "flux_r",
            "flux_z",
            "mag_g",
            "mag_r",
            "mag_z",
            "nobs_g",
            "nobs_r",
            "nobs_z",
            "mtype",
        ]
        writer = csv.DictWriter(oFile, fieldnames=oFields)
        for o in objects:
            row = {field: o[field] for field in oFields}
            writer.writerow(row)
    if folder_done:
        objects = False
    return objects, next_start_file, next_start_object, next_c


def initiate_download_files(
    path, DR, outstart=("tractor-0010p292.fits", "0", "0", "001")
):
    """
    If first run of program (i.e. not resuming), this creates the necessary files and folders for program to work
    """
    os.makedirs("{}cutouts/".format(path))
    csvfile = "{}classifications_dr{}".format(path, DR)
    objectfile = "{}objectinfo_dr{}".format(path, DR)
    outfile = "{}outfile_dr{}".format(path, DR)

    print("initializing empty classifications csv file...")
    with open(csvfile + ".csv", "w") as myFile:
        myFields = [
            "ID",
            "is_lens",
            "Einstein_area",
            "numb_pix_lensed_image",
            "flux_lensed_image_in_sigma",
        ]
        writer = csv.DictWriter(myFile, fieldnames=myFields)
        writer.writeheader()
    print("done.")

    print("initializing empty object info csv file...")
    with open(objectfile + ".csv", "w") as oFile:
        # omitting 'image' bc it's a lot to put in the csv file and we already have it
        oFields = [
            "filename",
            "brickname",
            "objid",
            "ra",
            "dec",
            "flux_g",
            "flux_r",
            "flux_z",
            "mag_g",
            "mag_r",
            "mag_z",
            "nobs_g",
            "nobs_r",
            "nobs_z",
            "mtype",
        ]
        writer = csv.DictWriter(oFile, fieldnames=oFields)
        writer.writeheader()
    print("done.")

    print("initializing outfile...")
    with open(outfile + ".txt", "w") as outFile:
        file, objid, c, t_folder = outstart
        outFile.write("{},{},{},{}".format(file, objid, c, t_folder))
    print("done.\n")

    return


def main(
    path,
    outfile,
    csvfile,
    objectinfo,
    DR=7,
    startfile=False,
    startobject=False,
    c=0,
    t_folder="000",
):
    t_folder = "011"
    ret_objects, next_start_file, next_start_object, next_c = download_Tractor2(
        path=path,
        csvfile=csvfile,
        objectcsvfile=objectinfo,
        DR=DR,
        t_folder=t_folder,
        n_objects=200,
        min_passes=3,
        counter_init=c,
        startfile=startfile,
        startobject=startobject,
    )

    # check if you need to continue getting files from the next folder
    if ret_objects == False:
        new_t_folder = "{:03d}".format(int(t_folder) + 1)
        # call main again, starting with the first object of the first file in the next tractor folder
        ret_objects, next_start_file, next_start_object, next_c = main(
            path,
            outfile,
            csvfile,
            objectinfo,
            DR=7,
            startfile=False,
            startobject=False,
            c=next_c,
            t_folder=new_t_folder,
        )

    print("\ndone.")
    return ret_objects, next_start_file, next_start_object, next_c


if __name__ == "__main__":
    # REQUIRED PARAMETERS
    DR = 7
    path = "D:/Data/lbnl/dr7/011/"  # <-- this needs to end in '/'

    # check if first run
    if not os.path.isdir("{}cutouts".format(path)):
        initiate_download_files(path, DR)

    output_filename = "{}outfile_dr{}.txt".format(path, DR)
    csvfile = "{}classifications_dr{}".format(path, DR)
    objectinfo = "{}objectinfo_dr{}".format(path, DR)

    # get the parameters to run the function with from outfile
    print("\nloading in parameters from {}".format(output_filename))
    with open(output_filename, "r") as output_file:
        outdata = output_file.readlines()
    startfile, startobject, c, t_folder = (
        str(outdata[-1].split(",")[0]),
        int(outdata[-1].split(",")[1]),
        int(outdata[-1].split(",")[2]),
        str(outdata[-1].split(",")[3]),
    )
    # run main
    start_time = time.time()
    ret_objects, next_start_file, next_start_object, next_c = main(
        path,
        output_filename,
        csvfile,
        objectinfo,
        DR,
        startfile,
        startobject,
        c,
        t_folder,
    )
    # write new parameters to outfile
    print(
        "\t- - - completed downloads in {} seconds - - -".format(
            time.time() - start_time
        )
    )
    print("writing parameters for next run to outfile...")
    with open(output_filename, "a") as output_file:
        output_file.write(
            "\n{},{},{},{}".format(next_start_file, next_start_object, next_c, t_folder)
        )
    print("done.\n")

