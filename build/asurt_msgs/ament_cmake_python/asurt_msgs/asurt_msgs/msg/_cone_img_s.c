// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from asurt_msgs:msg/ConeImg.idl
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
#include "asurt_msgs/msg/detail/cone_img__struct.h"
#include "asurt_msgs/msg/detail/cone_img__functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool sensor_msgs__msg__image__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * sensor_msgs__msg__image__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool asurt_msgs__msg__cone_img__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[33];
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
    assert(strncmp("asurt_msgs.msg._cone_img.ConeImg", full_classname_dest, 32) == 0);
  }
  asurt_msgs__msg__ConeImg * ros_message = _ros_message;
  {  // detection_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "detection_id");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->detection_id = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // rows
    PyObject * field = PyObject_GetAttrString(_pymsg, "rows");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->rows = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // cols
    PyObject * field = PyObject_GetAttrString(_pymsg, "cols");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->cols = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // img
    PyObject * field = PyObject_GetAttrString(_pymsg, "img");
    if (!field) {
      return false;
    }
    if (!sensor_msgs__msg__image__convert_from_py(field, &ros_message->img)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // track_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "track_id");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->track_id = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * asurt_msgs__msg__cone_img__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of ConeImg */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("asurt_msgs.msg._cone_img");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "ConeImg");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  asurt_msgs__msg__ConeImg * ros_message = (asurt_msgs__msg__ConeImg *)raw_ros_message;
  {  // detection_id
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->detection_id);
    {
      int rc = PyObject_SetAttrString(_pymessage, "detection_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // rows
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->rows);
    {
      int rc = PyObject_SetAttrString(_pymessage, "rows", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // cols
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->cols);
    {
      int rc = PyObject_SetAttrString(_pymessage, "cols", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // img
    PyObject * field = NULL;
    field = sensor_msgs__msg__image__convert_to_py(&ros_message->img);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "img", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // track_id
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->track_id);
    {
      int rc = PyObject_SetAttrString(_pymessage, "track_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
