# generated from rosidl_generator_py/resource/_idl.py.em
# with input from asurt_msgs:msg/KeyPoints.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

# Member 'track_ids'
# Member 'classes'
# Member 'keypoints'
import array  # noqa: E402, I100

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_KeyPoints(type):
    """Metaclass of message 'KeyPoints'."""

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
            module = import_type_support('asurt_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'asurt_msgs.msg.KeyPoints')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__key_points
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__key_points
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__key_points
            cls._TYPE_SUPPORT = module.type_support_msg__msg__key_points
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__key_points

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class KeyPoints(metaclass=Metaclass_KeyPoints):
    """Message class 'KeyPoints'."""

    __slots__ = [
        '_view_id',
        '_object_count',
        '_track_ids',
        '_classes',
        '_keypoints',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'view_id': 'uint32',
        'object_count': 'uint16',
        'track_ids': 'sequence<uint8>',
        'classes': 'sequence<uint8>',
        'keypoints': 'sequence<uint16>',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint8')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint8')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint16')),  # noqa: E501
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
        self.view_id = kwargs.get('view_id', int())
        self.object_count = kwargs.get('object_count', int())
        self.track_ids = array.array('B', kwargs.get('track_ids', []))
        self.classes = array.array('B', kwargs.get('classes', []))
        self.keypoints = array.array('H', kwargs.get('keypoints', []))

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
        if self.view_id != other.view_id:
            return False
        if self.object_count != other.object_count:
            return False
        if self.track_ids != other.track_ids:
            return False
        if self.classes != other.classes:
            return False
        if self.keypoints != other.keypoints:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def view_id(self):
        """Message field 'view_id'."""
        return self._view_id

    @view_id.setter
    def view_id(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'view_id' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'view_id' field must be an unsigned integer in [0, 4294967295]"
        self._view_id = value

    @builtins.property
    def object_count(self):
        """Message field 'object_count'."""
        return self._object_count

    @object_count.setter
    def object_count(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'object_count' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'object_count' field must be an unsigned integer in [0, 65535]"
        self._object_count = value

    @builtins.property
    def track_ids(self):
        """Message field 'track_ids'."""
        return self._track_ids

    @track_ids.setter
    def track_ids(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'B', \
                    "The 'track_ids' array.array() must have the type code of 'B'"
                self._track_ids = value
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
                 all(val >= 0 and val < 256 for val in value)), \
                "The 'track_ids' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 255]"
        self._track_ids = array.array('B', value)

    @builtins.property
    def classes(self):
        """Message field 'classes'."""
        return self._classes

    @classes.setter
    def classes(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'B', \
                    "The 'classes' array.array() must have the type code of 'B'"
                self._classes = value
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
                 all(val >= 0 and val < 256 for val in value)), \
                "The 'classes' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 255]"
        self._classes = array.array('B', value)

    @builtins.property
    def keypoints(self):
        """Message field 'keypoints'."""
        return self._keypoints

    @keypoints.setter
    def keypoints(self, value):
        if self._check_fields:
            if isinstance(value, array.array):
                assert value.typecode == 'H', \
                    "The 'keypoints' array.array() must have the type code of 'H'"
                self._keypoints = value
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
                 all(val >= 0 and val < 65536 for val in value)), \
                "The 'keypoints' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 65535]"
        self._keypoints = array.array('H', value)
