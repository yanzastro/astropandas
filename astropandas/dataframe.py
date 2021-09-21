import sys

import numpy as np
import pandas as pd
try:
    import fitsio
    _FITSIO = True
except ImportError:
    import astropy.io
    _FITSIO = False

from .match import Matcher


def _convert_byteorder(data):
    dtype = data.dtype
    # check if the byte order matches the native order, identified by the
    # numpy dtype string representation: little endian = "<" and
    # big endian = ">"
    if dtype.str.startswith(("<", ">")):
        if sys.byteorder == "little":
            dtype = np.dtype("<" + dtype.base.str.strip("><"))
        elif sys.byteorder == "big":
            dtype = np.dtype(">" + dtype.base.str.strip("><"))
    return data.astype(dtype, casting="equiv", copy=False)


def read_fits(fpath, cols=None, hdu=1):
    """
    Read a FITS data table into a pandas.DataFrame.

    Parameters:
    -----------
    fpath : str
        Path to the FITS file.
    hdu : int (optional)
        Index of the extension to read from the FITS file, defaults to 1.
    columns : list of str (optional)
        Subset of columns to read from the table, defaults to all.
    
    Returns:
        df : pandas.DataFrame
            Table data converted to a DataFrame instance.
    """
    # load the FITS data
    if _FITSIO:
        fits = fitsio.FITS(fpath)
        if cols is None:
            data = fits[hdu][:]
        else:
            data = fits[hdu][cols][:]
        fits.close()
    else:
        with astropy.io.fits.open(fpath) as fits:
            if cols is None:
                data = fits[hdu]
            else:
                data = fits[hdu][cols]
    # construct the data frame
    df = pd.DataFrame(data={
        colname: _convert_byteorder(data[colname])
        for colname, _ in data.dtype.fields.items()})
    return df


def to_fits(df, fpath):
    """
    Write a pandas.DataFrame as FITS table file.

    Parameters:
    -----------
    df : pandas.DataFrame
        Data frame to write as FITS table.
    fpath : str
        Path to the FITS file.
    """
    # load the FITS data
    if _FITSIO:
        dtype = np.dtype(list(df.dtypes.items()))
        array = np.empty(len(df), dtype=dtype)
        for column in df.columns:
            array[column] = df[column]
        with fitsio.FITS(fpath, "rw") as fits:
            fits.write(array)
    else:
        columns = [
            astropy.io.fits.Column(name=col, array=df[col])
            for col in df.columns]
        hdu = astropy.io.fits.BinTableHDU.from_columns(columns)
        hdu.writeto(fpath)
