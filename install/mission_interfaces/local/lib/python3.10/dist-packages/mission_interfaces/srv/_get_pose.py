# generated from rosidl_generator_py/resource/_idl.py.em
# with input from mission_interfaces:srv/GetPose.idl
# generated code does not contain a copyright notice


# Import statements for member types

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_GetPose_Request(type):
    """Metaclass of message 'GetPose_Request'."""

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
            module = import_type_support('mission_interfaces')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'mission_interfaces.srv.GetPose_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__get_pose__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__get_pose__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__get_pose__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__get_pose__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__get_pose__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GetPose_Request(metaclass=Metaclass_GetPose_Request):
    """Message class 'GetPose_Request'."""

    __slots__ = [
    ]

    _fields_and_field_types = {
    }

    SLOT_TYPES = (
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))

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
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

# already imported above
# import rosidl_parser.definition


class Metaclass_GetPose_Response(type):
    """Metaclass of message 'GetPose_Response'."""

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
            module = import_type_support('mission_interfaces')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'mission_interfaces.srv.GetPose_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__get_pose__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__get_pose__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__get_pose__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__get_pose__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__get_pose__response

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GetPose_Response(metaclass=Metaclass_GetPose_Response):
    """Message class 'GetPose_Response'."""

    __slots__ = [
        '_success',
        '_message',
        '_position_x',
        '_position_y',
        '_position_z',
        '_orientation_x',
        '_orientation_y',
        '_orientation_z',
        '_orientation_w',
    ]

    _fields_and_field_types = {
        'success': 'boolean',
        'message': 'string',
        'position_x': 'double',
        'position_y': 'double',
        'position_z': 'double',
        'orientation_x': 'double',
        'orientation_y': 'double',
        'orientation_z': 'double',
        'orientation_w': 'double',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.success = kwargs.get('success', bool())
        self.message = kwargs.get('message', str())
        self.position_x = kwargs.get('position_x', float())
        self.position_y = kwargs.get('position_y', float())
        self.position_z = kwargs.get('position_z', float())
        self.orientation_x = kwargs.get('orientation_x', float())
        self.orientation_y = kwargs.get('orientation_y', float())
        self.orientation_z = kwargs.get('orientation_z', float())
        self.orientation_w = kwargs.get('orientation_w', float())

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
        if self.success != other.success:
            return False
        if self.message != other.message:
            return False
        if self.position_x != other.position_x:
            return False
        if self.position_y != other.position_y:
            return False
        if self.position_z != other.position_z:
            return False
        if self.orientation_x != other.orientation_x:
            return False
        if self.orientation_y != other.orientation_y:
            return False
        if self.orientation_z != other.orientation_z:
            return False
        if self.orientation_w != other.orientation_w:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def success(self):
        """Message field 'success'."""
        return self._success

    @success.setter
    def success(self, value):
        if __debug__:
            assert \
                isinstance(value, bool), \
                "The 'success' field must be of type 'bool'"
        self._success = value

    @builtins.property
    def message(self):
        """Message field 'message'."""
        return self._message

    @message.setter
    def message(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'message' field must be of type 'str'"
        self._message = value

    @builtins.property
    def position_x(self):
        """Message field 'position_x'."""
        return self._position_x

    @position_x.setter
    def position_x(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'position_x' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'position_x' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._position_x = value

    @builtins.property
    def position_y(self):
        """Message field 'position_y'."""
        return self._position_y

    @position_y.setter
    def position_y(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'position_y' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'position_y' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._position_y = value

    @builtins.property
    def position_z(self):
        """Message field 'position_z'."""
        return self._position_z

    @position_z.setter
    def position_z(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'position_z' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'position_z' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._position_z = value

    @builtins.property
    def orientation_x(self):
        """Message field 'orientation_x'."""
        return self._orientation_x

    @orientation_x.setter
    def orientation_x(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'orientation_x' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'orientation_x' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._orientation_x = value

    @builtins.property
    def orientation_y(self):
        """Message field 'orientation_y'."""
        return self._orientation_y

    @orientation_y.setter
    def orientation_y(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'orientation_y' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'orientation_y' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._orientation_y = value

    @builtins.property
    def orientation_z(self):
        """Message field 'orientation_z'."""
        return self._orientation_z

    @orientation_z.setter
    def orientation_z(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'orientation_z' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'orientation_z' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._orientation_z = value

    @builtins.property
    def orientation_w(self):
        """Message field 'orientation_w'."""
        return self._orientation_w

    @orientation_w.setter
    def orientation_w(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'orientation_w' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'orientation_w' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._orientation_w = value


class Metaclass_GetPose(type):
    """Metaclass of service 'GetPose'."""

    _TYPE_SUPPORT = None

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('mission_interfaces')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'mission_interfaces.srv.GetPose')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__get_pose

            from mission_interfaces.srv import _get_pose
            if _get_pose.Metaclass_GetPose_Request._TYPE_SUPPORT is None:
                _get_pose.Metaclass_GetPose_Request.__import_type_support__()
            if _get_pose.Metaclass_GetPose_Response._TYPE_SUPPORT is None:
                _get_pose.Metaclass_GetPose_Response.__import_type_support__()


class GetPose(metaclass=Metaclass_GetPose):
    from mission_interfaces.srv._get_pose import GetPose_Request as Request
    from mission_interfaces.srv._get_pose import GetPose_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
