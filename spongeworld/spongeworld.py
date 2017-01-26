from flask import Blueprint, request, g
from collections import defaultdict
import json
from .utils import debug, getdoc
from .autodoc import auto

Sponge_Flask_Obj = Blueprint('Sponge_Flask_Obj', __name__, template_folder='templates')


@Sponge_Flask_Obj.route('/sequence/info', methods=['GET'])
@auto.doc()
def sequence_info():
    '''
    Title: Get sequence information
    URL: /sequence/info
    Description : Get the sequence distribution information
    Method: GET
    URL Params:
    Data Params: JSON
        {
            sequence : str (ACGT sequence)
                the sequence to get information about
            fields : list of str or None (optional)
                if None (default) return distribution information about all fields except #SampleID.
                Otherwise, return distribution information only in the specified fields
            threshold : float (optional)
                If supplied, use > this frequency threshold for presence/absence call.
                If not supplied use>0 for presence/absence
        }
    Success Response:
        Code : 200
        Content :
        {
            'total_samples' : int
                the total amount of samples in the database
            'total_observed' : int
                the total number of samples where the sequence is present
            'info' : dict of {field(str): information(dict)}
                the frequency of the sequence in each field.
                information is a dict of {value(str): distribution(dict)}
                distribution contains the following key/values:
                    'total_samples': int
                        the total number of samples having this value
                    'observed_samples': int
                        the number of samples with this value which have the sequence present in them
                }
        }
    Validation:
    '''
    debug(1, 'sequence info')
    db = g.db
    alldat = request.get_json()
    if alldat is None:
        return(getdoc(sequence_info))
    sequence = alldat.get('sequence')
    if sequence is None:
        return('sequence parameter missing', 400)
    threshold = alldat.get('threshold', 0)
    fields = alldat.get('fields')

    err, res = get_sequence_info(db, sequence, fields, threshold)
    if err:
        return 'error encountered: %s' % err, 400
    return json.dumps(res)


def get_sequence_info(db, sequence, fields=None, threshold=0, mincounts=4):
    '''Get all total frequencies of the sequences in the various fields/values

    Parameters
    ----------
    sequence : str of list of str
        The DNA sequences to get information about.
    fields : list of str or None (optional)
        if None (default) return distribution information about all fields except #SampleID.
        Otherwise, return distribution information only in the specified fields
    threshold : float (optional)
        If supplied, use > this frequency threshold for presence/absence call.
        If not supplied use>0 for presence/absence
    mincounts : int (optional)
        the minimal total number of counts for a field/value in order to be returned

    Returns
    -------
    err : str
        the error encountered or '' if ok
    res : dict with the following key/values:
        'total_samples' : int
            the total amount of samples in the database
        'total_observed' : int
            the total number of samples where the sequence is present
        'info' : dict of {field(str): information(dict)}
            the frequency of the sequence in each field.
            information is a dict of {value(str): distribution(dict)}
            distribution contains the following key/values:
                'total_samples': int
                    the total number of samples having this value
                'observed_samples': int
                    the number of samples with this value which have the sequence present in them
    '''
    if fields is None:
        fields = db.get_fields(exclude=['#SampleID'])

    if isinstance(sequence, str):
        sequence = [sequence]

    total_samples = 0
    total_observed = 0
    seqs_processed = 0
    total_field_val_samples = defaultdict(dict)
    res = {}
    res['info'] = defaultdict(dict)
    for csequence in sequence:
        # trim and upper case the sequence
        if len(csequence) < db.seq_length:
            continue
        seqs_processed += 1
        csequence = csequence[:db.seq_length].upper()
        total_samples += db.get_total_samples()
        total_observed += db.get_total_observed(csequence, threshold=threshold)
        for cfield in fields:
            debug(1, 'processing field %s' % cfield)
            cinfo = db.get_info(csequence, field=cfield, threshold=threshold)
            for cval, cvalinfo in cinfo.items():
                if cval not in res['info'][cfield]:
                    res['info'][cfield][cval] = {'total_samples': 0, 'observed_samples': 0}
                total_field_val_samples[cfield][cval] = cvalinfo['total_samples']
                # res['info'][cfield][cval]['total_samples'] += cvalinfo['total_samples']
                res['info'][cfield][cval]['observed_samples'] += cvalinfo['observed_samples']

    # remove field/values with < minreads
    # and add the total number of samples tested in the field
    field_del_list = []
    for cfield, cinfo in res['info'].items():
        del_list = []
        for cval, cvalinfo in cinfo.items():
            if cvalinfo['observed_samples'] < mincounts:
                del_list.append(cval)
            else:
                print(cfield)
                print(cval)
                print(res['info'][cfield][cval]['total_samples'])
                print(total_field_val_samples[cfield])
                print(total_field_val_samples[cfield][cval])
                res['info'][cfield][cval]['total_samples'] = seqs_processed * total_field_val_samples[cfield][cval]
        # delete the values that don't have enough entries
        for cdel in del_list:
            del res['info'][cfield][cdel]
        if len(res['info'][cfield]) == 0:
            field_del_list.append(cfield)
    # and delete the fields with no values in them anymore
    # for cdel in field_del_list:
    #     del res['info'][cdel]

    res['total_samples'] = total_samples
    res['total_observed'] = total_observed
    if seqs_processed == 0:
        debug(3, 'No sequences processed')
        return 'All sequences too short. minimal length is %d' % db.seq_length, None
    return '', res


@Sponge_Flask_Obj.route('/docs')
def documentation():
    return auto.html()
