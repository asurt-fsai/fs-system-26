// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from asurt_msgs:msg/ConeImg.idl
// generated code does not contain a copyright notice
#include "asurt_msgs/msg/detail/cone_img__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
asurt_msgs__msg__ConeImg__init(asurt_msgs__msg__ConeImg * msg)
{
  if (!msg) {
    return false;
  }
  // id
  // rows
  // cols
  // data
  if (!rosidl_runtime_c__uint8__Sequence__init(&msg->data, 0)) {
    asurt_msgs__msg__ConeImg__fini(msg);
    return false;
  }
  return true;
}

void
asurt_msgs__msg__ConeImg__fini(asurt_msgs__msg__ConeImg * msg)
{
  if (!msg) {
    return;
  }
  // id
  // rows
  // cols
  // data
  rosidl_runtime_c__uint8__Sequence__fini(&msg->data);
}

bool
asurt_msgs__msg__ConeImg__are_equal(const asurt_msgs__msg__ConeImg * lhs, const asurt_msgs__msg__ConeImg * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // id
  if (lhs->id != rhs->id) {
    return false;
  }
  // rows
  if (lhs->rows != rhs->rows) {
    return false;
  }
  // cols
  if (lhs->cols != rhs->cols) {
    return false;
  }
  // data
  if (!rosidl_runtime_c__uint8__Sequence__are_equal(
      &(lhs->data), &(rhs->data)))
  {
    return false;
  }
  return true;
}

bool
asurt_msgs__msg__ConeImg__copy(
  const asurt_msgs__msg__ConeImg * input,
  asurt_msgs__msg__ConeImg * output)
{
  if (!input || !output) {
    return false;
  }
  // id
  output->id = input->id;
  // rows
  output->rows = input->rows;
  // cols
  output->cols = input->cols;
  // data
  if (!rosidl_runtime_c__uint8__Sequence__copy(
      &(input->data), &(output->data)))
  {
    return false;
  }
  return true;
}

asurt_msgs__msg__ConeImg *
asurt_msgs__msg__ConeImg__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  asurt_msgs__msg__ConeImg * msg = (asurt_msgs__msg__ConeImg *)allocator.allocate(sizeof(asurt_msgs__msg__ConeImg), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(asurt_msgs__msg__ConeImg));
  bool success = asurt_msgs__msg__ConeImg__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
asurt_msgs__msg__ConeImg__destroy(asurt_msgs__msg__ConeImg * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    asurt_msgs__msg__ConeImg__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
asurt_msgs__msg__ConeImg__Sequence__init(asurt_msgs__msg__ConeImg__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  asurt_msgs__msg__ConeImg * data = NULL;

  if (size) {
    data = (asurt_msgs__msg__ConeImg *)allocator.zero_allocate(size, sizeof(asurt_msgs__msg__ConeImg), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = asurt_msgs__msg__ConeImg__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        asurt_msgs__msg__ConeImg__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
asurt_msgs__msg__ConeImg__Sequence__fini(asurt_msgs__msg__ConeImg__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      asurt_msgs__msg__ConeImg__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

asurt_msgs__msg__ConeImg__Sequence *
asurt_msgs__msg__ConeImg__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  asurt_msgs__msg__ConeImg__Sequence * array = (asurt_msgs__msg__ConeImg__Sequence *)allocator.allocate(sizeof(asurt_msgs__msg__ConeImg__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = asurt_msgs__msg__ConeImg__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
asurt_msgs__msg__ConeImg__Sequence__destroy(asurt_msgs__msg__ConeImg__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    asurt_msgs__msg__ConeImg__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
asurt_msgs__msg__ConeImg__Sequence__are_equal(const asurt_msgs__msg__ConeImg__Sequence * lhs, const asurt_msgs__msg__ConeImg__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!asurt_msgs__msg__ConeImg__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
asurt_msgs__msg__ConeImg__Sequence__copy(
  const asurt_msgs__msg__ConeImg__Sequence * input,
  asurt_msgs__msg__ConeImg__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(asurt_msgs__msg__ConeImg);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    asurt_msgs__msg__ConeImg * data =
      (asurt_msgs__msg__ConeImg *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!asurt_msgs__msg__ConeImg__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          asurt_msgs__msg__ConeImg__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!asurt_msgs__msg__ConeImg__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
