import numpy as np
from astropy.io import fits

fits_catalog_keys = {'brickname', 'objid', 'ra', 'dec', 'type', 'flux_g', 'flux_r', 'flux_z', 'nobs_g', 'nobs_r', 'nobs_z'}

dr7_fits = "D:/Data/lbnl/tractor-0001m002_dr7.fits"
dr7_fits_vals = []
with fits.open(dr7_fits) as hdul:
    data = hdul[1].data
    dr7_fits_vals = [{key: datum[key] for key in fits_catalog_keys} for datum in data]

dr6_fits = "D:/Data/lbnl/tractor-0001m002_dr6.fits"
dr6_fits_vals = []
with fits.open(dr6_fits) as hdul:
    data = hdul[1].data
    dr6_fits_vals = [{key: datum[key] for key in fits_catalog_keys} for datum in data]

def checkDif(dict1, dict2, key):
    if dict1[key] == dict2[key]:
        return True
    print(str(key) + " diff")
    return False

check_keys = ['brickname', 'objid', 'ra', 'dec']

l6 = len(dr6_fits_vals)
l7 = len(dr7_fits_vals)

for i in range(min(l6, l7)):
    if not all (checkDif(dr6_fits_vals[i], dr7_fits_vals[i], key) for key in check_keys):
        print("...")
        print("{}\n{}\n{}".format(i, dr6_fits_vals[i], dr7_fits_vals[i]))
        break
