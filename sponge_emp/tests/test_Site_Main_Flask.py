from unittest import main, TestCase

from sponge_emp.database import DBData
from sponge_emp.sponge_emp import get_sequence_info
from sponge_emp.utils import get_data_path
from sponge_emp.Site_Main_Flask import get_annotation_string


class DatabaseTests(TestCase):
    def setUp(self):
        super().setUp()
        self.db = DBData(biomfile=get_data_path('test1.biom'), mapfile=get_data_path('test1.map.txt'))
        self.goodseq = 'TACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTATGTAAGACAGTTGTGAAATCCCCGGGCTCAACCTGGGAACTGCATCTGTGACTGCATAGCTAGAGTACGGTAGAGGGGGATGGAATTCCGCG'
        self.badseq = 'TACGGAGGATGCGAGCGTTATCTGGAATCATTGGGTTTAAAGGGTCCGTAGGCGGGTTGATAAGTCAGAGGTGAAAGCGCTTAGCTCAACTAAGCAACTGCCTTTGAAACTGTCAGTCTTGAATGATTGTGAAGTAGTTGGAATGTGTAG'

    def test_import_data(self):
        db = self.db
        db.import_data()

        err, info = get_sequence_info(db, self.goodseq, fields=None, threshold=0)
        self.assertEqual(err, '')
        desc = get_annotation_string(info)
        self.assertEqual(desc, ['group:2 (9/9)'])

        err, info = get_sequence_info(db, self.badseq, fields=None, threshold=0)
        self.assertEqual(err, '')
        desc = get_annotation_string(info)
        self.assertEqual(desc, [])


if __name__ == '__main__':
    main()
