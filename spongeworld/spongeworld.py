from flask import Blueprint, request, g
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


def get_sequence_info(db, sequence, fields=None, threshold=0):
    '''Get all frequencies of the sequence in the various fields/values

    Parameters
    ----------
    sequence :
        The DNA sequence to get information about.
    fields : list of str or None (optional)
        if None (default) return distribution information about all fields except #SampleID.
        Otherwise, return distribution information only in the specified fields
    threshold : float (optional)
        If supplied, use > this frequency threshold for presence/absence call.
        If not supplied use>0 for presence/absence

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
    # trim and upper case the sequence
    if len(sequence) < db.seq_length:
        return 'sequence too short. minimal length is %d' % db.seq_length, None
    sequence = sequence[:db.seq_length].upper()
    if fields is None:
        fields = db.get_fields(exclude=['#SampleID'])

    res = {}
    res['total_samples'] = db.get_total_samples()
    res['total_observed'] = db.get_total_observed(sequence, threshold=threshold)
    res['info'] = {}
    for cfield in fields:
        debug(1, 'processing field %s' % cfield)
        cinfo = db.get_info(sequence, field=cfield, threshold=threshold)
        res['info'][cfield] = cinfo
    return '', res


@Sponge_Flask_Obj.route('/docs')
def documentation():
    return auto.html()
