// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from asurt_msgs:msg/ConeImgArray.idl
// generated code does not contain a copyright notice

#include "asurt_msgs/msg/detail/cone_img_array__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_asurt_msgs
const rosidl_type_hash_t *
asurt_msgs__msg__ConeImgArray__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xd5, 0xe2, 0x25, 0x53, 0xa3, 0x43, 0x47, 0xb3,
      0x6e, 0x6b, 0x5c, 0xb1, 0x67, 0x76, 0x01, 0x83,
      0x65, 0x02, 0x5e, 0xea, 0xe2, 0x2e, 0x24, 0x0d,
      0x8e, 0x7a, 0x44, 0x3d, 0x5c, 0x7f, 0xf6, 0x25,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "std_msgs/msg/detail/header__functions.h"
#include "sensor_msgs/msg/detail/image__functions.h"
#include "asurt_msgs/msg/detail/cone_img__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t asurt_msgs__msg__ConeImg__EXPECTED_HASH = {1, {
    0x09, 0x50, 0x81, 0xbd, 0x79, 0xac, 0xb9, 0x7a,
    0xa9, 0x5d, 0x8e, 0x4e, 0x0e, 0x09, 0x86, 0xe5,
    0x59, 0xcd, 0xe1, 0x93, 0xa8, 0x89, 0x4c, 0x4b,
    0xfc, 0x9a, 0xea, 0x09, 0xdc, 0xcc, 0xda, 0x96,
  }};
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t sensor_msgs__msg__Image__EXPECTED_HASH = {1, {
    0xd3, 0x1d, 0x41, 0xa9, 0xa4, 0xc4, 0xbc, 0x8e,
    0xae, 0x9b, 0xe7, 0x57, 0xb0, 0xbe, 0xed, 0x30,
    0x65, 0x64, 0xf7, 0x52, 0x6c, 0x88, 0xea, 0x6a,
    0x45, 0x88, 0xfb, 0x95, 0x82, 0x52, 0x7d, 0x47,
  }};
static const rosidl_type_hash_t std_msgs__msg__Header__EXPECTED_HASH = {1, {
    0xf4, 0x9f, 0xb3, 0xae, 0x2c, 0xf0, 0x70, 0xf7,
    0x93, 0x64, 0x5f, 0xf7, 0x49, 0x68, 0x3a, 0xc6,
    0xb0, 0x62, 0x03, 0xe4, 0x1c, 0x89, 0x1e, 0x17,
    0x70, 0x1b, 0x1c, 0xb5, 0x97, 0xce, 0x6a, 0x01,
  }};
#endif

static char asurt_msgs__msg__ConeImgArray__TYPE_NAME[] = "asurt_msgs/msg/ConeImgArray";
static char asurt_msgs__msg__ConeImg__TYPE_NAME[] = "asurt_msgs/msg/ConeImg";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char sensor_msgs__msg__Image__TYPE_NAME[] = "sensor_msgs/msg/Image";
static char std_msgs__msg__Header__TYPE_NAME[] = "std_msgs/msg/Header";

// Define type names, field names, and default values
static char asurt_msgs__msg__ConeImgArray__FIELD_NAME__view_id[] = "view_id";
static char asurt_msgs__msg__ConeImgArray__FIELD_NAME__object_count[] = "object_count";
static char asurt_msgs__msg__ConeImgArray__FIELD_NAME__imgs[] = "imgs";

static rosidl_runtime_c__type_description__Field asurt_msgs__msg__ConeImgArray__FIELDS[] = {
  {
    {asurt_msgs__msg__ConeImgArray__FIELD_NAME__view_id, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__ConeImgArray__FIELD_NAME__object_count, 12, 12},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT16,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {asurt_msgs__msg__ConeImgArray__FIELD_NAME__imgs, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE,
      0,
      0,
      {asurt_msgs__msg__ConeImg__TYPE_NAME, 22, 22},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription asurt_msgs__msg__ConeImgArray__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {asurt_msgs__msg__ConeImg__TYPE_NAME, 22, 22},
    {NULL, 0, 0},
  },
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {sensor_msgs__msg__Image__TYPE_NAME, 21, 21},
    {NULL, 0, 0},
  },
  {
    {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
asurt_msgs__msg__ConeImgArray__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {asurt_msgs__msg__ConeImgArray__TYPE_NAME, 27, 27},
      {asurt_msgs__msg__ConeImgArray__FIELDS, 3, 3},
    },
    {asurt_msgs__msg__ConeImgArray__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&asurt_msgs__msg__ConeImg__EXPECTED_HASH, asurt_msgs__msg__ConeImg__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = asurt_msgs__msg__ConeImg__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&sensor_msgs__msg__Image__EXPECTED_HASH, sensor_msgs__msg__Image__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[2].fields = sensor_msgs__msg__Image__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&std_msgs__msg__Header__EXPECTED_HASH, std_msgs__msg__Header__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = std_msgs__msg__Header__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "string view_id\n"
  "uint16 object_count\n"
  "asurt_msgs/ConeImg[] imgs";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
asurt_msgs__msg__ConeImgArray__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {asurt_msgs__msg__ConeImgArray__TYPE_NAME, 27, 27},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 60, 60},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
asurt_msgs__msg__ConeImgArray__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *asurt_msgs__msg__ConeImgArray__get_individual_type_description_source(NULL),
    sources[1] = *asurt_msgs__msg__ConeImg__get_individual_type_description_source(NULL);
    sources[2] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[3] = *sensor_msgs__msg__Image__get_individual_type_description_source(NULL);
    sources[4] = *std_msgs__msg__Header__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
