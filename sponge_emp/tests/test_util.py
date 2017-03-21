from unittest import main, TestCase
import os.path
from sponge_emp.utils import get_data_path, getdoc, get_fasta_seqs


class SpongeEMPTests(TestCase):
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

    def test_get_fasta_seqs(self):
        # test with file name
        fastafile = get_data_path('seqs1.fasta')
        seqs = get_fasta_seqs(fastafile)
        self.assertEqual(len(seqs), 3)
        self.assertEqual(seqs[2], 'AAACCCGGGTTT')

        # test with an already opened file
        fl = open(fastafile)
        seqs = get_fasta_seqs(fl)
        self.assertEqual(len(seqs), 3)
        self.assertEqual(seqs[2], 'AAACCCGGGTTT')

if __name__ == '__main__':
    main()
