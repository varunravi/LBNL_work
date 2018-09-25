import numpy as np
from astropy.io import fits

FITS_CATALOG_KEYS = {
    "brickname",
    "objid",
    "ra",
    "dec",
    "type",
    "flux_g",
    "flux_r",
    "flux_z",
    "nobs_g",
    "nobs_r",
    "nobs_z",
}

def extract_from_fits_file(fits_file, keys={}):
    with fits.open(fits_file) as hdul:
        data = hdul[1].data
        if not keys:
            keys = hdul[1].columns.names
        return [{key: datum[key] for key in FITS_CATALOG_KEYS} for datum in data]


def check_dict_key(dict1, dict2, key):
    if dict1[key] == dict2[key]:
        return True
    print(str(key) + " diff")
    return False

def match_two_fits_files(fits_file1, fits_file2, matching_keys):
    fits1_vals = extract_from_fits_file(fits_file1, FITS_CATALOG_KEYS)
    fits2_vals = extract_from_fits_file(fits_file2, FITS_CATALOG_KEYS)

    for i in range(min(len(fits1_vals), len(fits2_vals))):
        if not all(check_dict_key(fits1_vals[i], fits2_vals[i], key) for key in matching_keys):
            print("Check failed.\n{{i:{},\nfits1[i]:{},\nfits2[i]:{}}}".format(i, fits1_vals[i], fits2_vals[i]))
            break
        print("checked " + str(i))

if __name__ == "__main__":
    dr6_fits = "D:/Data/lbnl/dr6/tractor-0001m002.fits"
    dr7_fits = "D:/Data/lbnl/dr7/tractor-0001m002.fits"

    check_keys = ["brickname", "objid", "ra", "dec"]
    match_two_fits_files(dr6_fits, dr7_fits, check_keys)

