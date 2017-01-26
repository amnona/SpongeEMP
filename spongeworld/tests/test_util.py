from unittest import main, TestCase
import os.path
from spongeworld.utils import get_data_path, getdoc


class SpongeworldTests(TestCase):
    def setUp(self):
        super().setUp()

    def test_getdoc(self):
        '''Test the getdoc function'''
        doc = getdoc(self.test_getdoc)
        self.assertTrue('getdoc function' in doc)

    def test_get_data_path(self):
        '''Test whether the data path test file exists'''
        fpath = get_data_path('test1.biom')
        self.assertTrue(os.path.exists(fpath))


if __name__ == '__main__':
    main()
