#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::religion::holy_site_relic {
inline constexpr std::string_view kQueryStep = "query-player-holy-site-relic-context-v1";
inline constexpr std::string_view kDomainKey = "player_holy_site_relic_context_v1";
using ReadMemory = bool (*)(void *, const void *, void *, std::size_t) noexcept;
struct Bindings;
// Returns whether the invocation itself completed; the native Boolean is out.
using RecognitionGetter = bool (*)(const Bindings &, const void *, std::uint32_t, bool &) noexcept;
using CurrentRarityGetter = bool (*)(const Bindings &, const void *, std::int32_t &) noexcept;
struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void **holy_site_storage = nullptr, **artifact_storage = nullptr;
  void **title_storage = nullptr, **character_storage = nullptr;
  void **rite_storage = nullptr, **faith_storage = nullptr;
  ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
  RecognitionGetter recognition = nullptr;
  CurrentRarityGetter current_rarity = nullptr;
  std::string_view getter_backend = "unavailable";
};
struct Recognition {
  bool available = false;
  std::optional<std::uint32_t> faith_id;
  std::optional<bool> value;
  std::string unavailable_reason = "recognition_not_read";
};
struct Artifact {
  std::uint32_t artifact_id = 0xFFFFFFFFU;
  bool available = false;
  std::optional<std::int32_t> rarity_level;
  std::optional<std::uint32_t> native_holy_site_owner_id;
  bool sanctified_faith_ids_available = false;
  std::vector<std::uint32_t> sanctified_faith_ids;
  Recognition recognition_for_player_faith{}, recognition_for_county_holder_faith{};
  std::string unavailable_reason = "artifact_not_read";
};
struct Slot {
  std::uint32_t slot_index = 0;
  std::optional<std::uint32_t> artifact_id;
};
struct CachedWorldState {
  bool available = false;
  std::optional<bool> is_active;
  std::optional<std::int32_t> total_active_artifact_rarity;
  std::string unavailable_reason = "world_cache_not_read";
};
struct CountyContext {
  bool available = false;
  std::optional<std::uint32_t> barony_title_id, county_title_id;
  std::optional<std::uint32_t> county_holder_id, county_holder_rite_id, county_holder_faith_id;
  std::string unavailable_reason = "county_context_not_read";
};
struct Inventory {
  bool available = false;
  std::vector<std::uint32_t> artifact_ids;
  std::vector<Slot> slots;
  std::vector<Artifact> artifact_objects;
  std::string unavailable_reason = "inventory_not_read";
};
struct CurrentEvaluation {
  bool available = false;
  std::optional<std::int32_t> inventory_artifact_count_raw;
  std::optional<bool> county_holder_faith_associated;
  std::optional<std::int32_t> active_artifact_rarity_sum;
  std::optional<bool> is_active, cache_evaluation_disagreement;
  std::string unavailable_reason = "current_relic_evaluation_not_read";
};
struct Snapshot {
  bool available = false;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0, played_character_id = -1;
  std::optional<std::uint32_t> player_rite_id, player_faith_id;
  std::uint32_t requested_holy_site_id = 0xFFFFFFFFU, holy_site_id = 0xFFFFFFFFU;
  bool associated_faith_ids_available = false;
  std::vector<std::uint32_t> associated_faith_ids;
  CachedWorldState cached_world_state{};
  CountyContext county_context{};
  Inventory inventory{};
  CurrentEvaluation current_relic_evaluation{};
  std::uint32_t native_getter_calls = 0;
  std::string getter_backend = "unavailable";
  std::string unavailable_reason = "holy_site_relic_context_not_read";
};
Bindings BindHolySiteRelicContextImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Existing paused application-main religion owner callback only. This does not
// refresh world caches, submit commands, choose a slot or declare beneficiaries.
// The original recognition getter allocates script context and uses TLS. Its
// deeper trigger/RNG state effects are unverified, and are disclosed in JSON.
bool ReadHolySiteRelicContext12004(const Bindings &,
    const ck3_12002::religion::Context &, std::uint32_t holy_site_id, Snapshot &) noexcept;
std::string SerializeHolySiteRelicContext12004(const Snapshot &);
std::string SerializeHolySiteRelicContextCommand12004(const Snapshot &,
    std::string_view request_id, std::uint64_t snapshot_revision, std::int64_t date_raw);
} // namespace xar::ck3_12004::religion::holy_site_relic
