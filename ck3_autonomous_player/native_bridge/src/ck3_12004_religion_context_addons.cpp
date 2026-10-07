#include "xar_bridge/ck3_12004_religion_context_addons.hpp"
#include "xar_bridge/ck3_12004_religion_profile.hpp"

#include <cstring>

namespace xar::ck3_12004::religion {
namespace {
namespace legacy = ck3_12002::religion;
namespace rite = ck3_12002::religion_conversion_rite;
namespace faith = ck3_12002::religion_conversion::faith;
namespace terms = ck3_12002::religion_conversion::terms;
namespace reasons = ck3_12002::religion_conversion::reasons;
namespace gates = legacy::conversion_gates;
namespace prediction = ck3_12002::religion_conversion_ai_inputs;
namespace outcome = ck3_12002::religion_conversion::outcome;

bool Admitted(std::uintptr_t base, std::string_view sha) noexcept {
  return base != 0 && sha == ck3_12004::kExecutableSha256;
}
template <typename T> T At(std::uintptr_t base, std::uintptr_t rva) noexcept {
  return reinterpret_cast<T>(base + rva);
}

// These are independently mapped native entrances and loaded RIP targets.
// No old image factory is given the new executable identity.
template <typename T> T DecisionBindings(std::uintptr_t base) noexcept {
  T b{};
  b.enabled = true;
  b.decision_database = At<decltype(b.decision_database)>(base, 0x5D1DEF0);
  b.decision_fallback = At<decltype(b.decision_fallback)>(base, 0x5D1F7E8);
  b.decision_hash = At<decltype(b.decision_hash)>(base, 0x3F7E220);
  b.decision_lookup = At<decltype(b.decision_lookup)>(base, 0xCAA8D0);
  b.root_construct = At<decltype(b.root_construct)>(base, 0x889F60);
  b.root_destroy = At<decltype(b.root_destroy)>(base, 0x87E0E0);
  b.decision_shown = At<decltype(b.decision_shown)>(base, 0x31033E0);
  b.decision_can_take = At<decltype(b.decision_can_take)>(base, 0x31034F0);
  b.decision_cost = At<decltype(b.decision_cost)>(base, 0x14706B0);
  b.cost_evaluate = At<decltype(b.cost_evaluate)>(base, 0x310CE50);
  b.cost_affordable = At<decltype(b.cost_affordable)>(base, 0x310B390);
  b.reason_destroy = At<decltype(b.reason_destroy)>(base, 0x856050);
  return b;
}

bool ReadLocalMemory(void *, std::uintptr_t address, void *out,
    std::size_t size) noexcept {
  if (!address || !out || !size) return false;
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    std::memcpy(out, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return false; }
#endif
}

enum class FrameFailure { none, bindings, played, paused };
FrameFailure SelectPlayedFrame(const CoreBindings &core,
    CoreSnapshotPrefix &frame) noexcept {
  if (!core.enabled) return FrameFailure::bindings;
#if defined(_WIN32) && defined(_MSC_VER)
  __try {
#endif
    if (!ck3_12004::ReadCoreSnapshot(core, frame) || !frame.map_ready ||
        !frame.has_played_character || !frame.played_character_alive ||
        !ck3_12004::ResolveCoreCharacter(core, frame.played_character_id))
      return FrameFailure::played;
    return frame.clock.paused ? FrameFailure::none : FrameFailure::paused;
#if defined(_WIN32) && defined(_MSC_VER)
  } __except (1) { return FrameFailure::played; }
#endif
}
const char *FrameReason(FrameFailure failure) noexcept {
  switch (failure) {
  case FrameFailure::none: return "none";
  case FrameFailure::bindings: return "bindings_unavailable";
  case FrameFailure::played: return "played_character_unavailable";
  case FrameFailure::paused: return "frame_not_paused";
  }
  return "played_character_unavailable";
}
template <typename T> void Stamp(T &out, std::uint64_t epoch,
    const CoreSnapshotPrefix &frame) noexcept {
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id =
      static_cast<decltype(out.played_character_id)>(frame.played_character_id);
}
template <typename Failure> Failure FrameFailureValue(FrameFailure value) noexcept {
  return value == FrameFailure::paused ? Failure::frame_not_paused
      : (value == FrameFailure::bindings ? Failure::bindings_unavailable
                                        : Failure::played_character_unavailable);
}
} // namespace

ContextAddonBindings BindReligionContextAddonsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ContextAddonBindings out{};
  if (!Admitted(base, sha)) return out;
  const auto core = ck3_12004::BindCoreImage(base, sha);

  auto &progress = out.progress_bindings;
  progress.enabled = true;
  progress.database_slot = At<decltype(progress.database_slot)>(base, 0x5D1F6D0);
  progress.type_for_character = At<decltype(progress.type_for_character)>(base, 0x3181BD0);
  progress.level_for_value = At<decltype(progress.level_for_value)>(base, 0x3181350);
  progress.progress_within_level = At<decltype(progress.progress_within_level)>(base, 0x1870000);
  progress.minimum = At<decltype(progress.minimum)>(base, 0x5C68E00);
  progress.maximum = At<decltype(progress.maximum)>(base, 0x5C68DF8);

  out.mystical_communion_bindings =
      DecisionBindings<decltype(out.mystical_communion_bindings)>(base);
  out.confession_bindings =
      DecisionBindings<decltype(out.confession_bindings)>(base);
  out.vow_of_poverty_bindings =
      DecisionBindings<decltype(out.vow_of_poverty_bindings)>(base);

  auto &pilgrimage = out.pilgrimage_bindings;
  pilgrimage.enabled = true;
  pilgrimage.activity_type_database = At<decltype(pilgrimage.activity_type_database)>(base, 0x5C67208);
  pilgrimage.activity_type_vtable = base + 0x48BFE60;
  pilgrimage.can_plan = At<decltype(pilgrimage.can_plan)>(base, 0x9DC990);
  pilgrimage.can_plan_tooltip = At<decltype(pilgrimage.can_plan_tooltip)>(base, 0x9DCC40);
  pilgrimage.reason_destroy = At<decltype(pilgrimage.reason_destroy)>(base, 0x856050);

  auto &activity = out.pilgrimage_activity_bindings;
  activity.activity_type = pilgrimage;
  auto &candidates = activity.candidates;
  candidates.enabled = true;
  candidates.provinces.enabled = true;
  candidates.provinces.game_state_slot = core.game_state_slot;
  candidates.character_rite = At<decltype(candidates.character_rite)>(base, profile::kCharacterRiteRva);
  candidates.rite_faith = At<decltype(candidates.rite_faith)>(base, profile::kRiteFaithRva);
  candidates.holy_site_storage = At<decltype(candidates.holy_site_storage)>(base, 0x5D1DE80);
  candidates.title_storage = At<decltype(candidates.title_storage)>(base, 0x5D1DAF8);
  candidates.province_array_allocator = At<decltype(candidates.province_array_allocator)>(base, 0x54DEF30);
  candidates.phase_choice_allocator = At<decltype(candidates.phase_choice_allocator)>(base, 0x54E13F8);
  candidates.filter_provinces = At<decltype(candidates.filter_provinces)>(base, 0x2C296F0);
  candidates.root_construct = At<decltype(candidates.root_construct)>(base, 0x889F60);
  candidates.actor_root_construct = At<decltype(candidates.actor_root_construct)>(base, 0x9F9E20);
  candidates.root_destroy = At<decltype(candidates.root_destroy)>(base, 0x87E0E0);
  candidates.named_scope_save = At<decltype(candidates.named_scope_save)>(base, 0x373A0F0);
  candidates.host_token = At<decltype(candidates.host_token)>(base, 0x5D4BE40);
  candidates.special_token = At<decltype(candidates.special_token)>(base, 0x5D4C0B8);
  candidates.location_token = At<decltype(candidates.location_token)>(base, 0x5D4BDDC);
  candidates.predicate = At<decltype(candidates.predicate)>(base, 0x372DF10);
  candidates.predicate_with_evaluator = At<decltype(candidates.predicate_with_evaluator)>(base, 0x372E4D0);
  candidates.allocate = At<decltype(candidates.allocate)>(base, 0x4223B94);
  candidates.deallocate = At<decltype(candidates.deallocate)>(base, 0x4223F44);
  candidates.evaluator_construct = At<decltype(candidates.evaluator_construct)>(base, 0x37C66C0);
  candidates.evaluator_prepare_first = At<decltype(candidates.evaluator_prepare_first)>(base, 0x37EB170);
  candidates.evaluator_prepare_second = At<decltype(candidates.evaluator_prepare_second)>(base, 0x37EB270);
  candidates.evaluator_format = At<decltype(candidates.evaluator_format)>(base, 0x375DCA0);
  candidates.evaluator_destroy = At<decltype(candidates.evaluator_destroy)>(base, 0x219FE00);
  candidates.reason_destroy = At<decltype(candidates.reason_destroy)>(base, 0x856050);
  candidates.total_phase_cap = At<decltype(candidates.total_phase_cap)>(base, 0x31144F0);
  candidates.same_province_phase_cap = At<decltype(candidates.same_province_phase_cap)>(base, 0x3114580);
  candidates.phase_offers = At<decltype(candidates.phase_offers)>(base, 0x1A721C0);
  activity.config_initialize = At<decltype(activity.config_initialize)>(base, 0x23FB430);
  activity.selected_special = At<decltype(activity.selected_special)>(base, 0x23FC7E0);
  activity.phase_insert = At<decltype(activity.phase_insert)>(base, 0x11BF700);
  activity.config_normalize = At<decltype(activity.config_normalize)>(base, 0x23FC560);
  activity.activity_cost = At<decltype(activity.activity_cost)>(base, 0x2BBE6F0);
  activity.activity_affordable = At<decltype(activity.activity_affordable)>(base, 0x310E6F0);
  activity.config_destroy = At<decltype(activity.config_destroy)>(base, 0x11B30E0);
  activity.reason_destroy = At<decltype(activity.reason_destroy)>(base, 0x856050);
  activity.enabled = activity.activity_type.enabled && candidates.enabled;

  auto &route = out.pilgrimage_route_bindings;
  route.enabled = true;
  route.provinces.enabled = true;
  route.provinces.game_state_slot = core.game_state_slot;
  route.participant_allocator = At<decltype(route.participant_allocator)>(base, 0x54DEC70);
  route.travel_option_allocator = At<decltype(route.travel_option_allocator)>(base, 0x54DEC68);
  route.descriptor_allocator = At<decltype(route.descriptor_allocator)>(base, 0x54DEC78);
  route.native_default_date = At<decltype(route.native_default_date)>(base, 0x5C7DD38);
  route.province_ids_initialize = At<decltype(route.province_ids_initialize)>(base, 0xB2C530);
  route.waypoints_initialize = At<decltype(route.waypoints_initialize)>(base, 0xB2C460);
  route.province_ids_append = At<decltype(route.province_ids_append)>(base, 0xADD0D0);
  route.root_construct = At<decltype(route.root_construct)>(base, 0x889F60);
  route.creation_input_destroy = At<decltype(route.creation_input_destroy)>(base, 0x9DDFF0);
  route.data_construct = At<decltype(route.data_construct)>(base, 0x2323780);
  route.data_destroy = At<decltype(route.data_destroy)>(base, 0x9DE150);
  route.start_province = At<decltype(route.start_province)>(base, 0x2324950);
  route.evaluate_route = At<decltype(route.evaluate_route)>(base, 0x2329530);
  route.evaluate_arrival = At<decltype(route.evaluate_arrival)>(base, 0x232A070);

  // This existing permission reader consumes only these two typed inputs.
  // Draft-window and unused source-filter callbacks are not prerequisites.
  auto &permission = out.confession_permission_bindings;
  permission.enabled = true;
  permission.tenet_database_global = At<decltype(permission.tenet_database_global)>(base, profile::kTenetDatabaseSlotRva);
  permission.source_main_rite_status = At<decltype(permission.source_main_rite_status)>(base, profile::kNativeTenetStateRva);

  auto &income = out.church_income_bindings;
  income.enabled = true;
  income.monthly_income = At<decltype(income.monthly_income)>(base, 0x2642300);
  auto &tax = out.church_tax_bindings;
  tax.enabled = true;
  tax.core = core;
  tax.game_state_slot = core.game_state_slot;
  tax.income_context = At<decltype(tax.income_context)>(base, 0x28BFC50);
  tax.character_faith = At<decltype(tax.character_faith)>(base, profile::kCharacterFaithRva);
  tax.faith_lease_contract = At<decltype(tax.faith_lease_contract)>(base, 0x2442E00);
  tax.lease_liege = At<decltype(tax.lease_liege)>(base, 0x2A22F80);
  tax.top_lease_liege_direct = At<decltype(tax.top_lease_liege_direct)>(base, 0x2A26880);
  tax.prior_share = At<decltype(tax.prior_share)>(base, 0x31BFA00);
  tax.ruler_share = At<decltype(tax.ruler_share)>(base, 0x31BFC30);
  tax.income_rules = At<decltype(tax.income_rules)>(base, 0x31C0190);
  tax.string_destroy = At<decltype(tax.string_destroy)>(base, 0x856050);
  tax.lease_liege_label = At<decltype(tax.lease_liege_label)>(base, 0x449F2F0);
  tax.top_lease_liege_direct_label = At<decltype(tax.top_lease_liege_direct_label)>(base, 0x46DB428);

  auto &devotion = out.devotion_bindings;
  devotion.enabled = true;
  devotion.effective_level = At<decltype(devotion.effective_level)>(base, 0x28BE0B0);
  devotion.progress_percent = At<decltype(devotion.progress_percent)>(base, 0x2BB0890);
  devotion.effective_cap = At<decltype(devotion.effective_cap)>(base, 0x2696650);
  devotion.threshold_progress = At<decltype(devotion.threshold_progress)>(base, 0x26979D0);
  devotion.threshold_vector = At<decltype(devotion.threshold_vector)>(base, 0x2696730);
  auto &virtue = out.rite_virtue_sin_bindings;
  virtue.enabled = true;
  virtue.trait_database = At<decltype(virtue.trait_database)>(base, 0x89E5B0);
  virtue.trait_lookup = At<decltype(virtue.trait_lookup)>(base, 0xC85E80);
  virtue.character_rite = At<decltype(virtue.character_rite)>(base, profile::kCharacterRiteRva);
  virtue.trait_classification = At<decltype(virtue.trait_classification)>(base, 0x2BD8480);
  return out;
}

HostilityBindings BindHostilityImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  HostilityBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.context = BindReligionContextImage12004(base, sha);
  b.rite_storage_slot = At<decltype(b.rite_storage_slot)>(base, profile::kRiteStorageSlotRva);
  b.rite_hostility = At<decltype(b.rite_hostility)>(base, 0x2591CC0);
  b.faith_hostility = At<decltype(b.faith_hostility)>(base, 0x243E930);
  return b;
}

rite::FaithAndRiteConversionCommand MakeReadOnlyConvertRiteValue12004(
    std::uintptr_t base, std::int32_t actor, std::uint32_t target,
    bool pay_piety) noexcept {
  rite::FaithAndRiteConversionCommand command{};
  command.primary_vtable = base + 0x4770350;
  command.secondary_vtable = base + 0x47703E8;
  command.actor_id = actor;
  command.target_rite_id = target;
  command.pay_piety = pay_piety ? 1 : 0;
  return command;
}

outcome::Bindings BindConversionOutcomeImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  outcome::Bindings b{};
  if (!Admitted(base, sha)) return b;
  b.actor.current_religion = BindReligionContextImage12004(base, sha);
  b.actor.read_memory = &ReadLocalMemory;
  auto &state = b.state;
  state.enabled = true;
  state.core = ck3_12004::BindCoreImage(base, sha);
  state.rite_storage_slot = At<decltype(state.rite_storage_slot)>(base, profile::kRiteStorageSlotRva);
  state.rite_knowledge = At<decltype(state.rite_knowledge)>(base, 0x2BDBDC0);
  state.existing_atom = At<decltype(state.existing_atom)>(base, 0x3F8A380);
  state.atom_pool = At<decltype(state.atom_pool)>(base, 0x5DC1390);
  state.character_flag_collection = At<decltype(state.character_flag_collection)>(base, 0x1D671E0);
  state.character_spiritual_fulfillment = At<decltype(state.character_spiritual_fulfillment)>(base, profile::kCharacterSpiritualFulfillmentRva);
  return b;
}

ConversionBindings BindReligionConversionImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  ConversionBindings b{};
  if (!Admitted(base, sha)) return b;
  const auto core = ck3_12004::BindCoreImage(base, sha);
  b.rite.enabled = true;
  b.rite.module_base = base;
  b.rite.core = core;
  b.rite.rite_storage_slot = At<decltype(b.rite.rite_storage_slot)>(base, profile::kRiteStorageSlotRva);
  b.rite.validate = At<decltype(b.rite.validate)>(base, 0x29A34A0);
  b.rite.character_faith = At<decltype(b.rite.character_faith)>(base, profile::kCharacterFaithRva);
  b.rite.faith_rites = At<decltype(b.rite.faith_rites)>(base, 0xB801B0);
  b.rite.read_only_value_factory = &MakeReadOnlyConvertRiteValue12004;
  b.faith.enabled = true;
  b.faith.core = core;
  b.faith.faith_storage_slot = At<decltype(b.faith.faith_storage_slot)>(base, 0x5D1E300);
  b.faith.character_faith = At<decltype(b.faith.character_faith)>(base, profile::kCharacterFaithRva);
  b.faith.faith_main_rite = At<decltype(b.faith.faith_main_rite)>(base, profile::kFaithMainRiteRva);
  b.faith.rite_faith = At<decltype(b.faith.rite_faith)>(base, profile::kRiteFaithRva);
  b.faith.faith_tag = At<decltype(b.faith.faith_tag)>(base, profile::kFaithTagRva);
  b.faith.conversion_rule = At<decltype(b.faith.conversion_rule)>(base, 0x1D635C0);
  b.cost.enabled = true;
  b.cost.core = core;
  b.cost.rite_database = At<decltype(b.cost.rite_database)>(base, profile::kRiteStorageSlotRva);
  b.cost.character_rite = At<decltype(b.cost.character_rite)>(base, profile::kCharacterRiteRva);
  b.cost.character_faith = At<decltype(b.cost.character_faith)>(base, profile::kCharacterFaithRva);
  b.cost.rite_faith = At<decltype(b.cost.rite_faith)>(base, profile::kRiteFaithRva);
  b.cost.final_piety_cost = At<decltype(b.cost.final_piety_cost)>(base, 0x29A3DC0);
  b.cost.command_vtable = base + 0x4770350;
  b.cost.command_secondary_vtable = base + 0x47703E8;
  b.terms = {b.rite, b.cost};
  b.reasons.rite = b.rite;
  b.reasons.destroy_string = At<decltype(b.reasons.destroy_string)>(base, 0x856050);
  b.gates.enabled = true;
  b.gates.state.enabled = true;
  b.gates.state.context = BindReligionContextImage12004(base, sha);
  b.gates.state.character_top_liege = At<decltype(b.gates.state.character_top_liege)>(base, 0x28BFD80);
  b.gates.state.character_primary_title = At<decltype(b.gates.state.character_primary_title)>(base, 0x289DA10);
  b.gates.state.title_state_rite = At<decltype(b.gates.state.title_state_rite)>(base, 0x2315010);
  b.gates.rite_storage_slot = At<decltype(b.gates.rite_storage_slot)>(base, profile::kRiteStorageSlotRva);
  b.gates.rite_knowledge = At<decltype(b.gates.rite_knowledge)>(base, 0x2BDBDC0);
  b.gates.existing_atom = At<decltype(b.gates.existing_atom)>(base, 0x3F8A380);
  b.gates.atom_pool = At<decltype(b.gates.atom_pool)>(base, 0x5DC1390);
  b.gates.character_flag_collection = At<decltype(b.gates.character_flag_collection)>(base, 0x1D671E0);
  b.prediction.enabled = true;
  b.prediction.core = core;
  b.prediction.rite_storage_slot = b.rite.rite_storage_slot;
  b.prediction.base_fulfillment = At<decltype(b.prediction.base_fulfillment)>(base, 0x2BFC250);
  b.outcome = BindConversionOutcomeImage12004(base, sha);
  return b;
}

bool ReadPlayedHostilityTowardsRite12004(const HostilityBindings &b,
    std::uint32_t target, std::uint64_t epoch,
    legacy::doctrine12002::HostilityObservation &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameFailureValue<legacy::doctrine12002::HostilityFailure>(failure);
    return false;
  }
  const bool read = legacy::doctrine12002::ReadPlayedHostilityTowardsRite12002(b, target, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedReligionConversionTerms12004(const terms::Bindings &b,
    std::uint32_t target, std::uint64_t epoch, terms::Terms &out) noexcept {
  out = {};
  out.target_rite_id = target;
  CoreSnapshotPrefix frame{};
  const auto failure = b.rite.enabled ? SelectPlayedFrame(b.rite.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = terms::Failure::final_gate_unavailable;
    Stamp(out.final_gate, epoch, frame);
    out.final_gate.target_rite_id = target;
    out.final_gate.failure = FrameFailureValue<rite::Failure>(failure);
    return false;
  }
  const bool read = terms::ReadPlayedReligionConversionTerms12002(b, target, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedFaithConversionChoices12004(const faith::Bindings &b,
    std::uint64_t epoch, faith::Choices &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) { out.unavailable_reason = FrameReason(failure); return false; }
  const bool read = faith::ReadPlayedFaithConversionChoices12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadCurrentFaithRites12004(const rite::Bindings &b,
    std::uint64_t epoch, rite::FaithRites &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameFailureValue<rite::Failure>(failure); return false;
  }
  const bool read = rite::ReadCurrentFaithRites12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedReligionConversionReasons12004(const reasons::Bindings &b,
    std::uint32_t target, std::uint64_t epoch, reasons::Reasons &out) noexcept {
  out = {};
  out.target_rite_id = target;
  CoreSnapshotPrefix frame{};
  const auto failure = b.rite.enabled ? SelectPlayedFrame(b.rite.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameFailureValue<reasons::Failure>(failure); return false;
  }
  const bool read = reasons::ReadPlayedReligionConversionReasons12002(b, target, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedReligionConversionGates12004(const gates::Bindings &b,
    std::uint32_t target, std::uint64_t epoch, gates::Context &out) noexcept {
  out = {};
  out.requested_target_rite_id = target;
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.state.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::played ? gates::Failure::played_character_unavailable
        : (failure == FrameFailure::paused ? gates::Failure::state_rite_unavailable
                                          : gates::Failure::bindings_unavailable);
    return false;
  }
  const bool read = gates::ReadPlayedReligionConversionGates12002(b, target, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadExpectedRiteFulfillment12004(const prediction::Bindings &b,
    std::uint64_t epoch, std::uint32_t target,
    prediction::FulfillmentInput &out) noexcept {
  out = {};
  out.target_rite_id = target;
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameFailureValue<prediction::Failure>(failure); return false;
  }
  const bool read = prediction::ReadExpectedRiteFulfillment12002(b, epoch, target, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedConversionFervorInputs12004(const gates::Bindings &b,
    std::uint32_t target, std::uint64_t epoch,
    legacy::conversion_fervor::Context &out) noexcept {
  out = {};
  out.requested_target_rite_id = target;
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.state.context.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = FrameFailureValue<legacy::conversion_fervor::Failure>(failure); return false;
  }
  const bool read = legacy::conversion_fervor::ReadPlayedConversionFervorInputs12003(b, target, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedConversionOutcome12004(const outcome::Bindings &b,
    std::uint32_t target, std::uint64_t epoch, outcome::Context &out) noexcept {
  out = {};
  out.target_rite_id = target;
  CoreSnapshotPrefix frame{};
  const auto failure = b.actor.current_religion.enabled
      ? SelectPlayedFrame(b.actor.current_religion.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = outcome::Failure::actor_and_state_unavailable;
    Stamp(out.actor, epoch, frame);
    Stamp(out.state, epoch, frame);
    out.state.requested_target_rite_id = target;
    out.actor.failure = FrameFailureValue<outcome::actor::Failure>(failure);
    out.state.failure = FrameFailureValue<outcome::state::Failure>(failure);
    return false;
  }
  const bool read = outcome::ReadPlayedConversionOutcome12002(b, target, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}
} // namespace xar::ck3_12004::religion
