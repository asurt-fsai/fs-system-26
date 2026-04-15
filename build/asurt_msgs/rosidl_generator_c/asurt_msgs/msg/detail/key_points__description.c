// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from asurt_msgs:msg/KeyPoints.idl
// generated code does not contain a copyright notice

#include "asurt_msgs/msg/detail/key_points__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_asurt_msgs
const rosidl_type_hash_t *
asurt_msgs__msg__KeyPoints__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x53, 0xeb, 0xa5, 0xa2, 0x33, 0xf2, 0xbe, 0x48,
      0x3c, 0x6a, 0xe7, 0x76, 0xe4, 0x65, 0x35, 0x98,
      0x74, 0xea, 0x19, 0xc8, 0x9e, 0xfb, 0xda, 0x86,
      0x68, 0x04, 0x1d, 0x95, 0xc9, 0xbf, 0xcb, 0x6f,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char asurt_msgs__msg__KeyPoints__TYPE_NAME[] = "asurt_msgs/msg/KeyPoints";

// Define type names, field names, and default values
static char asurt_msgs__msg__KeyPoints__FIELD_NAME__view_id[] = "view_id";
static char asurt_msgs__msg__KeyPoints__FIELD_NAME__object_count[] = "object_count";
static char asurt_msgs__msg__KeyPoints__FIELD_NAME__track_ids[] = "track_ids";
static char asurt_msgs__msg__KeyPoints__FIELD_NAME__classes[] = "classes";
static char asurt_msgs__msg__KeyPoints__FIELD_NAME__keypoints[] = "keypoints";

static rosidl_runtime_c__type_description__Field asurt_msgs__msg__KeyPoints__FIELDS[] = {
  {
    {asurt_msgs__msg__KeyPoints__FIELD_NAME__view_id, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__KeyPoints__FIELD_NAME__object_count, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__KeyPoints__FIELD_NAME__track_ids, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__KeyPoints__FIELD_NAME__classes, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__KeyPoints__FIELD_NAME__keypoints, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
asurt_msgs__msg__KeyPoints__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {asurt_msgs__msg__KeyPoints__TYPE_NAME, 24, 24},
      {asurt_msgs__msg__KeyPoints__FIELDS, 5, 5},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "uint32 view_id\n"
  "uint16 object_count\n"
  "uint8[] track_ids\n"
  "uint8[] classes\n"
  "uint16[] keypoints";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
asurt_msgs__msg__KeyPoints__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {asurt_msgs__msg__KeyPoints__TYPE_NAME, 24, 24},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 88, 88},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
asurt_msgs__msg__KeyPoints__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *asurt_msgs__msg__KeyPoints__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
