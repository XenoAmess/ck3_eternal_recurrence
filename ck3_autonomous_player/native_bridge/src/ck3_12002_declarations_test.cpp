#include "xar_bridge/ck3_12002_declarations.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar::ck3_12002;
template <class T> void Put(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *p, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value)); return value;
}
void Array(void *p, const std::int32_t *values, std::int32_t count) {
  Put(p, 0, values); Put(p, 8, count); Put(p, 12, count);
}
struct War {
  std::array<std::byte, 0x58> bytes{};
  std::vector<std::int32_t> titles;
  void Sync() { Array(bytes.data() + 0x10, titles.data(), static_cast<std::int32_t>(titles.size())); }
};
struct World {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> player{};
  std::vector<std::byte> data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> entry{};
  std::array<void *, 1> entries{entry.data()};
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x40> slots{};
  std::array<std::byte, 0x1D8> actor{}, target{}, dead{};
  std::array<std::byte, 0x98> cb_database{};
  std::array<std::byte, 0xF80> interaction_database{};
  std::array<std::byte, 0x1550> type{}, disabled_type{};
  std::array<std::byte, 0x218> rule{}, disabled_rule{};
  std::array<void *, 2> types{type.data(), disabled_type.data()};
  std::array<std::byte, 0x18> scratch{};
  std::array<std::byte, 0x98 * 3> configurations{};
  std::array<std::int32_t, 2> first_titles{0x010000A1, 0x010000A2};
  std::array<std::int32_t, 1> third_titles{0x010000A3};
  std::array<std::uintptr_t, 9> command_vtable{};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data(), *storage_ptr = storage.data();
  DeclarationsBindings bindings;
  bool validate = true, reject = false, zero_configurations = false, malformed = false;
  int evaluations = 0, config_destroys = 0, context_destroys = 0, queues = 0;
  std::uint32_t sent_flags = 0;
  std::vector<std::int32_t> sent_titles;
  std::int32_t sent_claimant = -1;
  inline static constexpr std::int32_t actor_id = 0x03000001;
  inline static constexpr std::int32_t target_id = 0x04000002;
};
World *world = nullptr;
void *Player(void *) { return world->player.data(); }
void *CbDatabase() { return world->cb_database.data(); }
void *InteractionDatabase() { return world->interaction_database.data(); }
bool Evaluate(void *type, void *actor, void *target, void *scratch, bool blocked,
              bool unknown, void *context) {
  assert(type == world->type.data() && actor == world->actor.data() && target == world->target.data());
  assert(!blocked && !unknown && !context && scratch == world->scratch.data());
  ++world->evaluations;
  Put(scratch, 0, world->configurations.data());
  Put(scratch, 8, std::int32_t{3});
  Put(scratch, 12, std::int32_t{world->zero_configurations ? 0 : 3});
  for (int i = 0; i < 3; ++i) Put(world->configurations.data(), i * 0x98, std::int32_t{0x03000001});
  Array(world->configurations.data() + 8, world->first_titles.data(), 2);
  Array(world->configurations.data() + 0x98 + 8, nullptr, 0);
  Array(world->configurations.data() + 0x98 * 2 + 8, world->third_titles.data(), 1);
  if (world->malformed) Put(world->configurations.data() + 8, 12, std::int32_t{3});
  return true;
}
void DestroyConfiguration(void *) { ++world->config_destroys; }
void *Construct(void *context, void *interaction, std::int32_t actor_id,
                std::int32_t target_id, void *extra, bool redirect) {
  assert(interaction == world->rule.data() && actor_id == World::actor_id &&
         target_id == World::target_id && !extra && redirect);
  Put(context, 0, interaction);
  Put(context, 0x2D8, actor_id); Put(context, 0x2DC, target_id);
  Put(context, 0x2EC, actor_id);
  auto *war = new War;
  Put(war->bytes.data(), 0, world->bindings.war_declaration_vtable);
  Put(context, 0x330, war->bytes.data());
  return context;
}
void Refresh(void *, bool refresh) { assert(refresh); }
void Finalize(void *) {}
bool Validate(void *context, void *errors) {
  assert(!errors && Get<std::int32_t>(context, 0x2EC) == World::actor_id);
  return world->validate;
}
void DestroyContext(void *context) {
  auto *war = static_cast<War *>(Get<void *>(context, 0x330));
  assert(war); delete war;
  Put(context, 0x330, static_cast<void *>(nullptr));
  ++world->context_destroys;
}
void Copy(void *destination, const void *source) {
  auto *war = reinterpret_cast<War *>(static_cast<std::byte *>(destination) - 0x10);
  auto *data = Get<const std::int32_t *>(source, 0);
  const auto count = Get<std::int32_t>(source, 12);
  war->titles.assign(data, data + count); war->Sync();
}
void Append(void *destination, std::int32_t insertion,
            const std::int32_t *begin, const std::int32_t *end) {
  auto *war = reinterpret_cast<War *>(static_cast<std::byte *>(destination) - 0x10);
  assert(insertion == static_cast<std::int32_t>(war->titles.size()));
  war->titles.insert(war->titles.end(), begin, end); war->Sync();
}
void CopyContext(void *destination, const void *source) {
  std::memcpy(destination, source, 0x338);
  auto *source_war = static_cast<War *>(Get<void *>(source, 0x330));
  auto *war = new War(*source_war); war->Sync();
  Put(destination, 0x330, war->bytes.data());
}
void *ConstructSend(void *command, const void *context) {
  Put(command, 0, world->bindings.send_primary_vtable);
  Put(command, 0x18, world->bindings.send_secondary_vtable);
  CopyContext(static_cast<std::byte *>(command) + 0x20, context);
  return command;
}
void *DeleteCommandFixture(void *command, std::uint32_t flags) {
  assert(flags == 1);
  DestroyContext(static_cast<std::byte *>(command) + 0x20);
  delete[] static_cast<std::byte *>(command); return nullptr;
}
void **Clone(const void *command, void **storage) {
  auto *copy = new std::byte[0x368];
  std::memcpy(copy, command, 0x368);
  CopyContext(copy + 0x20, static_cast<const std::byte *>(command) + 0x20);
  *storage = copy; return storage;
}
bool Queue(void *manager, void **owned, std::uint32_t flags) {
  assert(manager == world && owned && *owned);
  auto *context = static_cast<std::byte *>(*owned) + 0x20;
  auto *war = static_cast<War *>(Get<void *>(context, 0x330));
  assert(Get<void *>(war, 8) == world->type.data());
  world->sent_flags = flags; world->sent_titles = war->titles;
  world->sent_claimant = Get<std::int32_t>(war, 0x28);
  ++world->queues;
  DeleteCommandFixture(*owned, 1); *owned = nullptr;
  return !world->reject;
}
void Initialize(World &w) {
  world = &w;
  Put(w.state.data(), 8, std::int32_t{53175816}); Put(w.state.data(), 0x70, std::int32_t{0});
  Put(w.state.data(), 0xA0, w.data.data());
  Put(w.jomini.data(), 0x18, w.players.data()); w.jomini[0x20] = std::byte{1};
  Put(w.players.data(), 0x1F0, std::int32_t{7}); Put(w.player.data(), 0x70, std::int32_t{7});
  Put(w.data.data(), 0x222E8 + 0x58, w.entries.data());
  Put(w.data.data(), 0x222E8 + 0x64, std::int32_t{1});
  Put(w.entry.data(), 0xD8, std::int32_t{7}); Put(w.entry.data(), 0xB0, World::actor_id);
  Put(w.storage.data(), 0x20, w.slots.data()); Put(w.storage.data(), 0x2C, std::int32_t{4});
  Put(w.slots.data(), 0x18, w.actor.data()); Put(w.slots.data(), 0x28, w.target.data());
  Put(w.slots.data(), 0x38, w.dead.data());
  Put(w.actor.data(), 0x18, World::actor_id); Put(w.target.data(), 0x18, World::target_id);
  Put(w.dead.data(), 0x18, std::int32_t{0x03000003}); Put(w.dead.data(), 0x1D0, w.rule.data());
  // Old offsets deliberately contain unusable values, including the old death
  // pointer and old database array/count. Passing needs the 1.20 ABI.
  Put(w.actor.data(), 0x1C8, w.rule.data()); Put(w.target.data(), 0x1C8, w.rule.data());
  Put(w.cb_database.data(), 0x50, w.types.data()); Put(w.cb_database.data(), 0x5C, std::int32_t{2});
  Put(w.cb_database.data(), 0x68, static_cast<void *>(nullptr));
  Put(w.cb_database.data(), 0x74, std::int32_t{-1});
  Put(w.type.data(), 0x40, w.rule.data()); Put(w.disabled_type.data(), 0x40, w.disabled_rule.data());
  w.disabled_rule[0x1F9] = std::byte{1};
  const char key[] = "test_cb";
  std::memcpy(w.type.data() + 0x18, key, sizeof(key));
  Put(w.type.data(), 0x28, std::size_t{7}); Put(w.type.data(), 0x30, std::size_t{15});
  Put(w.interaction_database.data(), 0xF60, w.rule.data());
  Put(w.interaction_database.data(), 0xF78, static_cast<void *>(nullptr));
  w.command_vtable[0] = reinterpret_cast<std::uintptr_t>(&DeleteCommandFixture);
  w.command_vtable[8] = reinterpret_cast<std::uintptr_t>(&Clone);
  auto &b = w.bindings;
  b.enabled = true; b.core = {true, &w.state_ptr, &w.jomini_ptr, &w.storage_ptr, &Player};
  b.commands.enabled = true; b.commands.command_manager = &w; b.commands.queue_owned_command = &Queue;
  b.configuration_scratch = w.scratch.data(); b.get_cb_database = &CbDatabase;
  b.get_interaction_database = &InteractionDatabase; b.evaluate_cb = &Evaluate;
  b.destroy_configuration = &DestroyConfiguration; b.construct_context = &Construct;
  b.refresh_context = &Refresh; b.finalize_context = &Finalize; b.validate_context = &Validate;
  b.destroy_context = &DestroyContext; b.construct_send = &ConstructSend;
  b.copy_int_array = &Copy; b.append_int_array = &Append;
  b.war_declaration_vtable = 0x452FFC0;
  b.send_primary_vtable = reinterpret_cast<std::uintptr_t>(w.command_vtable.data());
  b.send_secondary_vtable = 0x448BCB0;
}
} // namespace

int main() {
  using namespace xar::ck3_12002;
  using xar::game::ReadDeclarableWarsResult;
  using xar::game::DeclareWarResult;
  World w; Initialize(w);
  std::vector<xar::game::DeclarableWarSnapshot> choices;
  assert(ReadDeclarableWarsForTarget(w.bindings, World::target_id, choices) == ReadDeclarableWarsResult::available);
  assert(choices.size() == 2 && choices[0].configuration_index == 0 && choices[1].configuration_index == 2);
  assert(choices[0].casus_belli_key == "test_cb" && choices[0].claimant_character_id == World::actor_id);
  assert(w.evaluations == 1 && w.config_destroys == 3 && Get<std::int32_t>(w.scratch.data(), 12) == 0);
  auto selected = choices[0];
  assert(SubmitDeclareWar(w.bindings, selected) == DeclareWarResult::submitted);
  assert(w.queues == 1 && w.sent_flags == 0x0E && w.context_destroys == 3);
  assert(w.sent_titles == selected.target_title_ids && w.sent_claimant == World::actor_id);
  auto stale = selected; stale.target_title_ids[0]++;
  assert(SubmitDeclareWar(w.bindings, stale) == DeclareWarResult::declaration_unavailable && w.queues == 1);
  w.validate = false;
  assert(SubmitDeclareWar(w.bindings, selected) == DeclareWarResult::validation_failed && w.queues == 1);
  w.validate = true; w.reject = true;
  assert(SubmitDeclareWar(w.bindings, selected) == DeclareWarResult::unavailable && w.queues == 2);
  w.reject = false;
  Put(w.type.data(), 0x1548, std::uint32_t{1U << 20});
  assert(ReadDeclarableWars(w.bindings, choices) && choices.size() == 1);
  assert(choices[0].configuration_index == -1 && choices[0].claimant_character_id == -1 && choices[0].target_title_ids.size() == 3);
  assert(SubmitDeclareWar(w.bindings, choices[0]) == DeclareWarResult::submitted && w.sent_titles.size() == 3 && w.sent_claimant == -1);
  w.zero_configurations = true;
  assert(ReadDeclarableWarsForTarget(w.bindings, World::target_id, choices) == ReadDeclarableWarsResult::available);
  assert(choices.size() == 1 && choices[0].target_title_ids.empty());
  w.zero_configurations = false; w.malformed = true;
  assert(ReadDeclarableWarsForTarget(w.bindings, World::target_id, choices) == ReadDeclarableWarsResult::unavailable && choices.empty());
  w.malformed = false;
  assert(ReadDeclarableWarsForTarget(w.bindings, 0x03000002, choices) == ReadDeclarableWarsResult::target_not_found);
  const char heap_key[] = "test_heap_casus_belli_key";
  Put(w.type.data(), 0x18, static_cast<const char *>(heap_key));
  Put(w.type.data(), 0x28, sizeof(heap_key) - 1);
  Put(w.type.data(), 0x30, sizeof(heap_key) - 1);
  assert(ReadDeclarableWarsForTarget(w.bindings, World::target_id, choices) == ReadDeclarableWarsResult::available);
  assert(choices.size() == 1 && choices[0].casus_belli_key == heap_key);
  w.jomini[0x20] = std::byte{};
  const int evaluated = w.evaluations;
  assert(!ReadDeclarableWars(w.bindings, choices) && choices.empty() && w.evaluations == evaluated);
  const auto bound = BindDeclarationsImage(0x140000000, kExecutableSha256);
  assert(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.configuration_scratch) == 0x1454E14B8);
  assert(!BindDeclarationsImage(0x140000000, "old").enabled && !BindDeclarationsImage(0, kExecutableSha256).enabled);
  std::cout << "PASS 1.20.0.2 declarations enumeration, stale choice, validation and native clone ownership fixtures\n";
}
