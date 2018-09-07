# pylint: disable=C,R,E1101

# Usage
# python3 fits_to_npz_3band.py output_empty_directory classifications.csv fits_cutout_directory

# EDITED BY ANDREW PILON TO WORK ON 1 FITS CUTOUT CONTAINING 3 BAND IMAGES

import csv
import numpy as np
import os
from astropy.io import fits
from sys import argv

def read_fits(cutout_path, flags, output):

    # lfn = list(zip(*[sorted(os.listdir(p)) for p in list_of_paths]))

    # assert len(lfn) == len(flags)

    # for fns, flag in zip(lfn, flags):
    #     print("read {}".format(fns))
    #     bands = ()
    #     for i, p in enumerate(list_of_paths):
    #         f = fits.open(os.path.join(p, fns[i]), memmap=False)
    #         bands += (f[0].data, )
    #         f.close()

    #     im = np.stack(bands, axis=2)

    #     if np.isnan(im).any() or np.isinf(im).any():
    #         print("Warning ! image contain Inf or NaN")

    #     ids = [int(f.split('.')[0].split('-')[-1]) for f in fns]

    #     # images of different bands must have the same ID
    #     assert [i == ids[0] for i in ids]

    #     # the ID from the CSV must match with the ID of the fits files
    #     assert ids[0] == int(flag[0])
    for i, filename in enumerate(sorted(os.listdir(cutout_path))[1:]): # pull after [0] to avoid random non fits file
        print('converting {}...'.format(filename))

        with fits.open(cutout_path+filename) as filedata: # AJPILON
            im = filedata[0].data
            print(im.shape)
            return

        cutout_id = filename.split('.')[0].split('_')[-1] # AJPILON

        assert int(cutout_id) == int(flags[i][0]) # AJPILON

        dic = {}
        dic['id'] = int(flags[i][0])
        dic['image'] = im
        dic['is_lens'] = int(flags[i][1])
        dic['einstein_area'] = 'nan' # AJPILON set these values to 'nan' bc no data from viewer
        dic['numb_pix_lensed_image'] = 'nan'
        dic['flux_lensed_image_in_sigma'] = 'nan'

        np.savez('{}/{}.npz'.format(output, cutout_id), **dic)


def read_csv(path):
    # returns array containing info from classifications csv file
    with open(path) as f:
        reader = csv.reader(f)
        rows = [r for r in reader][1:]
        rows = [[float(x) for x in r] for r in rows]
    return np.array(rows)

def main(output, csv_path, cutout_path):
    flags = read_csv(csv_path)
    read_fits(cutout_path, flags, output)


if __name__ == '__main__':
    # outputfile, classifications csvfile, "bands" which may just become fits cutout folder
    main(str(argv[1]), str(argv[2]), str(argv[3]))
