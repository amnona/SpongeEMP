import sys
import inspect
import os.path


debuglevel = 2


def debug(level, msg):
    """
    print a debug message
    input:
    level : int
        error level (0=debug...10=critical)
    msg : str
        the debug message
    """
    global debuglevel

    if level >= debuglevel:
        print(msg, file=sys.stderr)


def SetDebugLevel(level):
    global debuglevel

    debuglevel = level


def getdoc(func):
    """
    return the json version of the doc for the function func
    input:
    func : function
        the function who's doc we want to return
    output:
    doc : str (html)
        the html of the doc of the function
    """
    print(func.__doc__)
    s = func.__doc__
    s = "<pre>\n%s\n</pre>" % s
    return(s)


def get_data_path(fn, subfolder='data'):
    """Return path to filename ``fn`` in the data folder.
    From skbio
    During testing it is often necessary to load data files. This
    function returns the full path to files in the ``data`` subfolder
    by default.
    Parameters
    ----------
    fn : str
        File name.
    subfolder : str, defaults to ``data``
        Name of the subfolder that contains the data.
    Returns
    -------
    str
        Inferred absolute path to the test data for the module where
        ``get_data_path(fn)`` is called.
    Notes
    -----
    The requested path may not point to an existing file, as its
    existence is not checked.
    """
    # getouterframes returns a list of tuples: the second tuple
    # contains info about the caller, and the second element is its
    # filename
    callers_filename = inspect.getouterframes(inspect.currentframe())[1][1]
    path = os.path.dirname(os.path.abspath(callers_filename))
    data_path = os.path.join(path, subfolder, fn)
    return data_path


def get_fasta_seqs(file):
    '''Get sequences from a fasta file

    Parameters
    ----------
    file : file or str
        the text fasta file to process.
        If str, it is the name of the file. If file, it is the io stream
        NOTE: file is closed after the read
    Returns
    -------
    seqs : list of str sequences (ACGT)
        the sequences in the fasta file
    '''
    debug(1, 'reading fasta file')
    try:
        if isinstance(file, str):
            debug(1, 'opening file %s' % file)
            file = open(file)

        seqs = []
        cseq = ''
        isfasta = False
        for cline in file:
            cline = cline.strip()
            if cline[0] == '>':
                isfasta = True
                if cseq:
                    seqs.append(cseq)
                cseq = ''
            else:
                cseq += cline
        # process the last sequence
        if cseq:
            seqs.append(cseq)

        file.close()

        # test if we encountered '>'
        if not isfasta:
            debug(2, 'not a fasta file')
            return None

        debug(1, 'read %d sequences' % len(seqs))
        return seqs
    except:
        debug(3, 'fasta file read failed. error encountered')
        return None
