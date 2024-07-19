""" Utilities for dictionaries of data. """

from typing import Iterable

import numpy as np
from . import units


_DATA_DICT = dict[str, np.ndarray]
_RAD_STR = "_rad"
_DEG_STR = "_deg"


class SharedKeyError(Exception):
    pass


def dict_to_3d_array(results: dict[str, np.ndarray]) -> np.ndarray:
    """
    Convert a dictionary of 2d arrays into a 3d array

    This function is usefult for concatenating saved dictionarys of state
    or input data into a single array. The array is build by concatenating
    the individual arrays row-wise, maintaining the original ordering of
    the dictionary keys. For example for a dictionary of d entries, each containing
    a (m,n) array, this function will return a (d,m,n) array.

    Parameters
    ----------
    results: dict[str, np.ndarray]
        Dictionary containing a number of 2d numpy arrays

    Returns
    -------
    np.ndarray
        3d array of values

    """
    val_list = []
    for val in results.values():
        val_list.append(np.expand_dims(val.T, axis=0))

    return np.concatenate(val_list, axis=0)


def add_first_timestamps(data: _DATA_DICT) -> _DATA_DICT:
    """
    Add dictionary entry with first timestamp for each time array entry.

    The new key will be named "(pre)0(post)" where the original time signal was
    named "(pre)(post)". The first element of each row is assumed to be the initial
    timestamp.

    Parameters
    ----------
    data: _DATA_DICT
        Dictionary containing time signal values

    Returns
    -------
    _DATA_DICT
        Dictionary containing first timestamp and time signal values

    """
    out_dict = {}
    for key, val in data.items():
        elems = key.rsplit(sep="__")
        if len(elems) == 1:
            out_dict[f"{key}0"] = val[:, 0].reshape((-1, 1))
        else:
            base, idx = elems
            out_dict[f"{base}0__{idx}"] = val[:, 0].reshape((-1, 1))

    return out_dict | data


def add_si_base_keys_to_dict(data: _DATA_DICT) -> _DATA_DICT:
    """
    Convert all signals with an SI prefix to base units.

    Note
    ----
    See SI_PREFIX_LIST for acceptable prefixes.

    Parameters
    ----------
    data: _DATA_DICT
        Dictionary containing prefixed signal values

    Returns
    -------
    _DATA_DICT
        Dictionary containing prefixed and base signal values

    """
    out_dict = {}

    for key, val in data.items():
        new_val, new_key = units.si_prefix_to_base_from_str(name=key, value=val)
        out_dict[new_key] = new_val

    return out_dict | data


def add_deg_keys_from_rad(data: _DATA_DICT) -> _DATA_DICT:
    """
    Add degree signals for all radian signals.

    Note
    ----
    This function skips any signal containing an SI prefix.  Running
    convert_to_SI_base before calling this function is recommended.

    Parameters
    ----------
    data: _DATA_DICT
        Dictionary containing radian signal values

    Returns
    -------
    _DATA_DICT
        Dictionary containing radian and degree signal values

    """
    out_dict = {}
    for key, val in data.items():
        if _RAD_STR in key:
            out_dict[key.replace(_RAD_STR, _DEG_STR)] = np.degrees(val)
    return out_dict | data


def preprocess_data(data_tuple: tuple[_DATA_DICT]) -> _DATA_DICT:
    """
    Apply convert_to_SI_base and add_deg_from_rad to data.

    Parameters
    ----------
    data_tuple: tuple[_DATA_DICT]
        Tuple of data dictionaries

    Returns
    -------
    tuple[_DATA_DICT]
        Tuple with processed data dictionaries

    """
    new_data = []
    for elem in data_tuple:
        new_elem = add_si_base_keys_to_dict(elem)
        new_elem = add_deg_keys_from_rad(elem)
        new_data.append(new_elem)

    return new_data


def merge_dictionaries(dict_tuple: Iterable[_DATA_DICT]) -> _DATA_DICT:
    """
    Merge many dictionaries together into one.

    Raises
    ------
    SharedKeyError
        If any dictionaries share a common key

    Parameters
    ----------
    dict_tuple: Iterable[_DATA_DICT]
        Iterable of dictionaries to merge

    """
    set_list = [set(elem.keys()) for elem in dict_tuple]
    set_lengths = [len(elem) for elem in set_list]

    if not len(set.union(*set_list)) == sum(set_lengths):
        raise SharedKeyError("Two or more dictionaries share at least one key.")

    out_dict = {}
    for elem in dict_tuple:
        out_dict |= elem

    return out_dict
