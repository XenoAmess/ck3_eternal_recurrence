#pragma once

#include "xar_bridge/ck3_12004_person_following_2922680.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12004 {
inline constexpr char kKnightStatConsumptionSchema12004[] =
    "xar.ck3.knight-stat-consumption-12004-v1";
inline constexpr std::size_t kKnightStatConsumptionCapacity12004 = 32;

struct KnightConsumedContext12004 {
  std::uint16_t property_key = 0;
  std::uint64_t caller_return_rva = 0;
  std::optional<std::uint32_t> selected_character_id;
  std::optional<std::uintptr_t> selected_character_identity;
  std::optional<std::uintptr_t> context_identity;
  std::optional<std::int64_t> operand_raw;
  PersonFollowing2922680Pc consumed_pc;
  std::optional<std::uint64_t> preparation_capture_sequence;
  std::optional<std::uintptr_t> preparation_model_identity;
  std::optional<std::uintptr_t> preparation_context_identity;
  std::optional<std::uint32_t> preparation_owner_character_id;
  std::optional<bool> context_matches_preparation;
  std::optional<bool> owner_matches_preparation;
  std::optional<bool> pc_matches_preparation_post;
  std::string reason;
  friend bool operator==(const KnightConsumedContext12004 &,
                         const KnightConsumedContext12004 &) = default;
};

struct KnightConsumedOutput12004 {
  bool ready = false;
  std::optional<std::int32_t> max_size;
  std::optional<std::int64_t> siege_value_raw, damage_raw, toughness_raw;
  std::optional<std::int64_t> pursuit_raw, screen_raw;
  std::string reason;
  friend bool operator==(const KnightConsumedOutput12004 &,
                         const KnightConsumedOutput12004 &) = default;
};

struct KnightStatConsumptionEvent12004 {
  std::uint64_t sequence = 0;
  std::uint32_t thread_id = 0;
  std::optional<std::int32_t> observed_date_raw;
  std::optional<std::uint64_t> wrapper_caller_return_rva;
  std::string origin = "native_wrapper_output_unclassified";
  std::optional<std::int32_t> regiment_id;
  std::optional<std::int32_t> target_province_id;
  std::optional<std::uint32_t> linked_character_id;
  std::optional<std::uintptr_t> linked_character_identity;
  std::optional<std::int32_t> linked_prowess_points;
  std::optional<std::int32_t> loaded_damage_multiplier;
  std::optional<std::int32_t> loaded_toughness_multiplier;
  std::uintptr_t output_cache_identity = 0;
  std::optional<std::uintptr_t> native_return_identity;
  std::vector<KnightConsumedContext12004> contexts;
  KnightConsumedOutput12004 observed_output;
  bool entry_association_proven = false;
  std::string capture_reason;
  friend bool operator==(const KnightStatConsumptionEvent12004 &,
                         const KnightStatConsumptionEvent12004 &) = default;
};

struct KnightStatConsumptionQuery12004 {
  std::string build_version = "1.20.0.4";
  std::string executable_sha256;
  bool configured = false;
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::vector<KnightStatConsumptionEvent12004> events;
  std::string reason;
  friend bool operator==(const KnightStatConsumptionQuery12004 &,
                         const KnightStatConsumptionQuery12004 &) = default;
};

std::string SerializeKnightStatConsumptionQuery12004(
    const KnightStatConsumptionQuery12004 &);
} // namespace xar::ck3_12004
