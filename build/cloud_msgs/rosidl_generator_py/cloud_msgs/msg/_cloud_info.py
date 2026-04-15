# generated from rosidl_generator_py/resource/_idl.py.em
# with input from cloud_msgs:msg/CloudInfo.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

# Member 'start_ring_index'
# Member 'end_ring_index'
# Member 'segmented_cloud_col_ind'
# Member 'segmented_cloud_range'
import array  # noqa: E402, I100

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_CloudInfo(type):
    """Metaclass of message 'CloudInfo'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('cloud_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'cloud_msgs.msg.CloudInfo')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__cloud_info
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__cloud_info
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__cloud_info
            cls._TYPE_SUPPORT = module.type_support_msg__msg__cloud_info
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__cloud_info

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class CloudInfo(metaclass=Metaclass_CloudInfo):
    """Message class 'CloudInfo'."""

    __slots__ = [
        '_header',
        '_start_ring_index',
        '_end_ring_index',
        '_start_orientation',
        '_end_orientation',
        '_orientation_diff',
        '_segmented_cloud_ground_flag',
        '_segmented_cloud_col_ind',
        '_segmented_cloud_range',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'start_ring_index': 'sequence<int32>',
        'end_ring_index': 'sequence<int32>',
        'start_orientation': 'float',
        'end_orientation': 'float',
        'orientation_diff': 'float',
        'segmented_cloud_ground_flag': 'sequence<boolean>',
        'segmented_cloud_col_ind': 'sequence<uint32>',
        'segmented_cloud_range': 'sequence<float>',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('int32')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('int32')),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('boolean')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint32')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('float')),  # noqa: E501
    )

    def __init__(self, **kwargs):
        if 'check_fields' in kwargs:
            self._check_fields = kwargs['check_fields']
        else:
            self._check_fields = ros_python_check_fields == '1'
        if self._check_fields:
            assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
                'Invalid arguments passed to constructor: %s' % \
                ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.start_ring_index = array.array('i', kwargs.get('start_ring_index', []))
        self.end_ring_index = array.array('i', kwargs.get('end_ring_index', []))
        self.start_orientation = kwargs.get('start_orientation', float())
        self.end_orientation = kwargs.get('end_orientation', float())
        self.orientation_diff = kwargs.get('orientation_diff', float())
        self.segmented_cloud_ground_flag = kwargs.get('segmented_cloud_ground_flag', [])
        self.segmented_cloud_col_ind = array.array('I', kwargs.get('segmented_cloud_col_ind', []))
        self.segmented_cloud_range = array.array('f', kwargs.get('segmented_cloud_range', []))

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.get_fields_and_field_types().keys(), self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    if self._check_fields:
                        assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.header != other.header:
            return False
        if self.start_ring_index != other.start_ring_index:
            return False
        if self.end_ring_index != other.end_ring_index:
            return False
        if self.start_orientation != other.start_orientation:
            return False
        if self.end_orientation != other.end_orientation:
            return False
        if self.orientation_diff != other.orientation_diff:
            return False
        if self.segmented_cloud_ground_flag != other.segmented_cloud_ground_flag:
            return False
        if self.segmented_cloud_col_ind != other.segmented_cloud_col_ind:
            return False
        if self.segmented_cloud_range != other.segmented_cloud_range:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if self._check_fields:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @builtins.property
    def start_ring_index(self):
        """Message field 'start_ring_index'."""
        return self._start_ring_index

    @start_ring_index.setter
    def start_ring_index(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'i', \
                    "The 'start_ring_index' array.array() must have the type code of 'i'"
                self._start_ring_index = value
                return
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, int) for v in value) and
                 all(val >= -2147483648 and val < 2147483648 for val in value)), \
                "The 'start_ring_index' field must be a set or sequence and each value of type 'int' and each integer in [-2147483648, 2147483647]"
        self._start_ring_index = array.array('i', value)

    @builtins.property
    def end_ring_index(self):
        """Message field 'end_ring_index'."""
        return self._end_ring_index

    @end_ring_index.setter
    def end_ring_index(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'i', \
                    "The 'end_ring_index' array.array() must have the type code of 'i'"
                self._end_ring_index = value
                return
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, int) for v in value) and
                 all(val >= -2147483648 and val < 2147483648 for val in value)), \
                "The 'end_ring_index' field must be a set or sequence and each value of type 'int' and each integer in [-2147483648, 2147483647]"
        self._end_ring_index = array.array('i', value)

    @builtins.property
    def start_orientation(self):
        """Message field 'start_orientation'."""
        return self._start_orientation

    @start_orientation.setter
    def start_orientation(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'start_orientation' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'start_orientation' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._start_orientation = value

    @builtins.property
    def end_orientation(self):
        """Message field 'end_orientation'."""
        return self._end_orientation

    @end_orientation.setter
    def end_orientation(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'end_orientation' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'end_orientation' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._end_orientation = value

    @builtins.property
    def orientation_diff(self):
        """Message field 'orientation_diff'."""
        return self._orientation_diff

    @orientation_diff.setter
    def orientation_diff(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'orientation_diff' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'orientation_diff' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._orientation_diff = value

    @builtins.property
    def segmented_cloud_ground_flag(self):
        """Message field 'segmented_cloud_ground_flag'."""
        return self._segmented_cloud_ground_flag

    @segmented_cloud_ground_flag.setter
    def segmented_cloud_ground_flag(self, value):
        if self._check_fields:
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, bool) for v in value) and
                 True), \
                "The 'segmented_cloud_ground_flag' field must be a set or sequence and each value of type 'bool'"
        self._segmented_cloud_ground_flag = value

    @builtins.property
    def segmented_cloud_col_ind(self):
        """Message field 'segmented_cloud_col_ind'."""
        return self._segmented_cloud_col_ind

    @segmented_cloud_col_ind.setter
    def segmented_cloud_col_ind(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'I', \
                    "The 'segmented_cloud_col_ind' array.array() must have the type code of 'I'"
                self._segmented_cloud_col_ind = value
                return
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, int) for v in value) and
                 all(val >= 0 and val < 4294967296 for val in value)), \
                "The 'segmented_cloud_col_ind' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 4294967295]"
        self._segmented_cloud_col_ind = array.array('I', value)

    @builtins.property
    def segmented_cloud_range(self):
        """Message field 'segmented_cloud_range'."""
        return self._segmented_cloud_range

    @segmented_cloud_range.setter
    def segmented_cloud_range(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'f', \
                    "The 'segmented_cloud_range' array.array() must have the type code of 'f'"
                self._segmented_cloud_range = value
                return
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, float) for v in value) and
                 all(not (val < -3.402823466e+38 or val > 3.402823466e+38) or math.isinf(val) for val in value)), \
                "The 'segmented_cloud_range' field must be a set or sequence and each value of type 'float' and each float in [-340282346600000016151267322115014000640.000000, 340282346600000016151267322115014000640.000000]"
        self._segmented_cloud_range = array.array('f', value)
