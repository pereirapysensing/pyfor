import os
import laspy
import pandas as pd
import pyfor
import geopandas as gpd

class Indexer:
    """
    Internal class used to index a directory of las files.
    """

class CloudDataFrame(gpd.GeoDataFrame):
    """
    Implements a data frame structure for processing and managing multiple cloud objects.
    """
    def __init__(self, *args, **kwargs):
        super(CloudDataFrame, self).__init__(*args, **kwargs)
        self.n_threads = 1

        if "bounding_box" in self.columns.values:
            self.set_geometry("bounding_box", inplace=True)

    @classmethod
    def from_dir(cls, las_dir, n_jobs=1, get_bounding_boxes = True):
        """
        Wrapped function for producing a CloudDataFrame from a directory of las files.
        :param las_dir:
        :param n_jobs: The number of threads used to construct information about the CloudDataFrame.
        :param get_bounding_boxes: If True, builds the bounding boxes for each las tile by manually reading in
        the file and computing the bounding box. For very large collections this may be computationally costly, and
        can be set to False.
        :return:
        """
        las_path_init = [[os.path.join(root, file) for file in files] for root, dirs, files in os.walk(las_dir)][0]
        cdf = CloudDataFrame({'las_path': las_path_init})
        cdf.n_threads = n_jobs

        if get_bounding_boxes == True:
            cdf._build_polygons()

        return(cdf)

    def set_index(self, *args):
        return CloudDataFrame(super(CloudDataFrame, self).set_index(*args))

    def par_apply(self, func, column='las_path', buffer_distance = 0, *args):
        """
        Apply a function to each las path. Allows for parallelization using the n_jobs argument. This is achieved \
        via joblib Parallel and delayed.

        :param func: The user defined function, must accept a single argument, the path of the las file.
        :param n_jobs: The number of threads to spawn, default of 1.
        :param column: The column to apply on, will be the first argument to func
        :param buffer_distance: The distance to buffer and aggregate each tile.
        :param *args: Further arguments to `func`
        """
        from joblib import Parallel, delayed
        if buffer_distance > 0:
            self._buffer(buffer_distance)
            for i, geom in enumerate(self["bounding_box"]):
                intersecting = self._get_intersecting(i)

                clip_geom = self['buffered_bounding_box'].iloc[i]
                print(clip_geom)
                parent_cloud = pyfor.cloud.Cloud(self["las_path"].iloc[i])
                for path in intersecting["las_path"]:
                    adjacent_cloud = pyfor.cloud.Cloud(path)
                    parent_cloud.data._append(adjacent_cloud.data)

        output = Parallel(n_jobs=self.n_threads)(delayed(func)(plot_path, *args) for plot_path in self[column])
        return output

    # TODO Many of these _functions are redundant due to a bug in joblib that prevents lambda functions
    # once this bug is fixed these functions can be drastically simplified and aggregated.
    def _get_bounding_box(self, las_path):
        """
        Vectorized function to get a bounding box from an individual las path.
        :param las_path:
        :return:
        """
        # segmentation of point clouds
        pc = laspy.file.File(las_path)
        min_x, max_x = pc.header.min[0], pc.header.max[0]
        min_y, max_y = pc.header.min[1], pc.header.max[1]
        return((min_x, max_x, min_y, max_y))

    def _get_bounding_boxes(self):
        """
        Retrieves a bounding box for each path in las path.
        :return:
        """
        return self.par_apply(self._get_bounding_box, column="las_path")

    def _build_polygons(self):
        """Builds the shapely polygons of the bounding boxes and adds them to self.data"""
        from shapely.geometry import Polygon
        bboxes = self._get_bounding_boxes()
        self["bounding_box"] = [Polygon(((bbox[0], bbox[2]), (bbox[1], bbox[2]),
                                           (bbox[1], bbox[3]), (bbox[0], bbox[3]))) for bbox in bboxes]
        self.set_geometry("bounding_box", inplace = True)

    def _get_intersecting(self, tile_index):
        """
        Gets the intersecting tiles for the given tile_index

        :param: The index of the tile within the CloudDataFrame
        :return: A CloudDataFrame of intersecting tiles
        """
        # TODO Seek more efficient solution...
        # FIXME this is probably a sloppy way
        intersect_bool = self.intersects(self["buffered_bounding_box"].iloc[tile_index])
        intersect_cdf = CloudDataFrame(self[intersect_bool])
        intersect_cdf.n_threads = self.n_threads
        return intersect_cdf


    def _buffer(self, distance, in_place = True):
        """
        Buffers the CloudDataFrame geometries.
        :return: A new CloudDataFrame with buffered geometries.
        """
        # TODO implement in_place
        # also, pretty sloppy, consider relegating to a function, like "copy" or something
        norm_geoms = self["bounding_box"].copy()
        buffered = super(CloudDataFrame, self).buffer(distance)
        cdf = CloudDataFrame(self)
        cdf["bounding_box"] = norm_geoms
        cdf["buffered_bounding_box"] = buffered
        cdf.n_threads = self.n_threads
        cdf.set_geometry("bounding_box", inplace=True)
        return cdf

    def clip(self):
        """
        Clips the CloudDataFrame with the supplied geometries.
        :return:
        """
        pass


    def plot(self, *args):
        """Plots the bounding boxes of the Cloud objects"""
        plot = super(CloudDataFrame, self).plot(*args)
        plot.figure.show()


def from_dir(las_dir, n_jobs=1):
    """
    Constructs a CloudDataFrame from a directory of las files.

    :param las_dir: The directory of las files.
    :return: A CloudDataFrame constructed from the directory of las files.
    """

    return CloudDataFrame.from_dir(las_dir, n_jobs= n_jobs)


def stitch_clouds(collection):
    """
    Holder function for some ideas.
    :return:

    """
