#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12002 {
struct OrdinaryHolyWarDeclarationContextV1;
}

namespace xar::ck3_12002::religion::holy_war_defender_join {

inline constexpr std::string_view kSchema12003 =
    "ck3_12003_holy_war_defender_join_inputs_v1";
inline constexpr std::uintptr_t kCollectorRva12003 = 0x2C0AAB0;
inline constexpr std::uintptr_t kEngineAllocatorRva12003 = 0x54DEDE0;

struct NativeCharacterVector {
  void **rows = nullptr;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
  void *allocator = nullptr;
};
static_assert(sizeof(NativeCharacterVector) == 0x18);
static_assert(offsetof(NativeCharacterVector, count) == 0x0C);
static_assert(offsetof(NativeCharacterVector, allocator) == 0x10);

using Collector = void (*)(void *, void *, void *, NativeCharacterVector *);
using FreeRows = void (*)(void *, void *, std::size_t);

struct Bindings {
  bool enabled = false;
  religion::Bindings faith{};
  Collector collector = nullptr;
  void *engine_allocator = nullptr;
  // Production uses the actual allocator's virtual slot +0x10. A fixture
  // supplies its own allocator callback without changing the collector ABI.
  FreeRows free_rows = nullptr;
};

enum class Failure {
  none,
  bindings_unavailable,
  declaration_context_unavailable,
  frame_not_paused,
  frame_mismatch,
  native_role_fallback,
  primary_attacker_unavailable,
  primary_defender_unavailable,
  native_collection_unavailable,
  native_vector_invalid,
  state_changed,
};

enum class FaithFailure {
  none,
  character_unavailable,
  rite_unavailable,
  faith_unavailable,
  faith_domain_mismatch,
  fervor_unavailable,
};

struct Joiner {
  std::uint32_t character_id = kAbsentReference;
  bool row_faith_available = false;
  bool row_fervor_available = false;
  FaithFailure failure = FaithFailure::character_unavailable;
  std::optional<std::uint32_t> rite_id;
  std::optional<std::uint32_t> faith_id;
  std::optional<std::int64_t> faith_fervor_raw;
  std::optional<bool> matches_primary_defender_faith;
};

struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t public_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::string declaration_id;
  game::DeclarableWarSnapshot selected;
  std::optional<std::uint32_t> primary_attacker_character_id;
  std::optional<std::uint32_t> primary_defender_character_id;
  bool primary_defender_faith_available = false;
  FaithFailure primary_defender_faith_failure = FaithFailure::character_unavailable;
  std::optional<std::uint32_t> primary_defender_rite_id;
  std::optional<std::uint32_t> primary_defender_faith_id;
  std::optional<std::uint32_t> cb_flags_raw;
  std::optional<bool> defender_faith_can_join;
  bool native_joiner_set_observed = false;
  std::vector<Joiner> joiners;
  static constexpr std::int64_t raw_scale = 100'000;
};

// Exact .3 binding only. The existing owner supplies its already-bound actual
// religion/core bindings; this binder performs address calculation only.
Bindings BindHolyWarDefenderJoinInputsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256,
    const religion::Bindings &actual_existing_faith) noexcept;

// Invoke once inside the existing finalized selected-context owner. Attacker
// is its additional role, defender its recipient; neither accepts a fallback.
bool ReadSelectedHolyWarDefenderJoinInputs12003(
    const Bindings &, void *actual_cb, void *actual_primary_attacker,
    void *actual_primary_defender, const OrdinaryHolyWarDeclarationContextV1 &,
    Context &) noexcept;
std::string SerializeHolyWarDefenderJoinInputs12003(const Context &);
const char *HolyWarDefenderJoinInputsFailureKey(Failure) noexcept;
const char *HolyWarDefenderJoinFaithFailureKey(FaithFailure) noexcept;

} // namespace xar::ck3_12002::religion::holy_war_defender_join
