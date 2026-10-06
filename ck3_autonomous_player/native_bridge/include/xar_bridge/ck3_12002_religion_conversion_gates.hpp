#pragma once

#include "xar_bridge/religion_rite_governance12002_state_rite.hpp"

namespace xar::ck3_12002::religion::conversion_gates {

inline constexpr std::uintptr_t kRiteStorageSlotRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kRiteKnowledgeRva = 0x2BDBDE0;
inline constexpr std::uintptr_t kExistingAtomLookupRva = 0x3F8A3A0;
inline constexpr std::uintptr_t kAtomPoolRva = 0x5DC1390;
inline constexpr std::uintptr_t kCharacterFlagCollectionRva = 0x1D67200;
inline constexpr std::size_t kCharacterScriptDataOffset = 0x1B0;
inline constexpr std::size_t kCharacterDummyOffset = 0x1A5;
inline constexpr std::size_t kFlagRowsOffset = 0x10;
inline constexpr std::size_t kFlagCountOffset = 0x1C;
inline constexpr std::size_t kFlagRowStride = 0x20;
inline constexpr std::size_t kFlagKeyOffset = 0x08;
inline constexpr char kRecentConversionFlag[] = "faith_conversion_recently_converted";

struct NativeStringView {
  const char *data = nullptr;
  std::int32_t length = 0;
  std::uint8_t range_comparison = 1;
  std::uint8_t reserved[3]{};
};
static_assert(sizeof(NativeStringView) == 0x10);
static_assert(offsetof(NativeStringView, range_comparison) == 0x0C);
using KnowledgeGetter = std::int64_t *(*)(std::int64_t *, void *, void *);
using ExistingAtomLookup = std::uint32_t *(*)(void *, std::uint32_t *, const NativeStringView *);

struct Bindings {
  bool enabled = false;
  state_rite::Bindings state{};
  void **rite_storage_slot = nullptr;
  KnowledgeGetter rite_knowledge = nullptr;
  ExistingAtomLookup existing_atom = nullptr;
  void *atom_pool = nullptr;
  ObjectGetter character_flag_collection = nullptr;
};

enum class Failure {
  none, bindings_unavailable, state_rite_unavailable, played_character_unavailable,
  target_rite_unavailable, actor_faith_unavailable, target_faith_unavailable,
  actor_religion_unavailable, target_religion_unavailable,
  knowledge_unavailable, flag_pool_unavailable, flag_collection_unavailable,
  state_changed,
};

struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = kAbsentReference;
  std::uint32_t requested_target_rite_id = kAbsentReference;
  std::optional<std::uint32_t> target_rite_id;
  std::optional<std::uint32_t> actor_faith_id;
  std::optional<std::uint32_t> target_faith_id;
  std::optional<std::uint32_t> actor_religion_id;
  std::optional<std::uint32_t> target_religion_id;
  std::optional<std::uint32_t> realm_state_rite_id;
  std::optional<std::uint32_t> realm_state_faith_id;
  std::optional<std::int64_t> knowledge_level_raw;
  std::optional<bool> recently_converted;
  std::optional<bool> recent_flag_key_registered;
  std::optional<bool> same_faith;
  std::optional<bool> same_religion;
  std::optional<bool> state_rite_target_match;
  std::optional<bool> state_faith_target_match;
};

Bindings BindReligionConversionGatesImage12002(std::uintptr_t module_base,
                                             std::string_view executable_sha256) noexcept;
// Current played character and one complete-generation Rite ref only, in the
// existing paused owner. This observes inputs; it is not final conversion legality.
bool ReadPlayedReligionConversionGates12002(const Bindings &, std::uint32_t target_rite_id,
                                          std::uint64_t capture_epoch, Context &) noexcept;
// Thin public seam over the existing full-generation target resolver.
void *ResolveConversionTargetRite12002(const Bindings &, std::uint32_t target_rite_id) noexcept;
std::string SerializePlayedReligionConversionGates12002(const Context &);
const char *ReligionConversionGatesFailureKey(Failure) noexcept;

} // namespace xar::ck3_12002::religion::conversion_gates
