from test_autolens.integration.tests.interferometer.lens_only import lens_light
from test_autolens.integration.tests.interferometer.runner import run_a_mock


class TestCase:
    def _test__lens_light(self):
        run_a_mock(lens_light)
