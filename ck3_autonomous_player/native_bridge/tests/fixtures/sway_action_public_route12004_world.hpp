#pragma once
// Test-only native memory/callback world; no image is dereferenced.
#include "xar_bridge/ck3_12002_sway_command.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <bit>
#include <charconv>
#include <limits>
#include <windows.h>
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#include "xar_bridge/ck3_12002_gift_opinion.hpp"

namespace {
using namespace xar::ck3_12002;
std::int32_t actor_id = 0x03000001, target_id = 0x03000002;
template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}
template <class T> T Load(const void *object, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T)); return value;
}
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *local_player = nullptr, *definition = nullptr, *state_to_mutate = nullptr;
bool can_send = false, shown = true, valid = true, queue_accepted = true;
bool copy_changes_recipient = false, context_changes_actor = false, drift = false;
int contexts = 0, destroys = 0, sends = 0, clones = 0, queues = 0, deletes = 0;
std::array<std::uintptr_t, 9> command_vtable{};
constexpr std::uintptr_t second_vtable = 0x1200201;
constexpr std::uintptr_t definition_primary = 0x1200202, definition_secondary = 0x1200203;
void *LocalPlayer(void *) { return local_player; }
void *Construct(void *out, void *def, std::int32_t actor, std::int32_t target,
    void *extra, bool redirect) {
  Check(def == definition && actor == actor_id && target == target_id &&
      extra == nullptr && !redirect, "native two-role Sway constructor ABI");
  ++contexts;
  Put(out, 0, def); Put(out, 0x2D8, context_changes_actor ? target : actor);
  Put(out, 0x2DC, target); Put(out, 0x2E0, std::int32_t{-1}); Put(out, 0x2E4, std::int32_t{-1});
  Put(out, 0x2E8, std::int32_t{-1}); Put(out, 0x2EC, actor);
  return out;
}
void Refresh(void *, bool full) { Check(full, "native full refresh"); }
void Finalize(void *) {}
bool Shown(void *) { return shown; }
bool Valid(void *, bool first, bool second, void *error) {
  Check(first && second && error == nullptr, "complete native interaction validity ABI"); return valid;
}
bool CanSend(void *ctx, void *error) {
  Check(error == nullptr && Load<std::int32_t>(ctx, 0x2D8) == actor_id &&
      Load<std::int32_t>(ctx, 0x2DC) == target_id, "complete CanSend exact actor/target");
  if (drift) Put(state_to_mutate, 8, std::int32_t{53220024});
  return can_send;
}
void Cost(const void *block, const void *scope, std::int64_t *out) {
  Check(block == static_cast<const std::byte *>(definition) + 0x40 &&
      Load<void *>(static_cast<const std::byte *>(scope) - 8, 0) == definition,
      "actual finalized context ten-resource evaluator ABI");
  for (int i = 0; i != 10; ++i) out[i] = i == 0 ? -20'000 : i * 10'000;
}
void Destroy(void *ctx) { ++destroys; Put(ctx, 0, static_cast<void *>(nullptr)); }
void *Send(void *out, const void *ctx) {
  ++sends;
  Put(out, 0, reinterpret_cast<std::uintptr_t>(command_vtable.data()));
  Put(out, 0x18, second_vtable);
  std::memcpy(static_cast<std::byte *>(out) + 0x20, ctx, 0x338);
  if (copy_changes_recipient) Put(out, 0x20 + 0x2DC, actor_id);
  return out;
}
void **Clone(const void *source, void **out) {
  ++clones;
  auto *owned = new std::array<std::byte, 0x368>;
  std::memcpy(owned->data(), source, owned->size()); *out = owned; return out;
}
void *Delete(void *owned, std::uint32_t flags) {
  Check(flags == 1, "native scalar deleting destructor flags");
  ++deletes; delete static_cast<std::array<std::byte, 0x368> *>(owned); return nullptr;
}
void (*apply_queued_scheme)() noexcept = nullptr;
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  Check(manager == &queues && owned != nullptr && *owned != nullptr && flags == 0x0E,
      "production owning queue exact Sway channel");
  ++queues;
  Check(Load<std::int32_t>(*owned, 0x20 + 0x2D8) == actor_id &&
      Load<std::int32_t>(*owned, 0x20 + 0x2DC) == target_id,
      "owning clone preserves typed Sway actor/target");
  // Exercise the existing SubmitCommandCopy residual destructor path, which
  // correctly releases a game-owned command if the queue leaves it owned.
  if (queue_accepted && apply_queued_scheme) apply_queued_scheme();
  return queue_accepted;
}
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game = std::vector<std::byte>(0x23000);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> store{};
  void *slots = nullptr;
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x78> database{};
  std::array<std::byte, 0x2760> def{};
  std::array<void *, 2> rows{def.data(), def.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(),
      *store_ptr = store.data(), *database_ptr = database.data();
  SwayCommandBindingsV1 bindings{};
  Fixture() {
    slots = VirtualAlloc(nullptr, 0x10000000, MEM_RESERVE, PAGE_NOACCESS);
    if (!slots) throw std::runtime_error("reserve actual24 slot range");
    SYSTEM_INFO info{}; GetSystemInfo(&info);
    for (const auto id : {actor_id, target_id}) {
      const auto offset = (static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 16ULL;
      const auto page = offset - offset % info.dwPageSize;
      if (!VirtualAlloc(static_cast<std::byte *>(slots) + page, info.dwPageSize, MEM_COMMIT, PAGE_READWRITE))
        throw std::runtime_error("commit owned slot page");
    }
    local_player = local.data(); definition = def.data(); state_to_mutate = state.data();
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data()); Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{0}); Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{0}); Put(entry.data(), 0xB0, actor_id);
    Put(store.data(), 0x20, slots); Put(store.data(), 0x2C, std::int32_t{0x1000000});
    for (int i = 0; i != 2; ++i) {
      const auto id = i == 0 ? actor_id : target_id;
      Put(characters[i].data(), 0x18, id);
      Put(slots, (static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 16ULL + 8, characters[i].data());
    }
    Put(database.data(), kSwayDatabaseRowsOffset, rows.data());
    Put(database.data(), kSwayDatabaseCountOffset, std::int32_t{1});
    Put(def.data(), 0, definition_primary);
    Put(def.data(), kSwayDefinitionSecondaryOffset, definition_secondary);
    Put(def.data(), 0x10, std::int32_t{5});
    Put(def.data(), 0x14, std::uint32_t{0x5783F850});
    static constexpr char key[] = "sway_interaction";
    Put(def.data(), 0x18, static_cast<const char *>(key));
    Put(def.data(), 0x28, std::uint64_t{16}); Put(def.data(), 0x30, std::uint64_t{31});
    Put(def.data(), 0x38, std::uint32_t{0x4744624F});
    command_vtable[0] = reinterpret_cast<std::uintptr_t>(&Delete);
    command_vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
    bindings.enabled = true;
    auto &c = bindings.context; c.enabled = true;
    c.core = {true, &state_ptr, &jomini_ptr, &store_ptr, &LocalPlayer};
    c.commands.enabled = true; c.commands.command_manager = &queues;
    c.commands.queue_owned_command = &Queue;
    c.interaction_database_slot = &database_ptr;
    c.refresh = &Refresh; c.finalize = &Finalize; c.validate = &CanSend;
    c.destroy = &Destroy; c.evaluate_cost = &Cost; c.construct_send_command = &Send;
    c.send_primary_vtable = reinterpret_cast<std::uintptr_t>(command_vtable.data());
    c.send_secondary_vtable = second_vtable;
    bindings.construct_two_roles = &Construct; bindings.shown = &Shown; bindings.valid = &Valid;
    bindings.definition_primary_vtable = definition_primary;
    bindings.definition_secondary_vtable = definition_secondary;
  }
  ~Fixture() { if (slots) VirtualFree(slots, 0, MEM_RELEASE); }
};
} // namespace

class FrameAdapter final : public xar::game::GameAdapter {
public:
  xar::game::Snapshot frame{};
  const DWORD owner = GetCurrentThreadId();
  mutable unsigned reads = 0;
  bool drift = false;
  xar::game::AdapterDescriptor identity{"ck3-1.20.0.4-msvc-x64", "1.20.0.4",
      xar::ck3_12004::kExecutableSha256, "m6-public-action-owned-fixture", {}};
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