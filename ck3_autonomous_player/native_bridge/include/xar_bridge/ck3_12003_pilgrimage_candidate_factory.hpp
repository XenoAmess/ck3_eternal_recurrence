#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::pilgrimage_candidate_factory {

struct PhaseRowView {
  const std::byte *data = nullptr;
  std::int32_t count = 0;
  static constexpr std::size_t stride = 0x38;
};
struct NativeArray {
  void *data = nullptr;
  std::int32_t capacity = 0, count = 0;
  const void *allocator = nullptr;
};
static_assert(sizeof(NativeArray) == 0x18);
struct PhaseContext {
  const void *activity_type = nullptr;
  void *actual_actor = nullptr;
  const void *selected_special = nullptr;
};
static_assert(sizeof(PhaseContext) == 0x18);
struct ScopeToken {
  std::int32_t kind = 0;
  std::int32_t padding = 0;
  std::uint64_t payload = 0;
};
static_assert(sizeof(ScopeToken) == 0x10);

using ObjectGetter = void *(*)(void *);
using ProvinceFilter = void (*)(const void *, void *, NativeArray *);
using RootConstruct = void *(*)(void *);
using ActorRootConstruct = void *(*)(void *, const std::int32_t *);
using Destroy = void (*)(void *);
using NamedScopeSave = void (*)(void *, std::int32_t, const ScopeToken *);
using Predicate = bool (*)(const void *, void *);
using PredicateWithEvaluator = bool (*)(const void *, void *, void *);
using Allocate = void *(*)(std::size_t);
using Deallocate = void (*)(void *, std::size_t);
using EvaluatorConstruct = void *(*)(void *);
using EvaluatorFormat = void (*)(void **, const void *, void *);
using PhaseCap = std::int32_t (*)(const void *, void *);
using PhaseOfferProvider = void (*)(const PhaseContext *, std::int32_t, const void *, NativeArray *);

struct Bindings {
  bool enabled = false;
  ck3_12002::ProvinceBindings provinces;
  ObjectGetter character_rite = nullptr, rite_faith = nullptr;
  void **holy_site_storage = nullptr, **title_storage = nullptr;
  const void *province_array_allocator = nullptr, *phase_choice_allocator = nullptr;
  ProvinceFilter filter_provinces = nullptr;
  RootConstruct root_construct = nullptr;
  ActorRootConstruct actor_root_construct = nullptr;
  Destroy root_destroy = nullptr;
  NamedScopeSave named_scope_save = nullptr;
  const std::int32_t *host_token = nullptr, *special_token = nullptr, *location_token = nullptr;
  Predicate predicate = nullptr;
  PredicateWithEvaluator predicate_with_evaluator = nullptr;
  Allocate allocate = nullptr;
  Deallocate deallocate = nullptr;
  EvaluatorConstruct evaluator_construct = nullptr;
  Destroy evaluator_prepare_first = nullptr, evaluator_prepare_second = nullptr;
  EvaluatorFormat evaluator_format = nullptr;
  Destroy evaluator_destroy = nullptr, reason_destroy = nullptr;
  PhaseCap total_phase_cap = nullptr, same_province_phase_cap = nullptr;
  PhaseOfferProvider phase_offers = nullptr;
};

struct PredicateResult {
  bool value = false;
  bool reasons_available = false;
  std::string reasons;
};
struct PhaseChoice {
  // Native definitions/Province objects remain world-owned. Never serialize
  // these addresses or delete them when the native backing array is released.
  const void *phase_definition = nullptr, *province = nullptr;
  std::int32_t phase_definition_index = -1, province_id = -1;
  std::int32_t native_ai_choice_score = 0;
  PredicateResult shown, location;
  bool can_select = false;
};
struct Candidate {
  std::uint32_t holy_site_id = 0xFFFFFFFFU, title_id = 0xFFFFFFFFU;
  std::int32_t province_id = -1;
  const void *province = nullptr;
  PredicateResult location_predicate;
  std::int32_t same_province_phase_count = 0;
  bool same_province_cap_applies = false;
  std::optional<std::int32_t> same_province_phase_cap;
  bool same_province_cap_allows = true;
  bool total_cap_applies = false;
  std::optional<bool> total_cap_allows;
  std::optional<bool> can_select;
  std::vector<PhaseChoice> phase_choices;
};
struct Candidates {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::int32_t played_character_id = -1;
  std::uint32_t rite_id = 0xFFFFFFFFU, faith_id = 0xFFFFFFFFU;
  std::int32_t native_filter = -1, configured_phase_count = 0, total_phase_cap = 0;
  bool single_location = false;
  // Raw row count is never substituted for the native valid-location count.
  // For fixed pilgrimage's native single_location branch this count is unused.
  std::optional<std::int32_t> resolved_location_phase_count;
  std::vector<Candidate> candidates;
};

Bindings BindPlayerPilgrimageCandidateFactoryImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// The actual owner supplies resolved player/type and a borrowed view of its
// fresh native activity config. The factory discovers its own native Faith
// holy-site candidates; no caller Province list can replace that discovery.
// Returns internal owned DTOs with world-owned borrowed definitions only.
// Call and consume within the same application owner callback/frame.
bool CollectPlayerPilgrimageCandidates12003(const Bindings &, void *actual_actor,
    std::int32_t full_played_actor_id, const void *actual_activity_type,
    const void *selected_special, PhaseRowView, Candidates &) noexcept;

} // namespace xar::ck3_12003::religion::pilgrimage_candidate_factory
