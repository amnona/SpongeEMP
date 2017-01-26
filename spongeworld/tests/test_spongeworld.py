from unittest import main, TestCase

from spongeworld.database import DBData
from spongeworld.spongeworld import get_sequence_info
from spongeworld.utils import get_data_path


class SpongeworldTests(TestCase):
    def setUp(self):
        super().setUp()
        self.db = DBData(biomfile=get_data_path('test1.biom'), mapfile=get_data_path('test1.map.txt'))
        self.db.import_data()
        self.goodseq = 'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTATGTAAGACAGTTGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGTGACTGCATAGCTAGAGTACGGTAGAGGGGGATGGAATTCCGCG'
        self.badseq = 'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTAGGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTGCCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG'

    def test_get_sequence_info(self):
        db = self.db

        err, res = get_sequence_info(db, 'AAAA')
        self.assertTrue(err)

        err, res = get_sequence_info(db, self.goodseq)
        self.assertTrue(err == '')
        self.assertEqual(res['total_samples'], 20)
        self.assertEqual(res['total_observed'], 9)
        info = res['info']
        # we have 2 fields
        self.assertEqual(len(info), 2)
        self.assertEqual(len(info['id']), 0)
        self.assertEqual(len(info['group']), 1)
        self.assertEqual(info['group']['2']['total_samples'], 9)
        self.assertEqual(info['group']['2']['observed_samples'], 9)

        err, res = get_sequence_info(db, self.badseq, fields=['group'], threshold=10 / 2500)
        info = res['info']
        # only 1 field supplied
        self.assertEqual(len(info), 1)
        self.assertEqual(len(info['group']), 0)


if __name__ == '__main__':
    main()
