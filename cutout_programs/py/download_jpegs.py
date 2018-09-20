import os
import wget
import urllib.request


def get_jpegs(csvfile,
              outfile,
              jpeg_folder,
              DR,
              num_jpegs,
              jpeg_start=0,
              step=200):
    '''
    *NOTE* I don't use the jpeg outfile anymore because urllib doesn't run into the download limit like wget did with cutouts.
    Therefore just have the step be however many should be downloaded. Otherwise it runs with a terminal script using the outfile,
    getting *step* images at a time.
    '''
    # specify layer
    if DR == 7:
        layer = 'decals-dr7'
    elif DR == 6:
        layer = 'mzls+bass-dr6'

    # # check if outfile exists, create if not, get c.
    # if os.path.isfile(outfile):
    #     with open(outfile, 'a') as outdata:
    #         outdata = outdata.readlines()
    #         c = int(outdata.split(',')[-1])
    #         outdata.write(','+str(c+step))
    # else:
    #     with open(outfile, 'w') as outdata:
    #         outdata.write(str(jpeg_start))
    #         outdata.write(','+str(jpeg_start+step))
    #     c = jpeg_start
    c = jpeg_start
    with open(csvfile) as csvdata:
        objectinfo = [line.split(',') for line in csvdata]
    count = 0
    for info in objectinfo[c + 1:c + step + 1]:
        print('getting jpeg for', info[0])
        jpeg_link = 'http://legacysurvey.org/viewer/jpeg-cutout?ra={}&dec={}&layer={}&pixscale=0.262&bands=grz&size=101'.format(
            info[3], info[4], layer)
        jpeg_file = jpeg_folder + info[0] + '.jpeg'
        # jpeg = wget.download(jpeg_link, jpeg_file)
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
    # get_jpegs('/Users/mac/Desktop/LBNL/DR6/objectinfo_dr6.csv', '/Users/mac/Desktop/LBNL/DR6/jpeg_outfile.txt', '/Users/mac/Desktop/LBNL/DR6/jpegs_dr6/', 6, 10000, 0, step)
    print('got {} images.'.format(jpeg_count))


if __name__ == '__main__':
    main()
