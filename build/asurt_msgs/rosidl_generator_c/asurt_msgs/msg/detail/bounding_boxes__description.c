// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from asurt_msgs:msg/BoundingBoxes.idl
// generated code does not contain a copyright notice

#include "asurt_msgs/msg/detail/bounding_boxes__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_asurt_msgs
const rosidl_type_hash_t *
asurt_msgs__msg__BoundingBoxes__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xa9, 0x23, 0x98, 0x75, 0x64, 0x00, 0x91, 0x2f,
      0x5b, 0xac, 0xa6, 0xc7, 0x3d, 0xd6, 0x65, 0x32,
      0x73, 0x42, 0xef, 0xca, 0xa8, 0xbe, 0x9a, 0x78,
      0x6a, 0x06, 0xda, 0x7e, 0x99, 0xb2, 0xea, 0x75,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "asurt_msgs/msg/detail/bounding_box__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t asurt_msgs__msg__BoundingBox__EXPECTED_HASH = {1, {
    0x87, 0xd2, 0x57, 0xee, 0x0e, 0x7e, 0x74, 0xc3,
    0x9f, 0x82, 0xcd, 0x85, 0x14, 0xa1, 0x2c, 0x01,
    0xf4, 0xdc, 0x6a, 0x6e, 0xcd, 0xdb, 0x5b, 0xcc,
    0x46, 0x92, 0xb5, 0x02, 0xac, 0x88, 0x69, 0x3a,
  }};
#endif

static char asurt_msgs__msg__BoundingBoxes__TYPE_NAME[] = "asurt_msgs/msg/BoundingBoxes";
static char asurt_msgs__msg__BoundingBox__TYPE_NAME[] = "asurt_msgs/msg/BoundingBox";

// Define type names, field names, and default values
static char asurt_msgs__msg__BoundingBoxes__FIELD_NAME__view_id[] = "view_id";
static char asurt_msgs__msg__BoundingBoxes__FIELD_NAME__object_count[] = "object_count";
static char asurt_msgs__msg__BoundingBoxes__FIELD_NAME__bounding_boxes[] = "bounding_boxes";

static rosidl_runtime_c__type_description__Field asurt_msgs__msg__BoundingBoxes__FIELDS[] = {
  {
    {asurt_msgs__msg__BoundingBoxes__FIELD_NAME__view_id, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBoxes__FIELD_NAME__object_count, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBoxes__FIELD_NAME__bounding_boxes, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE,
      0,
      0,
      {asurt_msgs__msg__BoundingBox__TYPE_NAME, 26, 26},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription asurt_msgs__msg__BoundingBoxes__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {asurt_msgs__msg__BoundingBox__TYPE_NAME, 26, 26},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
asurt_msgs__msg__BoundingBoxes__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {asurt_msgs__msg__BoundingBoxes__TYPE_NAME, 28, 28},
      {asurt_msgs__msg__BoundingBoxes__FIELDS, 3, 3},
    },
    {asurt_msgs__msg__BoundingBoxes__REFERENCED_TYPE_DESCRIPTIONS, 1, 1},
  };
  if (!constructed) {
    assert(0 == memcmp(&asurt_msgs__msg__BoundingBox__EXPECTED_HASH, asurt_msgs__msg__BoundingBox__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = asurt_msgs__msg__BoundingBox__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "string view_id\n"
  "uint16 object_count\n"
  "asurt_msgs/BoundingBox[] bounding_boxes";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
asurt_msgs__msg__BoundingBoxes__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {asurt_msgs__msg__BoundingBoxes__TYPE_NAME, 28, 28},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 74, 74},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
asurt_msgs__msg__BoundingBoxes__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[2];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 2, 2};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *asurt_msgs__msg__BoundingBoxes__get_individual_type_description_source(NULL),
    sources[1] = *asurt_msgs__msg__BoundingBox__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
