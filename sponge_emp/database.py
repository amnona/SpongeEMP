from collections import defaultdict
import os.path

import pandas as pd
import numpy as np
import scipy.sparse
import biom

from .utils import debug


class DBData:
    def __init__(self, biomfile='data/final.withtax.biom', mapfile='data/map.txt', filepath=''):
        '''The database class used for data access

        Parameters
        ----------
        biomfile : str (optional)
            Name of the biom table
        mapfile : str
            Name of the mapping file
        filepath : str (optional)
            The path to the application
        '''
        print(biomfile)
        biomfile = os.path.join(filepath, biomfile)
        mapfile = os.path.join(filepath, mapfile)
        self._biom_file_name = biomfile
        self._map_file_name = mapfile

    def import_data(self):
        '''
        Load the data into memory
        '''
        debug(5, 'Loading biom table %s' % self._biom_file_name)
        table = biom.load_table(self._biom_file_name)
        table.norm(axis='sample', inplace=True)
        self.data = scipy.sparse.csr_matrix(table.matrix_data)

        self.sids = table.ids(axis='sample')
        self.fids = table.ids(axis='observation')

        s_metadata = pd.read_table(self._map_file_name, sep='\t')
        s_metadata.fillna('na', inplace=True)
        s_metadata.set_index(s_metadata.columns[0], drop=False, inplace=True)
        s_metadata.index = s_metadata.index.astype(np.str)
        common_samples_pos = [cpos for cpos in range(len(self.sids)) if self.sids[cpos] in s_metadata.index]
        common_samples = [self.sids[cpos] for cpos in common_samples_pos]
        self.data = self.data[:, common_samples_pos]
        self.sample_metadata = s_metadata.loc[common_samples, ]

        f_metadata = table.metadata(axis='observation')

        if f_metadata is None:
            debug(1, 'No metadata associated with features in biom table')
        else:
            f_metadata = [dict(tmd) for tmd in f_metadata]
        md_df = pd.DataFrame(f_metadata)
        md_df['ids'] = self.fids
        md_df.set_index('ids', drop=False, inplace=True)
        self.feature_metadata = md_df

        self.seq_length = len(self.feature_metadata.index[0])

    def get_fields(self, exclude=[]):
        '''Get the list of fields in the database sample metadata

        Parameters
        ----------
        exclude : list of str(optional)
            do not return fields in the exclude list

        Returns
        -------
        fields : list of str
            the list of fields in the database sample metadata
        '''
        fields = self.sample_metadata.columns
        fields = [cfield for cfield in fields if cfield not in exclude]
        return fields

    def get_total_samples(self):
        '''Get the total number of samples in the database

        Returns
        -------
        num_samples : int
            total number of samples in the database
        '''
        num_samples = self.data.shape[1]
        return int(num_samples)

    def get_taxonomy(self, sequence):
        '''Get the taxonomy for a given sequence

        Parameters
        ----------
        sequence : str
            The DNA sequence to get the taxonomy for

        Returns
        -------
        tax : str
            the taxonomy string (if exists) or 'na'
        '''
        if len(sequence) < self.seq_length:
            return('na')
            debug(2, 'sequence too short for taxonomy')
        sequence = sequence[:self.seq_length].upper()
        if 'taxonomy' not in self.feature_metadata:
            debug(2, 'taxonomy not in biom table')
            return('na')
        if sequence not in self.feature_metadata.index:
            debug(2, 'sequence not in biom table')
            return('na')
        tax = self.feature_metadata['taxonomy'][sequence]
        return tax

    def get_seq_pos(self, sequence):
        '''Get the row of a sequence in the database

        Parameters
        ----------
        sequence : str (ACGT sequence)
            the sequence to look for

        Returns
        -------
        pos : int
            the row of the sequence in the data array or None if not found
        '''
        debug(1, 'get seq pos for sequence %s' % sequence)
        if sequence in self.feature_metadata.index:
            return self.feature_metadata.index.get_loc(sequence)
        debug(3, 'sequence %s not found' % sequence)
        return None

    def get_total_observed(self, sequence, threshold=0):
        '''Get the number of samples in the database where the sequence is present at > threshold

        Parameters
        ----------
        sequence : str
            the DNA sequence to look for
        threhold : float (optional)
            the minimal frequency for the sequence to be present in the sample in order to call it observed (using > threshold)
        '''
        pos = self.get_seq_pos(sequence)
        if pos is None:
            return 0

        num_observed = np.sum(self.data[pos, :] > threshold)
        debug(1, 'sequence observed in %d samples' % num_observed)
        return int(num_observed)

    def get_value_samples(self, field, value):
        '''Get the number of samples containing a given value in field

        Parameters
        ----------
        field : str
            name of the field
        value : str
            the value to look for

        Returns
        -------
        num_samples : int
            the number of samples with value in field
        '''
        num_samples = np.sum(self.sample_metadata[field] == value)
        return num_samples

    def get_info(self, sequence, field, threshold=0, mincounts=4):
        '''Get the total samples, observed samples per value in field

        Note, values for which the sequence does not appear (i.e. observed samples=0) are not returned

        Parameters
        ----------
        sequence : str or list of str
            the DNA sequences to look for
        field : str
            the name of the field to get the values for
        threhold : float (optional)
            the minimal frequency for the sequence to be present in the sample in order to call it observed (using > threshold)
        mincounts : int (optional)
            the minimal total number of counts for a field/value in order to be returned

        Returns
        -------
        info : dict of {value: distribution}
            value : str
                the value of the field
            distribution : dict containing the following key/values:
                'total_samples': int
                    the total number of samples having this value
                'observed_samples': int
                    the number of samples with this value which have the sequence present in them
        '''
        if isinstance(sequence, str):
            sequence = [sequence]

        allsum = np.zeros(self.data.shape[1])
        for csequence in sequence:
            pos = self.get_seq_pos(csequence)
            if pos is None:
                continue
            present = self.data[pos, :] > threshold
            allsum[present.nonzero()[1]] += 1

        present_pos = allsum.nonzero()[0]
        counts = defaultdict(int)
        for cpos in present_pos:
            cvalue = self.sample_metadata[field].iloc[cpos]
            counts[cvalue] += allsum[cpos]

        info = {}
        for cvalue, ccount in counts.items():
            if ccount < mincounts:
                continue
            cinfo = {}
            cinfo['observed_samples'] = int(ccount)
            cinfo['total_samples'] = int(self.get_value_samples(field, cvalue)) * len(sequence)
            info[str(cvalue)] = cinfo
        return info
