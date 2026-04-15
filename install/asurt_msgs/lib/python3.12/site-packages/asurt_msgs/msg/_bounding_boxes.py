# generated from rosidl_generator_py/resource/_idl.py.em
# with input from asurt_msgs:msg/BoundingBoxes.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_BoundingBoxes(type):
    """Metaclass of message 'BoundingBoxes'."""

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
                'asurt_msgs.msg.BoundingBoxes')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__bounding_boxes
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__bounding_boxes
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__bounding_boxes
            cls._TYPE_SUPPORT = module.type_support_msg__msg__bounding_boxes
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__bounding_boxes

            from asurt_msgs.msg import BoundingBox
            if BoundingBox.__class__._TYPE_SUPPORT is None:
                BoundingBox.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class BoundingBoxes(metaclass=Metaclass_BoundingBoxes):
    """Message class 'BoundingBoxes'."""

    __slots__ = [
        '_view_id',
        '_object_count',
        '_bounding_boxes',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'view_id': 'string',
        'object_count': 'uint16',
        'bounding_boxes': 'sequence<asurt_msgs/BoundingBox>',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.NamespacedType(['asurt_msgs', 'msg'], 'BoundingBox')),  # noqa: E501
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
        self.view_id = kwargs.get('view_id', str())
        self.object_count = kwargs.get('object_count', int())
        self.bounding_boxes = kwargs.get('bounding_boxes', [])

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
        if self.bounding_boxes != other.bounding_boxes:
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
                isinstance(value, str), \
                "The 'view_id' field must be of type 'str'"
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
    def bounding_boxes(self):
        """Message field 'bounding_boxes'."""
        return self._bounding_boxes

    @bounding_boxes.setter
    def bounding_boxes(self, value):
        if self._check_fields:
            from asurt_msgs.msg import BoundingBox
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
                 all(isinstance(v, BoundingBox) for v in value) and
                 True), \
                "The 'bounding_boxes' field must be a set or sequence and each value of type 'BoundingBox'"
        self._bounding_boxes = value
