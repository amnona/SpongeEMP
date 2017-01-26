from unittest import main, TestCase

import numpy as np

from spongeworld.database import DBData
from spongeworld.utils import get_data_path


class DatabaseTests(TestCase):
    def setUp(self):
        super().setUp()
        self.db = DBData(biomfile=get_data_path('test1.biom'), mapfile=get_data_path('test1.map.txt'))
        self.goodseq = 'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTATGTAAGACAGTTGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGTGACTGCATAGCTAGAGTACGGTAGAGGGGGATGGAATTCCGCG'
        self.badseq = 'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTAGGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTGCCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG'

    def test_import_data(self):
        db = self.db
        db.import_data()

        # we get the right sequence length
        self.assertEqual(db.seq_length, 150)
        # we load the correct number of samples and sequnces
        self.assertEqual(len(db.sample_metadata['#SampleID']), 20)
        self.assertEqual(len(db.feature_metadata['ids']), 12)
        # we normalize each sample to sum 1
        self.assertEqual(np.sum(np.sum(db.data, axis=0) == 1), db.data.shape[1])
        # we load the data correctly
        self.assertEqual(db.data[db.get_seq_pos(self.badseq), db.sample_metadata.index.get_loc('S7')], 3/1700)
        self.assertEqual(db.data[db.get_seq_pos(self.goodseq), db.sample_metadata.index.get_loc('S11')], 0)
        self.assertNotEqual(db.data[db.get_seq_pos(self.goodseq), db.sample_metadata.index.get_loc('S12')], 0)

    def test_get_fields(self):
        db = self.db
        db.import_data()

        # we have the correct fields:
        self.assertCountEqual(db.get_fields(), db.sample_metadata.columns)
        self.assertTrue('#SampleID' not in db.get_fields(exclude='#SampleID'))

    def test_get_total_samples(self):
        db = self.db
        db.import_data()

        self.assertEqual(db.get_total_samples(), 20)

    def test_get_seq_pos(self):
        db = self.db
        db.import_data()

        self.assertEqual(self.badseq, db.feature_metadata.index[db.get_seq_pos(self.badseq)])
        self.assertEqual(self.goodseq, db.feature_metadata.index[db.get_seq_pos(self.goodseq)])

    def test_get_total_observed(self):
        db = self.db
        db.import_data()

        self.assertEqual(db.get_total_observed(self.goodseq), 9)
        self.assertEqual(db.get_total_observed(self.badseq), 10)
        self.assertEqual(db.get_total_observed(self.badseq, threshold=10 / 2500), 5)

    def test_get_value_samples(self):
        db = self.db
        db.import_data()

        # a value that exists
        self.assertEqual(db.get_value_samples('group', '2'), 9)
        # a value that doesn't exists
        self.assertEqual(db.get_value_samples('group', '3'), 0)

    def test_get_info(self):
        db = self.db
        db.import_data()

        info = db.get_info(self.goodseq, 'group')
        self.assertTrue('1' not in info)
        self.assertEqual(info['2']['total_samples'], 9)
        self.assertEqual(info['2']['observed_samples'], 9)

        info = db.get_info(self.badseq, 'group')
        self.assertEqual(info['1']['total_samples'], 11)
        self.assertEqual(info['1']['observed_samples'], 6)
        self.assertEqual(info['2']['total_samples'], 9)
        self.assertEqual(info['2']['observed_samples'], 4)

        # test threshold
        info = db.get_info(self.badseq, 'group', threshold=10 / 2500)
        self.assertEqual(info['2']['total_samples'], 9)
        self.assertEqual(info['2']['observed_samples'], 3)

if __name__ == '__main__':
    main()
