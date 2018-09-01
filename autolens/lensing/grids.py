from autolens.imaging import imaging_util
import numpy as np

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)


class ImageGrid(np.ndarray):
    """Abstract class for a regular grid of coordinates. On a regular grid, each pixel's arc-second coordinates \
    are represented by the value at the centre of the pixel.

    Coordinates are defined from the top-left corner, such that data_to_image in the top-left corner of an \
    masked_image (e.g. [0,0]) have a negative x-value and positive y-value in arc seconds. The masked_image pixel indexes are \
    also counted from the top-left.

    A regular *grid_coords* is a NumPy array of image_shape [image_pixels, 2]. Therefore, the first element maps \
    to the masked_image pixel index, and second element to its (x,y) arc second coordinates. For example, the value \
    [3,1] gives the 4th masked_image pixel's y coordinate.

    Below is a visual illustration of a regular grid, where a total of 10 data_to_image are unmasked and therefore \
    included in the grid.

    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|     This is an example masked_image.Mask, where:
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|o|o|x|x|x|x|     x = True (Pixel is masked and excluded from lensing)
    |x|x|x|o|o|o|o|x|x|x|     o = False (Pixel is not masked and included in lensing)
    |x|x|x|o|o|o|o|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|

    This masked_image pixel index's will come out like this (and the direction of arc-second coordinates is highlighted
    around the masked_image.

    pixel_scale = 1.0"

    <--- -ve  x  +ve -->

    |x|x|x|x|x|x|x|x|x|x|  ^   grid_coords[0] = [-0.5,  1.5]
    |x|x|x|x|x|x|x|x|x|x|  |   grid_coords[1] = [ 0.5,  1.5]
    |x|x|x|x|x|x|x|x|x|x|  |   grid_coords[2] = [-1.5,  0.5]
    |x|x|x|x|0|1|x|x|x|x| +ve  grid_coords[3] = [-0.5,  0.5]
    |x|x|x|2|3|4|5|x|x|x|  y   grid_coords[4] = [ 0.5,  0.5]
    |x|x|x|6|7|8|9|x|x|x| -ve  grid_coords[5] = [ 1.5,  0.5]
    |x|x|x|x|x|x|x|x|x|x|  |   grid_coords[6] = [-1.5, -0.5]
    |x|x|x|x|x|x|x|x|x|x|  |   grid_coords[7] = [-0.5, -0.5]
    |x|x|x|x|x|x|x|x|x|x| \/   grid_coords[8] = [ 0.5, -0.5]
    |x|x|x|x|x|x|x|x|x|x|      grid_coords[9] = [ 1.5, -0.5]
    """

    @property
    def no_pixels(self):
        return self.shape[0]

    @classmethod
    def blurring_grid_from_mask_and_psf_shape(cls, mask, psf_shape):
        blurring_mask = mask.blurring_mask_for_psf_shape(psf_shape)
        return ImageGrid(blurring_mask.masked_image_grid)

    def __new__(cls, arr, *args, **kwargs):
        return arr.view(cls)

    def __reduce__(self):
        # Get the parent's __reduce__ tuple
        pickled_state = super(ImageGrid, self).__reduce__()
        # Create our own tuple to pass to __setstate__
        class_dict = {}
        for key, value in self.__dict__.items():
            class_dict[key] = value
        new_state = pickled_state[2] + (class_dict,)
        # Return a tuple that replaces the parent's __setstate__ tuple with our own
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state):

        for key, value in state[-1].items():
            setattr(self, key, value)
        super(ImageGrid, self).__setstate__(state[0:-1])

    @property
    def xticks(self):
        return np.around(np.linspace(np.amin(self[:,0]), np.amax(self[:,0]), 4), 2)

    @property
    def yticks(self):
        return np.around(np.linspace(np.amin(self[:,1]), np.amax(self[:,1]), 4), 2)


class SubGrid(ImageGrid):
    """Abstract class for a sub of coordinates. On a sub-grid, each pixel is sub-gridded into a uniform grid of
     sub-coordinates, which are used to perform over-sampling in the lens lensing.

    Coordinates are defined from the top-left corner, such that data_to_image in the top-left corner of an
    masked_image (e.g. [0,0]) have a negative x-value and positive y-value in arc seconds. The masked_image pixel indexes are
    also counted from the top-left.

    A sub *grid_coords* is a NumPy array of image_shape [image_pixels, sub_grid_pixels, 2]. Therefore, the first
    element maps to the masked_image pixel index, the second element to the sub-pixel index and third element to that
    sub pixel's (x,y) arc second coordinates. For example, the value [3, 6, 1] gives the 4th masked_image pixel's
    7th sub-pixel's y coordinate.

    Below is a visual illustration of a sub grid. Like the regular grid, the indexing of each sub-pixel goes from
    the top-left corner. In contrast to the regular grid above, our illustration below restricts the mask to just
    2 data_to_image, to keep the illustration brief.

    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|     This is an example masked_image.Mask, where:
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|     x = True (Pixel is masked and excluded from lensing)
    |x|x|x|x|o|o|x|x|x|x|     o = False (Pixel is not masked and included in lensing)
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|
    |x|x|x|x|x|x|x|x|x|x|

    Our regular-grid looks like it did before:

    pixel_scale = 1.0"

    <--- -ve  x  +ve -->

    |x|x|x|x|x|x|x|x|x|x|  ^
    |x|x|x|x|x|x|x|x|x|x|  |
    |x|x|x|x|x|x|x|x|x|x|  |
    |x|x|x|x|x|x|x|x|x|x| +ve  grid_coords[0] = [-1.5,  0.5]
    |x|x|x|0|1|x|x|x|x|x|  y   grid_coords[1] = [-0.5,  0.5]
    |x|x|x|x|x|x|x|x|x|x| -ve
    |x|x|x|x|x|x|x|x|x|x|  |
    |x|x|x|x|x|x|x|x|x|x|  |
    |x|x|x|x|x|x|x|x|x|x| \/
    |x|x|x|x|x|x|x|x|x|x|

    However, we now go to each masked_image-pixel and derive a sub-pixel grid for it. For example, for pixel 0,
    if *sub_grid_size=2*, we use a 2x2 sub-grid:

    Pixel 0 - (2x2):

           grid_coords[0,0] = [-1.66, 0.66]
    |0|1|  grid_coords[0,1] = [-1.33, 0.66]
    |2|3|  grid_coords[0,2] = [-1.66, 0.33]
           grid_coords[0,3] = [-1.33, 0.33]

    Now, we'd normally sub-grid all data_to_image using the same *sub_grid_size*, but for this illustration lets
    pretend we used a sub_grid_size of 3x3 for pixel 1:

             grid_coords[0,0] = [-0.75, 0.75]
             grid_coords[0,1] = [-0.5,  0.75]
             grid_coords[0,2] = [-0.25, 0.75]
    |0|1|2|  grid_coords[0,3] = [-0.75,  0.5]
    |3|4|5|  grid_coords[0,4] = [-0.5,   0.5]
    |6|7|8|  grid_coords[0,5] = [-0.25,  0.5]
             grid_coords[0,6] = [-0.75, 0.25]
             grid_coords[0,7] = [-0.5,  0.25]
             grid_coords[0,8] = [-0.25, 0.25]

    """

    def __init__(self, array, mask, sub_grid_size=1):
        # noinspection PyArgumentList
        super(SubGrid, self).__init__()
        self.sub_grid_size = sub_grid_size
        self.sub_grid_length = int(sub_grid_size ** 2.0)
        self.sub_grid_fraction = 1.0 / self.sub_grid_length
        self.mask = mask

    @classmethod
    def grid_from_mask_and_sub_grid_size(cls, mask, sub_grid_size=1):
        sub_grid_masked = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask, mask.pixel_scale,
                                                                                               sub_grid_size)
        return SubGrid(sub_grid_masked, mask, sub_grid_size)

    def __array_finalize__(self, obj):
        if isinstance(obj, SubGrid):
            self.sub_grid_size = obj.sub_grid_size
            self.sub_grid_length = obj.sub_grid_length
            self.sub_grid_fraction = obj.sub_grid_fraction
            self.mask = obj.mask

    def sub_data_to_image(self, data):
        return np.multiply(self.sub_grid_fraction, data.reshape(-1, self.sub_grid_length).sum(axis=1))

    @property
    @imaging_util.Memoizer()
    def sub_to_image(self):
        """ Compute the pairing of every sub-pixel to its original masked_image pixel from a mask. """
        return imaging_util.sub_to_image_from_mask(self.mask, self.sub_grid_size).astype('int')


class GridMapper(object):
    pass


class ImageGridMapper(ImageGrid, GridMapper):

    def __new__(cls, arr, original_shape, padded_shape, *args, **kwargs):
        arr = arr.view(cls)
        arr.original_shape = original_shape
        arr.padded_shape = padded_shape
        return arr

    def trim_padded_array_to_original_shape(self, padded_array_2d):
        x_trim = int((self.padded_shape[0] - self.original_shape[0]) / 2)
        y_trim = int((self.padded_shape[1] - self.original_shape[1]) / 2)
        return padded_array_2d[x_trim:self.padded_shape[0] - x_trim, y_trim:self.padded_shape[1] - y_trim]

    def convolve_unmasked_array_with_psf_and_trim(self, array_1d, psf):
        padded_array_2d = imaging_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(array_1d,
                                                                                                 self.padded_shape)
        blurred_padded_array_2d = psf.convolve(padded_array_2d)
        blurred_array_2d = self.trim_padded_array_to_original_shape(blurred_padded_array_2d)
        return imaging_util.map_2d_array_to_masked_1d_array_from_array_2d_and_mask(array_2d=blurred_array_2d,
                                                                    mask=np.full(self.original_shape, False))

    def map_unmasked_1d_array_to_2d_array(self, array_1d):
        """Use mapper to map an input data-set from a *GridData* to its original 2D masked_image.
        Parameters
        -----------
        array_1d : ndarray
            The grid-data which is mapped to its 2D masked_image.
        """
        return imaging_util.map_unmasked_1d_array_to_2d_array_from_array_1d_and_shape(array_1d, self.original_shape)

    @classmethod
    def mapper_from_shapes_and_pixel_scale(self, shape, psf_shape, pixel_scale):
        padded_shape = (shape[0] + psf_shape[0] - 1, shape[1] + psf_shape[1] - 1)
        padded_image_grid = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full(padded_shape, False),
                                                                        pixel_scale=pixel_scale)
        return ImageGridMapper(arr=padded_image_grid, original_shape=shape, padded_shape=padded_shape)


class SubGridMapper(SubGrid, GridMapper):

    def __init__(self, arr, mask, original_shape, padded_shape, sub_grid_size=1):

        super(SubGridMapper, self).__init__(arr, mask, sub_grid_size)
        self.original_shape = original_shape
        self.padded_shape = padded_shape

    @classmethod
    def mapper_from_mask_sub_grid_size_and_psf_shape(cls, mask, sub_grid_size, psf_shape):
        padded_shape = (mask.shape[0] + psf_shape[0] - 1, mask.shape[1] + psf_shape[1] - 1)
        padded_sub_grid = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=np.full(padded_shape, False),
                                                        pixel_scale=mask.pixel_scale, sub_grid_size=sub_grid_size)
        return SubGridMapper(arr=padded_sub_grid, mask=mask, original_shape=mask.shape, padded_shape=padded_shape,
                             sub_grid_size=sub_grid_size)

    def __array_finalize__(self, obj):
        if isinstance(obj, SubGridMapper):
            self.sub_grid_size = obj.sub_grid_size
            self.sub_grid_length = obj.sub_grid_length
            self.sub_grid_fraction = obj.sub_grid_fraction
            self.mask = obj.mask
            self.original_shape = obj.original_shape
            self.padded_shape = obj.padded_shape


class LensingGrids(object):

    def __init__(self, image, sub, blurring):
        """
        A collection of grids which contain the coordinates of an masked_image. This includes the masked_image's regular grid,
        sub-grid, blurring region, etc. Coordinate grids are passed through the ray-tracing module to set up the masked_image,
        lens and source planes.

        Parameters
        -----------
        image : GridCoordsImage
            A grid of coordinates for the regular masked_image grid.
        sub : GridCoordsImageSub
            A grid of coordinates for the sub-gridded masked_image grid.
        blurring : GridCoordsBlurring
            A grid of coordinates for the blurring regions.
        """
        self.image = image
        self.sub = sub
        self.blurring = blurring

    @classmethod
    def from_mask_sub_grid_size_and_blurring_shape(cls, mask, sub_grid_size, blurring_shape):
        image_grid = ImageGrid(mask.masked_image_grid)
        sub_grid = SubGrid.grid_from_mask_and_sub_grid_size(mask, sub_grid_size)
        blurring_grid = ImageGrid.blurring_grid_from_mask_and_psf_shape(mask, blurring_shape)
        return LensingGrids(image_grid, sub_grid, blurring_grid)

    @classmethod
    def grid_mappers_from_mask_sub_grid_size_and_psf_shape(cls, mask, sub_grid_size, psf_shape):
        image_grid_mapper = ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=mask.shape, psf_shape=psf_shape,
                                                                               pixel_scale=mask.pixel_scale)
        sub_grid_mapper = SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=mask,
                                                                                     sub_grid_size=sub_grid_size,
                                                                                     psf_shape=psf_shape)
        # TODO : The blurring grid is not used when the grid mapper is called, the 0.0 0.0 stops errors inr ayT_racing
        # TODO : implement a more explicit solution
        return LensingGrids(image_grid_mapper, sub_grid_mapper, np.array([[0.0, 0.0]]))

    @classmethod
    def for_simulation(cls, shape, pixel_scale, psf_shape, sub_grid_size=1):
        from autolens.imaging import mask
        return cls.grid_mappers_from_mask_sub_grid_size_and_psf_shape(mask=mask.Mask(array=np.full(shape, False),
                                                                                pixel_scale=pixel_scale),
                                                                      sub_grid_size=sub_grid_size, psf_shape=psf_shape)

    def apply_function(self, func):
        if self.blurring is not None:
            return LensingGrids(func(self.image), func(self.sub), func(self.blurring))
        else:
            return LensingGrids(func(self.image), func(self.sub), None)

    def map_function(self, func, *arg_lists):
        return LensingGrids(*[func(*args) for args in zip(self, *arg_lists)])

    @property
    def sub_pixels(self):
        return self.sub.shape[0]

    def __getitem__(self, item):
        return [self.image, self.sub, self.blurring][item]


class ImageGridBorder(np.ndarray):

    @property
    def no_pixels(self):
        return self.shape[0]

    def __new__(cls, arr, polynomial_degree=3, centre=(0.0, 0.0), *args, **kwargs):
        border = arr.view(cls)
        border.polynomial_degree = polynomial_degree
        border.centre = centre
        return border

    @classmethod
    def from_mask(cls, mask, polynomial_degree=3, centre=(0.0, 0.0)):
        return cls(mask.border_pixel_indices, polynomial_degree, centre)

    def __reduce__(self):
        # Get the parent's __reduce__ tuple
        pickled_state = super(ImageGridBorder, self).__reduce__()
        # Create our own tuple to pass to __setstate__
        class_dict = {}
        for key, value in self.__dict__.items():
            class_dict[key] = value
        new_state = pickled_state[2] + (class_dict,)
        # Return a tuple that replaces the parent's __setstate__ tuple with our own
        return pickled_state[0], pickled_state[1], new_state

    def __setstate__(self, state):

        for key, value in state[-1].items():
            setattr(self, key, value)
        super(ImageGridBorder, self).__setstate__(state[0:-1])

    def grid_to_radii(self, grid):
        """
        Convert coordinates to a circular radius.

        If the coordinates have not been transformed to the profile's geometry, this is performed automatically.

        Parameters
        ----------
        grid

        Returns
        -------
        The radius at those coordinates
        """

        return np.sqrt(np.add(np.square(np.subtract(grid[:, 0], self.centre[0])),
                              np.square(np.subtract(grid[:, 1], self.centre[1]))))

    def grid_to_thetas(self, grid):
        """
        Compute the angle in degrees between the image_grid and plane positive x-axis, defined counter-clockwise.

        Parameters
        ----------
        grid : Union((float, float), ndarray)
            The x and y image_grid of the plane.

        Returns
        ----------
        The angle between the image_grid and the x-axis.
        """
        shifted_grid = np.subtract(grid, self.centre)
        theta_from_x = np.degrees(np.arctan2(shifted_grid[:, 1], shifted_grid[:, 0]))
        theta_from_x[theta_from_x < 0.0] += 360.
        return theta_from_x

    def polynomial_fit_to_border(self, grid):

        border_grid = grid[self]

        return np.polyfit(self.grid_to_thetas(border_grid), self.grid_to_radii(border_grid), self.polynomial_degree)

    def move_factors_from_grid(self, grid):
        """Get the move factor of a coordinate.
         A move-factor defines how far a coordinate outside the source-plane setup_border_pixels must be moved in order
         to lie on it. PlaneCoordinates already within the setup_border_pixels return a move-factor of 1.0, signifying
         they are already within the setup_border_pixels.

        Parameters
        ----------
        grid : ndarray
            The x and y image_grid of the pixel to have its move-factor computed.
        """
        grid_thetas = self.grid_to_thetas(grid)
        grid_radii = self.grid_to_radii(grid)
        poly = self.polynomial_fit_to_border(grid)

        with np.errstate(divide='ignore'):
            move_factors = np.divide(np.polyval(poly, grid_thetas), grid_radii)
        move_factors[move_factors > 1.0] = 1.0

        return move_factors

    def relocated_grid_from_grid(self, grid):
        move_factors = self.move_factors_from_grid(grid)
        return np.multiply(grid, move_factors[:, None])


class SubGridBorder(ImageGridBorder):

    @classmethod
    def from_mask(cls, mask, sub_grid_size, polynomial_degree=3, centre=(0.0, 0.0)):
        return cls(mask.border_sub_pixel_indices(sub_grid_size), polynomial_degree, centre)


class BorderCollection(object):

    def __init__(self, image, sub):
        self.image = image
        self.sub = sub

    @classmethod
    def from_mask_and_sub_grid_size(cls, mask, sub_grid_size, polynomial_degree=3, centre=(0.0, 0.0)):
        image_border = ImageGridBorder.from_mask(mask, polynomial_degree, centre)
        sub_border = SubGridBorder.from_mask(mask, sub_grid_size, polynomial_degree, centre)
        return BorderCollection(image_border, sub_border)

    def relocated_grids_from_grids(self, grids):
        return LensingGrids(image=self.image.relocated_grid_from_grid(grids.image),
                            sub=self.sub.relocated_grid_from_grid(grids.sub),
                            blurring=None)