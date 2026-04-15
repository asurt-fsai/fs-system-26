// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from cloud_msgs:msg/CloudInfo.idl
// generated code does not contain a copyright notice

#include "cloud_msgs/msg/detail/cloud_info__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_cloud_msgs
const rosidl_type_hash_t *
cloud_msgs__msg__CloudInfo__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x78, 0xfd, 0x5a, 0xc4, 0x08, 0xef, 0xd6, 0xe1,
      0x1c, 0xdb, 0x08, 0x36, 0x90, 0x5e, 0x81, 0xa2,
      0xd8, 0x5c, 0xcc, 0x91, 0x1a, 0x5d, 0x23, 0x89,
      0xcd, 0xb5, 0x19, 0xe4, 0xe5, 0xdd, 0xf6, 0x85,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "std_msgs/msg/detail/header__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t std_msgs__msg__Header__EXPECTED_HASH = {1, {
    0xf4, 0x9f, 0xb3, 0xae, 0x2c, 0xf0, 0x70, 0xf7,
    0x93, 0x64, 0x5f, 0xf7, 0x49, 0x68, 0x3a, 0xc6,
    0xb0, 0x62, 0x03, 0xe4, 0x1c, 0x89, 0x1e, 0x17,
    0x70, 0x1b, 0x1c, 0xb5, 0x97, 0xce, 0x6a, 0x01,
  }};
#endif

static char cloud_msgs__msg__CloudInfo__TYPE_NAME[] = "cloud_msgs/msg/CloudInfo";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char std_msgs__msg__Header__TYPE_NAME[] = "std_msgs/msg/Header";

// Define type names, field names, and default values
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__header[] = "header";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__start_ring_index[] = "start_ring_index";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__end_ring_index[] = "end_ring_index";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__start_orientation[] = "start_orientation";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__end_orientation[] = "end_orientation";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__orientation_diff[] = "orientation_diff";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__segmented_cloud_ground_flag[] = "segmented_cloud_ground_flag";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__segmented_cloud_col_ind[] = "segmented_cloud_col_ind";
static char cloud_msgs__msg__CloudInfo__FIELD_NAME__segmented_cloud_range[] = "segmented_cloud_range";

static rosidl_runtime_c__type_description__Field cloud_msgs__msg__CloudInfo__FIELDS[] = {
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__header, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__start_ring_index, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__end_ring_index, 14, 14},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__start_orientation, 17, 17},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__end_orientation, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__orientation_diff, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__segmented_cloud_ground_flag, 27, 27},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__segmented_cloud_col_ind, 23, 23},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT32_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {cloud_msgs__msg__CloudInfo__FIELD_NAME__segmented_cloud_range, 21, 21},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT_UNBOUNDED_SEQUENCE,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription cloud_msgs__msg__CloudInfo__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
cloud_msgs__msg__CloudInfo__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {cloud_msgs__msg__CloudInfo__TYPE_NAME, 24, 24},
      {cloud_msgs__msg__CloudInfo__FIELDS, 9, 9},
    },
    {cloud_msgs__msg__CloudInfo__REFERENCED_TYPE_DESCRIPTIONS, 2, 2},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&std_msgs__msg__Header__EXPECTED_HASH, std_msgs__msg__Header__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = std_msgs__msg__Header__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "std_msgs/Header header\n"
  "\n"
  "int32[] start_ring_index\n"
  "int32[] end_ring_index\n"
  "\n"
  "float32 start_orientation\n"
  "float32 end_orientation\n"
  "float32 orientation_diff\n"
  "\n"
  "# true - ground point, false - other points\n"
  "bool[]    segmented_cloud_ground_flag\n"
  "# point column index in range image\n"
  "uint32[]  segmented_cloud_col_ind\n"
  "# point range\n"
  "float32[] segmented_cloud_range";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
cloud_msgs__msg__CloudInfo__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {cloud_msgs__msg__CloudInfo__TYPE_NAME, 24, 24},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 347, 347},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
cloud_msgs__msg__CloudInfo__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[3];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 3, 3};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *cloud_msgs__msg__CloudInfo__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *std_msgs__msg__Header__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
