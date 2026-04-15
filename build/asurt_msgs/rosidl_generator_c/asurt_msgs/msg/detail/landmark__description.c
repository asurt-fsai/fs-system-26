// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from asurt_msgs:msg/Landmark.idl
// generated code does not contain a copyright notice

#include "asurt_msgs/msg/detail/landmark__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_asurt_msgs
const rosidl_type_hash_t *
asurt_msgs__msg__Landmark__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xb4, 0x43, 0x6b, 0x6e, 0xb3, 0x62, 0x6b, 0xc6,
      0xea, 0xbe, 0x61, 0xa5, 0xff, 0xbf, 0xdf, 0x79,
      0x8a, 0x35, 0x3f, 0xca, 0xd4, 0x32, 0x33, 0xbd,
      0xdb, 0xe1, 0xab, 0x2d, 0xe7, 0x0c, 0xe6, 0xd4,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "geometry_msgs/msg/detail/point__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t geometry_msgs__msg__Point__EXPECTED_HASH = {1, {
    0x69, 0x63, 0x08, 0x48, 0x42, 0xa9, 0xb0, 0x44,
    0x94, 0xd6, 0xb2, 0x94, 0x1d, 0x11, 0x44, 0x47,
    0x08, 0xd8, 0x92, 0xda, 0x2f, 0x4b, 0x09, 0x84,
    0x3b, 0x9c, 0x43, 0xf4, 0x2a, 0x7f, 0x68, 0x81,
  }};
#endif

static char asurt_msgs__msg__Landmark__TYPE_NAME[] = "asurt_msgs/msg/Landmark";
static char geometry_msgs__msg__Point__TYPE_NAME[] = "geometry_msgs/msg/Point";

// Define type names, field names, and default values
static char asurt_msgs__msg__Landmark__FIELD_NAME__position[] = "position";
static char asurt_msgs__msg__Landmark__FIELD_NAME__type[] = "type";
static char asurt_msgs__msg__Landmark__FIELD_NAME__identifier[] = "identifier";
static char asurt_msgs__msg__Landmark__FIELD_NAME__probability[] = "probability";

static rosidl_runtime_c__type_description__Field asurt_msgs__msg__Landmark__FIELDS[] = {
  {
    {asurt_msgs__msg__Landmark__FIELD_NAME__position, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {geometry_msgs__msg__Point__TYPE_NAME, 23, 23},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__Landmark__FIELD_NAME__type, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__Landmark__FIELD_NAME__identifier, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__Landmark__FIELD_NAME__probability, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_DOUBLE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription asurt_msgs__msg__Landmark__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {geometry_msgs__msg__Point__TYPE_NAME, 23, 23},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
asurt_msgs__msg__Landmark__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {asurt_msgs__msg__Landmark__TYPE_NAME, 23, 23},
      {asurt_msgs__msg__Landmark__FIELDS, 4, 4},
    },
    {asurt_msgs__msg__Landmark__REFERENCED_TYPE_DESCRIPTIONS, 1, 1},
  };
  if (!constructed) {
    assert(0 == memcmp(&geometry_msgs__msg__Point__EXPECTED_HASH, geometry_msgs__msg__Point__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = geometry_msgs__msg__Point__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "geometry_msgs/Point position\n"
  "uint32 type\n"
  "int32 identifier \\t\\t# Used if there's a data association system available\n"
  "float64 probability\n"
  "uint8 BLUE_CONE = 0\n"
  "uint8 YELLOW_CONE = 1\n"
  "uint8 ORANGE_CONE = 2\n"
  "uint8 LARGE_CONE = 3\n"
  "uint8 CONE_TYPE_UNKNOWN = 4";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
asurt_msgs__msg__Landmark__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {asurt_msgs__msg__Landmark__TYPE_NAME, 23, 23},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 247, 247},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
asurt_msgs__msg__Landmark__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[2];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 2, 2};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *asurt_msgs__msg__Landmark__get_individual_type_description_source(NULL),
    sources[1] = *geometry_msgs__msg__Point__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
