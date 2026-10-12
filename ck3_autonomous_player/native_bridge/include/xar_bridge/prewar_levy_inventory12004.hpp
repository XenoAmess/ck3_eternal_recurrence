#pragma once

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_military.hpp"
#include "xar_bridge/ck3_12003_army_reserve.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kPrewarLevyCollectorRva12004 = 0x2C175B0;
inline constexpr std::uintptr_t kPrewarLevyCountRva12004 = 0x2C10B60;
inline constexpr std::uintptr_t kPrewarLevyDescriptorVtableRva12004 = 0x44DEFB8;

enum class PrewarLevyInventoryStatus12004 { unavailable, partial, available };

struct PrewarLevyInventoryRequest12004 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  // Native full-generation subject, independent of the current player. Only
  // -1 is the absent native reference; no owner identity is encoded in a row.
  std::int32_t owner_character_id = -1;
};

struct PrewarLevyDescriptor12004 {
  std::int32_t source_ordinal = -1;
  std::optional<std::uintptr_t> descriptor_vtable_rva;
  bool descriptor_identity_ready = false;
  std::optional<std::int32_t> persistent_regiment_id;
  std::optional<std::int32_t> chunk_ordinal;
  std::optional<std::int32_t> contribution_cap_raw;
  std::optional<std::uint8_t> flag14_raw;
  std::optional<std::uint8_t> flag15_raw;
  std::optional<std::int32_t> observed_persistent_full_id;
  std::optional<std::int32_t> persistent_owner_character_id;
  std::optional<std::int32_t> chunk_persistent_backlink;
  std::optional<std::int32_t> native_chunk_ordinal;
  std::optional<std::int32_t> army_regiment_id;
  std::optional<std::int32_t> current_soldiers_raw;
  std::optional<std::int32_t> maximum_soldiers_raw;
  std::optional<std::uint8_t> pending_raw;
  std::optional<std::int32_t> state_raw;
  std::optional<std::int32_t> source_province_id;
  bool physical_fields_ready = false;
  bool native_count_inputs_ready = false;
  std::string failure;
  bool operator==(const PrewarLevyDescriptor12004 &) const = default;
};

struct PrewarLevyInventorySnapshot12004 {
  PrewarLevyInventoryStatus12004 status =
      PrewarLevyInventoryStatus12004::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::int32_t owner_character_id = -1;
  bool exact_build_ready = false;
  bool owner_identity_ready = false;
  bool source_frame_ready = false;
  bool cleanup_ready = false;
  std::optional<std::int32_t> source_count;
  bool collection_complete = false;
  // All mask-F occurrences, including assigned/pending shares. Order and
  // duplicates are retained. The leading native vtable is never an owner ID.
  std::string source_scope = "native_character_mask_f_levy_descriptors";
  std::vector<PrewarLevyDescriptor12004> descriptors;
  // Stock mode 0 uses min(cap,effective current), including maximum==0 -> cap
  // and state==3/current==0 -> maximum. Mode 1 adds cap; state==1 is skipped
  // by both. These exact signed32 results are separate from physical raw
  // soldiers, full military strength, a force bound and final raise legality.
  std::optional<std::int32_t> native_mode0_count;
  std::optional<std::int32_t> native_mode1_count;
  bool native_counts_ready = false;
  std::string failure;
  bool operator==(const PrewarLevyInventorySnapshot12004 &) const = default;
};

struct PrewarLevyInventoryBindings12004 {
  bool enabled = false;
  std::uintptr_t module_base = 0;
  void **persistent_regiment_storage_slot = nullptr;
  ck3_12003::PlayerArmyReserveBindingsV1 lifetime;
  // The stock wrapper derives its native Q100000 contribution factor and calls
  // the six-argument recursive collector. Do not replace it with a fixed factor.
  void (*collect)(void *character, void *descriptor_vector,
                  std::uint32_t mask) = nullptr;
  std::int32_t (*count)(void *descriptor_vector, std::int32_t mode) = nullptr;
};

PrewarLevyInventoryBindings12004 BindPrewarLevyInventoryImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::ArmyBindings &armies) noexcept;

// Caller owns the paused application-main ticket and accepted revision, and
// compares every provider's complete DTO in two passes. Native temporary data,
// allocator addresses and Character pointers never enter the copied DTO. This
// constructs an empty local ArmyComposition and collects directly into +0x50;
// it never invokes the owner initializer, levy partition, raising or a command.
PrewarLevyInventoryStatus12004 ReadPrewarLevyInventory12004(
    const PrewarLevyInventoryBindings12004 &bindings,
    const ck3_12002::MilitaryWorldAccess &world,
    const PrewarLevyInventoryRequest12004 &request,
    PrewarLevyInventorySnapshot12004 &output) noexcept;

} // namespace xar::ck3_12004
