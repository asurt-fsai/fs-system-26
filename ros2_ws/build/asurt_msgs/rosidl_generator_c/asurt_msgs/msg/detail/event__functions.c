// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from asurt_msgs:msg/Event.idl
// generated code does not contain a copyright notice
#include "asurt_msgs/msg/detail/event__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"
// Member `severity`
// Member `category`
// Member `event_type`
// Member `source`
// Member `details_json`
#include "rosidl_runtime_c/string_functions.h"

bool
asurt_msgs__msg__Event__init(asurt_msgs__msg__Event * msg)
{
  if (!msg) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    asurt_msgs__msg__Event__fini(msg);
    return false;
  }
  // severity
  if (!rosidl_runtime_c__String__init(&msg->severity)) {
    asurt_msgs__msg__Event__fini(msg);
    return false;
  }
  // category
  if (!rosidl_runtime_c__String__init(&msg->category)) {
    asurt_msgs__msg__Event__fini(msg);
    return false;
  }
  // event_type
  if (!rosidl_runtime_c__String__init(&msg->event_type)) {
    asurt_msgs__msg__Event__fini(msg);
    return false;
  }
  // source
  if (!rosidl_runtime_c__String__init(&msg->source)) {
    asurt_msgs__msg__Event__fini(msg);
    return false;
  }
  // details_json
  if (!rosidl_runtime_c__String__init(&msg->details_json)) {
    asurt_msgs__msg__Event__fini(msg);
    return false;
  }
  return true;
}

void
asurt_msgs__msg__Event__fini(asurt_msgs__msg__Event * msg)
{
  if (!msg) {
    return;
  }
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
  // severity
  rosidl_runtime_c__String__fini(&msg->severity);
  // category
  rosidl_runtime_c__String__fini(&msg->category);
  // event_type
  rosidl_runtime_c__String__fini(&msg->event_type);
  // source
  rosidl_runtime_c__String__fini(&msg->source);
  // details_json
  rosidl_runtime_c__String__fini(&msg->details_json);
}

bool
asurt_msgs__msg__Event__are_equal(const asurt_msgs__msg__Event * lhs, const asurt_msgs__msg__Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  // severity
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->severity), &(rhs->severity)))
  {
    return false;
  }
  // category
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->category), &(rhs->category)))
  {
    return false;
  }
  // event_type
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->event_type), &(rhs->event_type)))
  {
    return false;
  }
  // source
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->source), &(rhs->source)))
  {
    return false;
  }
  // details_json
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->details_json), &(rhs->details_json)))
  {
    return false;
  }
  return true;
}

bool
asurt_msgs__msg__Event__copy(
  const asurt_msgs__msg__Event * input,
  asurt_msgs__msg__Event * output)
{
  if (!input || !output) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  // severity
  if (!rosidl_runtime_c__String__copy(
      &(input->severity), &(output->severity)))
  {
    return false;
  }
  // category
  if (!rosidl_runtime_c__String__copy(
      &(input->category), &(output->category)))
  {
    return false;
  }
  // event_type
  if (!rosidl_runtime_c__String__copy(
      &(input->event_type), &(output->event_type)))
  {
    return false;
  }
  // source
  if (!rosidl_runtime_c__String__copy(
      &(input->source), &(output->source)))
  {
    return false;
  }
  // details_json
  if (!rosidl_runtime_c__String__copy(
      &(input->details_json), &(output->details_json)))
  {
    return false;
  }
  return true;
}

asurt_msgs__msg__Event *
asurt_msgs__msg__Event__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  asurt_msgs__msg__Event * msg = (asurt_msgs__msg__Event *)allocator.allocate(sizeof(asurt_msgs__msg__Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(asurt_msgs__msg__Event));
  bool success = asurt_msgs__msg__Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
asurt_msgs__msg__Event__destroy(asurt_msgs__msg__Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    asurt_msgs__msg__Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
asurt_msgs__msg__Event__Sequence__init(asurt_msgs__msg__Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  asurt_msgs__msg__Event * data = NULL;

  if (size) {
    data = (asurt_msgs__msg__Event *)allocator.zero_allocate(size, sizeof(asurt_msgs__msg__Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = asurt_msgs__msg__Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        asurt_msgs__msg__Event__fini(&data[i - 1]);
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
asurt_msgs__msg__Event__Sequence__fini(asurt_msgs__msg__Event__Sequence * array)
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
      asurt_msgs__msg__Event__fini(&array->data[i]);
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

asurt_msgs__msg__Event__Sequence *
asurt_msgs__msg__Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  asurt_msgs__msg__Event__Sequence * array = (asurt_msgs__msg__Event__Sequence *)allocator.allocate(sizeof(asurt_msgs__msg__Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = asurt_msgs__msg__Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
asurt_msgs__msg__Event__Sequence__destroy(asurt_msgs__msg__Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    asurt_msgs__msg__Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
asurt_msgs__msg__Event__Sequence__are_equal(const asurt_msgs__msg__Event__Sequence * lhs, const asurt_msgs__msg__Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!asurt_msgs__msg__Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
asurt_msgs__msg__Event__Sequence__copy(
  const asurt_msgs__msg__Event__Sequence * input,
  asurt_msgs__msg__Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(asurt_msgs__msg__Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    asurt_msgs__msg__Event * data =
      (asurt_msgs__msg__Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!asurt_msgs__msg__Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          asurt_msgs__msg__Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!asurt_msgs__msg__Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
