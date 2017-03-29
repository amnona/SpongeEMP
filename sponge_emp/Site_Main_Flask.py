from io import TextIOWrapper, BytesIO
from collections import defaultdict
import operator
import urllib

from flask import Blueprint, request, render_template, redirect, g
import scipy.stats
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .utils import debug, get_fasta_seqs
from .sponge_emp import get_sequence_info

Site_Main_Flask_Obj = Blueprint('Site_Main_Flask_Obj', __name__, template_folder='templates')


@Site_Main_Flask_Obj.route('/', methods=['POST', 'GET'])
def landing_page():
    '''
    Redirect to the main search page
    '''
    # TODO: fix to non hard-coded
    return redirect('main')


@Site_Main_Flask_Obj.route('/main', methods=['POST', 'GET'])
def main_html():
    """
    Title: the main SpongeEMP page and search tool
    URL: site/main_html
    Method: GET
    """
    webPage = render_template('searchpage.html')
    return webPage


@Site_Main_Flask_Obj.route('/search_results', methods=['POST', 'GET'])
def search_results():
    """
    Title: Search results page
    URL: site/search_results
    Method: POST
    """
    db = g.db

    if request.method == 'GET':
        sequence = request.args['sequence']
    else:
        sequence = request.form['sequence']

    # if there is no sequence but a file attached, process the fasta file
    if sequence == '':
        if 'fasta file' in request.files:
            debug(1, 'Fasta file uploaded, processing it')
            file = request.files['fasta file']
            textfile = TextIOWrapper(file)
            seqs = get_fasta_seqs(textfile)
            if seqs is None:
                return('Error: Uploaded file not recognized as fasta\nPlease use <a href=https://en.wikipedia.org/wiki/FASTA_format>fasta</a> formatted files without ";" comment lines', 400)
            err, webpage = get_sequence_annotations(db, seqs)
            if err:
                return err, 400
            return webpage

    err, webPage = get_sequence_annotations(db, sequence)
    if err:
        return err, 400
    return webPage


@Site_Main_Flask_Obj.route('/sequence_annotations/<string:sequence>')
def get_sequence_annotations(db, sequence):
    '''Get annotations for a DNA sequence
    '''
    err, info = get_sequence_info(db, sequence, fields=None, threshold=0)
    if err:
        return err, ''
    desc = get_annotation_string(info)
    if isinstance(sequence, str):
        seqname = sequence
        taxonomy = db.get_taxonomy(sequence)
        # sometimes biom gives taxonomy as list and not string
        if isinstance(taxonomy, list):
            taxonomy = ';'.join(taxonomy)
    else:
        seqname = 'Set of %d sequences' % len(sequence)
        taxonomy = 'Set of %d sequences' % len(sequence)
    webPage = render_template('seqinfo.html', sequence=seqname, taxonomy=taxonomy)

    if isinstance(sequence, str):
        webPage += '<a href="http://dbbact.org/sequence_annotations/%s" target="_blank">More info from dbBact</a>' % sequence
        webPage += '<br>'

    total_observed = info['total_observed']
    total_samples = info['total_samples']

    webPage += 'Present in %f of samples (%d / %d)' % (total_observed/total_samples, total_observed, total_samples)
    webPage += '<br>'
    webPage += '<br>'

    if total_observed == 0:
        debug(2, 'sequence %s not found in database')
        webPage += 'Sequence Not observed in database'
        return '', webPage

    int_fields = ['host_scientific_name', 'env_feature', 'country']
    for idx, cfield in enumerate(int_fields):
        # draw the pie chart
        fdesc = get_annotation_string(info, field_name=cfield)
        # open by default the first entry
        if idx == 0:
            webPage += '<details open="open">\n'
        else:
            webPage += '<details>\n'
        webPage += '<summary>'
        webPage += '%s (%d significant)' % (cfield, len(fdesc))
        webPage += '</summary>\n'
        webPage += '<pre>\n'
        piechart_image = plot_pie_chart(info, cfield, min_size=0)
        webPage += render_template('imageplace.html', wordcloudimage=urllib.parse.quote(piechart_image))
        piechart_image_rel = plot_pie_chart(info, cfield, min_size=0, show_orig=True)
        webPage += render_template('imageplace.html', wordcloudimage=urllib.parse.quote(piechart_image_rel))
        webPage += '<br>'
        webPage += '<b>Significant enrichment:</b><br>'
        for cdesc in fdesc:
            webPage += cdesc + '<br>'
        webPage += '<br>'
        webPage += '</pre>\n'
        webPage += '</details>\n'

    webPage += '<details>\n'
    webPage += '<summary>'
    webPage += 'ALL (%d significant)' % len(desc)
    webPage += '</summary>\n'
    webPage += '<pre>\n'
    webPage += 'Significant enrichment:<br>'
    for cdesc in desc:
        webPage += cdesc + '<br>'
    webPage += '<br>'
    webPage += '</pre>\n'
    webPage += '</details>\n'
    webPage += "</body>"
    webPage += "</html>"
    return '', webPage


def get_annotation_string(info, pval=0.1, field_name=None):
    '''Get nice string summaries of annotations

    Parameters
    ----------
    info : dict (see get_sequence_annotations)
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
    pval : float
    field_name : str or None
        The field to get the statistics for
        None (default) is for all fields

    Returns
    -------
    desc : list of str
        a short summary of each annotation, sorted by importance
    '''
    keep = []
    total_observed = info['total_observed']
    if total_observed == 0:
        debug(2, 'sequence %s not found in database')
        return []
    total_samples = info['total_samples']
    null_pv = 1 - (total_observed / total_samples)
    if field_name is None:
        field_name = list(info['info'].keys())
    else:
        field_name = [field_name]
    for cfield in field_name:
        for cval, cdist in info['info'][cfield].items():
            observed_val_samples = cdist['observed_samples']
            total_val_samples = cdist['total_samples']
            cfrac = observed_val_samples / total_val_samples
            cpval = scipy.stats.binom.cdf(total_val_samples - observed_val_samples, total_val_samples, null_pv)
            if cpval <= pval:
                cdesc = '%s:%s (%d/%d)' % (cfield, cval, observed_val_samples, total_val_samples)
                keep.append([cdesc, cfrac, cpval])
    debug(1, 'found %d significant annotations' % len(keep))

    # sort first by p-value and then by fraction (so fraction is more important)
    keep = sorted(keep, key=operator.itemgetter(2), reverse=False)
    keep = sorted(keep, key=operator.itemgetter(1), reverse=True)
    desc = [ckeep[0] for ckeep in keep]
    # desc = ['Found in %f samples (%d / %d)' % (total_observed / total_samples, total_observed, total_samples)] + desc
    return desc


def plot_pie_chart(info, field, relative=False, show_orig=False, min_size=0):
    '''Plot a pie chart for number of observations in each of the field values

    Parameters
    ----------
    info :
    info : dict (see get_sequence_annotations)
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
    field : str
        The name of the field to plot the pie chart for
    relative : bool (optional)
        False (default) to plot absolute counts in pie chart.
        True to plot relative abundances in pie chart
    show_orig : bool (optional)
        True to show number of original samples instead of number where it is present
    min_size : int (optional)
        minimum number of observations of the otu in order to plot a separate slice. otherwise goes into 'Other'

    Returns
    -------
    '''
    nums = defaultdict(float)
    cinfo = info['info'][field]
    nums['~Other'] = 0
    for cval, cvinfo in cinfo.items():
        # if cvinfo['observed_samples'] == 0:
        #     continue
        if show_orig:
            cnum = cvinfo['total_samples']
        elif relative:
            cnum = 100 * cvinfo['observed_samples'] / cvinfo['total_samples']
        else:
            cnum = cvinfo['observed_samples']
        if cnum < min_size:
            cval = '~Other'
        nums[cval] += cnum
    if show_orig:
        nums['~Other'] += info['total_samples'] - np.sum(list(nums.values()))
    labels, x = zip(*sorted(nums.items(), key=lambda i: i[0], reverse=True))
    allsum = np.sum(x)
    x = list(x)
    labels = list(labels)
    for idx, cnum in enumerate(x):
        x[idx] = cnum / allsum
        if x[idx] < 0.01:
            labels[idx] = ''

    fig = plt.figure()
    a = plt.gca()
    a.pie(x, labels=labels)
    plt.axis("off")
    if show_orig:
        plt.title('Sample number distribution', fontsize=20)
    elif relative:
        plt.title('Relative abundance', fontsize=20)
    else:
        plt.title('Absolute abundance', fontsize=20)
    fig.tight_layout()
    figfile = BytesIO()
    fig.savefig(figfile, format='png', bbox_inches='tight')
    figfile.seek(0)  # rewind to beginning of file
    import base64
    figdata_png = base64.b64encode(figfile.getvalue())
    figfile.close()
    return figdata_png
