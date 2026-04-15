# generated from rosidl_generator_py/resource/_idl.py.em
# with input from asurt_msgs:msg/BoundingBox.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_BoundingBox(type):
    """Metaclass of message 'BoundingBox'."""

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
                'asurt_msgs.msg.BoundingBox')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__bounding_box
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__bounding_box
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__bounding_box
            cls._TYPE_SUPPORT = module.type_support_msg__msg__bounding_box
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__bounding_box

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class BoundingBox(metaclass=Metaclass_BoundingBox):
    """Message class 'BoundingBox'."""

    __slots__ = [
        '_probability',
        '_xmin',
        '_ymin',
        '_xmax',
        '_ymax',
        '_x_center',
        '_y_center',
        '_width',
        '_height',
        '_detection_id',
        '_track_id',
        '_type',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'probability': 'float',
        'xmin': 'uint16',
        'ymin': 'uint16',
        'xmax': 'uint16',
        'ymax': 'uint16',
        'x_center': 'uint16',
        'y_center': 'uint16',
        'width': 'uint16',
        'height': 'uint16',
        'detection_id': 'uint16',
        'track_id': 'uint16',
        'type': 'uint8',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint8'),  # noqa: E501
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
        self.probability = kwargs.get('probability', float())
        self.xmin = kwargs.get('xmin', int())
        self.ymin = kwargs.get('ymin', int())
        self.xmax = kwargs.get('xmax', int())
        self.ymax = kwargs.get('ymax', int())
        self.x_center = kwargs.get('x_center', int())
        self.y_center = kwargs.get('y_center', int())
        self.width = kwargs.get('width', int())
        self.height = kwargs.get('height', int())
        self.detection_id = kwargs.get('detection_id', int())
        self.track_id = kwargs.get('track_id', int())
        self.type = kwargs.get('type', int())

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
        if self.probability != other.probability:
            return False
        if self.xmin != other.xmin:
            return False
        if self.ymin != other.ymin:
            return False
        if self.xmax != other.xmax:
            return False
        if self.ymax != other.ymax:
            return False
        if self.x_center != other.x_center:
            return False
        if self.y_center != other.y_center:
            return False
        if self.width != other.width:
            return False
        if self.height != other.height:
            return False
        if self.detection_id != other.detection_id:
            return False
        if self.track_id != other.track_id:
            return False
        if self.type != other.type:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def probability(self):
        """Message field 'probability'."""
        return self._probability

    @probability.setter
    def probability(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'probability' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'probability' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._probability = value

    @builtins.property
    def xmin(self):
        """Message field 'xmin'."""
        return self._xmin

    @xmin.setter
    def xmin(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'xmin' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'xmin' field must be an unsigned integer in [0, 65535]"
        self._xmin = value

    @builtins.property
    def ymin(self):
        """Message field 'ymin'."""
        return self._ymin

    @ymin.setter
    def ymin(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'ymin' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'ymin' field must be an unsigned integer in [0, 65535]"
        self._ymin = value

    @builtins.property
    def xmax(self):
        """Message field 'xmax'."""
        return self._xmax

    @xmax.setter
    def xmax(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'xmax' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'xmax' field must be an unsigned integer in [0, 65535]"
        self._xmax = value

    @builtins.property
    def ymax(self):
        """Message field 'ymax'."""
        return self._ymax

    @ymax.setter
    def ymax(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'ymax' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'ymax' field must be an unsigned integer in [0, 65535]"
        self._ymax = value

    @builtins.property
    def x_center(self):
        """Message field 'x_center'."""
        return self._x_center

    @x_center.setter
    def x_center(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'x_center' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'x_center' field must be an unsigned integer in [0, 65535]"
        self._x_center = value

    @builtins.property
    def y_center(self):
        """Message field 'y_center'."""
        return self._y_center

    @y_center.setter
    def y_center(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'y_center' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'y_center' field must be an unsigned integer in [0, 65535]"
        self._y_center = value

    @builtins.property
    def width(self):
        """Message field 'width'."""
        return self._width

    @width.setter
    def width(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'width' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'width' field must be an unsigned integer in [0, 65535]"
        self._width = value

    @builtins.property
    def height(self):
        """Message field 'height'."""
        return self._height

    @height.setter
    def height(self, value):
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'height' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'height' field must be an unsigned integer in [0, 65535]"
        self._height = value

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

    @builtins.property  # noqa: A003
    def type(self):  # noqa: A003
        """Message field 'type'."""
        return self._type

    @type.setter  # noqa: A003
    def type(self, value):  # noqa: A003
        if self._check_fields:
            assert \
                isinstance(value, int), \
                "The 'type' field must be of type 'int'"
            assert value >= 0 and value < 256, \
                "The 'type' field must be an unsigned integer in [0, 255]"
        self._type = value
