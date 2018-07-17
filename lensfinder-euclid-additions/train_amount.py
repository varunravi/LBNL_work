# pylint: disable=C,R,no-member

# Usage
# python3 neural_train.py arch?/arch.py path_to_npz_files output_path number_of_iteration # (number_of_images, added by AJPILON)

import math
import tensorflow as tf
import numpy as np
from sys import argv
from time import time, sleep
import queue
import threading
from sklearn import metrics
from astropy.io import fits
import importlib.util
from shutil import copy2
import os
import sys
import glob
import scipy
import scipy.ndimage as ndimage

def make_fits(files, labels, predict, path='.', suffix='', maxi=500, band=0):
    # pylint: disable=no-member
    assert labels.dtype == 'bool'
    assert predict.dtype == 'bool'

    fp = np.where(np.logical_and(labels == False, predict == True))[0]
    fn = np.where(np.logical_and(labels == True,  predict == False))[0]
    tp = np.where(np.logical_and(labels == True,  predict == True))[0]
    tn = np.where(np.logical_and(labels == False, predict == False))[0]

    np.savetxt('{}/fp{}.txt'.format(path, suffix), [np.load(files[i])['id'] for i in fp], "%s  ")
    np.savetxt('{}/fn{}.txt'.format(path, suffix), [np.load(files[i])['id'] for i in fn], "%s  ")
    np.savetxt('{}/tp{}.txt'.format(path, suffix), [np.load(files[i])['id'] for i in tp], "%s  ")
    np.savetxt('{}/tn{}.txt'.format(path, suffix), [np.load(files[i])['id'] for i in tn], "%s  ")

    fits.PrimaryHDU([np.load(files[i])['image'][:,:,band] for i in fp[:maxi]]).writeto('{}/fp{}.fits'.format(path, suffix), overwrite=True)
    fits.PrimaryHDU([np.load(files[i])['image'][:,:,band] for i in fn[:maxi]]).writeto('{}/fn{}.fits'.format(path, suffix), overwrite=True)
    fits.PrimaryHDU([np.load(files[i])['image'][:,:,band] for i in tp[:maxi]]).writeto('{}/tp{}.fits'.format(path, suffix), overwrite=True)
    fits.PrimaryHDU([np.load(files[i])['image'][:,:,band] for i in tn[:maxi]]).writeto('{}/tn{}.fits'.format(path, suffix), overwrite=True)

def images_to_sprite(data):
    """Creates the sprite image along with any necessary padding

    Args:
      data: NxHxW[x3] tensor containing the images.

    Returns:
      data: Properly shaped HxWx3 image with any necessary padding.
    """
    if len(data.shape) == 3:
        data = np.tile(data[...,np.newaxis], (1,1,1,3))
    data = data.astype(np.float32)
    min_ = np.min(data.reshape((data.shape[0], -1)), axis=1)
    data = (data.transpose(1,2,3,0) - min_).transpose(3,0,1,2)
    max_ = np.max(data.reshape((data.shape[0], -1)), axis=1)
    data = (data.transpose(1,2,3,0) / max_).transpose(3,0,1,2)
    # Inverting the colors seems to look better for MNIST
    data = 1 - data

    n = int(np.ceil(np.sqrt(data.shape[0])))
    padding = ((0, n ** 2 - data.shape[0]), (0, 0),
            (0, 0)) + ((0, 0),) * (data.ndim - 3)
    data = np.pad(data, padding, mode='constant',
            constant_values=0)
    # Tile the individual thumbnails into an image.
    data = data.reshape((n, n) + data.shape[1:]).transpose((0, 2, 1, 3)
            + tuple(range(4, data.ndim + 1)))
    data = data.reshape((n * data.shape[1], n * data.shape[3]) + data.shape[4:])
    data = (data * 255).astype(np.uint8)
    return data

def predict_all(session, CNN, cnn, files, f, step=50):
    q = queue.Queue(20)  # batches in the queue
    ps = np.zeros(len(files), np.float64)
    xent_list = []

    def compute():
        for j in range(0, len(files), step):
            t0 = time()

            rem = len(files) // step - j // step
            if q.qsize() < min(2, rem):
                while q.qsize() < min(20, rem):
                    sleep(0.05)

            xs, ys = q.get()
            t1 = time()

            k = min(j + step, len(files))
            ps[j:k], xent = cnn.predict_xentropy(session, xs, ys)
            xent_list.append(xent * (k-j))

            t2 = time()
            f.write('{}/{} ({}) {: >6.3f}s+{:.3f}s\n'.format(
                j, len(files), q.qsize(), t1 - t0, t2 - t1))
            f.flush()

            q.task_done()

    t = threading.Thread(target=compute)
    t.daemon = True
    t.start()

    for j in range(0, len(files), step):
        k = min(j + step, len(files))
        xs = CNN.load(files[j:k])
        ys = np.array([np.load(f)['is_lens'] for f in files[j:k]]).astype(np.float32)
        q.put((xs, ys))

    q.join()

    return ps, np.sum(xent_list) / len(files)


def main(arch_path, images_path, output_path, n_iter, n_data, n_run):
    time_total_0 = time()
    output_path = output_path + '_{}'.format(n_run)
    if os.path.isdir(output_path):
        resume = True
        if not os.path.isdir(output_path + '/iter'):
            sys.exit("Try to resume computation : no iter dir in the directory")
        if not arch_path.startswith(output_path):
            sys.exit("Try to resume computation : you need to resume with the same architecture")
        f = open(output_path + '/log.txt', 'a')
        fs = open(output_path + '/stats_test.txt', 'a')
        fst = open(output_path + '/stats_train.txt', 'a')
        fm = open(output_path + '/metrics.txt', 'a')
        fx = open(output_path + '/xent_batch.txt', 'a')
    else:
        resume = False
        os.makedirs(output_path)
        os.makedirs(output_path + '/iter')
        f = open(output_path + '/log.txt', 'w')
        fs = open(output_path + '/stats_test.txt', 'w')
        fst = open(output_path + '/stats_train.txt', 'w')
        fm = open(output_path + '/metrics.txt', 'w')
        fx = open(output_path + '/xent_batch.txt', 'w')

        f.write("{}\n".format(argv))
        f.flush()

        copy2(arch_path, output_path + '/arch.py')
        copy2('layers_dihedral_equi.py', output_path + '/layers_dihedral_equi.py')
        copy2('layers_normal.py', output_path + '/layers_normal.py')

    f.write("Loading {}...".format(arch_path))
    f.flush()

    spec = importlib.util.spec_from_file_location("module.name", arch_path)
    neural = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(neural)
    CNN = neural.CNN

    cnn = CNN()

    f.write(" Done\nSplit data set...")
    f.flush()

    files_test, files_train = CNN.split_test_train(images_path, n_data)
    files_train = files_train[:7000] # AJP - restrict data amount?

    f.write(" Done\n")
    f.write("{: <6} images into train set\n".format(len(files_train)))
    f.write("{: <6} images into test set\n".format(len(files_test)))
    f.write("Create TF session...")
    f.flush()

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.graph_options.optimizer_options.global_jit_level = tf.OptimizerOptions.ON_1
    session = tf.Session(config=config)

    f.write(" Done\nCreate graph...")
    f.flush()

    bands = np.load(files_train[0])['image'].shape[2]
    cnn.create_architecture(bands=bands)
    f.write("Done\n{} bands\n".format(bands))
    f.flush()

    f.write("Extract test labels...")
    f.flush()
    labels_test = []
    for fi in files_test:
        with np.load(fi) as data:
            labels_test.append(data['is_lens'])
    labels_test = np.array(labels_test, np.float32)
    f.write(" Done\nExtract train labels...")
    f.flush()
    labels_train = []
    for fi in files_train:
        with np.load(fi) as data:
            labels_train.append(data['is_lens'])
    labels_train = np.array(labels_train, np.float32)
    f.write(" Done\n")
    f.flush()

    f.write("Merge summary...")
    f.flush()
    summary = tf.summary.merge_all()
    f.write(" Done\n")
    f.flush()

    f.write("Create writer...")
    f.flush()
    writer = tf.summary.FileWriter(output_path + "/tensorboard")
    writer.add_graph(session.graph)
    f.write(" Done\nEmbedding...")
    f.flush()

    embedding_amount = 1000 #AJP
    # Make sprite and labels.
    sprite_path = output_path + '/../sprite{}.png'.format(bands)
    if not os.path.isfile(sprite_path):
        images = ndimage.zoom(CNN.load(files_test[:embedding_amount]), (1, 64/101, 64/101, 1))
        assert(images.shape == (embedding_amount, 64, 64, bands))
        if bands == 1:
            images = images[:, :, :, 0]
        if bands == 4:
            images = images[:, :, :, :3]
        sprite = images_to_sprite(images)
        scipy.misc.imsave(sprite_path, sprite)

    tsv_path = output_path + '/../labels{}.tsv'.format(bands)
    if not os.path.isfile(tsv_path):
        metadata_file = open(tsv_path, 'w')
        metadata_file.write('id\tis_lens\tnumb_pix_lensed_image\teinstein_area\tflux_lensed_image_in_sigma\n')
        for i in range(embedding_amount):
            with np.load(files_test[i]) as data:
                is_lens = data['is_lens']
                metadata_file.write('{}\t{}\t{}\t{}\t{}\n'.format(data['id'], is_lens, is_lens * data['numb_pix_lensed_image'], is_lens * data['einstein_area'], is_lens * data['flux_lensed_image_in_sigma']))
        metadata_file.close()

    embedding_size = np.prod(cnn.embedding_input.get_shape().as_list()[1:])
    embedding = tf.Variable(tf.zeros([embedding_amount, embedding_size]), name="test_embedding")
    embedding_placeholder = tf.placeholder(tf.float32, embedding.get_shape())
    embedding_assignment = embedding.assign(embedding_placeholder)
    embedding_saver = tf.train.Saver([embedding])

    embedding_input_flatten = tf.reshape(cnn.embedding_input, [-1, embedding_size])

    config = tf.contrib.tensorboard.plugins.projector.ProjectorConfig()
    embedding_config = config.embeddings.add()
    embedding_config.tensor_name = embedding.name
    embedding_config.sprite.image_path = sprite_path
    embedding_config.metadata_path = tsv_path
    # Specify the width and height of a single thumbnail.
    embedding_config.sprite.single_image_dim.extend([64, 64])
    tf.contrib.tensorboard.plugins.projector.visualize_embeddings(writer, config)
    f.write(" Done\n")
    f.flush()

    saver = tf.train.Saver(max_to_keep=20)

    if not resume:
        fs.write("# predictions on the test set\n")
        fs.write("# iteration | probabilities\n")
        fs.write("-1 {}\n".format(" ".join([str(l) for l in labels_test])))
        fs.flush()

        fst.write("# predictions on the training set\n")
        fst.write("# iteration | probabilities\n")
        fst.write("-1 {}\n".format(" ".join([str(l) for l in labels_train[:len(labels_test)]])))
        fst.flush()

        fm.write("# iteration xent_test auc_test xent_train auc_train\n")
        fx.write("# iteration xent_batch \n")

    if resume:
        f.write("Restore session...")
        f.flush()
        backup = sorted(glob.glob(output_path + '/iter/*.data.index'))[-1]
        backup = backup.rsplit('.', 1)[0] # remove .index
        resume_iter = int(backup.split('/')[-1].split('.')[0])
        saver.restore(session, backup)
        f.write(' Done\nBackup file : {}\n'.format(backup))
        f.flush()
    else:
        f.write("Initialize variables...")
        f.flush()
        resume_iter = 0
        session.run(tf.global_variables_initializer())
        f.write(" Done\n")
        f.flush()

    cnn.train_counter = resume_iter

    def print_log(xs, ys):
        ps, xent = cnn.predict_xentropy(session, xs, ys)
        ys = ys.astype(np.int32)

        f.write('{}\n'.format(' '.join(['{:.2f}/{}'.format(p, y) for (p, y) in zip(ps, ys) if y == 1])))
        f.write('{}\n'.format(' '.join(['{:.2f}/{}'.format(p, y) for (p, y) in zip(ps, ys) if y == 0])))
        f.write('=> xent = {:.4}\n'.format(xent))
        f.write('< pred|label=1 > = {:.3g}\n'.format(np.sum(ps * ys) / np.sum(ys == 1)))
        f.write('< pred|label=0 > = {:.3g}\n'.format(np.sum(ps * (1. - ys)) / np.sum(ys == 0)))
        ps = (ps > 0.5).astype(np.int32)
        tp = np.sum(np.logical_and(ys == 1, ps == 1))
        tn = np.sum(np.logical_and(ys == 0, ps == 0))
        fp = np.sum(np.logical_and(ys == 0, ps == 1))
        fn = np.sum(np.logical_and(ys == 1, ps == 0))
        f.write('tp:{} tn:{} fp:{} fn:{}\n'.format(tp, tn, fp, fn))
        f.flush()

    def save_statistics(i):
        if (i // 1000) % 3 == 1: #AJP 1000 -> 100
            data = np.zeros((embedding_amount, embedding_size), np.float32)
            for j in range(0, embedding_amount, 100): #AJP 100 -> 10
                f.write('{}/{}\n'.format(j, embedding_amount))
                f.flush()
                data[j: j+100] = session.run(embedding_input_flatten, feed_dict={ cnn.tfx: CNN.load(files_test[j: j+100]) }) #AJP 100 -> 10
            session.run(embedding_assignment, feed_dict={ embedding_placeholder: data })

            embedding_saver.save(session, '{}/tensorboard/model.ckpt'.format(output_path), i)

        save_path = saver.save(session, '{}/iter/{:06d}.data'.format(output_path, i))
        f.write('Model saved in file: {}\n'.format(save_path))

        ps_test, xentropy_test = predict_all(session, CNN, cnn, files_test, f)
        ps_train, xentropy_train = predict_all(session, CNN, cnn, files_train[:len(files_test)], f)

        auc_test = metrics.roc_auc_score(labels_test, ps_test)
        auc_train = metrics.roc_auc_score(labels_train[:len(files_test)], ps_train)

        fm.write("{} {:.8g} {:.8g} {:.8g} {:.8g}\n".format(i, xentropy_test, auc_test, xentropy_train, auc_train))
        fm.flush()

        f.write("     |  TEST    |  TRAIN\n")
        f.write("-----+----------+-------\n")
        f.write("xent |  {: <8.4}|  {:.4}\n".format(xentropy_test, xentropy_train))
        f.write("auc  |  {: <8.4}|  {:.4}\n".format(auc_test, auc_train))
        f.flush()

        fs.write("{} {}\n".format(i, " ".join(["{:.12g}".format(p) for p in ps_test])))
        fs.flush()
        fst.write("{} {}\n".format(i, " ".join(["{:.12g}".format(p) for p in ps_train])))
        fst.flush()

        s = tf.Summary()
        s.value.add(tag="xent_test", simple_value=xentropy_test)
        s.value.add(tag="xent_train", simple_value=xentropy_train)
        s.value.add(tag="auc_test", simple_value=auc_test)
        s.value.add(tag="auc_train", simple_value=auc_train)
        writer.add_summary(s, i)

        #make_fits(files_test, labels_test == 1, ps_test > 0.5, output_path + '/iter', "_{:06d}".format(i))

    f.write("Start daemon...")
    f.flush()

    # Use a Queue to generate batches and train in parallel
    q = queue.Queue(30)  # batches in the queue

    def trainer():
        for i in range(resume_iter, resume_iter + n_iter + 1):
            t0 = time()

            rem = resume_iter + n_iter + 1 - i
            if q.qsize() < min(3, rem):
                while q.qsize() < min(30, rem):
                    sleep(0.05)

            xs, ys = q.get()
            t1 = time()

            if i % 100 == 0 and i != 0: #AJP 100 -> 10
                f.write("Before the training\n")
                f.write("===================\n")
                f.flush()
                print_log(xs, ys)

            if i == 102 or i == 1002:
                from tensorflow.python.client import timeline
                run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
                run_metadata = tf.RunMetadata()

                xentropy, _ = cnn.train(session, xs, ys, options=run_options, run_metadata=run_metadata)
                if xentropy == 'nan': # AJP
                    f.write('\nNAN DETECTED BEEP BOOP BEEP BOOP !!!!\nline 378\n_ = ', _) # AJP
                    SAVE_XENTROPY = (xentropy, _) # AJP
                # google chrome : chrome://tracing/

                tl = timeline.Timeline(run_metadata.step_stats)
                ctf = tl.generate_chrome_trace_format()
                with open(output_path + '/timeline.json', 'w') as tlf:
                    tlf.write(ctf)
            elif i % 100 == 0: #AJP 100 -> 10
                xentropy, s = cnn.train(session, xs, ys, tensors=[summary])
                if xentropy == 'nan': # AJP
                    f.write('\nNAN DETECTED BEEP BOOP BEEP BOOP !!!!\nline 391\ns = ', _) # AJP
                    SAVE_XENTROPY = (xentropy, _) # AJP
                writer.add_summary(s[0], i)
            else:
                xentropy, _ = cnn.train(session, xs, ys)
                if xentropy == 'nan': # AJP
                    f.write('\nNAN DETECTED BEEP BOOP BEEP BOOP !!!!\nline 395\n_ = ', _) # AJP
                    SAVE_XENTROPY = (xentropy, _) # AJP

            fx.write('{}    {:.6} \n'.format(i, xentropy))
            s = tf.Summary()
            s.value.add(tag="xent_batch", simple_value=xentropy)
            writer.add_summary(s, i)

            if i % 100 == 0 and i != 0: #AJP 100 -> 10
                f.write("\nAfter the training\n")
                f.write("==================\n")
                print_log(xs, ys)
                fx.flush()

            if i % 100 == 0 and i != 0: #AJP 100 -> 10
                save_statistics(i)

            t2 = time()
            f.write('{:06d}: ({}) {: >6.3f}s+{:.3f}s {} xent_batch={:.3f}\n'.format(
                i, q.qsize(), t1 - t0, t2 - t1, xs.shape, xentropy))
            f.flush()

            q.task_done()

            if math.isnan(xentropy) or math.isinf(xentropy):
                f.write('BEEP BOOP BEEP BOP, THE PROGRAM FOUND OUT NOW ABOUT THE NAN\n') # AJP
                f.write(SAVE_XENTROPY) # AJP
                return

    t = threading.Thread(target=trainer)
    t.daemon = True
    t.start()

    f.write(" Done\nStart feeders...")
    f.flush()

    # the n+1
    xs, ys = CNN.batch(files_train, labels_train)
    q.put((xs, ys))

    n_feeders = 2
    assert n_iter % n_feeders == 0
    def feeder():
        for _ in range(n_iter // n_feeders):
            xs, ys = CNN.batch(files_train, labels_train)
            q.put((xs, ys))

    threads = [threading.Thread(target=feeder) for _ in range(n_feeders)]
    for t in threads:
        t.start()
    f.write("Done\n")
    f.flush()
    for t in threads:
        t.join()

    q.join()
    session.close()

    t = time() - time_total_0
    f.write("total time : {}h {}min".format(t // 3600, (t % 3600) // 60))

    f.close()
    fs.close()
    fm.close()
    fx.close()


if __name__ == '__main__':
    for i in range(5):
        main(argv[1], argv[2], argv[3], int(argv[4]), int(argv[5]), i)
