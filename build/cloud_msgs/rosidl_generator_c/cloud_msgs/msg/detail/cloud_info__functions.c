// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from cloud_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice
#include "cloud_msgs/msg/detail/cloud_info__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `start_ring_index`
// Member `end_ring_index`
// Member `segmented_cloud_ground_flag`
// Member `segmented_cloud_col_ind`
// Member `segmented_cloud_range`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
cloud_msgs__msg__CloudInfo__init(cloud_msgs__msg__CloudInfo * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    cloud_msgs__msg__CloudInfo__fini(msg);
    return false;
  }
  // start_ring_index
  if (!rosidl_runtime_c__int32__Sequence__init(&msg->start_ring_index, 0)) {
    cloud_msgs__msg__CloudInfo__fini(msg);
    return false;
  }
  // end_ring_index
  if (!rosidl_runtime_c__int32__Sequence__init(&msg->end_ring_index, 0)) {
    cloud_msgs__msg__CloudInfo__fini(msg);
    return false;
  }
  // start_orientation
  // end_orientation
  // orientation_diff
  // segmented_cloud_ground_flag
  if (!rosidl_runtime_c__boolean__Sequence__init(&msg->segmented_cloud_ground_flag, 0)) {
    cloud_msgs__msg__CloudInfo__fini(msg);
    return false;
  }
  // segmented_cloud_col_ind
  if (!rosidl_runtime_c__uint32__Sequence__init(&msg->segmented_cloud_col_ind, 0)) {
    cloud_msgs__msg__CloudInfo__fini(msg);
    return false;
  }
  // segmented_cloud_range
  if (!rosidl_runtime_c__float__Sequence__init(&msg->segmented_cloud_range, 0)) {
    cloud_msgs__msg__CloudInfo__fini(msg);
    return false;
  }
  return true;
}

void
cloud_msgs__msg__CloudInfo__fini(cloud_msgs__msg__CloudInfo * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // start_ring_index
  rosidl_runtime_c__int32__Sequence__fini(&msg->start_ring_index);
  // end_ring_index
  rosidl_runtime_c__int32__Sequence__fini(&msg->end_ring_index);
  // start_orientation
  // end_orientation
  // orientation_diff
  // segmented_cloud_ground_flag
  rosidl_runtime_c__boolean__Sequence__fini(&msg->segmented_cloud_ground_flag);
  // segmented_cloud_col_ind
  rosidl_runtime_c__uint32__Sequence__fini(&msg->segmented_cloud_col_ind);
  // segmented_cloud_range
  rosidl_runtime_c__float__Sequence__fini(&msg->segmented_cloud_range);
}

bool
cloud_msgs__msg__CloudInfo__are_equal(const cloud_msgs__msg__CloudInfo * lhs, const cloud_msgs__msg__CloudInfo * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // start_ring_index
  if (!rosidl_runtime_c__int32__Sequence__are_equal(
      &(lhs->start_ring_index), &(rhs->start_ring_index)))
  {
    return false;
  }
  // end_ring_index
  if (!rosidl_runtime_c__int32__Sequence__are_equal(
      &(lhs->end_ring_index), &(rhs->end_ring_index)))
  {
    return false;
  }
  // start_orientation
  if (lhs->start_orientation != rhs->start_orientation) {
    return false;
  }
  // end_orientation
  if (lhs->end_orientation != rhs->end_orientation) {
    return false;
  }
  // orientation_diff
  if (lhs->orientation_diff != rhs->orientation_diff) {
    return false;
  }
  // segmented_cloud_ground_flag
  if (!rosidl_runtime_c__boolean__Sequence__are_equal(
      &(lhs->segmented_cloud_ground_flag), &(rhs->segmented_cloud_ground_flag)))
  {
    return false;
  }
  // segmented_cloud_col_ind
  if (!rosidl_runtime_c__uint32__Sequence__are_equal(
      &(lhs->segmented_cloud_col_ind), &(rhs->segmented_cloud_col_ind)))
  {
    return false;
  }
  // segmented_cloud_range
  if (!rosidl_runtime_c__float__Sequence__are_equal(
      &(lhs->segmented_cloud_range), &(rhs->segmented_cloud_range)))
  {
    return false;
  }
  return true;
}

bool
cloud_msgs__msg__CloudInfo__copy(
  const cloud_msgs__msg__CloudInfo * input,
  cloud_msgs__msg__CloudInfo * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // start_ring_index
  if (!rosidl_runtime_c__int32__Sequence__copy(
      &(input->start_ring_index), &(output->start_ring_index)))
  {
    return false;
  }
  // end_ring_index
  if (!rosidl_runtime_c__int32__Sequence__copy(
      &(input->end_ring_index), &(output->end_ring_index)))
  {
    return false;
  }
  // start_orientation
  output->start_orientation = input->start_orientation;
  // end_orientation
  output->end_orientation = input->end_orientation;
  // orientation_diff
  output->orientation_diff = input->orientation_diff;
  // segmented_cloud_ground_flag
  if (!rosidl_runtime_c__boolean__Sequence__copy(
      &(input->segmented_cloud_ground_flag), &(output->segmented_cloud_ground_flag)))
  {
    return false;
  }
  // segmented_cloud_col_ind
  if (!rosidl_runtime_c__uint32__Sequence__copy(
      &(input->segmented_cloud_col_ind), &(output->segmented_cloud_col_ind)))
  {
    return false;
  }
  // segmented_cloud_range
  if (!rosidl_runtime_c__float__Sequence__copy(
      &(input->segmented_cloud_range), &(output->segmented_cloud_range)))
  {
    return false;
  }
  return true;
}

cloud_msgs__msg__CloudInfo *
cloud_msgs__msg__CloudInfo__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  cloud_msgs__msg__CloudInfo * msg = (cloud_msgs__msg__CloudInfo *)allocator.allocate(sizeof(cloud_msgs__msg__CloudInfo), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(cloud_msgs__msg__CloudInfo));
  bool success = cloud_msgs__msg__CloudInfo__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
cloud_msgs__msg__CloudInfo__destroy(cloud_msgs__msg__CloudInfo * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    cloud_msgs__msg__CloudInfo__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
cloud_msgs__msg__CloudInfo__Sequence__init(cloud_msgs__msg__CloudInfo__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  cloud_msgs__msg__CloudInfo * data = NULL;

  if (size) {
    data = (cloud_msgs__msg__CloudInfo *)allocator.zero_allocate(size, sizeof(cloud_msgs__msg__CloudInfo), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = cloud_msgs__msg__CloudInfo__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        cloud_msgs__msg__CloudInfo__fini(&data[i - 1]);
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
cloud_msgs__msg__CloudInfo__Sequence__fini(cloud_msgs__msg__CloudInfo__Sequence * array)
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
      cloud_msgs__msg__CloudInfo__fini(&array->data[i]);
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

cloud_msgs__msg__CloudInfo__Sequence *
cloud_msgs__msg__CloudInfo__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  cloud_msgs__msg__CloudInfo__Sequence * array = (cloud_msgs__msg__CloudInfo__Sequence *)allocator.allocate(sizeof(cloud_msgs__msg__CloudInfo__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = cloud_msgs__msg__CloudInfo__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
cloud_msgs__msg__CloudInfo__Sequence__destroy(cloud_msgs__msg__CloudInfo__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    cloud_msgs__msg__CloudInfo__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
cloud_msgs__msg__CloudInfo__Sequence__are_equal(const cloud_msgs__msg__CloudInfo__Sequence * lhs, const cloud_msgs__msg__CloudInfo__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!cloud_msgs__msg__CloudInfo__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
cloud_msgs__msg__CloudInfo__Sequence__copy(
  const cloud_msgs__msg__CloudInfo__Sequence * input,
  cloud_msgs__msg__CloudInfo__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(cloud_msgs__msg__CloudInfo);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    cloud_msgs__msg__CloudInfo * data =
      (cloud_msgs__msg__CloudInfo *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!cloud_msgs__msg__CloudInfo__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          cloud_msgs__msg__CloudInfo__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!cloud_msgs__msg__CloudInfo__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
