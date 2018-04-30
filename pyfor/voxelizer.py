import numpy as np

class VoxelGrid:
    """A 3 dimensional grid representation of a point cloud. This is analagous to the rasterizer.Grid class, but
    with three axes instead of two. VoxelGrids are generally used to produce VoxelRaster objects."""
    def __init__(self, cloud, cell_size):
        self.cell_size = cell_size
        self.cloud = cloud
        self.cell_size = cell_size

        min_x, max_x = self.cloud.las.min[0], self.cloud.las.max[0]
        min_y, max_y = self.cloud.las.min[1], self.cloud.las.max[1]
        min_z, max_z = self.cloud.las.min[2], self.cloud.las.max[2]

        self.m = int(np.floor((max_y - min_y) / cell_size))
        self.n = int(np.floor((max_x - min_x) / cell_size))
        self.p = int(np.floor((max_z - min_z) / cell_size))

        # Create bins
        bins_x = np.searchsorted(np.linspace(min_x, max_x, self.n), self.cloud.las.points["x"])
        bins_y = np.searchsorted(np.linspace(min_y, max_y, self.m), self.cloud.las.points["y"])
        bins_z = np.searchsorted(np.linspace(min_z, max_z, self.p), self.cloud.las.points["z"])

        self.data = self.cloud.las.points
        self.data["bins_x"] = bins_x
        self.data["bins_y"] = bins_y
        self.data["bins_z"] = bins_z

        self.cells = self.data.groupby(['bins_x', 'bins_y', 'bins_z'])

    def voxel_raster(self, func, dim):
        """Creates a 3 dimensional voxel raster, analagous to rasterizer.Grid.raster.

        :param func: The function to summarize within each voxel.
        :param dim: The dimension upon which to summarize (i.e. "z", "intensity", etc.)
        """

        # TODO for now this is a standalone function, at some point there will be a VoxelRaster class that will
        # handle most of the below in its __init__ function.
        voxel_grid = np.zeros((self.m, self.n, self.p))
        cells = self.data.groupby(['bins_x', 'bins_y', 'bins_z']).agg({'z':'max'}).reset_index()

        # Set the values of the grid
        voxel_grid[cells["bins_x"], cells["bins_y"], cells["bins_z"]] = cells["z"]

        return(voxel_grid)
