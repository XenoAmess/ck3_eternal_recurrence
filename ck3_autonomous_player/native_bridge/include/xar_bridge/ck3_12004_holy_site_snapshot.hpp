#pragma once

#include "xar_bridge/ck3_12004_religion_bindings.hpp"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::religion::holy_site {

inline constexpr std::string_view kQueryStep = "query-player-holy-site-v1";
inline constexpr std::string_view kDomainKey = "player_holy_site_v1";
using ReadMemory = bool (*)(void *, const void *, void *, std::size_t) noexcept;

// Offsets are copied from the actual4 registered getters/serialization and
// native full-reference consumers. No old-image binder is admitted here.
struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  void **holy_site_storage = nullptr;
  void **faith_storage = nullptr;
  ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
};

struct FaithRelation {
  std::uint32_t faith_id = 0xFFFFFFFFU;
  bool available = false;
  bool faith_lists_site = false;
  bool eminent = false;
  std::string unavailable_reason;
};

struct Inventory {
  // HolySite.GetInventory returns the embedded object at site+0x28. There
  // is no observed independent inventory ID to substitute for its owner.
  bool available = false;
  std::uint32_t owner_holy_site_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> native_holy_site_owner_id;
  std::optional<std::uint32_t> native_character_owner_id;
  std::vector<std::uint32_t> artifact_ids;
  std::string unavailable_reason;
};

struct Site {
  bool available = false;
  std::uint32_t holy_site_id = 0xFFFFFFFFU;
  std::string type_key;
  std::uint32_t barony_title_id = 0xFFFFFFFFU;
  std::vector<FaithRelation> associated_faiths;
  Inventory inventory{};
  std::string unavailable_reason;
};

struct WindowModel {
  bool available = false;
  bool present = false;
  bool root_present = false;
  std::optional<std::uint32_t> holy_site_id;
  std::optional<std::uint32_t> holy_site_item_raw;
  std::string unavailable_reason;
};

struct RosterEntry {
  std::uint32_t holy_site_id = 0xFFFFFFFFU;
  std::string type_key;
  std::uint32_t barony_title_id = 0xFFFFFFFFU;
};

struct Snapshot {
  bool available = false;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::uint32_t> player_rite_id;
  std::optional<std::uint32_t> player_faith_id;
  std::optional<std::uint32_t> requested_holy_site_id;
  std::vector<std::uint32_t> current_faith_holy_site_ids;
  std::vector<Site> current_faith_sites;
  bool loaded_registry_roster_available = false;
  std::uint32_t loaded_registry_slot_count = 0;
  std::uint32_t loaded_registry_unreadable_slots = 0;
  std::vector<RosterEntry> loaded_registry_roster;
  WindowModel window_model{};
  std::optional<Site> selected_holy_site;
  std::string selection_source;
  std::string unavailable_reason;
};

Bindings BindHolySiteSnapshotImage12004(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;
// Only the existing religion owner mailbox supplies the current Jomini owner
// and actor/frame. A hidden registered window model is not rendered UI proof.
bool ReadHolySiteSnapshot12004(const Bindings &, const void *jomini_owner,
    const ck3_12002::religion::Context &,
    std::optional<std::uint32_t> requested_holy_site_id, Snapshot &) noexcept;
std::string SerializeHolySiteSnapshot12004(const Snapshot &);
std::string SerializeHolySiteCommand12004(const Snapshot &, std::string_view request_id,
    std::uint64_t snapshot_revision, std::int64_t date_raw);

} // namespace xar::ck3_12004::religion::holy_site
