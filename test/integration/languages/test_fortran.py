import os.path

from .. import *


@unittest.skipIf(env.platform.name == 'windows', 'no fortran on windows')
class TestF77(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'f77'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], ' hello from f77!\n')


@unittest.skipIf(env.platform.name == 'windows', 'no fortran on windows')
class TestF95(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join('languages', 'f95'), *args, **kwargs
        )

    def test_build(self):
        self.build(executable('program'))
        self.assertOutput([executable('program')], ' hello from f95!\n')
