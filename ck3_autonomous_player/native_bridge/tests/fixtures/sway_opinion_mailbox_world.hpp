#pragma once
// Test-only owned memory and callback world. No native image is dereferenced.
#include "xar_bridge/ck3_12004_sway.hpp"
#include "xar_bridge/protocol.hpp"
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <windows.h>



#include <atomic>
#include <chrono>
#include <thread>
#include "xar_bridge/ck3_12002_sway_outcome_mailbox.hpp"
namespace xar::ck3_12004 { ck3_12002::SwayOutcomeBindings RealBindSwayOutcomeOpinionImage12004(std::uintptr_t,std::string_view) noexcept; }
namespace {
namespace native = xar::ck3_12002;
namespace actual4 = xar::ck3_12004;
int checks = 0, failures = 0, opinions = 0, groups = 0;
std::int32_t actor_expected = -1, target_expected = -1;
void *actor_pointer = nullptr, *target_pointer = nullptr, *extension_pointer = nullptr;
void *database_pointer = nullptr, *group_pointer = nullptr, *sway_pointer = nullptr, *blocker_pointer = nullptr;
bool callback_identity = true;
constexpr std::uint32_t sway_hash = 0x12004001, blocker_hash = 0x12004002;
template<class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template<class T> T Get(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value)); return value;
}
void Check(bool value, const char *what) {
  ++checks; if (!value) { ++failures; std::cout << "FAIL " << what << '\n'; }
}
std::int32_t Opinion(void *recipient, void *actor) {
  ++opinions;
  callback_identity &= recipient == target_pointer && actor == actor_pointer &&
      Get<std::int32_t>(actor, 0x18) == actor_expected && Get<std::int32_t>(recipient, 0x18) == target_expected;
  return 37;
}
void *FindGroup(void *extension, std::uint32_t actor) {
  ++groups;
  callback_identity &= extension == extension_pointer && actor == static_cast<std::uint32_t>(actor_expected);
  return callback_identity ? group_pointer : nullptr;
}
void *Lookup(void *database, std::uint32_t hash) {
  callback_identity &= database == database_pointer;
  return hash == sway_hash ? sway_pointer : hash == blocker_hash ? blocker_pointer : nullptr;
}
std::int32_t Hash(void *database, const char *key, std::uint32_t length) {
  callback_identity &= database == database_pointer;
  const std::string_view text{key, length};
  return text == "scheme_sway_opinion" ? static_cast<std::int32_t>(sway_hash) : text == "sway_blocker_opinion" ? static_cast<std::int32_t>(blocker_hash) : 0;
}
std::int32_t Sum(void *group, void *definition) {
  callback_identity &= group == group_pointer && definition == sway_pointer;
  return 0; // Actual observed present-zero, distinct from absent-null.
}
struct World {
  native::SwayOutcomeBindings binding{};
  std::array<std::byte, 0x40> storage{};
  void *storage_pointer = storage.data(), *slots = nullptr;
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x20> extension{}, group{};
  std::array<std::byte, 0x30> temporary{};
  std::array<void *, 1> rows{temporary.data()};
  std::array<std::array<std::byte, 0x90>, 2> definitions{};
  std::array<std::array<char, 64>, 2> keys{};
  explicit World(std::int32_t actor, std::int32_t target) {
    binding = actual4::RealBindSwayOutcomeOpinionImage12004(0x140000000, actual4::kExecutableSha256);
    Check(binding.event_window.events.core.enabled && binding.build_version == "1.20.0.4" &&
        reinterpret_cast<std::uintptr_t>(binding.target_opinion) == 0x1428BC470 &&
        reinterpret_cast<std::uintptr_t>(binding.opinion_modifiers.find_group) == 0x142949A80,
        "real actual4 pure factory selects current opinion/group operands");
    slots = VirtualAlloc(nullptr, 0x10000000, MEM_RESERVE, PAGE_NOACCESS);
    if (!slots) throw std::runtime_error("owned slot reserve");
    SYSTEM_INFO system{}; GetSystemInfo(&system);
    const std::array<std::int32_t, 2> ids{actor, target};
    for (std::size_t i = 0; i < ids.size(); ++i) {
      const auto at = (static_cast<std::uint32_t>(ids[i]) & 0xFFFFFFU) * 16ULL + 8;
      const auto page = at - at % system.dwPageSize;
      if (!VirtualAlloc(static_cast<std::byte *>(slots) + page, system.dwPageSize, MEM_COMMIT, PAGE_READWRITE))
        throw std::runtime_error("owned slot commit");
      Put(characters[i].data(), 0x18, ids[i]); Put(slots, static_cast<std::size_t>(at), characters[i].data());
    }
    Put(storage.data(), 0x20, slots); Put(storage.data(), 0x2C, std::int32_t{0x1000000});
    binding.event_window.events.core.character_storage_slot = &storage_pointer;
    binding.target_opinion = &Opinion; binding.event_window.hash_stable_key = &Hash;
    auto &modifier = binding.opinion_modifiers;
    modifier.modifier_database_slot = &database_pointer;
    modifier.read_opinion = &Opinion; modifier.lookup_modifier = &Lookup;
    modifier.find_group = &FindGroup; modifier.sum_modifier = &Sum;
    for (std::size_t i = 0; i < definitions.size(); ++i) {
      auto *definition = definitions[i].data();
      const char *key = i == 0 ? "scheme_sway_opinion" : "sway_blocker_opinion";
      std::memcpy(keys[i].data(), key, std::strlen(key) + 1);
      Put(definition, 0, modifier.modifier_primary_vtable); Put(definition, 0x88, modifier.modifier_secondary_vtable);
      Put(definition, 0x14, i == 0 ? sway_hash : blocker_hash);
      Put(definition, 0x18, keys[i].data()); Put(definition, 0x28, static_cast<std::uint64_t>(std::strlen(key)));
      Put(definition, 0x30, std::uint64_t{63}); Put(definition, 0x38, std::uint32_t{0x4744624F});
    }
    Put(characters[1].data(), 0x1B0, extension.data());
    Put(group.data(), 8, rows.data()); Put(group.data(), 0x14, std::int32_t{1});
    Put(temporary.data(), 0, modifier.temporary_opinion_vtable); Put(temporary.data(), 8, definitions[0].data());
    actor_expected = actor; target_expected = target; actor_pointer = characters[0].data(); target_pointer = characters[1].data();
    extension_pointer = extension.data(); database_pointer = storage.data(); group_pointer = group.data();
    sway_pointer = definitions[0].data(); blocker_pointer = definitions[1].data();
    opinions = groups = 0; callback_identity = true;
  }
  ~World() { if (slots) VirtualFree(slots, 0, MEM_RELEASE); }
  World(const World &) = delete;
  World &operator=(const World &) = delete;
};
class FrameAdapter final : public xar::game::GameAdapter {
public:
  xar::game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  xar::game::AdapterDescriptor identity{"ck3-1.20.0.4-msvc-x64", "1.20.0.4",
      actual4::kExecutableSha256, "sway-opinion-mailbox-route-fixture", {}};
  const xar::game::AdapterDescriptor &descriptor() const noexcept override { return identity; }
  bool enabled() const noexcept override { return true; }
  bool read_snapshot(xar::game::Snapshot &out) const noexcept override {
    if (GetCurrentThreadId() != owner) return false;
    out = frame;
    if (++reads > 1 && drift) ++out.date_raw;
    return true;
  }
  bool submit_set_speed(std::int32_t) const noexcept override { return false; }
  xar::game::SaveCheckpointResult submit_save_checkpoint() const noexcept override { return {}; }
  xar::game::PreviewMoveArmyResult preview_move_army(std::int32_t, std::int32_t) const noexcept override { return {}; }
  bool read_declarable_wars(std::vector<xar::game::DeclarableWarSnapshot> &) const noexcept override { return false; }
#define ABSENT(Result, Name, Params) xar::game::Result Name Params const noexcept override { return xar::game::Result::unavailable; }
  ABSENT(PauseSubmitResult, submit_pause_map, (xar::game::Snapshot *))
  ABSENT(ResumeSubmitResult, submit_resume_map, (xar::game::Snapshot *))
  ABSENT(SelectEventOptionResult, submit_select_event_option, (std::int32_t))
  ABSENT(ReplyPendingInteractionResult, submit_reply_to_pending_interaction, (xar::game::PendingInteractionReply))
  ABSENT(RaiseTroopsResult, submit_raise_troops_default, ())
  ABSENT(MoveArmyResult, submit_move_army, (std::int32_t, std::int32_t))
  ABSENT(DisbandArmyResult, submit_disband_army, (std::int32_t))
  ABSENT(SplitArmyHalfResult, submit_split_army_half, (std::int32_t))
  ABSENT(MergeArmiesResult, submit_merge_armies, (std::int32_t, std::int32_t))
  ABSENT(StartAssaultResult, submit_start_assault, (std::int32_t))
  ABSENT(StopAssaultResult, submit_stop_assault, (std::int32_t))
  ABSENT(ReadDeclarableWarsResult, read_declarable_wars_for_target, (std::int32_t, std::vector<xar::game::DeclarableWarSnapshot> &))
  ABSENT(DeclareWarResult, submit_declare_war, (const xar::game::DeclarableWarSnapshot &))
  ABSENT(ReadArrangeMarriageChoicesResult, read_arrange_marriage_choices, (std::vector<xar::game::ArrangeMarriageChoice> &, xar::game::ArrangeMarriageQueryDiagnostics &))
  ABSENT(ArrangeMarriageResult, submit_arrange_marriage, (const xar::game::ArrangeMarriageChoice &))
  ABSENT(EnforceDemandsResult, submit_enforce_demands, (std::int32_t))
  ABSENT(SurrenderWarResult, submit_surrender_war, (std::int32_t))
  ABSENT(OfferWhitePeaceResult, submit_offer_white_peace, (std::int32_t))
  ABSENT(ReadArmyStrengthsResult, read_army_strengths, (std::vector<xar::game::ArmyStrengthSnapshot> &))
  ABSENT(ReadCombatSimulationInputsResult, read_combat_simulation_inputs, (const xar::game::CombatSimulationInputsRequest &, xar::game::CombatSimulationInputsSnapshot &))
  ABSENT(ReadCombatSimulationInputsV3Result, read_combat_simulation_inputs_v3, (const xar::game::CombatSimulationInputsRequest &, xar::game::CombatSimulationInputsV3Snapshot &))
  ABSENT(ReadWarTerminationOptionsResult, read_war_termination_options, (std::int32_t, xar::game::WarTerminationOptionsSnapshot &))
  ABSENT(ReadWarTerminationTermsResult, read_war_termination_terms, (std::int32_t, xar::game::WarTerminationTermsSnapshot &))
  ABSENT(ReadWarTerminationExitTermsResult, read_war_termination_exit_terms, (std::int32_t, xar::game::WarTerminationExitTermsSnapshot &))
#undef ABSENT
};

}
