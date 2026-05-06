// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from asurt_msgs:msg/Landmark.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "asurt_msgs/msg/detail/landmark__struct.h"
#include "asurt_msgs/msg/detail/landmark__functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool geometry_msgs__msg__point__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * geometry_msgs__msg__point__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool asurt_msgs__msg__landmark__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[34];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("asurt_msgs.msg._landmark.Landmark", full_classname_dest, 33) == 0);
  }
  asurt_msgs__msg__Landmark * ros_message = _ros_message;
  {  // position
    PyObject * field = PyObject_GetAttrString(_pymsg, "position");
    if (!field) {
      return false;
    }
    if (!geometry_msgs__msg__point__convert_from_py(field, &ros_message->position)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // type
    PyObject * field = PyObject_GetAttrString(_pymsg, "type");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->type = PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // identifier
    PyObject * field = PyObject_GetAttrString(_pymsg, "identifier");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->identifier = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // probability
    PyObject * field = PyObject_GetAttrString(_pymsg, "probability");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->probability = PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * asurt_msgs__msg__landmark__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of Landmark */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("asurt_msgs.msg._landmark");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "Landmark");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  asurt_msgs__msg__Landmark * ros_message = (asurt_msgs__msg__Landmark *)raw_ros_message;
  {  // position
    PyObject * field = NULL;
    field = geometry_msgs__msg__point__convert_to_py(&ros_message->position);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "position", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // type
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->type);
    {
      int rc = PyObject_SetAttrString(_pymessage, "type", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // identifier
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->identifier);
    {
      int rc = PyObject_SetAttrString(_pymessage, "identifier", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // probability
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->probability);
    {
      int rc = PyObject_SetAttrString(_pymessage, "probability", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
