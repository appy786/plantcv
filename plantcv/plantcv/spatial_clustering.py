# Segment objects into spatial based clusters within an image

import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler
from plantcv.plantcv import params
from plantcv.plantcv import print_image
from plantcv.plantcv import plot_image
from plantcv.plantcv import color_palette


def spatial_clustering(mask, algorithm="OPTICS", min_cluster_size=5, max_distance=0, njobs=-1):
    """Counts and segments portions of an image based on distance between two pixels.
    Masks showing all clusters, plus masks of individual clusters, are returned.

    img: Image to segment.
    Algorithm: Algorithm to use for segregating different clusters.
               Currently supporting OPTICS and DBSCAN. (Default="OPTICS")
    min_cluster_size: The minimum size a section of a mask must be (in pixels)
               before it can be considered its own cluster. (Default=5)
    max_distance: The total distance between two pixels for them to be considered a part
               of the same cluster.  For the DBSCAN algorithm, value must be between
               0 and 1.  For OPTICS, the value is in pixels and depends on the size
               of your picture.  (Default=0)
    njobs: The number of processors to use for calculation of the clusters.
               Default is all available processors.
    """

    al_upper = algorithm.upper()
    if "OPTICS" in al_upper:
        max_distance = np.inf
    elif "DBSCAN" in al_upper:
        max_distance = 0.2
    else:
        raise NameError("Please use only 'OPTICS' or 'DBSCAN' ")

    if not max_distance == 0:
        max_distance = max_distance

    vis = mask
    backtorgb = cv2.cvtColor(vis, cv2.COLOR_GRAY2RGB)
    x, y = np.where(np.all(backtorgb == [255, 255, 255], axis=2))
    zipped = np.column_stack((x, y))

    if "OPTICS" in al_upper:
        scaled = StandardScaler(with_mean=False, with_std=False).fit_transform(zipped)
        db = OPTICS(max_eps=max_distance, min_samples=min_cluster_size, n_jobs=njobs).fit(scaled)
    elif "DBSCAN" in al_upper:
        scaled = StandardScaler().fit_transform(zipped)
        db = DBSCAN(eps=max_distance, min_samples=min_cluster_size, n_jobs=njobs).fit(scaled)

    n_clusters_ = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
    colors = color_palette(n_clusters_ + 1)
    dict_of_colors = {}
    sub_mask = []
    h, w = backtorgb.shape[:2]
    image = np.zeros((h, w, 3), np.uint8)
    for y in range(-1, n_clusters_ + 1):
        dict_of_colors[str(y)] = colors[y]
    for y in range(0, n_clusters_):
        sub_mask.append(np.zeros((h, w, 3), np.uint8))
    dict_of_colors[str(-1)] = (255, 255, 255)
    for z in range(0, len(db.labels_)):
        if not db.labels_[z] == -1:
            sub_mask[db.labels_[z]][zipped[z][0], zipped[z][1]] = (dict_of_colors[str(db.labels_[z])][2],
                                                                   dict_of_colors[str(db.labels_[z])][1],
                                                                   dict_of_colors[str(db.labels_[z])][0])

        image[zipped[z][0], zipped[z][1]] = (dict_of_colors[str(db.labels_[z])][2],
                                             dict_of_colors[str(db.labels_[z])][1],
                                             dict_of_colors[str(db.labels_[z])][0])
    params.device += 1

    if params.debug == 'print':
        print_image(image, "full_image_mask.png")
        for c in range(0, len(sub_mask)):
            print_image(sub_mask[c], "subimage_cluster_" + str(c) + ".png")
    elif params.debug == 'plot':
        plot_image(image)
        for c in range(0, len(sub_mask)):
            plot_image(sub_mask[c])

    return image, sub_mask
