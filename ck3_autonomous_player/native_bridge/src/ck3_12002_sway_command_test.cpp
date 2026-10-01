#include "xar_bridge/ck3_12002_sway_command.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12002;
constexpr std::int32_t actor_id = 0x03000001, target_id = 0x03000002;
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
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  Check(manager == &queues && owned != nullptr && *owned != nullptr && flags == 0x0E,
      "production owning queue exact Sway channel");
  ++queues;
  Check(Load<std::int32_t>(*owned, 0x20 + 0x2D8) == actor_id &&
      Load<std::int32_t>(*owned, 0x20 + 0x2DC) == target_id,
      "owning clone preserves typed Sway actor/target");
  // Exercise the existing SubmitCommandCopy residual destructor path, which
  // correctly releases a game-owned command if the queue leaves it owned.
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
  std::array<std::byte, 16 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x78> database{};
  std::array<std::byte, 0x2760> def{};
  std::array<void *, 2> rows{def.data(), def.data()};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(),
      *store_ptr = store.data(), *database_ptr = database.data();
  SwayCommandBindingsV1 bindings{};
  Fixture() {
    local_player = local.data(); definition = def.data(); state_to_mutate = state.data();
    Put(state.data(), 8, std::int32_t{53220000}); Put(state.data(), 0xA0, game.data());
    Put(jomini.data(), 0x18, players.data()); Put(jomini.data(), 0x20, std::uint8_t{1});
    Put(players.data(), 0x1F0, std::int32_t{0}); Put(local.data(), 0x70, std::int32_t{0});
    Put(game.data(), kPlayerCharacterManagerOffset + 0x58, entries.data());
    Put(game.data(), kPlayerCharacterManagerOffset + 0x64, std::int32_t{1});
    Put(entry.data(), 0xD8, std::int32_t{0}); Put(entry.data(), 0xB0, actor_id);
    Put(store.data(), 0x20, slots.data()); Put(store.data(), 0x2C, std::int32_t{16});
    for (int i = 0; i != 2; ++i) {
      Put(characters[i].data(), 0x18, actor_id + i);
      Put(slots.data(), (i + 1) * 0x10 + 8, characters[i].data());
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
};
} // namespace

int main() {
  try {
    using Result = SwayCommandSubmitResultV1;
    const auto bound = BindSwayCommandImage(0x140000000, kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.construct_two_roles) ==
        0x140000000 + 0x3076C90 && reinterpret_cast<std::uintptr_t>(bound.context.validate) ==
        0x140000000 + 0x307C040, "bind actual 1.20 context and complete CanSend addresses");
    Check(bound.context.commands.command_manager == reinterpret_cast<void *>(0x140000000 + 0x5CC1240) &&
        reinterpret_cast<std::uintptr_t>(bound.context.commands.queue_owned_command) ==
        0x140000000 + 0x37F06F0, "bind owning queue rather than old raw submit");
    Check(!BindSwayCommandImage(0x140000000, "1.19.0.6").enabled, "old executable not qualified");
    Fixture f;
    SwayCommandTermsV1 terms{};
    Check(ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 4, terms) &&
        terms.precondition.available && terms.precondition.paused && terms.final_legality_sampled &&
        !terms.complete_can_send && !terms.precondition.can_start_scheme &&
        terms.precondition.native_reason_key == "native_complete_validator_rejected" &&
        terms.precondition.shown && terms.precondition.valid &&
        terms.send_costs_raw[0] == -20'000 && terms.send_costs_raw[9] == 90'000,
        "legal native negative remains observable with signed costs and distinct shown/valid");
    xar::bridge::ActiveSchemeSemanticActionV1PrivateCommand command{
        "fixture-sway-start", "sway_interaction", "sway", actor_id,
        xar::bridge::ActiveSchemeStateV1PrivateTargetKind::character, target_id, {}};
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::rejected && queues == 0 && clones == 0,
        "native CanSend false does not send");
    can_send = true;
    Check(ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 5, terms) && terms.complete_can_send &&
        terms.precondition.success_chance.status ==
        xar::bridge::ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable,
        "complete native positive keeps existing explicit-unavailable preview boundary");
    const auto before_destroy = destroys;
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::submitted && queues == 1 &&
        clones == 1 && sends == 1 && deletes == 1 && destroys == before_destroy + 2,
        "actual provider uses production clone/queue once and releases both caller contexts");
    Check(terms.precondition.capture_epoch == 5 && terms.precondition.date_raw == 53220000 &&
        terms.precondition.actor_character_id == actor_id && terms.precondition.target_id == target_id,
        "typed precondition retains exact source frame and pair");
    queue_accepted = false;
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::rejected && queues == 2 &&
        clones == 2 && deletes == 2, "native queue rejection preserved with owning release");
    queue_accepted = true; copy_changes_recipient = true;
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::unavailable && queues == 2 && clones == 2,
        "copied context target must still match before queue");
    copy_changes_recipient = false; context_changes_actor = true;
    Check(!ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 6, terms) &&
        !terms.precondition.available, "context cannot borrow another actor permission");
    context_changes_actor = false;
    command.interaction_key = "start_murder_interaction";
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::rejected && queues == 2,
        "no other interaction route");
    command.interaction_key = "sway_interaction"; command.selected_starter_package = "agent_focus_success";
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::rejected && queues == 2,
        "Sway cannot send scheme starter option");
    command.selected_starter_package.clear(); command.actor_character_id = target_id;
    Check(SubmitSwayCommandV1(f.bindings, command) == Result::unavailable && queues == 2,
        "only currently played actor");
    command.actor_character_id = actor_id;
    Put(f.characters[1].data(), 0x18, std::int32_t{0x04000002});
    Check(!ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 7, terms),
        "full-generation target mismatch is unavailable");
    Put(f.characters[1].data(), 0x18, target_id);
    drift = true;
    Check(!ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 8, terms) &&
        !terms.precondition.available, "actual reader rejects changed core frame");
    drift = false; Put(f.state.data(), 8, std::int32_t{53220000});
    Put(f.database.data(), kSwayDatabaseCountOffset, std::int32_t{2});
    Check(!ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 9, terms),
        "loaded canonical definition must resolve uniquely");
    Put(f.database.data(), kSwayDatabaseCountOffset, std::int32_t{1});
    Put(f.def.data(), kSwayDefinitionSecondaryOffset, std::uintptr_t{0});
    Check(!ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 10, terms),
        "actual loaded definition secondary object layout");
    Put(f.def.data(), kSwayDefinitionSecondaryOffset, definition_secondary);
    shown = false;
    Check(ReadSwayCommandTermsV1(f.bindings, actor_id, target_id, 11, terms) &&
        !terms.precondition.shown && SubmitSwayCommandV1(f.bindings, command) == Result::rejected && queues == 2,
        "negative independently sampled shown gates submit");
    std::cout << "PASS CK3 1.20.0.2 Sway command: actual provider negative/positive, typed roles, owning clone/queue, cleanup\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n'; return 1;
  }
}
