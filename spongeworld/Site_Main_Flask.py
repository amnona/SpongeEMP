from io import TextIOWrapper, BytesIO
from collections import defaultdict
import operator
import urllib

from flask import Blueprint, request, render_template, redirect, g
import scipy.stats
import matplotlib.pyplot as plt

from .utils import debug, get_fasta_seqs
from .spongeworld import get_sequence_info

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
    Title: the main SpongeWorld page and search tool
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
                return('Error: Uploaded file not recognized as fasta', 400)
            err, webpage = get_sequence_annotations(db, seqs, relpath='')
            if err:
                return err, 400
            return webpage

    # if it is short, try if it is taxonomy
        # err, webPage = get_taxonomy_info(sequence, relpath='')
        # if not err:
        #     return webPage
        # return('term %s not found in ontology or taxonomy' % sequence, 400)

    err, webPage = get_sequence_annotations(db, sequence, relpath='')
    if err:
        return err, 400
    return webPage


@Site_Main_Flask_Obj.route('/sequence_annotations/<string:sequence>')
def get_sequence_annotations(db, sequence, relpath='../'):
    '''Get annotations for a DNA sequence
    '''
    err, info = get_sequence_info(db, sequence, fields=None, threshold=0)
    if err:
        return err, ''
    desc = get_annotation_string(info)
    webPage = render_template('seqinfo.html', sequence=sequence)
    if isinstance(sequence, str):
        webPage += 'Taxonomy: %s <br>' % db.get_taxonomy(sequence)
    webPage += '<br>'

    # draw the pie chart
    piechart_image = plot_pie_chart(info, 'host_common_name')
    webPage += render_template('imageplace.html', wordcloudimage=urllib.parse.quote(piechart_image))

    for cdesc in desc:
        webPage += cdesc + '<br>'
    webPage += "</body>"
    webPage += "</html>"
    return '', webPage


def get_annotation_string(info, pval=0.1):
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
    for cfield in info['info'].keys():
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
    desc = ['Found in %f samples (%d / %d)' % (total_observed / total_samples, total_observed, total_samples)] + desc
    return desc


def plot_pie_chart(info, field, relative=False, min_size=0):
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
    min_size : int (optional)
        minimum number of observations of the otu in order to plot a separate slice. otherwise goes into 'Other'

    Returns
    -------
    '''
    nums = defaultdict(float)
    cinfo = info['info'][field]
    for cval, cvinfo in cinfo.items():
        if cvinfo['observed_samples'] == 0:
            continue
        if relative:
            cnum = 100 * cvinfo['observed_samples'] / cvinfo['total_samples']
        else:
            cnum = cvinfo['observed_samples']
        if cnum < min_size:
            cval = 'Other'
        nums[cval] += cnum
    labels, x = zip(*sorted(nums.items(), key=lambda x: x[1]))

    fig = plt.figure()
    a = plt.gca()
    a.pie(x, labels=labels)
    plt.axis("off")
    fig.tight_layout()
    figfile = BytesIO()
    fig.savefig(figfile, format='png', bbox_inches='tight')
    figfile.seek(0)  # rewind to beginning of file
    import base64
    figdata_png = base64.b64encode(figfile.getvalue())
    figfile.close()
    return figdata_png
