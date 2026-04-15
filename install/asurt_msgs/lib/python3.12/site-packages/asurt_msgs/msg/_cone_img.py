# generated from rosidl_generator_py/resource/_idl.py.em
# with input from asurt_msgs:msg/ConeImg.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_ConeImg(type):
    """Metaclass of message 'ConeImg'."""

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
                'asurt_msgs.msg.ConeImg')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__cone_img
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__cone_img
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__cone_img
            cls._TYPE_SUPPORT = module.type_support_msg__msg__cone_img
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__cone_img

            from sensor_msgs.msg import Image
            if Image.__class__._TYPE_SUPPORT is None:
                Image.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class ConeImg(metaclass=Metaclass_ConeImg):
    """Message class 'ConeImg'."""

    __slots__ = [
        '_detection_id',
        '_rows',
        '_cols',
        '_img',
        '_track_id',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'detection_id': 'uint16',
        'rows': 'uint16',
        'cols': 'uint16',
        'img': 'sensor_msgs/Image',
        'track_id': 'uint16',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['sensor_msgs', 'msg'], 'Image'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
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
        self.detection_id = kwargs.get('detection_id', int())
        self.rows = kwargs.get('rows', int())
        self.cols = kwargs.get('cols', int())
        from sensor_msgs.msg import Image
        self.img = kwargs.get('img', Image())
        self.track_id = kwargs.get('track_id', int())

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
        if self.detection_id != other.detection_id:
            return False
        if self.rows != other.rows:
            return False
        if self.cols != other.cols:
            return False
        if self.img != other.img:
            return False
        if self.track_id != other.track_id:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def detection_id(self):
        """Message field 'detection_id'."""
        return self._detection_id

    @detection_id.setter
    def detection_id(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'detection_id' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'detection_id' field must be an unsigned integer in [0, 65535]"
        self._detection_id = value

    @builtins.property
    def rows(self):
        """Message field 'rows'."""
        return self._rows

    @rows.setter
    def rows(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'rows' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'rows' field must be an unsigned integer in [0, 65535]"
        self._rows = value

    @builtins.property
    def cols(self):
        """Message field 'cols'."""
        return self._cols

    @cols.setter
    def cols(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'cols' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'cols' field must be an unsigned integer in [0, 65535]"
        self._cols = value

    @builtins.property
    def img(self):
        """Message field 'img'."""
        return self._img

    @img.setter
    def img(self, value):
        if self._check_fields:
            from sensor_msgs.msg import Image
            assert \
                isinstance(value, Image), \
                "The 'img' field must be a sub message of type 'Image'"
        self._img = value

    @builtins.property
    def track_id(self):
        """Message field 'track_id'."""
        return self._track_id

    @track_id.setter
    def track_id(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'track_id' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'track_id' field must be an unsigned integer in [0, 65535]"
        self._track_id = value
