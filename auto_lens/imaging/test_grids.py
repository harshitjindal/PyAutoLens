from __future__ import division, print_function
import pytest
import numpy as np
from auto_lens.imaging import grids
from auto_lens.imaging import imaging
from auto_lens import galaxy
from auto_lens.profiles import light_profiles, mass_profiles
import os

test_data_dir = "{}/../../data/test_data/".format(os.path.dirname(os.path.realpath(__file__)))

@pytest.fixture(scope='function')
def galaxy_no_profiles():
    return galaxy.Galaxy()

@pytest.fixture(scope='function')
def galaxy_mass_sis():
    sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)
    return galaxy.Galaxy(mass_profiles=[sis])

@pytest.fixture(scope='function')
def galaxy_light_sersic():
    sersic = light_profiles.EllipticalSersic(axis_ratio=0.5, phi=0.0, intensity=1.0, effective_radius=0.6,
                                             sersic_index=4.0)
    return galaxy.Galaxy(light_profiles=[sersic])

class TestGridCoordsCollection(object):
    
    
    class TestConstructor(object):
        
        def test__simple_grid_input__all_grids_used__sets_up_attributes(self):

            image_grid = grids.GridCoordsImage(np.array([[1.0, 1.0],
                                                         [2.0, 2.0],
                                                         [3.0, 3.0]]))

            sub_grid = grids.GridCoordsImageSub(np.array([[[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]],
                                                          [[2.0, 2.0], [2.0, 2.0], [2.0, 2.0], [2.0, 2.0]]]),
                                                grid_sub_size=2)

            blurring_grid = grids.GridCoordsBlurring(np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0],
                                                               [1.0, 1.0]]))
            
            grid_collection = grids.GridCoordsCollection(image_grid, sub_grid, blurring_grid)
            
            assert (grid_collection.image.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_collection.image.grid_coords[1] == np.array([2.0, 2.0])).all()
            assert (grid_collection.image.grid_coords[2] == np.array([3.0, 3.0])).all()

            assert (grid_collection.sub.grid_coords[0,0] == np.array([1.0, 1.0])).all()
            assert (grid_collection.sub.grid_coords[0,1] == np.array([1.0, 1.0])).all()
            assert (grid_collection.sub.grid_coords[0,2] == np.array([1.0, 1.0])).all()
            assert (grid_collection.sub.grid_coords[0,3] == np.array([1.0, 1.0])).all()
            assert (grid_collection.sub.grid_coords[1,0] == np.array([2.0, 2.0])).all()
            assert (grid_collection.sub.grid_coords[1,1] == np.array([2.0, 2.0])).all()
            assert (grid_collection.sub.grid_coords[1,2] == np.array([2.0, 2.0])).all()
            assert (grid_collection.sub.grid_coords[1,3] == np.array([2.0, 2.0])).all()

            assert (grid_collection.blurring.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_collection.blurring.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_collection.blurring.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_collection.blurring.grid_coords[0] == np.array([1.0, 1.0])).all()

        def test__simple_grid_input__sub_and_blurring_are_none__sets_up_attributes(self):

            image_grid = grids.GridCoordsImage(np.array([[1.0, 1.0],
                                                         [2.0, 2.0],
                                                         [3.0, 3.0]]))

            grid_collection = grids.GridCoordsCollection(image_grid)

            assert (grid_collection.image.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_collection.image.grid_coords[1] == np.array([2.0, 2.0])).all()
            assert (grid_collection.image.grid_coords[2] == np.array([3.0, 3.0])).all()

            assert grid_collection.sub == None

            assert grid_collection.blurring == None


    class TestFromMask(object):

        def test__all_grids_from_masks__correct_grids_setup(self):

            mask = np.array([[True, True, True],
                             [True, False, True],
                             [True, True, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            image_grid = mask.compute_grid_coords_image()
            sub_grid = mask.compute_grid_coords_image_sub(sub_grid_size=2)
            blurring_grid = mask.compute_grid_coords_blurring(psf_size=(3, 3))

            grid_collection = grids.GridCoordsCollection.from_mask(mask, sub_grid_size=2, blurring_size=(3, 3))

            assert (grid_collection.image.grid_coords == image_grid).all()
            assert (grid_collection.sub.grid_coords == sub_grid).all()
            assert (grid_collection.blurring.grid_coords == blurring_grid).all()

        def test__sub_and_blurring_grids_are_none__correct_grids_setup(self):

            mask = np.array([[True, True, True],
                             [True, False, True],
                             [True, True, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            image_grid = mask.compute_grid_coords_image()

            grid_collection = grids.GridCoordsCollection.from_mask(mask)

            assert (grid_collection.image.grid_coords == image_grid).all()
            assert grid_collection.sub == None
            assert grid_collection.blurring == None


    class TestDeflectionAnglesViaGalaxy(object):

        def test__image_coordinates_only(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])

            image_grid = grids.GridCoordsImage(image_grid)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid)
            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis])

            assert deflections.image.grid_coords == pytest.approx(np.array([[0.707, 0.707]]), 1e-3)
            assert deflections.sub == None
            assert deflections.blurring == None

        def test__image_and_sub_grid(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])
            sub_grid = np.array([[[1.0, 1.0], [1.0, 0.0]]])

            image_grid = grids.GridCoordsImage(image_grid)
            sub_grid = grids.GridCoordsImageSub(sub_grid, grid_sub_size=2)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, sub=sub_grid)
            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis])

            assert deflections.image.grid_coords == pytest.approx(np.array([[0.707, 0.707]]), 1e-3)
            assert deflections.sub.grid_coords[0,0] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
            assert deflections.sub.grid_coords[0,1] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert deflections.sub.sub_grid_size == 2
            assert deflections.blurring == None

        def test__image_and_blurring_grid(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])
            blurring_grid = np.array([[1.0, 0.0]])

            image_grid = grids.GridCoordsImage(image_grid)
            blurring_grid = grids.GridCoordsBlurring(blurring_grid)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, blurring=blurring_grid)
            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis])

            assert deflections.image.grid_coords == pytest.approx(np.array([[0.707, 0.707]]), 1e-3)
            assert deflections.sub == None
            assert deflections.blurring.grid_coords[0] == pytest.approx(np.array([1.0, 0.0]), 1e-3)

        def test_all_coordinates(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])
            sub_grid = np.array([[[1.0, 1.0], [1.0, 0.0]]])
            blurring_grid = np.array([[1.0, 0.0]])

            image_grid = grids.GridCoordsImage(image_grid)
            sub_grid = grids.GridCoordsImageSub(sub_grid, grid_sub_size=2)
            blurring_grid = grids.GridCoordsBlurring(blurring_grid)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, sub=sub_grid, blurring=blurring_grid)

            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis])

            assert deflections.image.grid_coords[0] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
            assert deflections.sub.grid_coords[0,0] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
            assert deflections.sub.grid_coords[0,1] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert deflections.sub.sub_grid_size == 2
            assert deflections.blurring.grid_coords[0] == pytest.approx(np.array([1.0, 0.0]), 1e-3)

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])
            sub_grid = np.array([[[1.0, 1.0], [1.0, 0.0]]])
            blurring_grid = np.array([[1.0, 0.0]])

            image_grid = grids.GridCoordsImage(image_grid)
            sub_grid = grids.GridCoordsImageSub(sub_grid, grid_sub_size=2)
            blurring_grid = grids.GridCoordsBlurring(blurring_grid)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, sub=sub_grid, blurring=blurring_grid)

            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            assert deflections.image.grid_coords == pytest.approx(np.array([[3.0*0.707, 3.0*0.707]]), 1e-3)
            assert deflections.sub.grid_coords[0,0] == pytest.approx(np.array([3.0*0.707, 3.0*0.707]), 1e-3)
            assert deflections.sub.grid_coords[0,1] == pytest.approx(np.array([3.0, 0.0]), 1e-3)
            assert deflections.sub.sub_grid_size == 2
            assert deflections.blurring.grid_coords[0] == pytest.approx(np.array([3.0, 0.0]), 1e-3)

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            image_grid = np.array([[1.0, 1.0]])
            sub_grid = np.array([[[1.0, 1.0], [1.0, 0.0]]])
            blurring_grid = np.array([[1.0, 0.0]])

            image_grid = grids.GridCoordsImage(image_grid)
            sub_grid = grids.GridCoordsImageSub(sub_grid, grid_sub_size=4)
            blurring_grid = grids.GridCoordsBlurring(blurring_grid)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3*[mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, sub=sub_grid, blurring=blurring_grid)

            deflections = ray_trace_grid.setup_all_deflections_grids([lens_sis_x3])

            assert deflections.image.grid_coords == pytest.approx(np.array([[3.0*0.707, 3.0*0.707]]), 1e-3)
            assert deflections.sub.grid_coords[0,0] == pytest.approx(np.array([3.0*0.707, 3.0*0.707]), 1e-3)
            assert deflections.sub.grid_coords[0,1] == pytest.approx(np.array([3.0, 0.0]), 1e-3)
            assert deflections.sub.sub_grid_size == 4
            assert deflections.blurring.grid_coords[0] == pytest.approx(np.array([3.0, 0.0]), 1e-3)

        def test__complex_mass_model(self):

            image_grid = np.array([[1.0, 1.0]])
            sub_grid = np.array([[[1.0, 1.0], [1.0, 0.0]]])
            blurring_grid = np.array([[1.0, 0.0]])

            image_grid = grids.GridCoordsImage(image_grid)
            sub_grid = grids.GridCoordsImageSub(sub_grid, grid_sub_size=4)
            blurring_grid = grids.GridCoordsBlurring(blurring_grid)

            power_law = mass_profiles.EllipticalPowerLaw(centre=(1.0, 4.0), axis_ratio=0.7, phi=30.0,
                                                                    einstein_radius=1.0, slope=2.2)

            nfw = mass_profiles.SphericalNFW(kappa_s=0.1, scale_radius=5.0)

            lens_galaxy = galaxy.Galaxy(redshift=0.1, mass_profiles=[power_law, nfw])

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, sub=sub_grid, blurring=blurring_grid)

            deflections = ray_trace_grid.setup_all_deflections_grids([lens_galaxy])


            defls = power_law.deflections_at_coordinates(image_grid.grid_coords[0]) + \
                    nfw.deflections_at_coordinates(image_grid.grid_coords[0])

            sub_defls_0 = power_law.deflections_at_coordinates(sub_grid.grid_coords[0, 0]) + \
                          nfw.deflections_at_coordinates(sub_grid.grid_coords[0, 0])

            sub_defls_1 = power_law.deflections_at_coordinates(sub_grid.grid_coords[0, 1]) + \
                          nfw.deflections_at_coordinates(sub_grid.grid_coords[0, 1])

            blurring_defls = power_law.deflections_at_coordinates(blurring_grid.grid_coords[0]) + \
                             nfw.deflections_at_coordinates(blurring_grid.grid_coords[0])

            assert deflections.image.grid_coords[0] == pytest.approx(defls, 1e-3)
            assert deflections.sub.grid_coords[0,0] == pytest.approx(sub_defls_0, 1e-3)
            assert deflections.sub.grid_coords[0,1] == pytest.approx(sub_defls_1, 1e-3)
            assert deflections.sub.sub_grid_size == 4
            assert deflections.blurring.grid_coords[0] == pytest.approx(blurring_defls, 1e-3)


    class TestSetupTracedGrids(object):

        def test__image_coordinates_only(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])

            image_grid = grids.GridCoordsImage(image_grid)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid)

            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis])

            traced = ray_trace_grid.setup_all_traced_grids(deflections)

            assert traced.image.grid_coords == pytest.approx(np.array([[1.0 - 0.707, 1.0 - 0.707]]), 1e-3)
            assert traced.sub == None
            assert traced.blurring == None

        def test_all_coordinates(self, galaxy_mass_sis):

            image_grid = np.array([[1.0, 1.0]])
            sub_grid = np.array([[[1.0, 1.0], [1.0, 0.0]]])
            blurring_grid = np.array([[1.0, 0.0]])

            image_grid = grids.GridCoordsImage(image_grid)
            sub_grid = grids.GridCoordsImageSub(sub_grid, grid_sub_size=2)
            blurring_grid = grids.GridCoordsBlurring(blurring_grid)

            ray_trace_grid = grids.GridCoordsCollection(image=image_grid, sub=sub_grid, blurring=blurring_grid)

            deflections = ray_trace_grid.setup_all_deflections_grids([galaxy_mass_sis])

            traced = ray_trace_grid.setup_all_traced_grids(deflections)

            assert traced.image.grid_coords[0] == pytest.approx(np.array([1.0 - 0.707, 1.0 - 0.707]), 1e-3)
            assert traced.sub.grid_coords[0,0] == pytest.approx(np.array([1.0 - 0.707, 1.0 - 0.707]), 1e-3)
            assert traced.sub.grid_coords[0,1] == pytest.approx(np.array([1.0 - 1.0, 0.0 - 0.0]), 1e-3)
            assert traced.sub.sub_grid_size == 2
            assert traced.blurring.grid_coords[0] == pytest.approx(np.array([1.0 - 1.0, 0.0 - 0.0]), 1e-3)


class TestGridCoordsRegular(object):


    class TestConstructor:

        def test__simple_grid_input__sets_up_grid_correctly_in_attributes(self):

            regular_grid_coords = np.array([[1.0, 1.0],
                                     [2.0, 2.0],
                                     [3.0, 3.0]])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            assert (grid_regular.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_regular.grid_coords[1] == np.array([2.0, 2.0])).all()
            assert (grid_regular.grid_coords[2] == np.array([3.0, 3.0])).all()


    class TestIntensityViaGrid:

        def test__no_galaxies__intensities_returned_as_0s(self, galaxy_no_profiles):

            regular_grid_coords = np.array([[1.0, 1.0],
                                            [2.0, 2.0],
                                            [3.0, 3.0]])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            intensities = grid_regular.intensities_via_grid(galaxies=[galaxy_no_profiles])

            assert (intensities[0] == np.array([0.0, 0.0])).all()
            assert (intensities[1] == np.array([0.0, 0.0])).all()
            assert (intensities[2] == np.array([0.0, 0.0])).all()

        def test__galaxy_sersic_light__intensities_returned_as_correct_values(self, galaxy_light_sersic):

            regular_grid_coords = np.array([[1.0, 1.0],
                                            [1.0, 0.0],
                                            [-1.0, 0.0]])

            intensity_0 = galaxy_light_sersic.intensity_at_coordinates(regular_grid_coords[0])
            intensity_1 = galaxy_light_sersic.intensity_at_coordinates(regular_grid_coords[1])
            intensity_2 = galaxy_light_sersic.intensity_at_coordinates(regular_grid_coords[2])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            intensities = grid_regular.intensities_via_grid(galaxies=[galaxy_light_sersic])

            assert intensities[0] == intensity_0
            assert intensities[1] == intensity_1
            assert intensities[2] == intensity_2

        def test__galaxy_sis_mass_x3__intensities_tripled_from_above(self, galaxy_light_sersic):

            regular_grid_coords = np.array([[1.0, 1.0],
                                            [1.0, 0.0],
                                            [-1.0, 0.0]])

            intensity_0 = galaxy_light_sersic.intensity_at_coordinates(regular_grid_coords[0])
            intensity_1 = galaxy_light_sersic.intensity_at_coordinates(regular_grid_coords[1])
            intensity_2 = galaxy_light_sersic.intensity_at_coordinates(regular_grid_coords[2])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            intensities = grid_regular.intensities_via_grid(galaxies=[galaxy_light_sersic, galaxy_light_sersic, galaxy_light_sersic])

            assert intensities[0] == 3.0*intensity_0
            assert intensities[1] == 3.0*intensity_1
            assert intensities[2] == 3.0*intensity_2


    class TestDeflectionsOnGrid:

        def test__no_galaxies__deflections_returned_as_0s(self, galaxy_no_profiles):

            regular_grid_coords = np.array([[1.0, 1.0],
                                     [2.0, 2.0],
                                     [3.0, 3.0]])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            deflections = grid_regular.deflections_on_grid(galaxies=[galaxy_no_profiles])

            assert (deflections[0] == np.array([0.0, 0.0])).all()
            assert (deflections[1] == np.array([0.0, 0.0])).all()
            assert (deflections[2] == np.array([0.0, 0.0])).all()

        def test__galaxy_sis_mass__deflections_returned_as_correct_values(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0],
                                            [1.0, 0.0],
                                            [-1.0, 0.0]])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            deflections = grid_regular.deflections_on_grid(galaxies=[galaxy_mass_sis])

            assert deflections[0] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert deflections[1] == pytest.approx(np.array([1.0, 0.0]), 1e-2)
            assert deflections[2] == pytest.approx(np.array([-1.0, 0.0]), 1e-2)

        def test__galaxy_sis_mass_x3__deflections_tripled_from_above(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0],
                                            [1.0, 0.0],
                                            [-1.0, 0.0]])

            grid_regular = grids.GridCoordsRegular(regular_grid_coords)

            deflections = grid_regular.deflections_on_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            assert deflections[0] == pytest.approx(3.0*np.array([0.707, 0.707]), 1e-2)
            assert deflections[1] == pytest.approx(3.0*np.array([1.0, 0.0]), 1e-2)
            assert deflections[2] == pytest.approx(3.0*np.array([-1.0, 0.0]), 1e-2)


class TestGridCoordsSub(object):


    class TestConstructor:

        def test__simple_grid_input__sets_up_grid_correctly_in_attributes(self):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]],
                                        [[2.0, 2.0], [2.0, 2.0], [2.0, 2.0], [2.0, 2.0]]])

            grid_sub = grids.GridCoordsSub(grid_coords=sub_grid_coords, grid_sub_size=2)

            assert grid_sub.sub_grid_size == 2
            assert grid_sub.sub_grid_size_squared == 4

            assert grid_sub.grid_coords[0, 0] == pytest.approx(np.array([1.0, 1.0]), 1e-2)
            assert grid_sub.grid_coords[0, 1] == pytest.approx(np.array([1.0, 1.0]), 1e-2)
            assert grid_sub.grid_coords[0, 2] == pytest.approx(np.array([1.0, 1.0]), 1e-2)
            assert grid_sub.grid_coords[0, 3] == pytest.approx(np.array([1.0, 1.0]), 1e-2)
            assert grid_sub.grid_coords[1, 0] == pytest.approx(np.array([2.0, 2.0]), 1e-2)
            assert grid_sub.grid_coords[1, 1] == pytest.approx(np.array([2.0, 2.0]), 1e-2)
            assert grid_sub.grid_coords[1, 2] == pytest.approx(np.array([2.0, 2.0]), 1e-2)
            assert grid_sub.grid_coords[1, 3] == pytest.approx(np.array([2.0, 2.0]), 1e-2)


    class TestIntensitiesViaGrid:

        def test__no_galaxies__intensities_returned_as_0s(self, galaxy_no_profiles):

            sub_grid_coords = np.array([[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [0.0, 0.0]],
                                        [[1.0, 1.0], [-1.0, 0.0], [0.0, 0.0], [0.0, 0.0]]])

            grid_sub = grids.GridCoordsSub(sub_grid_coords, grid_sub_size=2)

            intensities = grid_sub.intensities_via_grid(galaxies=[galaxy_no_profiles])

            assert intensities[0] == 0.0
            assert intensities[1] == 0.0

        def test__galaxy_light_sersic__deflections_returned_as_correct_values(self, galaxy_light_sersic):

            sub_grid_coords = np.array([[[1.0, 1.0], [0.0, 1.0], [0.0, -1.0], [0.0, -1.0]],
                                        [[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [0.0, -1.0]]])

            intensity_00 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,0])
            intensity_01 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,1])
            intensity_02 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,2])
            intensity_03 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,3])
            intensity_10 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,0])
            intensity_11 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,1])
            intensity_12 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,2])
            intensity_13 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,3])

            intensity_0 = (intensity_00 + intensity_01 + intensity_02 + intensity_03) / 4.0
            intensity_1 = (intensity_10 + intensity_11 + intensity_12 + intensity_13) / 4.0

            grid_sub = grids.GridCoordsSub(sub_grid_coords, grid_sub_size=2)

            intensities = grid_sub.intensities_via_grid(galaxies=[galaxy_light_sersic])

            assert intensities[0] == intensity_0
            assert intensities[1] == intensity_1

        def test__galaxy_light_sersic_x3__deflections_tripled_from_above(self, galaxy_light_sersic):

            sub_grid_coords = np.array([[[1.0, 1.0], [0.0, 1.0], [0.0, -1.0], [0.0, -1.0]],
                                        [[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [0.0, -1.0]]])

            intensity_00 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,0])
            intensity_01 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,1])
            intensity_02 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,2])
            intensity_03 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[0,3])
            intensity_10 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,0])
            intensity_11 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,1])
            intensity_12 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,2])
            intensity_13 = galaxy_light_sersic.intensity_at_coordinates(sub_grid_coords[1,3])

            intensity_0 = (intensity_00 + intensity_01 + intensity_02 + intensity_03) / 4.0
            intensity_1 = (intensity_10 + intensity_11 + intensity_12 + intensity_13) / 4.0

            grid_sub = grids.GridCoordsSub(sub_grid_coords, grid_sub_size=2)

            intensities = grid_sub.intensities_via_grid(galaxies=[galaxy_light_sersic, galaxy_light_sersic,
                                                                  galaxy_light_sersic])

            assert intensities[0] == pytest.approx(3.0*intensity_0, 1e-3)
            assert intensities[1] == pytest.approx(3.0*intensity_1, 1e-3)


    class TestDeflectionsOnGrid:

        def test__no_galaxies__deflections_returned_as_0s(self, galaxy_no_profiles):

            sub_grid_coords = np.array([[[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [0.0, 0.0]],
                                        [[1.0, 1.0], [-1.0, 0.0], [0.0, 0.0], [0.0, 0.0]]])

            grid_sub = grids.GridCoordsSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_sub.deflections_on_grid(galaxies=[galaxy_no_profiles])

            assert deflections[0,0] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[0,1] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[0,2] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[0,3] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[1,0] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[1,1] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[1,2] == pytest.approx(np.array([0.0, 0.0]), 1e-2)
            assert deflections[1,3] == pytest.approx(np.array([0.0, 0.0]), 1e-2)

        def test__galaxy_sis_mass__deflections_returned_as_correct_values(self, galaxy_mass_sis):

            sub_grid_coords = np.array([[[1.0, 1.0], [0.0, 1.0], [0.0, -1.0], [0.0, -1.0]],
                                        [[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [0.0, -1.0]]])

            grid_sub = grids.GridCoordsSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_sub.deflections_on_grid(galaxies=[galaxy_mass_sis])

            assert deflections[0,0] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert deflections[0,1] == pytest.approx(np.array([0.0, 1.0]), 1e-2)
            assert deflections[0,2] == pytest.approx(np.array([0.0, -1.0]), 1e-2)
            assert deflections[0,3] == pytest.approx(np.array([0.0, -1.0]), 1e-2)
            assert deflections[1,0] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert deflections[1,1] == pytest.approx(np.array([-1.0, 0.0]), 1e-2)
            assert deflections[1,2] == pytest.approx(np.array([0.0, -1.0]), 1e-2)
            assert deflections[1,3] == pytest.approx(np.array([0.0, -1.0]), 1e-2)

        def test__galaxy_sis_mass_x3__deflections_tripled_from_above(self, galaxy_mass_sis):

            sub_grid_coords = np.array([[[1.0, 1.0], [0.0, 1.0], [0.0, -1.0], [0.0, -1.0]],
                                        [[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [0.0, -1.0]]])

            grid_sub = grids.GridCoordsSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_sub.deflections_on_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            assert deflections[0,0] == pytest.approx(3.0*np.array([0.707, 0.707]), 1e-2)
            assert deflections[0,1] == pytest.approx(3.0*np.array([0.0, 1.0]), 1e-2)
            assert deflections[0,2] == pytest.approx(3.0*np.array([0.0, -1.0]), 1e-2)
            assert deflections[0,3] == pytest.approx(3.0*np.array([0.0, -1.0]), 1e-2)
            assert deflections[1,0] == pytest.approx(3.0*np.array([0.707, 0.707]), 1e-2)
            assert deflections[1,1] == pytest.approx(3.0*np.array([-1.0, 0.0]), 1e-2)
            assert deflections[1,2] == pytest.approx(3.0*np.array([0.0, -1.0]), 1e-2)
            assert deflections[1,3] == pytest.approx(3.0*np.array([0.0, -1.0]), 1e-2)


class TestGridCoordsImage(object):


    class TestConstructor:

        def test__simple_grid_input__sets_up_grid_correctly_in_attributes(self):

            regular_grid_coords = np.array([[1.0, 1.0],
                             [2.0, 2.0],
                             [3.0, 3.0]])

            grid_image = grids.GridCoordsImage(regular_grid_coords)

            assert (grid_image.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_image.grid_coords[1] == np.array([2.0, 2.0])).all()
            assert (grid_image.grid_coords[2] == np.array([3.0, 3.0])).all()


    class TestFromMask:
        
        def test__calcalate_from_simple_mask__check_coordinates_are_correct(self):

            mask = np.array([[True, False, True],
                             [False, False, False],
                             [True, False, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            regular_grid_coords = mask.compute_grid_coords_image()

            grid_image = grids.GridCoordsImage.from_mask(mask)

            assert (grid_image.grid_coords[0] == np.array([0.0, 3.0])).all()
            assert (grid_image.grid_coords[1] == np.array([-3.0, 0.0])).all()
            assert (grid_image.grid_coords[2] == np.array([0.0, 0.0])).all()
            assert (grid_image.grid_coords[3] == np.array([3.0, 0.0])).all()
            assert (grid_image.grid_coords[4] == np.array([0.0, -3.0])).all()

        def test__manually_compare_to_setting_up_directly_via_mask(self):

            mask = np.array([[True, True, False, False],
                             [True, False, True, True],
                             [True, True, True, False]])

            mask = imaging.Mask(mask=mask, pixel_scale=6.0)

            regular_grid_coords = mask.compute_grid_coords_image()

            grid_image = grids.GridCoordsImage(regular_grid_coords)

            grid_from_mask = grids.GridCoordsImage.from_mask(mask)

            assert (grid_image.grid_coords == grid_from_mask.grid_coords).all()


    class TestSetupDeflectionsGrid:

        def test__simple_sis_model__deflection_angles(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0], [-1.0, -1.0]])

            grid_image = grids.GridCoordsImage(regular_grid_coords)

            grid_deflections = grid_image.setup_deflections_grid(galaxies=[galaxy_mass_sis])

            assert grid_deflections.grid_coords[0] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert grid_deflections.grid_coords[1] == pytest.approx(np.array([-0.707, -0.707]), 1e-2)

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            grid_image = np.array([[1.0, 1.0]])

            grid_image = grids.GridCoordsImage(grid_image)

            grid_deflections = grid_image.setup_deflections_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            assert grid_deflections.grid_coords == pytest.approx(np.array([[3.0*0.707, 3.0*0.707]]), 1e-3)

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            grid_image = np.array([[1.0, 1.0]])

            grid_image = grids.GridCoordsImage(grid_image)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3*[mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            grid_deflections = grid_image.setup_deflections_grid(galaxies=[lens_sis_x3])

            assert grid_deflections.grid_coords == pytest.approx(np.array([[3.0*0.707, 3.0*0.707]]), 1e-3)


    class TestSetupTracedGrid:

        def test__simple_sis_model__deflection_angles(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0],
                                          [-1.0, -1.0]])

            grid_image = grids.GridCoordsImage(regular_grid_coords)

            deflections = grid_image.setup_deflections_grid(galaxies=[galaxy_mass_sis])

            grid_traced = grid_image.setup_traced_grid(deflections)

            assert grid_traced.grid_coords[0] == pytest.approx(np.array([1.0-0.707, 1.0-0.707]), 1e-2)
            assert grid_traced.grid_coords[1] == pytest.approx(np.array([-1.0+0.707,-1.0+0.707]), 1e-2)

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0]])

            grid_image = grids.GridCoordsImage(regular_grid_coords)

            deflections = grid_image.setup_deflections_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            grid_traced = grid_image.setup_traced_grid(deflections)

            assert grid_traced.grid_coords == pytest.approx(np.array([[1.0 - 3.0*0.707, 1.0 - 3.0*0.707]]), 1e-3)

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            regular_grid_coords = np.array([[1.0, 1.0]])

            grid_image = grids.GridCoordsImage(regular_grid_coords)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3*[mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            deflections = grid_image.setup_deflections_grid(galaxies=[lens_sis_x3])

            grid_traced = grid_image.setup_traced_grid(deflections)

            assert grid_traced.grid_coords == pytest.approx(np.array([[1.0 - 3.0*0.707, 1.0 - 3.0*0.707]]), 1e-3)


class TestGridCoordsImageSub(object):


    class TestConstructor:

        def test__simple_grid_input__sets_up_grid_in_attributes(self):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]],
                             [[2.0, 2.0], [2.0, 2.0], [2.0, 2.0], [2.0, 2.0]]])

            grid_image_sub = grids.GridCoordsImageSub(grid_coords=sub_grid_coords, grid_sub_size=2)

            assert (grid_image_sub.grid_coords[0, 0] == np.array([1.0, 1.0])).all()
            assert (grid_image_sub.grid_coords[0, 1] == np.array([1.0, 1.0])).all()
            assert (grid_image_sub.grid_coords[0, 2] == np.array([1.0, 1.0])).all()
            assert (grid_image_sub.grid_coords[0, 3] == np.array([1.0, 1.0])).all()
            assert (grid_image_sub.grid_coords[1, 0] == np.array([2.0, 2.0])).all()
            assert (grid_image_sub.grid_coords[1, 1] == np.array([2.0, 2.0])).all()
            assert (grid_image_sub.grid_coords[1, 2] == np.array([2.0, 2.0])).all()
            assert (grid_image_sub.grid_coords[1, 3] == np.array([2.0, 2.0])).all()


    class TestFromMask:

        def test__simple_constructor__compare_to_manual_setup_via_mask(self):

            mask = np.array([[True, True, True],
                             [True, False, True],
                             [True, True, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            sub_grid_coords = mask.compute_grid_coords_image_sub(sub_grid_size=2)

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            grid_from_mask = grids.GridCoordsImageSub.from_mask(mask, sub_grid_size=2)

            assert (grid_image_sub.grid_coords == grid_from_mask.grid_coords).all()


    class TestSetupDeflectionsGrid:

        def test__simple_sis_model__deflection_angles(self, galaxy_mass_sis):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0]],
                             [[-1.0, -1.0], [-1.0, -1.0]]])

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_image_sub.setup_deflections_grid(galaxies=[galaxy_mass_sis])

            assert deflections.grid_coords[0,0] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert deflections.grid_coords[0,1] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert deflections.grid_coords[1,0] == pytest.approx(np.array([-0.707, -0.707]), 1e-2)
            assert deflections.grid_coords[1,1] == pytest.approx(np.array([-0.707, -0.707]), 1e-2)

            assert  deflections.sub_grid_size == 2

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0]],
                                [[-1.0, -1.0], [-1.0, -1.0]]])

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_image_sub.setup_deflections_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            assert deflections.grid_coords[0,0] == pytest.approx(np.array([3.0*0.707, 3.0*0.707]), 1e-2)
            assert deflections.grid_coords[0,1] == pytest.approx(np.array([3.0*0.707, 3.0*0.707]), 1e-2)
            assert deflections.grid_coords[1,0] == pytest.approx(np.array([-3.0*0.707, -3.0*0.707]), 1e-2)
            assert deflections.grid_coords[1,1] == pytest.approx(np.array([-3.0*0.707, -3.0*0.707]), 1e-2)

            assert  deflections.sub_grid_size == 2

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0]],
                             [[-1.0, -1.0], [-1.0, -1.0]]])

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3 * [mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            deflections = grid_image_sub.setup_deflections_grid(galaxies=[lens_sis_x3])

            assert deflections.grid_coords[0, 0] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]), 1e-2)
            assert deflections.grid_coords[0, 1] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]), 1e-2)
            assert deflections.grid_coords[1, 0] == pytest.approx(np.array([-3.0 * 0.707, -3.0 * 0.707]), 1e-2)
            assert deflections.grid_coords[1, 1] == pytest.approx(np.array([-3.0 * 0.707, -3.0 * 0.707]), 1e-2)

            assert deflections.sub_grid_size == 2


    class TestSetupTracedGrid:

        def test__simple_sis_model__deflection_angles(self, galaxy_mass_sis):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0]],
                             [[-1.0, -1.0], [-1.0, -1.0]]])

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_image_sub.setup_deflections_grid(galaxies=[galaxy_mass_sis])

            grid_traced = grid_image_sub.setup_traced_grid(deflections)

            assert grid_traced.grid_coords[0,0] == pytest.approx(np.array([1.0-0.707, 1.0-0.707]), 1e-2)
            assert grid_traced.grid_coords[0,1] == pytest.approx(np.array([1.0-0.707, 1.0-0.707]), 1e-2)
            assert grid_traced.grid_coords[1,0] == pytest.approx(np.array([-1.0+0.707, -1.0+0.707]), 1e-2)
            assert grid_traced.grid_coords[1,1] == pytest.approx(np.array([-1.0+0.707, -1.0+0.707]), 1e-2)

            assert grid_traced.sub_grid_size == 2

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0]],
                             [[-1.0, -1.0], [-1.0, -1.0]]])

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            deflections = grid_image_sub.setup_deflections_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            grid_traced = grid_image_sub.setup_traced_grid(deflections)

            assert grid_traced.grid_coords[0,0] == pytest.approx(np.array([1.0 - 3.0*0.707, 1.0 - 3.0*0.707]), 1e-2)
            assert grid_traced.grid_coords[0,1] == pytest.approx(np.array([1.0 - 3.0*0.707, 1.0 - 3.0*0.707]), 1e-2)
            assert grid_traced.grid_coords[1,0] == pytest.approx(np.array([-1.0 + 3.0*0.707, -1.0 + 3.0*0.707]), 1e-2)
            assert grid_traced.grid_coords[1,1] == pytest.approx(np.array([-1.0 + 3.0*0.707, -1.0 + 3.0*0.707]), 1e-2)

            assert  grid_traced.sub_grid_size == 2

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            sub_grid_coords = np.array([[[1.0, 1.0], [1.0, 1.0]],
                             [[-1.0, -1.0], [-1.0, -1.0]]])

            grid_image_sub = grids.GridCoordsImageSub(sub_grid_coords, grid_sub_size=2)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3 * [mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            deflections = grid_image_sub.setup_deflections_grid(galaxies=[lens_sis_x3])

            grid_traced = grid_image_sub.setup_traced_grid(deflections)

            assert grid_traced.grid_coords[0, 0] == pytest.approx(np.array([1.0 - 3.0 * 0.707, 1.0 - 3.0 * 0.707]), 1e-2)
            assert grid_traced.grid_coords[0, 1] == pytest.approx(np.array([1.0 - 3.0 * 0.707, 1.0 - 3.0 * 0.707]), 1e-2)
            assert grid_traced.grid_coords[1, 0] == pytest.approx(np.array([-1.0 + 3.0 * 0.707, -1.0 + 3.0 * 0.707]), 1e-2)
            assert grid_traced.grid_coords[1, 1] == pytest.approx(np.array([-1.0 + 3.0 * 0.707, -1.0 + 3.0 * 0.707]), 1e-2)

            assert deflections.sub_grid_size == 2


class TestGridCoordsBlurring(object):


    class TestConstructor:

        def test__simple_grid_input__sets_up_grid_in_attributes(self):

            regular_grid_coords = np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0], [1.0, 1.0]])

            grid_blurring = grids.GridCoordsBlurring(grid_coords=regular_grid_coords)

            assert (grid_blurring.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_blurring.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_blurring.grid_coords[0] == np.array([1.0, 1.0])).all()
            assert (grid_blurring.grid_coords[0] == np.array([1.0, 1.0])).all()


    class TestFromMask:

        def test__simple_constructor__compare_to_manual_setup_via_mask(self):

            mask = np.array([[True, True, True],
                             [True, False, True],
                             [True, True, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            regular_grid_coords = mask.compute_grid_coords_blurring(psf_size=(3, 3))

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            grid_from_mask = grids.GridCoordsBlurring.from_mask(mask, psf_size=(3, 3))

            assert (grid_blurring.grid_coords == grid_from_mask.grid_coords).all()


    class TestSetupDeflectionsGrid:

        def test__simple_sis_model__deflection_angles(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0], [-1.0, -1.0]])

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            grid_deflections = grid_blurring.setup_deflections_grid(galaxies=[galaxy_mass_sis])

            assert grid_deflections.grid_coords[0] == pytest.approx(np.array([0.707, 0.707]), 1e-2)
            assert grid_deflections.grid_coords[1] == pytest.approx(np.array([-0.707, -0.707]), 1e-2)

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0]])

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            grid_deflections = grid_blurring.setup_deflections_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            assert grid_deflections.grid_coords == pytest.approx(np.array([[3.0 * 0.707, 3.0 * 0.707]]), 1e-3)

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            regular_grid_coords = np.array([[1.0, 1.0]])

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3 * [mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            grid_deflections = grid_blurring.setup_deflections_grid(galaxies=[lens_sis_x3])

            assert grid_deflections.grid_coords == pytest.approx(np.array([[3.0 * 0.707, 3.0 * 0.707]]), 1e-3)


    class TestSetupTracedGrid:

        def test__simple_sis_model__deflection_angles(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0],
                             [-1.0, -1.0]])

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            deflections = grid_blurring.setup_deflections_grid(galaxies=[galaxy_mass_sis])

            traced = grid_blurring.setup_traced_grid(deflections)

            assert traced.grid_coords[0] == pytest.approx(np.array([1.0-0.707, 1.0-0.707]), 1e-2)
            assert traced.grid_coords[1] == pytest.approx(np.array([-1.0+0.707,-1.0+0.707]), 1e-2)

        def test_three_identical_lenses__deflection_angles_triple(self, galaxy_mass_sis):

            regular_grid_coords = np.array([[1.0, 1.0]])

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            deflections = grid_blurring.setup_deflections_grid(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis])

            traced = grid_blurring.setup_traced_grid(deflections)

            assert traced.grid_coords == pytest.approx(np.array([[1.0 - 3.0*0.707, 1.0 - 3.0*0.707]]), 1e-3)

        def test_one_lens_with_three_identical_mass_profiles__deflection_angles_triple(self):

            regular_grid_coords = np.array([[1.0, 1.0]])

            grid_blurring = grids.GridCoordsBlurring(regular_grid_coords)

            lens_sis_x3 = galaxy.Galaxy(mass_profiles=3*[mass_profiles.SphericalIsothermal(einstein_radius=1.0)])

            deflections = grid_blurring.setup_deflections_grid(galaxies=[lens_sis_x3])

            traced = grid_blurring.setup_traced_grid(deflections)

            assert traced.grid_coords == pytest.approx(np.array([[1.0 - 3.0*0.707, 1.0 - 3.0*0.707]]), 1e-3)


class TestGridData(object):


    class TestConstructor:

        def test__simple_grid_input__sets_up_grid_correctly_in_attributes(self):

            grid_data = np.array([1, 2, 3])

            grid_data = grids.GridData(grid_data)

            assert (grid_data.grid_data[0] == np.array([1])).all()
            assert (grid_data.grid_data[1] == np.array([2])).all()
            assert (grid_data.grid_data[2] == np.array([3])).all()


    class TestFromMask:

        def test__simple_grid_input_via_mask(self):

            data = np.array([[1, 2, 3],
                             [4, 5, 6],
                             [7, 8, 9]])

            mask = np.array([[True,  False, True],
                             [False, False, False],
                             [True,  False, True]])

            mask = imaging.Mask(mask, pixel_scale=3.0)

            grid_data = grids.GridData.from_mask(data, mask)

            assert (grid_data.grid_data[0] == np.array([2])).all()
            assert (grid_data.grid_data[1] == np.array([4])).all()
            assert (grid_data.grid_data[2] == np.array([5])).all()
            assert (grid_data.grid_data[3] == np.array([6])).all()
            assert (grid_data.grid_data[4] == np.array([8])).all()


class TestGridMapperDataTo2D(object):


    class TestConstructor:

        def test__simple_mapper_input__sets_up_grid_in_attributes(self):

            data_to_2d = np.array([[0,0],
                                   [0,1],
                                   [0,2]])

            mapper = grids.GridMapperDataTo2D(data_to_2d)

            assert (mapper.data_to_2d[0] == np.array([0,0])).all()
            assert (mapper.data_to_2d[1] == np.array([0,1])).all()
            assert (mapper.data_to_2d[2] == np.array([0,2])).all()


    class TestFromMask:
         
        def test__calcalate_from_simple_mask__mappings_are_correct(self):

            mask = np.array([[True, False, True],
                             [False, False, False],
                             [True, False, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            mapper = grids.GridMapperDataTo2D.from_mask(mask)

            assert (mapper.data_to_2d[0] == np.array([0, 1])).all()
            assert (mapper.data_to_2d[1] == np.array([1, 0])).all()
            assert (mapper.data_to_2d[2] == np.array([1, 1])).all()
            assert (mapper.data_to_2d[3] == np.array([1, 2])).all()
            assert (mapper.data_to_2d[4] == np.array([2, 1])).all()

        def test__manually_compare_to_setting_up_directly_via_mask(self):

            mask = np.array([[True, True, False, False],
                             [True, False, True, True],
                             [True, True, True, False]])

            mask = imaging.Mask(mask=mask, pixel_scale=6.0)

            mapper = mask.compute_grid_mapper_data_to_2d()
            mapper_from_mask = grids.GridMapperDataTo2D.from_mask(mask)

            assert (mapper == mapper_from_mask.data_to_2d).all()
        

class TestGridMapperSparse(object):


    class TestConstructor:

        def test__simple_mappeer_input__sets_up_grid_in_attributes(self):

            sparse_to_image = np.array([1, 2, 3, 5])
            image_to_sparse = np.array([6, 7, 2, 3])

            analysis_mapper = grids.GridMapperSparse(sparse_to_image, image_to_sparse)

            assert (analysis_mapper.sparse_to_image == np.array([1, 2, 3, 5])).all()
            assert (analysis_mapper.image_to_sparse == np.array([6, 7, 2, 3])).all()


    class TestFromMask:

        def test__simple_constructor__compare_to_manual_setup_via_mask(self):

            mask = np.array([[True, True, True],
                             [True, False, True],
                             [True, True, True]])

            mask = imaging.Mask(mask=mask, pixel_scale=3.0)

            sparse_to_image, image_to_sparse = mask.compute_grid_mapper_sparse(sparse_grid_size=1)

            analysis_mapper = grids.GridMapperSparse(sparse_to_image, image_to_sparse)

            analysis_mapper_from_mask = grids.GridMapperSparse.from_mask(mask, sparse_grid_size=1)

            assert (analysis_mapper.sparse_to_image == analysis_mapper_from_mask.sparse_to_image).all()


class TestGridBorder(object):


    class TestCoordinatesAngleFromX(object):

        def test__angle_is_zero__angles_follow_trig(self):

            coordinates = np.array([1.0, 0.0])

            border = grids.GridBorder(border_pixels=np.array([0]), polynomial_degree=3)

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == 0.0

        def test__angle_is_forty_five__angles_follow_trig(self):
            coordinates = np.array([1.0, 1.0])

            border = grids.GridBorder(border_pixels=np.array([0]), polynomial_degree=3)

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == 45.0

        def test__angle_is_sixty__angles_follow_trig(self):
            coordinates = np.array([1.0, 1.7320])

            border = grids.GridBorder(border_pixels=np.array([0]), polynomial_degree=3)

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == pytest.approx(60.0, 1e-3)

        def test__top_left_quandrant__angle_goes_above_90(self):
            
            coordinates = np.array([-1.0, 1.0])

            border = grids.GridBorder(border_pixels=np.array([0]), polynomial_degree=3)

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == 135.0

        def test__bottom_left_quandrant__angle_continues_above_180(self):
            coordinates = np.array([-1.0, -1.0])

            border = grids.GridBorder(border_pixels=np.array([1]), polynomial_degree=3)

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == 225.0

        def test__bottom_right_quandrant__angle_flips_back_to_above_90(self):
            coordinates = np.array([1.0, -1.0])

            border = grids.GridBorder(border_pixels=np.array([0]), polynomial_degree=3)

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == 315.0

        def test__include_source_plane_centre__angle_takes_into_accounts(self):
            coordinates = np.array([2.0, 2.0])

            border = grids.GridBorder(border_pixels=np.array([0]), polynomial_degree=3, centre=(1.0, 1.0))

            theta_from_x = border.coordinates_angle_from_x(coordinates)

            assert theta_from_x == 45.0


    class TestThetasAndRadii:

        def test__four_coordinates_in_circle__all_in_border__correct_radii_and_thetas(self):
            
            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.radii == [1.0, 1.0, 1.0, 1.0]
            assert border.thetas == [0.0, 90.0, 180.0, 270.0]

        def test__other_thetas_radii(self):
            
            coordinates = np.array([[2.0, 0.0], [2.0, 2.0], [-1.0, -1.0], [0.0, -3.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.radii == [2.0, 2.0 * np.sqrt(2), np.sqrt(2.0), 3.0]
            assert border.thetas == [0.0, 45.0, 225.0, 270.0]

        def test__border_centre_offset__coordinates_same_r_and_theta_shifted(self):
            
            coordinates = np.array([[2.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 0.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3, centre=(1.0, 1.0))
            border.polynomial_fit_to_border(coordinates)

            assert border.radii == [1.0, 1.0, 1.0, 1.0]
            assert border.thetas == [0.0, 90.0, 180.0, 270.0]


    class TestBorderPolynomial(object):

        def test__four_coordinates_in_circle__thetas_at_radius_are_each_coordinates_radius(self):

            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.radius_at_theta(theta=0.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=90.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=180.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=270.0) == pytest.approx(1.0, 1e-3)

        def test__eight_coordinates_in_circle__thetas_at_each_coordinates_are_the_radius(self):

            coordinates = np.array([[1.0, 0.0], [0.5 * np.sqrt(2), 0.5 * np.sqrt(2)],
                                    [0.0, 1.0], [-0.5 * np.sqrt(2), 0.5 * np.sqrt(2)],
                                    [-1.0, 0.0], [-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)],
                                    [0.0, -1.0], [0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]])

            border = grids.GridBorder(border_pixels=np.arange(8), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.radius_at_theta(theta=0.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=45.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=90.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=135.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=180.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=225.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=270.0) == pytest.approx(1.0, 1e-3)
            assert border.radius_at_theta(theta=315.0) == pytest.approx(1.0, 1e-3)


    class TestMoveFactors(object):

        def test__inside_border__move_factor_is_1(self):
            
            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.move_factor(coordinate=(0.5, 0.0)) == 1.0
            assert border.move_factor(coordinate=(-0.5, 0.0)) == 1.0
            assert border.move_factor(coordinate=(0.25, 0.25)) == 1.0
            assert border.move_factor(coordinate=(0.0, 0.0)) == 1.0

        def test__outside_border_double_its_radius__move_factor_is_05(self):
            
            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.move_factor(coordinate=(2.0, 0.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(0.0, 2.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(-2.0, 0.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(0.0, -2.0)) == pytest.approx(0.5, 1e-3)

        def test__outside_border_double_its_radius_and_offset__move_factor_is_05(self):
            
            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.move_factor(coordinate=(2.0, 0.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(0.0, 2.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(0.0, 2.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(2.0, 0.0)) == pytest.approx(0.5, 1e-3)

        def test__outside_border_as_above__but_shift_for_source_plane_centre(self):

            coordinates = np.array([[2.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 0.0]])
            
            border = grids.GridBorder(border_pixels=np.arange(4), polynomial_degree=3, centre=(1.0, 1.0))
            border.polynomial_fit_to_border(coordinates)

            assert border.move_factor(coordinate=(3.0, 1.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(1.0, 3.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(1.0, 3.0)) == pytest.approx(0.5, 1e-3)
            assert border.move_factor(coordinate=(3.0, 1.0)) == pytest.approx(0.5, 1e-3)


    class TestRelocateCoordinates(object):

        def test__inside_border_no_relocations(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            coordinates = np.asarray(list(map(lambda x: (np.cos(x), np.sin(x)), thetas)))

            border = grids.GridBorder(border_pixels=np.arange(32), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.relocated_coordinate(coordinate=np.array([0.1, 0.0])) == \
                   pytest.approx(np.array([0.1, 0.0]), 1e-3)

            assert border.relocated_coordinate(coordinate=np.array([-0.2, -0.3])) == \
                   pytest.approx(np.array([-0.2, -0.3]), 1e-3)

            assert border.relocated_coordinate(coordinate=np.array([0.5, 0.4])) == \
                   pytest.approx(np.array([0.5, 0.4]), 1e-3)

            assert border.relocated_coordinate(coordinate=np.array([0.7, -0.1])) == \
                   pytest.approx(np.array([0.7, -0.1]), 1e-3)

        def test__outside_border_simple_cases__relocates_to_source_border(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            coordinates = np.asarray(list(map(lambda x: (np.cos(x), np.sin(x)), thetas)))

            border = grids.GridBorder(border_pixels=np.arange(32), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.relocated_coordinate(coordinate=np.array([2.5, 0.0])) == \
                   pytest.approx(np.array([1.0, 0.0]), 1e-3)

            assert border.relocated_coordinate(coordinate=np.array([0.0, 3.0])) == \
                   pytest.approx(np.array([0.0, 1.0]), 1e-3)

            assert border.relocated_coordinate(coordinate=np.array([-2.5, 0.0])) == \
                   pytest.approx(np.array([-1.0, 0.0]), 1e-3)

            assert border.relocated_coordinate(coordinate=np.array([-5.0, 5.0])) == \
                   pytest.approx(np.array([-0.707, 0.707]), 1e-3)

        def test__outside_border_simple_cases_2__relocates_to_source_border(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 16)
            coordinates = np.asarray(list(map(lambda x: (np.cos(x), np.sin(x)), thetas)))

            border = grids.GridBorder(border_pixels=np.arange(16), polynomial_degree=3)
            border.polynomial_fit_to_border(coordinates)

            assert border.relocated_coordinate(coordinate=(2.0, 0.0)) == pytest.approx((1.0, 0.0), 1e-3)

            assert border.relocated_coordinate(coordinate=(0.0, 2.0)) == pytest.approx((0.0, 1.0), 1e-3)

            assert border.relocated_coordinate(coordinate=(-2.0, 0.0)) == pytest.approx((-1.0, 0.0), 1e-3)

            assert border.relocated_coordinate(coordinate=(0.0, -1.0)) == pytest.approx((0.0, -1.0), 1e-3)

            assert border.relocated_coordinate(coordinate=(1.0, 1.0)) == \
                   pytest.approx((0.5 * np.sqrt(2), 0.5 * np.sqrt(2)), 1e-3)

            assert border.relocated_coordinate(coordinate=(-1.0, 1.0)) == \
                   pytest.approx((-0.5 * np.sqrt(2), 0.5 * np.sqrt(2)), 1e-3)

            assert border.relocated_coordinate(coordinate=(-1.0, -1.0)) == \
                   pytest.approx((-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)), 1e-3)

            assert border.relocated_coordinate(coordinate=(1.0, -1.0)) == \
                   pytest.approx((0.5 * np.sqrt(2), -0.5 * np.sqrt(2)), 1e-3)


    class TestRelocateAllCoordinatesOutsideBorder(object):

        def test__coordinates_inside_border__no_relocations(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 16)
            circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))

            coordinates = np.asarray(circle + [(0.1, 0.0), (0.1, 0.0), (0.0, 0.1), (-0.1, 0.0),
                                               (-0.1, 0.0), (-0.1, -0.0), (0.0, -0.1), (0.1, -0.0)])

            border_pixels = np.arange(16)
            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)
            
            assert relocated_coordinates == pytest.approx(coordinates, 1e-3)

        def test__all_coordinates_inside_border_again__no_relocations(self):
            
            thetas = np.linspace(0.0, 2.0 * np.pi, 16)
            circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))

            coordinates = np.asarray(circle + [(0.5, 0.0), (0.5, 0.5), (0.0, 0.5), (-0.5, 0.5),
                                               (-0.5, 0.0), (-0.5, -0.5), (0.0, -0.5), (0.5, -0.5)])

            border_pixels = np.arange(16)
            border = grids.GridBorder(border_pixels, polynomial_degree=3)


            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)

            assert relocated_coordinates == pytest.approx(coordinates, 1e-3)

        def test__6_coordinates_total__2_outside_border__relocate_to_source_border(self):
            
            coordinates = np.array([[1.0, 0.0], [20., 20.], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [1.0, 1.0]])
            border_pixels = np.array([0, 2, 3, 4])

            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)

            assert relocated_coordinates[0] == pytest.approx(coordinates[0], 1e-3)
            assert relocated_coordinates[1] == pytest.approx(np.array([0.7071, 0.7071]), 1e-3)
            assert relocated_coordinates[2] == pytest.approx(coordinates[2], 1e-3)
            assert relocated_coordinates[3] == pytest.approx(coordinates[3], 1e-3)
            assert relocated_coordinates[4] == pytest.approx(coordinates[4], 1e-3)
            assert relocated_coordinates[5] == pytest.approx(np.array([0.7071, 0.7071]), 1e-3)

        def test__24_coordinates_total__8_coordinates_outside_border__relocate_to_source_border(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 16)
            circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            coordinates = np.asarray(circle + [(2.0, 0.0), (1.0, 1.0), (0.0, 2.0), (-1.0, 1.0),
                                               (-2.0, 0.0), (-1.0, -1.0), (0.0, -2.0), (1.0, -1.0)])

            border_pixels = np.arange(16)
            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)

            assert relocated_coordinates[0:16] == pytest.approx(coordinates[0:16], 1e-3)
            assert relocated_coordinates[16] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert relocated_coordinates[17] == pytest.approx(np.array([0.5 * np.sqrt(2), 0.5 * np.sqrt(2)]),
                                                                         1e-3)
            assert relocated_coordinates[18] == pytest.approx(np.array([0.0, 1.0]), 1e-3)
            assert relocated_coordinates[19] == pytest.approx(
                np.array([-0.5 * np.sqrt(2), 0.5 * np.sqrt(2)]), 1e-3)
            assert relocated_coordinates[20] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_coordinates[21] == pytest.approx(
                np.array([-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]), 1e-3)
            assert relocated_coordinates[22] == pytest.approx(np.array([0.0, -1.0]), 1e-3)
            assert relocated_coordinates[23] == pytest.approx(
                np.array([0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]), 1e-3)

        def test__24_coordinates_total__4_coordinates_outside_border__relates_to_source_border(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 16)
            circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            coordinates = np.asarray(circle + [(0.5, 0.0), (0.5, 0.5), (0.0, 0.5), (-0.5, 0.5),
                                               (-2.0, 0.0), (-1.0, -1.0), (0.0, -2.0), (1.0, -1.0)])

            border_pixels = np.arange(16)
            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)

            assert relocated_coordinates[0:20] == pytest.approx(coordinates[0:20], 1e-3)
            assert relocated_coordinates[20] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_coordinates[21] == pytest.approx(
                np.array([-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]), 1e-3)
            assert relocated_coordinates[22] == pytest.approx(np.array([0.0, -1.0]), 1e-3)
            assert relocated_coordinates[23] == pytest.approx(
                np.array([0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]), 1e-3)

        def test__change_pixel_order_and_border_pixels__works_as_above(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 16)
            circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            coordinates = np.asarray([(-2.0, 0.0), (-1.0, -1.0), (0.0, -2.0), (1.0, -1.0)] + circle + \
                                     [(0.5, 0.0), (0.5, 0.5), (0.0, 0.5), (-0.5, 0.5)])

            border_pixels = np.array([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)

            assert relocated_coordinates[0] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_coordinates[1] == pytest.approx(
                np.array([-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]), 1e-3)
            assert relocated_coordinates[2] == pytest.approx(np.array([0.0, -1.0]), 1e-3)
            assert relocated_coordinates[3] == pytest.approx(np.array([0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]),
                                                                        1e-3)
            assert relocated_coordinates[4:24] == pytest.approx(coordinates[4:24], 1e-3)

        def test__sub_pixels_in_border__are_not_relocated(self):

            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            sub_coordinates = np.array([[[0.1, 0.0], [0.2, 0.0], [0.3, 0.0], [0.4, 0.0]],
                                        [[0.1, 0.0], [0.2, 0.0], [0.3, 0.0], [0.4, 0.0]],
                                        [[0.1, 0.0], [0.2, 0.0], [0.3, 0.0], [0.4, 0.0]],
                                        [[0.1, 0.0], [0.2, 0.0], [0.3, 0.0], [0.4, 0.0]]])

            border_pixels = np.array([0, 1, 2, 3])
            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)
            relocated_sub_coordinates = border.relocate_sub_coordinates_outside_border(coordinates, sub_coordinates)

            assert relocated_coordinates == pytest.approx(coordinates, 1e-3)
            assert relocated_sub_coordinates == pytest.approx(sub_coordinates, 1e-3)

        def test__sub_pixels_outside_border__are_relocated(self):
            
            coordinates = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            sub_coordinates = np.array([[[2.0, 0.0], [0.2, 0.0], [2.0, 2.0], [0.4, 0.0]],
                                        [[0.0, 2.0], [-2.0, 2.0], [0.3, 0.0], [0.4, 0.0]],
                                        [[-2.0, 0.0], [0.2, 0.0], [0.3, 0.0], [2.0, -2.0]],
                                        [[0.0, -2.0], [0.2, 0.0], [0.3, 0.0], [0.4, 0.0]]])

            border_pixels = np.array([0, 1, 2, 3])
            border = grids.GridBorder(border_pixels, polynomial_degree=3)

            relocated_coordinates = border.relocate_coordinates_outside_border(coordinates)
            relocated_sub_coordinates = border.relocate_sub_coordinates_outside_border(coordinates, sub_coordinates)

            assert relocated_coordinates == pytest.approx(coordinates, 1e-3)

            assert (relocated_sub_coordinates[0, 0] == pytest.approx(np.array([1.0, 0.0]), 1e-3))
            assert (relocated_sub_coordinates[0, 1] == sub_coordinates[0, 1]).all()
            assert (relocated_sub_coordinates[0, 2] == pytest.approx(np.array([0.707, 0.707]), 1e-3))
            assert (relocated_sub_coordinates[0, 3] == sub_coordinates[0, 3]).all()

            assert (relocated_sub_coordinates[1, 0] == pytest.approx(np.array([0.0, 1.0]), 1e-3))
            assert (relocated_sub_coordinates[1, 1] == pytest.approx(np.array([-0.707, 0.707]), 1e-3))
            assert (relocated_sub_coordinates[1, 2] == sub_coordinates[1, 2]).all()
            assert (relocated_sub_coordinates[1, 3] == sub_coordinates[1, 3]).all()

            assert (relocated_sub_coordinates[2, 0] == pytest.approx(np.array([-1.0, 0.0]), 1e-3))
            assert (relocated_sub_coordinates[2, 1] == sub_coordinates[2, 1]).all()
            assert (relocated_sub_coordinates[2, 2] == sub_coordinates[2, 2]).all()
            assert (relocated_sub_coordinates[2, 3] == pytest.approx(np.array([0.707, -0.707]), 1e-3))

            assert (relocated_sub_coordinates[3, 0] == pytest.approx(np.array([0.0, -1.0]), 1e-3))
            assert (relocated_sub_coordinates[3, 1] == sub_coordinates[3, 1]).all()
            assert (relocated_sub_coordinates[3, 2] == sub_coordinates[3, 2]).all()
            assert (relocated_sub_coordinates[3, 3] == sub_coordinates[3, 3]).all()