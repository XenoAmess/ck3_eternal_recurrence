#include "xar_bridge/ck3_12004_religion_adopted_observers.hpp"

#include <utility>

namespace xar::ck3_12004::religion::adopted {
namespace {
namespace legacy = ck3_12002::religion;
namespace reform = ck3_12002::religion_reform;

// Actual .4 finite spans and retained operands are recorded in the adopted
// observer-coverage functions23/leaf9/layout3 packets. Shared context/Core
// callbacks retain their existing actual .4 factory and source-use proof.
constexpr std::uintptr_t kHighestTierRva = 0x28AC690;
constexpr std::uintptr_t kIndependentRulerRva = 0x28BFFE0;
constexpr std::uintptr_t kRarePeriodsSlotRva = 0x5449D90;
constexpr std::uintptr_t kReformationToggleRva = 0x5448579;
constexpr std::uintptr_t kTopLiegeRva = 0x28BFD80;
constexpr std::uintptr_t kPrimaryTitleRva = 0x289DA10;
constexpr std::uintptr_t kTitleStateRiteRva = 0x2315010;
constexpr std::uintptr_t kRiteHeadIdRva = 0xD55CF0;
constexpr std::uintptr_t kRiteHeadRva = 0x24FC5F0;
constexpr std::uintptr_t kFaithHeadRva = 0x2439DF0;
constexpr std::uintptr_t kFaithHeadTitleRva = 0x2443F80;
constexpr std::uintptr_t kCountyCountRva = 0xB80410;
constexpr std::uintptr_t kFollowerCountRva = 0xEDDB90;
constexpr std::uintptr_t kFaithCollectorRva = 0x1C610C0;
constexpr std::uintptr_t kRiteCountyCollectorRva = 0x1D2B6D0;
// The county collector's actual RIP operands at +250/+522 resolve this slot.
constexpr std::uintptr_t kTitleStorageSlotRva = 0x5D1DAF8;

bool Admitted(std::uintptr_t base, std::string_view sha) noexcept {
  return base != 0 && sha == ck3_12004::kExecutableSha256;
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
template <typename T> void Stamp(T &out, std::uint64_t epoch,
    const CoreSnapshotPrefix &frame) noexcept {
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id =
      static_cast<decltype(out.played_character_id)>(frame.played_character_id);
}
bool ContextObserved(reform::AIContextStatus status) noexcept {
  return status == reform::AIContextStatus::observed_no_ai ||
      status == reform::AIContextStatus::observed_controllers;
}
bool ScheduleCacheObserved(const reform::ScheduleInputs &value) noexcept {
  return value.status == reform::ScheduleStatus::observed &&
      (value.ai_status == reform::ScheduleAIStatus::gates_only ||
       value.ai_status == reform::ScheduleAIStatus::observed);
}
bool ReadAIInputsOnce(const AIReformInputsBindings &b, std::uint64_t epoch,
    ck3_12002::PlayerReligionAIReformInputsObservation12002 &out) {
  CoreSnapshotPrefix before{};
  const auto failure = SelectPlayedFrame(b.core, before);
  Stamp(out, epoch, before);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::bindings ? "bindings_unavailable" :
        (failure == FrameFailure::paused ? "frame_not_paused" : "played_character_unavailable");
    return false;
  }
  auto *actor = ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id);
  if (!actor) { out.failure = "played_character_unavailable"; return false; }
  const auto id = static_cast<std::uint32_t>(before.played_character_id);
  out.context = reform::ReadActorReformAIContext12002(b.context, actor, id);
  out.schedule_base = reform::ReadReformScheduleInputs12002(b.schedule, actor, id, nullptr);
  for (std::size_t index = 0; index < out.context.controllers.size(); ++index) {
    ck3_12002::PlayerReligionAIReformControllerInputs12002 row{};
    row.context_index = static_cast<std::uint32_t>(index);
    row.schedule = reform::ReadReformScheduleInputs12002(
        b.schedule, actor, id, out.context.controllers[index].actual_ai);
    out.controller_inputs.push_back(row);
  }
  if (out.context.status == reform::AIContextStatus::observed_no_ai) {
    out.gate_inputs_observation_complete = true;
  } else if (out.context.status == reform::AIContextStatus::observed_controllers) {
    out.gate_inputs_observation_complete = !out.controller_inputs.empty();
    for (const auto &row : out.controller_inputs)
      out.gate_inputs_observation_complete =
          out.gate_inputs_observation_complete && ScheduleCacheObserved(row.schedule);
  }
  CoreSnapshotPrefix after{};
  if (SelectPlayedFrame(b.core, after) != FrameFailure::none ||
      after.clock.date_raw != before.clock.date_raw ||
      after.played_character_id != before.played_character_id ||
      ck3_12004::ResolveCoreCharacter(b.core, before.played_character_id) != actor) {
    out.failure = "state_changed"; return false;
  }
  out.available = ContextObserved(out.context.status) ||
      out.schedule_base.status == reform::ScheduleStatus::observed;
  out.failure = out.available ? "none" : "actual_ai_inputs_unavailable";
  return out.available;
}
bool ReadAIInputsGuarded(const AIReformInputsBindings &b, std::uint64_t epoch,
    ck3_12002::PlayerReligionAIReformInputsObservation12002 &out) {
#if defined(_WIN32) && defined(_MSC_VER)
  __try { return ReadAIInputsOnce(b, epoch, out); }
  __except (1) { out.failure = "native_observation_unavailable"; return false; }
#else
  return ReadAIInputsOnce(b, epoch, out);
#endif
}
} // namespace

AIReformInputsBindings BindPlayerReligionAIReformInputsImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  AIReformInputsBindings b{};
  if (!Admitted(base, sha)) return b;
  b.core = ck3_12004::BindCoreImage(base, sha);
  b.context.enabled = true;
  b.context.game_state_slot =
      reinterpret_cast<const void *const *>(b.core.game_state_slot);
  b.schedule.enabled = true;
  b.schedule.highest_tier = reinterpret_cast<decltype(b.schedule.highest_tier)>(base + kHighestTierRva);
  b.schedule.independent_ruler = reinterpret_cast<decltype(b.schedule.independent_ruler)>(base + kIndependentRulerRva);
  b.schedule.rare_periods = reinterpret_cast<decltype(b.schedule.rare_periods)>(base + kRarePeriodsSlotRva);
  b.schedule.reformation_toggle = reinterpret_cast<decltype(b.schedule.reformation_toggle)>(base + kReformationToggleRva);
  return b;
}

GovernanceBindings BindRiteGovernanceImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  GovernanceBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.core = ck3_12004::BindCoreImage(base, sha);
  const auto context = religion::BindReligionContextImage12004(base, sha);
  b.state_rite.enabled = true;
  b.state_rite.context = context;
  b.state_rite.character_top_liege = reinterpret_cast<legacy::ObjectGetter>(base + kTopLiegeRva);
  b.state_rite.character_primary_title = reinterpret_cast<legacy::ObjectGetter>(base + kPrimaryTitleRva);
  b.state_rite.title_state_rite = reinterpret_cast<legacy::ObjectGetter>(base + kTitleStateRiteRva);
  b.heads.enabled = true;
  b.heads.context = context;
  b.heads.rite_head_id = reinterpret_cast<legacy::head::HeadIdGetter>(base + kRiteHeadIdRva);
  b.heads.rite_head = reinterpret_cast<legacy::ObjectGetter>(base + kRiteHeadRva);
  b.heads.faith_religious_head = reinterpret_cast<legacy::ObjectGetter>(base + kFaithHeadRva);
  b.heads.faith_religious_head_title = reinterpret_cast<legacy::ObjectGetter>(base + kFaithHeadTitleRva);
  b.organization.enabled = true;
  b.organization.core = b.core;
  b.organization.character_rite = context.character_rite;
  b.organization.county_count = reinterpret_cast<legacy::organization::CountGetter>(base + kCountyCountRva);
  b.organization.character_follower_count = reinterpret_cast<legacy::organization::CountGetter>(base + kFollowerCountRva);
  return b;
}

MembersBindings BindOrganizationMembersImage12004(std::uintptr_t base,
    std::string_view sha) noexcept {
  MembersBindings b{};
  if (!Admitted(base, sha)) return b;
  b.enabled = true;
  b.core = ck3_12004::BindCoreImage(base, sha);
  const auto context = religion::BindReligionContextImage12004(base, sha);
  b.character_rite = context.character_rite;
  b.rite_faith = context.rite_faith;
  b.faith_religion = context.faith_religion;
  b.title_storage_slot = reinterpret_cast<void **>(base + kTitleStorageSlotRva);
  b.faith_characters = reinterpret_cast<legacy::organization::members::Collector>(base + kFaithCollectorRva);
  b.rite_counties = reinterpret_cast<legacy::organization::members::Collector>(base + kRiteCountyCollectorRva);
  return b;
}

bool ReadPlayerReligionAIReformInputs12004(const AIReformInputsBindings &b,
    std::uint64_t epoch, ck3_12002::PlayerReligionAIReformInputsObservation12002 &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  try {
    ck3_12002::PlayerReligionAIReformInputsObservation12002 candidate{};
    candidate.capture_epoch = epoch;
    if (!ReadAIInputsGuarded(b, epoch, candidate)) {
      out.failure = std::move(candidate.failure);
      out.date_raw = candidate.date_raw;
      out.played_character_id = candidate.played_character_id;
      return false;
    }
    out = std::move(candidate);
    return true;
  } catch (...) { out.failure = "native_observation_unavailable"; return false; }
}

bool ReadPlayedRiteGovernance12004(const GovernanceBindings &b,
    std::uint64_t epoch, legacy::governance::Context &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::paused ? legacy::governance::Failure::frame_not_paused :
        (failure == FrameFailure::bindings ? legacy::governance::Failure::bindings_unavailable :
                                            legacy::governance::Failure::played_character_unavailable);
    return false;
  }
  const bool read = legacy::governance::ReadPlayedRiteGovernance12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}

bool ReadPlayedOrganizationMembers12004(const MembersBindings &b,
    std::uint64_t epoch, legacy::organization::members::Snapshot &out) noexcept {
  out = {};
  CoreSnapshotPrefix frame{};
  const auto failure = b.enabled ? SelectPlayedFrame(b.core, frame) : FrameFailure::bindings;
  Stamp(out, epoch, frame);
  if (failure != FrameFailure::none) {
    out.failure = failure == FrameFailure::paused ? legacy::organization::members::Failure::frame_not_paused :
        (failure == FrameFailure::bindings ? legacy::organization::members::Failure::bindings_unavailable :
                                            legacy::organization::members::Failure::frame_unavailable);
    return false;
  }
  const bool read = legacy::organization::members::ReadPlayedOrganizationMembers12002(b, epoch, out);
  if (!read) Stamp(out, epoch, frame);
  return read;
}
} // namespace xar::ck3_12004::religion::adopted
