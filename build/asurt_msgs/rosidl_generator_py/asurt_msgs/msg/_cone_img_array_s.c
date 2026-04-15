// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from asurt_msgs:msg/ConeImgArray.idl
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
#include "asurt_msgs/msg/detail/cone_img_array__struct.h"
#include "asurt_msgs/msg/detail/cone_img_array__functions.h"

#include "rosidl_runtime_c/string.h"
#include "rosidl_runtime_c/string_functions.h"

#include "rosidl_runtime_c/primitives_sequence.h"
#include "rosidl_runtime_c/primitives_sequence_functions.h"

// Nested array functions includes
#include "asurt_msgs/msg/detail/cone_img__functions.h"
// end nested array functions include
bool asurt_msgs__msg__cone_img__convert_from_py(PyObject * _pymsg, void * _ros_message);
PyObject * asurt_msgs__msg__cone_img__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool asurt_msgs__msg__cone_img_array__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[44];
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
    assert(strncmp("asurt_msgs.msg._cone_img_array.ConeImgArray", full_classname_dest, 43) == 0);
  }
  asurt_msgs__msg__ConeImgArray * ros_message = _ros_message;
  {  // view_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "view_id");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->view_id, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }
  {  // object_count
    PyObject * field = PyObject_GetAttrString(_pymsg, "object_count");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->object_count = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // imgs
    PyObject * field = PyObject_GetAttrString(_pymsg, "imgs");
    if (!field) {
      return false;
    }
    PyObject * seq_field = PySequence_Fast(field, "expected a sequence in 'imgs'");
    if (!seq_field) {
      Py_DECREF(field);
      return false;
    }
    Py_ssize_t size = PySequence_Size(field);
    if (-1 == size) {
      Py_DECREF(seq_field);
      Py_DECREF(field);
      return false;
    }
    if (!asurt_msgs__msg__ConeImg__Sequence__init(&(ros_message->imgs), size)) {
      PyErr_SetString(PyExc_RuntimeError, "unable to create asurt_msgs__msg__ConeImg__Sequence ros_message");
      Py_DECREF(seq_field);
      Py_DECREF(field);
      return false;
    }
    asurt_msgs__msg__ConeImg * dest = ros_message->imgs.data;
    for (Py_ssize_t i = 0; i < size; ++i) {
      if (!asurt_msgs__msg__cone_img__convert_from_py(PySequence_Fast_GET_ITEM(seq_field, i), &dest[i])) {
        Py_DECREF(seq_field);
        Py_DECREF(field);
        return false;
      }
    }
    Py_DECREF(seq_field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * asurt_msgs__msg__cone_img_array__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of ConeImgArray */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("asurt_msgs.msg._cone_img_array");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "ConeImgArray");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  asurt_msgs__msg__ConeImgArray * ros_message = (asurt_msgs__msg__ConeImgArray *)raw_ros_message;
  {  // view_id
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->view_id.data,
      strlen(ros_message->view_id.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "view_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // object_count
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->object_count);
    {
      int rc = PyObject_SetAttrString(_pymessage, "object_count", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // imgs
    PyObject * field = NULL;
    size_t size = ros_message->imgs.size;
    field = PyList_New(size);
    if (!field) {
      return NULL;
    }
    asurt_msgs__msg__ConeImg * item;
    for (size_t i = 0; i < size; ++i) {
      item = &(ros_message->imgs.data[i]);
      PyObject * pyitem = asurt_msgs__msg__cone_img__convert_to_py(item);
      if (!pyitem) {
        Py_DECREF(field);
        return NULL;
      }
      int rc = PyList_SetItem(field, i, pyitem);
      (void)rc;
      assert(rc == 0);
    }
    assert(PySequence_Check(field));
    {
      int rc = PyObject_SetAttrString(_pymessage, "imgs", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
