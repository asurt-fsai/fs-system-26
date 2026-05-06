# generated from rosidl_generator_py/resource/_idl.py.em
# with input from asurt_msgs:msg/ConeImgArray.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_ConeImgArray(type):
    """Metaclass of message 'ConeImgArray'."""

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
                'asurt_msgs.msg.ConeImgArray')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__cone_img_array
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__cone_img_array
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__cone_img_array
            cls._TYPE_SUPPORT = module.type_support_msg__msg__cone_img_array
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__cone_img_array

            from asurt_msgs.msg import ConeImg
            if ConeImg.__class__._TYPE_SUPPORT is None:
                ConeImg.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class ConeImgArray(metaclass=Metaclass_ConeImgArray):
    """Message class 'ConeImgArray'."""

    __slots__ = [
        '_frame_id',
        '_object_count',
        '_imgs',
    ]

    _fields_and_field_types = {
        'frame_id': 'uint32',
        'object_count': 'uint16',
        'imgs': 'sequence<asurt_msgs/ConeImg>',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('uint16'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.NamespacedType(['asurt_msgs', 'msg'], 'ConeImg')),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.frame_id = kwargs.get('frame_id', int())
        self.object_count = kwargs.get('object_count', int())
        self.imgs = kwargs.get('imgs', [])

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
        if self.frame_id != other.frame_id:
            return False
        if self.object_count != other.object_count:
            return False
        if self.imgs != other.imgs:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def frame_id(self):
        """Message field 'frame_id'."""
        return self._frame_id

    @frame_id.setter
    def frame_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'frame_id' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'frame_id' field must be an unsigned integer in [0, 4294967295]"
        self._frame_id = value

    @builtins.property
    def object_count(self):
        """Message field 'object_count'."""
        return self._object_count

    @object_count.setter
    def object_count(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'object_count' field must be of type 'int'"
            assert value >= 0 and value < 65536, \
                "The 'object_count' field must be an unsigned integer in [0, 65535]"
        self._object_count = value

    @builtins.property
    def imgs(self):
        """Message field 'imgs'."""
        return self._imgs

    @imgs.setter
    def imgs(self, value):
        if __debug__:
            from asurt_msgs.msg import ConeImg
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
                 all(isinstance(v, ConeImg) for v in value) and
                 True), \
                "The 'imgs' field must be a set or sequence and each value of type 'ConeImg'"
        self._imgs = value
