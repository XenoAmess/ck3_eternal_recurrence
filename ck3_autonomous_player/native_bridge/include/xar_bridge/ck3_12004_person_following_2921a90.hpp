#pragma once

#include "xar_bridge/ck3_12004_person_carrier_direct.hpp"

namespace xar::ck3_12004 {
inline constexpr char kPersonFollowing2921a90Schema[] =
    "xar.ck3.person-following-2921a90-12004-v1";
inline constexpr std::uintptr_t kPersonFollowing2921a90RegistryRva = 0x5D1EB80;
inline constexpr std::uintptr_t kPersonFollowing2921a90FallbackRva = 0x5D1EB38;

struct PersonFollowing2921a90Row {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> object_identity;
  std::optional<std::uintptr_t> source_pc_identity;
  std::optional<std::int32_t> pc_count_i32;
  std::optional<PersonCarrierDirect12004Properties> properties;
  std::int64_t weight_q100000 = kPersonCarrierDirectWeight12004;
  friend bool operator==(const PersonFollowing2921a90Row &,
                         const PersonFollowing2921a90Row &) = default;
};

struct PersonFollowing2921a90DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> selected_model_identity;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> destination_pc_identity;
  std::optional<bool> carrier_present;
  std::optional<std::uintptr_t> carrier_identity;
  std::optional<std::uint32_t> requested_full_id_u32;
  std::optional<std::uintptr_t> registry_identity;
  std::optional<std::uint32_t> registry_count_u32;
  std::optional<std::uintptr_t> registry_slots_identity;
  std::string resolution_selection = "unavailable";
  std::optional<std::uintptr_t> selected_object_identity;
  std::optional<std::uint32_t> selected_full_id_u32;
  std::optional<std::uint32_t> selected_magic_u32;
  std::optional<bool> admitted;
  bool direct_ready = false;
  std::string direct_reason;
  std::optional<std::uintptr_t> direct_array_identity;
  std::optional<std::int32_t> direct_count_i32;
  std::vector<PersonFollowing2921a90Row> direct_rows;
  bool conditional_ready = false;
  std::string conditional_reason;
  std::optional<std::uintptr_t> conditional_definition_identity;
  std::optional<std::int32_t> conditional_b8c_count_i32;
  std::optional<std::int32_t> conditional_bbc_count_i32;
  std::optional<std::uint32_t> conditional_occurrence_count;
  friend bool operator==(const PersonFollowing2921a90DTO &,
                         const PersonFollowing2921a90DTO &) = default;
};

// Source-closed actual4 read-only inputs. Uses the existing exact4 binding;
// no new binder, classifier, evaluator, constructor, merger, or native call.
PersonFollowing2921a90DTO ReadPersonFollowing2921a90ForModel12004(
    const PersonCarrierDirect12004Bindings &bindings, std::uintptr_t actual_model);
PersonFollowing2921a90DTO ReadPersonFollowing2921a90ForCharacter12004(
    const PersonCarrierDirect12004Bindings &bindings,
    std::uintptr_t actual_character);
std::string SerializePersonFollowing2921a90(const PersonFollowing2921a90DTO &dto);
} // namespace xar::ck3_12004
