// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from asurt_msgs:msg/BoundingBox.idl
// generated code does not contain a copyright notice

#include "asurt_msgs/msg/detail/bounding_box__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_asurt_msgs
const rosidl_type_hash_t *
asurt_msgs__msg__BoundingBox__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x87, 0xd2, 0x57, 0xee, 0x0e, 0x7e, 0x74, 0xc3,
      0x9f, 0x82, 0xcd, 0x85, 0x14, 0xa1, 0x2c, 0x01,
      0xf4, 0xdc, 0x6a, 0x6e, 0xcd, 0xdb, 0x5b, 0xcc,
      0x46, 0x92, 0xb5, 0x02, 0xac, 0x88, 0x69, 0x3a,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char asurt_msgs__msg__BoundingBox__TYPE_NAME[] = "asurt_msgs/msg/BoundingBox";

// Define type names, field names, and default values
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__probability[] = "probability";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__xmin[] = "xmin";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__ymin[] = "ymin";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__xmax[] = "xmax";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__ymax[] = "ymax";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__x_center[] = "x_center";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__y_center[] = "y_center";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__width[] = "width";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__height[] = "height";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__detection_id[] = "detection_id";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__track_id[] = "track_id";
static char asurt_msgs__msg__BoundingBox__FIELD_NAME__type[] = "type";

static rosidl_runtime_c__type_description__Field asurt_msgs__msg__BoundingBox__FIELDS[] = {
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__probability, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__xmin, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__ymin, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__xmax, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__ymax, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__x_center, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__y_center, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__width, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__height, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__detection_id, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__track_id, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__BoundingBox__FIELD_NAME__type, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
asurt_msgs__msg__BoundingBox__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {asurt_msgs__msg__BoundingBox__TYPE_NAME, 26, 26},
      {asurt_msgs__msg__BoundingBox__FIELDS, 12, 12},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float32 probability\n"
  "uint16 xmin\n"
  "uint16 ymin\n"
  "uint16 xmax\n"
  "uint16 ymax\n"
  "uint16 x_center\n"
  "uint16 y_center\n"
  "uint16 width\n"
  "uint16 height\n"
  "uint16 detection_id\n"
  "uint16 track_id\n"
  "uint8 type";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
asurt_msgs__msg__BoundingBox__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {asurt_msgs__msg__BoundingBox__TYPE_NAME, 26, 26},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 174, 174},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
asurt_msgs__msg__BoundingBox__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *asurt_msgs__msg__BoundingBox__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
