# generated from rosidl_generator_py/resource/_idl.py.em
# with input from asurt_msgs:msg/Landmark.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_Landmark(type):
    """Metaclass of message 'Landmark'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
        'BLUE_CONE': 0,
        'YELLOW_CONE': 1,
        'ORANGE_CONE': 2,
        'LARGE_CONE': 3,
        'CONE_TYPE_UNKNOWN': 4,
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
                'asurt_msgs.msg.Landmark')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__landmark
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__landmark
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__landmark
            cls._TYPE_SUPPORT = module.type_support_msg__msg__landmark
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__landmark

            from geometry_msgs.msg import Point
            if Point.__class__._TYPE_SUPPORT is None:
                Point.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
            'BLUE_CONE': cls.__constants['BLUE_CONE'],
            'YELLOW_CONE': cls.__constants['YELLOW_CONE'],
            'ORANGE_CONE': cls.__constants['ORANGE_CONE'],
            'LARGE_CONE': cls.__constants['LARGE_CONE'],
            'CONE_TYPE_UNKNOWN': cls.__constants['CONE_TYPE_UNKNOWN'],
        }

    @property
    def BLUE_CONE(self):
        """Message constant 'BLUE_CONE'."""
        return Metaclass_Landmark.__constants['BLUE_CONE']

    @property
    def YELLOW_CONE(self):
        """Message constant 'YELLOW_CONE'."""
        return Metaclass_Landmark.__constants['YELLOW_CONE']

    @property
    def ORANGE_CONE(self):
        """Message constant 'ORANGE_CONE'."""
        return Metaclass_Landmark.__constants['ORANGE_CONE']

    @property
    def LARGE_CONE(self):
        """Message constant 'LARGE_CONE'."""
        return Metaclass_Landmark.__constants['LARGE_CONE']

    @property
    def CONE_TYPE_UNKNOWN(self):
        """Message constant 'CONE_TYPE_UNKNOWN'."""
        return Metaclass_Landmark.__constants['CONE_TYPE_UNKNOWN']


class Landmark(metaclass=Metaclass_Landmark):
    """
    Message class 'Landmark'.

    Constants:
      BLUE_CONE
      YELLOW_CONE
      ORANGE_CONE
      LARGE_CONE
      CONE_TYPE_UNKNOWN
    """

    __slots__ = [
        '_position',
        '_type',
        '_identifier',
        '_probability',
    ]

    _fields_and_field_types = {
        'position': 'geometry_msgs/Point',
        'type': 'uint32',
        'identifier': 'int32',
        'probability': 'double',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['geometry_msgs', 'msg'], 'Point'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from geometry_msgs.msg import Point
        self.position = kwargs.get('position', Point())
        self.type = kwargs.get('type', int())
        self.identifier = kwargs.get('identifier', int())
        self.probability = kwargs.get('probability', float())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
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
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.position != other.position:
            return False
        if self.type != other.type:
            return False
        if self.identifier != other.identifier:
            return False
        if self.probability != other.probability:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def position(self):
        """Message field 'position'."""
        return self._position

    @position.setter
    def position(self, value):
        if __debug__:
            from geometry_msgs.msg import Point
            assert \
                isinstance(value, Point), \
                "The 'position' field must be a sub message of type 'Point'"
        self._position = value

    @builtins.property  # noqa: A003
    def type(self):  # noqa: A003
        """Message field 'type'."""
        return self._type

    @type.setter  # noqa: A003
    def type(self, value):  # noqa: A003
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'type' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'type' field must be an unsigned integer in [0, 4294967295]"
        self._type = value

    @builtins.property
    def identifier(self):
        """Message field 'identifier'."""
        return self._identifier

    @identifier.setter
    def identifier(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'identifier' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'identifier' field must be an integer in [-2147483648, 2147483647]"
        self._identifier = value

    @builtins.property
    def probability(self):
        """Message field 'probability'."""
        return self._probability

    @probability.setter
    def probability(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'probability' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'probability' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._probability = value
