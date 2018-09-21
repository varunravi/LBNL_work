import os
import urllib.request


def get_jpegs(csvfile,
              outfile,
              jpeg_folder,
              DR,
              num_jpegs,
              jpeg_start=0,
              step=200):
    # configure the layer parameter for the url
    layer = ''
    if DR == 7:
        layer = 'decals-dr7'
    elif DR == 6:
        layer = 'mzls+bass-dr6'
    else:
        return 0
    c = jpeg_start
    # use the fits csv to download the jpeg images
    with open(csvfile) as csvdata:
        objectinfo = [line.split(',') for line in csvdata]
    # download the files
    count = 0
    for info in objectinfo[c + 1:c + step + 1]:
        print('downloading jpeg for', info[0])
        jpeg_link = 'http://legacysurvey.org/viewer/jpeg-cutout?ra={}&dec={}&layer={}&pixscale=0.262&bands=grz&size=101'.format(
            info[3], info[4], layer)
        jpeg_file = jpeg_folder + info[0] + '.jpeg'
        urllib.request.urlretrieve(jpeg_link, jpeg_file)
        count += 1
    return count


def main():
    step = 10000  # number of fits to get jpegs for
    fits_csv_file = 'C:/Data/lbnl/dr7/010/objectinfo_dr7.csv'
    # this can be ignored
    jpeg_outfile = 'C:/Data/lbnl/dr7/010/jpeg_outfile.txt'
    jpeg_folder = 'C:/Data/lbnl/dr7/010/jpegs/'
    jpeg_count = get_jpegs(fits_csv_file, jpeg_outfile, jpeg_folder, 7, step,
                           0, step)
    print('got {} images.'.format(jpeg_count))


if __name__ == '__main__':
    main()
