#pragma once

#include "xar_bridge/ck3_12004_person_carrier_direct.hpp"

namespace xar::ck3_12004 {

inline constexpr char kPersonFollowing2922680Schema[] =
    "xar.ck3.person-following-2922680-12004-v1";

struct PersonFollowing2922680Resolution {
  bool ready = false;
  std::string reason;
  std::string selection = "unavailable";
  std::optional<std::uint32_t> requested_full_id_u32;
  std::optional<std::uintptr_t> registry_identity;
  std::optional<std::uint32_t> registry_count_u32;
  std::optional<std::uintptr_t> registry_slots_identity;
  std::optional<std::uintptr_t> candidate_identity;
  std::optional<std::uint32_t> candidate_full_id_u32;
  std::optional<std::uintptr_t> selected_identity;
  friend bool operator==(const PersonFollowing2922680Resolution &,
                         const PersonFollowing2922680Resolution &) = default;
};

struct PersonFollowing2922680Pc {
  bool ready = false;
  std::string reason;
  std::optional<bool> admitted;
  std::optional<std::uintptr_t> identity;
  std::optional<std::int32_t> count_i32;
  std::optional<PersonCarrierDirect12004Properties> properties;
  std::int64_t weight_q100000 = 100000;
  friend bool operator==(const PersonFollowing2922680Pc &,
                         const PersonFollowing2922680Pc &) = default;
};
struct PersonFollowing2922680Append : PersonFollowing2922680Pc {
  std::string kind;
  std::uint32_t outer_index = 0;
  std::uint32_t source_index = 0;
  std::uint32_t item_index = 0;
  std::optional<std::uint32_t> nested_index;
  std::optional<std::uint32_t> descriptor_index;
  friend bool operator==(const PersonFollowing2922680Append &,
                         const PersonFollowing2922680Append &) = default;
};
struct PersonFollowing2922680MembershipRow {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> key_identity;
  std::optional<bool> admitted;
  friend bool operator==(const PersonFollowing2922680MembershipRow &,
                         const PersonFollowing2922680MembershipRow &) = default;
};
struct PersonFollowing2922680Membership {
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> header_identity;
  std::optional<std::int32_t> count_i32;
  std::optional<std::uintptr_t> array_identity;
  std::optional<std::int32_t> membership_count_i32;
  std::optional<std::uintptr_t> membership_array_identity;
  std::optional<std::vector<std::uintptr_t>> membership_identities;
  std::vector<PersonFollowing2922680MembershipRow> rows;
  friend bool operator==(const PersonFollowing2922680Membership &,
                         const PersonFollowing2922680Membership &) = default;
};
struct PersonFollowing2922680Probe {
  std::uint32_t native_index = 0;
  std::optional<std::uintptr_t> slot_identity;
  std::optional<std::uint8_t> control_u8;
  std::optional<std::uint32_t> key_u32;
  friend bool operator==(const PersonFollowing2922680Probe &,
                         const PersonFollowing2922680Probe &) = default;
};
struct PersonFollowing2922680Getter {
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> input_magic_u32;
  std::optional<std::uint32_t> input_full_id_u32;
  std::optional<std::uint32_t> hash_u32;
  std::optional<std::int32_t> mask_i32;
  std::optional<std::uintptr_t> table_identity;
  std::optional<std::int64_t> start_index_i64;
  std::optional<std::uint8_t> overflow_u8;
  std::optional<std::uintptr_t> end_slot_identity;
  std::optional<std::uintptr_t> found_slot_identity;
  std::vector<PersonFollowing2922680Probe> probes;
  std::optional<std::uint32_t> selected_value_u32;
  PersonFollowing2922680Resolution value_resolution;
  std::optional<std::uintptr_t> result_identity;
  std::optional<std::uint32_t> result_magic_u32;
  std::optional<std::uint32_t> result_full_id_u32;
  std::optional<bool> admitted;
  friend bool operator==(const PersonFollowing2922680Getter &,
                         const PersonFollowing2922680Getter &) = default;
};
struct PersonFollowing2922680Nested {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> object_identity;
  std::optional<std::uint32_t> selector_id_u32;
  std::optional<bool> matched;
  PersonFollowing2922680Pc primary_pc;
  PersonFollowing2922680Membership membership;
  friend bool operator==(const PersonFollowing2922680Nested &,
                         const PersonFollowing2922680Nested &) = default;
};
struct PersonFollowing2922680Item {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<std::uintptr_t> object_identity;
  std::optional<std::uint8_t> enabled_3f0_u8;
  PersonFollowing2922680Pc primary_pc;
  PersonFollowing2922680Membership membership;
  std::optional<std::int32_t> nested_count_i32;
  std::optional<std::uintptr_t> nested_array_identity;
  std::vector<PersonFollowing2922680Nested> nested;
  friend bool operator==(const PersonFollowing2922680Item &,
                         const PersonFollowing2922680Item &) = default;
};
struct PersonFollowing2922680SourceRow {
  std::uint32_t native_index = 0;
  bool ready = false;
  std::string reason;
  std::optional<bool> list_id_demanded;
  std::optional<std::uint32_t> list_full_id_u32;
  PersonFollowing2922680Resolution resolution;
  PersonFollowing2922680Getter getter;
  bool direct_ready = false;
  std::optional<std::uintptr_t> match_definition_identity;
  std::optional<std::uint32_t> match_id_u32;
  std::optional<std::uintptr_t> item_container_identity;
  std::optional<std::int32_t> item_count_i32;
  std::optional<std::uintptr_t> item_array_identity;
  std::vector<PersonFollowing2922680Item> items;
  friend bool operator==(const PersonFollowing2922680SourceRow &,
                         const PersonFollowing2922680SourceRow &) = default;
};

struct PersonFollowing2922680Row {
  std::uint32_t native_index = 0;
  bool ready = false;
  bool primary_ready = false;
  std::string reason;
  std::optional<bool> list_id_demanded;
  std::optional<std::uint32_t> list_full_id_u32;
  PersonFollowing2922680Resolution resolution;
  std::optional<std::int16_t> cached_date_c7ce_i16;
  std::optional<std::int32_t> raw_date_c7c8_i32;
  std::optional<std::int32_t> derived_year_i32;
  std::optional<std::uintptr_t> current_game_data_identity;
  std::optional<std::int32_t> current_date_i32;
  std::string date_branch = "unavailable";
  std::optional<bool> date_admitted;
  bool known_no_contribution = false;
  std::optional<std::int32_t> source_list_count_i32;
  std::optional<std::uintptr_t> source_list_array_identity;
  std::vector<PersonFollowing2922680SourceRow> sources;
  friend bool operator==(const PersonFollowing2922680Row &,
                         const PersonFollowing2922680Row &) = default;
};

struct PersonFollowing2922680DTO {
  std::string build_version;
  std::string executable_sha256;
  bool ready = false;
  std::string reason;
  std::optional<std::uint32_t> character_id;
  std::optional<std::uintptr_t> character_identity;
  std::optional<std::uintptr_t> selected_model_identity;
  // Identity only; never copied or used as a post-reset baseline.
  std::optional<std::uintptr_t> destination_pc_identity;
  std::optional<std::uintptr_t> character_context_1c0_identity;
  std::optional<std::uintptr_t> character_gate_1d0_identity;
  std::string header_selection = "unavailable";
  std::optional<std::uintptr_t> list_header_identity;
  std::optional<std::int32_t> list_count_i32;
  std::optional<std::uintptr_t> list_array_identity;
  PersonFollowing2922680Resolution rite_resolution;
  PersonFollowing2922680Resolution context_resolution;
  PersonFollowing2922680Resolution operand_rite_resolution;
  // Actual243EA10 returns selected Rite+750. Its pointed-to layout is not
  // inferred from this pointer getter; no PC array or weight is manufactured.
  bool source_operand_ready = false;
  std::string source_operand_reason;
  std::optional<std::uintptr_t> source_operand_identity;
  std::vector<PersonFollowing2922680Row> rows;
  bool primary_ready = false;
  std::vector<PersonFollowing2922680Append> append_occurrences;
  friend bool operator==(const PersonFollowing2922680DTO &,
                         const PersonFollowing2922680DTO &) = default;
};

// Same exact4 guarded-copy binding; no native getter, initializer, row
// consumer, context writer or Model callback is invoked.
PersonFollowing2922680DTO ReadPersonFollowing2922680ForModel12004(
    const PersonCarrierDirect12004Bindings &, std::uintptr_t actual_model);
PersonFollowing2922680DTO ReadPersonFollowing2922680ForCharacter12004(
    const PersonCarrierDirect12004Bindings &, std::uintptr_t actual_character);
std::string SerializePersonFollowing2922680(
    const PersonFollowing2922680DTO &);

} // namespace xar::ck3_12004
