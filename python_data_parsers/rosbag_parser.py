import array
from numbers import Number
from pathlib import Path
from typing import Any

import numpy as np
import rosbag2_py
from ndarray import conversion
from ndarray_msgs.msg import NDArray
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from std_msgs.msg import Header

PACKAGE_DIR = Path(__file__).parent.parent
ROSBAG_DIR = PACKAGE_DIR.joinpath("rosbags")


def squeeze_numpy_fields(in_dict: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    for key, value in in_dict.items():
        in_dict[key] = value.squeeze()

    return in_dict


def parse_scalar(value: Number, in_array: np.ndarray) -> np.ndarray:
    if in_array is None:
        return np.array([value])

    return np.append(in_array, value)


def parse_time_stamp(header: Header, in_array: np.ndarray) -> np.ndarray:
    secs = header.stamp.sec
    nsecs = header.stamp.nanosec
    stamp = secs + (nsecs * 1e-9)

    return parse_scalar(stamp, in_array=in_array)


def parse_array(value_array: array.array, in_array: np.ndarray) -> np.ndarray:
    np_array = np.array(value_array)

    if in_array is None and np_array.size == 0:
        return None
    elif in_array is None:
        return np_array
    elif np_array.size == 0:
        np_array = -1717.0 * np.ones(in_array.shape[1:])

    return np.row_stack((in_array, np_array))


def parse_ndarray(value_ndarray: NDArray, in_ndarray: np.ndarray) -> np.ndarray:
    np_array = conversion.msg_to_array(value_ndarray)

    if in_ndarray is None and np_array.size == 0:
        return None
    if in_ndarray is None:
        return np_array[np.newaxis, ...]
    elif np_array.size == 0:
        np_array = -1717.0 * np.ones(in_ndarray.shape[1:])

    return np.append(in_ndarray, np_array[np.newaxis, ...], axis=0)


def parse_message(msg, in_dict: dict[str, Any]) -> dict[str, Any]:
    if in_dict is None:
        in_dict = {}

    for field in msg.get_fields_and_field_types().keys():
        raw_val = getattr(msg, field)
        old_entry = in_dict.get(field, None)

        if isinstance(raw_val, Header):
            field = "stamp_s"
            old_entry = in_dict.get(field, None)
            val = parse_time_stamp(header=raw_val, in_array=old_entry)
        elif isinstance(raw_val, Number):
            val = parse_scalar(value=raw_val, in_array=old_entry)
        elif isinstance(raw_val, array.array):
            val = parse_array(value_array=raw_val, in_array=old_entry)
        elif isinstance(raw_val, NDArray):
            val = parse_ndarray(value_ndarray=raw_val, in_ndarray=old_entry)
        else:
            val = parse_message(raw_val, old_entry)

        in_dict[field] = val

    return in_dict


def parse_topics(
    storage_opts: rosbag2_py.StorageOptions,
    converter_opts: rosbag2_py.ConverterOptions,
) -> dict[str, dict[str, Any]]:
    reader = rosbag2_py.SequentialReader()
    reader.open(storage_opts, converter_opts)

    topic_types = reader.get_all_topics_and_types()
    type_map = {topic.name: topic.type for topic in topic_types}

    ros_data_dict = {}

    while reader.has_next():
        topic, data, _ = reader.read_next()

        msg_type = get_message(type_map[topic])
        msg = deserialize_message(data, msg_type)

        try:
            ros_data_dict[topic] = parse_message(msg=msg, in_dict=ros_data_dict[topic])
        except KeyError:
            ros_data_dict[topic] = parse_message(msg=msg, in_dict={})

    return ros_data_dict


def parse_rosbag(rosbag_path: Path) -> dict[str, dict]:
    storage_options = rosbag2_py.StorageOptions(
        uri=str(rosbag_path), storage_id="sqlite3"
    )

    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr",
        output_serialization_format="cdr",
    )

    return parse_topics(
        storage_opts=storage_options,
        converter_opts=converter_options,
    )
