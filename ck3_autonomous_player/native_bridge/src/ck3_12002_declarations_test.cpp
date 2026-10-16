#include "xar_bridge/ck3_12002_declarations.hpp"

#include "xar_bridge/ck3_12004_declaration_candidates.hpp"
#include <array>
#include <cassert>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>
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
  bool extra_target = false, extra_type = false, available = true;
  bool restrict_first_cb = false, candidate_facts_available = true;
  bool exclude_all_candidates = false, candidate_realm_available = true;
  int candidate_fact_reads = 0, candidate_realm_reads = 0;
  std::vector<void *> candidate_realm;
  std::vector<std::pair<std::int32_t, std::int32_t>> evaluation_order;
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
  assert((type == world->type.data() || (world->extra_type && type == world->disabled_type.data())) &&
         actor == world->actor.data() &&
         (target == world->target.data() || (world->extra_target && target == world->dead.data())));
  world->evaluation_order.push_back({Get<std::int32_t>(target, 0x18),
                                    type == world->type.data() ? 0 : 2});
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
  return world->available && !(world->restrict_first_cb &&
      type == world->type.data() && target == world->dead.data());
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
void QueryLocalReuseFixture() {
  World w; Initialize(w);
  w.extra_target = true;
  Put(w.dead.data(), 0x1D0, static_cast<void *>(nullptr));
  std::array<void *, 3> types{w.type.data(), nullptr, w.disabled_type.data()};
  Put(w.cb_database.data(), 0x50, types.data());
  Put(w.cb_database.data(), 0x5C, std::int32_t{3});
  // Preexisting scratch must be destroyed once before the first evaluation.
  Put(w.scratch.data(), 0, w.configurations.data());
  Put(w.scratch.data(), 8, std::int32_t{3});
  Put(w.scratch.data(), 12, std::int32_t{1});
  std::vector<xar::game::DeclarableWarSnapshot> rows;
  assert(ReadDeclarableWars(w.bindings, rows) && rows.size() == 4);
  assert(w.config_destroys == 7 && w.evaluations == 2);
  assert(rows[0].target_character_id == World::target_id &&
         rows[1].configuration_index == 2 &&
         rows[2].target_character_id == 0x03000003);
  // A later query must reread enabled definitions, retaining ordinal2.
  w.extra_type = true;
  std::memcpy(w.disabled_type.data(), w.type.data(), w.type.size());
  Put(w.disabled_type.data(), 0x40, w.disabled_rule.data());
  w.disabled_rule[0x1F9] = std::byte{};
  w.evaluation_order.clear();
  assert(ReadDeclarableWars(w.bindings, rows) && rows.size() == 8);
  const std::vector<std::pair<std::int32_t, std::int32_t>> expected{
      {World::target_id, 0}, {World::target_id, 2},
      {0x03000003, 0}, {0x03000003, 2}};
  assert(w.evaluation_order == expected && rows[2].casus_belli_index == 2);
  // False evaluator output still owns configurations and must be cleaned.
  w.available = false;
  const int destroyed = w.config_destroys;
  assert(ReadDeclarableWars(w.bindings, rows) && rows.empty());
  assert(w.config_destroys == destroyed + 12);
  w.available = true; w.malformed = true;
  assert(!ReadDeclarableWars(w.bindings, rows) && rows.empty());
  assert(Get<std::int32_t>(w.scratch.data(), 12) == 0);
  w.malformed = false;
  Put(w.scratch.data(), 8, std::int32_t{0});
  Put(w.scratch.data(), 12, std::int32_t{1});
  const int evaluated = w.evaluations;
  assert(!ReadDeclarableWars(w.bindings, rows) && rows.empty() &&
         w.evaluations == evaluated);
}

void SetProfilePath(const std::string &path) {
#if defined(_MSC_VER)
  assert(_putenv_s("XAR_CK3_DECLARATIONS_PROFILE_JSONL", path.c_str()) == 0);
#else
  if (path.empty()) assert(unsetenv("XAR_CK3_DECLARATIONS_PROFILE_JSONL") == 0);
  else assert(setenv("XAR_CK3_DECLARATIONS_PROFILE_JSONL", path.c_str(), 1) == 0);
#endif
}

void QueryProfileFixture(const char *requested_path) {
  const auto ticks = std::chrono::steady_clock::now().time_since_epoch().count();
  const auto path = requested_path ? std::filesystem::path(requested_path)
      : std::filesystem::temp_directory_path() /
          ("xar-declarable-profile-" + std::to_string(ticks) + ".jsonl");
  // Only the uniquely created fixture file is owned by this test.
  assert(!std::filesystem::exists(path));
  World w; Initialize(w);
  w.extra_target = w.extra_type = true;
  Put(w.dead.data(), 0x1D0, static_cast<void *>(nullptr));
  std::array<void *, 3> types{w.type.data(), nullptr, w.disabled_type.data()};
  Put(w.cb_database.data(), 0x50, types.data());
  Put(w.cb_database.data(), 0x5C, std::int32_t{3});
  std::memcpy(w.disabled_type.data(), w.type.data(), w.type.size());
  Put(w.disabled_type.data(), 0x40, w.disabled_rule.data());
  w.disabled_rule[0x1F9] = std::byte{};
  const char heap_key[] = "cb_quoted_\"_\\_\n_key";
  Put(w.disabled_type.data(), 0x18, static_cast<const char *>(heap_key));
  Put(w.disabled_type.data(), 0x28, sizeof(heap_key) - 1);
  Put(w.disabled_type.data(), 0x30, sizeof(heap_key) - 1);
  std::vector<xar::game::DeclarableWarSnapshot> baseline, profiled;
  SetProfilePath("");
  assert(ReadDeclarableWars(w.bindings, baseline));
  const auto baseline_order = w.evaluation_order;
  const auto baseline_evaluations = w.evaluations;
  const auto baseline_destroys = w.config_destroys;
  w.evaluation_order.clear();
  SetProfilePath(path.string());
  assert(ReadDeclarableWars(w.bindings, profiled) && profiled == baseline);
  assert(w.evaluation_order == baseline_order);
  assert(w.evaluations == 2 * baseline_evaluations &&
         w.config_destroys == 2 * baseline_destroys);
  w.available = false;
  assert(ReadDeclarableWars(w.bindings, profiled) && profiled.empty());
  w.available = true; w.malformed = true;
  assert(!ReadDeclarableWars(w.bindings, profiled) && profiled.empty());
  assert(Get<std::int32_t>(w.scratch.data(), 12) == 0);
  w.malformed = false;
  // A diagnostic sink failure cannot remove a declaration or stop gameplay.
  SetProfilePath((path / "missing-parent" / "ignored.jsonl").string());
  assert(ReadDeclarableWars(w.bindings, profiled) && profiled == baseline);
  SetProfilePath("");
  std::ifstream stream(path, std::ios::binary);
  std::string line;
  int lines = 0;
  while (std::getline(stream, line)) {
    assert(line.find("\"schema\":\"ck3-declarable-query-profile-v1\"") != std::string::npos);
    ++lines;
  }
  assert(lines == 3);
  stream.close();
  if (!requested_path) std::filesystem::remove(path);
}
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
bool CandidateFacts(std::uintptr_t, void *target, DeclarationsCandidateFactsV1 &out) noexcept {
  ++world->candidate_fact_reads;
  out.independent = target == world->dead.data() || world->exclude_all_candidates
      ? DeclarationsCandidateFactV1::no : DeclarationsCandidateFactV1::yes;
  return world->candidate_facts_available;
}
bool CandidateRealm(std::uintptr_t, void *, std::vector<void *> &out) noexcept {
  ++world->candidate_realm_reads; out = world->candidate_realm;
  return world->candidate_realm_available;
}
bool FixtureBytes(const void *source, void *destination, std::size_t size) noexcept {
  if (!source || !destination) return false;
  std::memcpy(destination, source, size); return true;
}
bool FailedBytes(const void *, void *, std::size_t) noexcept { return false; }

void RealmCandidateLayoutFixture() {
  std::array<std::byte, 0x1D8> actor{};
  std::array<std::byte, 0x900> cache{};
  std::array<void *, 3> normal{actor.data(), nullptr, cache.data()};
  std::array<void *, 2> replacement{cache.data(), cache.data()};
  std::array<void *, 1> extra{actor.data()};
  Put(actor.data(), 0x1C8, cache.data());
  const auto pointers_at = [&cache](std::size_t offset, void **data, std::int32_t count) {
    Put(cache.data(), offset, data); Put(cache.data(), offset + 8, count); Put(cache.data(), offset + 12, count);
  };
  pointers_at(0x688, normal.data(), 3); pointers_at(0x7B0, extra.data(), 1);
  std::vector<void *> pointers;
  Require(xar::ck3_12004::ReadDeclarationRealmCandidates12004(actor.data(), &FixtureBytes, pointers) &&
          pointers == std::vector<void *>{actor.data(), nullptr, cache.data(), actor.data()},
          "normal realm pointer union must preserve exact pointer identities");
  pointers_at(0x8E0, replacement.data(), 2);
  Require(xar::ck3_12004::ReadDeclarationRealmCandidates12004(actor.data(), &FixtureBytes, pointers) &&
          pointers == std::vector<void *>{cache.data(), cache.data(), actor.data()},
          "nonempty replacement vector must supersede normal vector");
  Put(cache.data(), 0x8EC, std::int32_t{-1});
  Require(!xar::ck3_12004::ReadDeclarationRealmCandidates12004(actor.data(), &FixtureBytes, pointers) && pointers.empty(),
          "malformed replacement must be unavailable, never empty-certified");
  Put(cache.data(), 0x8EC, std::int32_t{0}); Put(cache.data(), 0x7BC, std::int32_t{2});
  Require(!xar::ck3_12004::ReadDeclarationRealmCandidates12004(actor.data(), &FixtureBytes, pointers),
          "malformed secondary vector must invalidate entire union");
  Put(cache.data(), 0x7BC, std::int32_t{1});
  Require(!xar::ck3_12004::ReadDeclarationRealmCandidates12004(actor.data(), &FailedBytes, pointers),
          "read failure must be unavailable");
  Put(actor.data(), 0x1C8, static_cast<void *>(nullptr));
  Require(!xar::ck3_12004::ReadDeclarationRealmCandidates12004(actor.data(), &FixtureBytes, pointers),
          "missing actor realm cache must remain unavailable");
}

void CandidateQueryFixture() {
  World w; Initialize(w);
  w.extra_target = w.extra_type = w.restrict_first_cb = true;
  Put(w.dead.data(), 0x1D0, static_cast<void *>(nullptr));
  std::array<void *, 3> types{w.type.data(), nullptr, w.disabled_type.data()};
  Put(w.cb_database.data(), 0x50, types.data()); Put(w.cb_database.data(), 0x5C, std::int32_t{3});
  std::memcpy(w.disabled_type.data(), w.type.data(), w.type.size());
  Put(w.disabled_type.data(), 0x40, w.disabled_rule.data()); w.disabled_rule[0x1F9] = std::byte{};
  const char unknown_key[] = "unknown_cb";
  std::memcpy(w.disabled_type.data() + 0x18, unknown_key, sizeof(unknown_key));
  Put(w.disabled_type.data(), 0x28, sizeof(unknown_key) - 1);
  w.bindings.read_candidate_facts = &CandidateFacts;
  constexpr std::string_view source_sha = "087d6151be86546d4b1fcb600230534cb14c6a57ec2762e4efdb3ae98f9227c9";
  const std::array<DeclarationsCandidateRuleV1, 1> rules{{{"test_cb", source_sha, kDeclarationsCandidateIndependentV1}}};
  DeclarationsCandidateOptionsV1 options{DeclarationsCandidateVariantV1::cb_first, rules, source_sha};
  std::vector<xar::game::DeclarableWarSnapshot> baseline, candidate;
  Require(ReadDeclarableWars(w.bindings, baseline) && baseline.size() == 6, "full baseline");
  DeclarationsCandidateDiagnosticV1 d;
  const int before = w.evaluations;
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline,
          "candidate tuples and original output order must equal full baseline");
  Require(w.evaluations - before == 3 && w.candidate_fact_reads == 2 &&
          d.casus_belli.size() == 2 && d.casus_belli[0].candidates == 1 && d.casus_belli[1].candidates == 2,
          "one-pass facts and unknown CB wide fallback");
  options.variant = DeclarationsCandidateVariantV1::shadow;
  const int shadow_before = w.evaluations;
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
          d.baseline_compared && d.same_frame && d.tuple_sets_equal &&
          w.evaluations - shadow_before == 4 && d.casus_belli[0].evaluations == 0 &&
          d.casus_belli[0].projected_candidate_evaluations == 1,
          "shadow uses one real full baseline; projected calls are not actual calls");
  w.exclude_all_candidates = true;
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
          !d.tuple_sets_equal && d.casus_belli[0].missing_tuples == 2,
          "shadow must expose incomplete superset and return complete original result");
  w.exclude_all_candidates = false; w.candidate_facts_available = false;
  options.variant = DeclarationsCandidateVariantV1::cb_first;
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
          d.casus_belli[0].candidates == 2, "unreadable facts must retain every target");
  w.candidate_facts_available = true; options.qualified_source_manifest_sha256 = "unqualified";
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
          !d.source_qualified && d.casus_belli[0].candidates == 2, "invalid source guard must disable script filter");
  w.bindings.read_candidate_realm = &CandidateRealm;
  w.bindings.candidate_target_titles_mode_offset = 0x6C8; w.candidate_realm = {w.target.data()};
  for (std::uint8_t mode = 1; mode <= 4; ++mode) {
    Put(w.type.data(), 0x6C8, mode);
    Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
            d.native_realm_index_complete && d.casus_belli[0].native_realm_index_used &&
            d.casus_belli[0].candidates == 1 && d.casus_belli[1].candidates == 2,
            "stock target_titles modes1..4 use complete native realm pointer union");
  }
  w.candidate_realm_available = false;
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
          !d.native_realm_index_complete && d.casus_belli[0].candidates == 2,
          "missing native realm index must use wide fallback");
  w.candidate_realm_available = true; Put(w.type.data(), 0x6C8, std::uint8_t{6});
  Require(ReadDeclarableWarsWithCandidatesV1(w.bindings, options, candidate, &d) && candidate == baseline &&
          !d.casus_belli[0].native_realm_index_used && d.casus_belli[0].candidates == 2,
          "claims/other unknown modes must not inherit realm-mode filter");
  options.qualified_source_manifest_sha256 = source_sha; w.bindings.candidate_options = options;
  const auto path = std::filesystem::temp_directory_path() /
      ("xar-candidate-policy-" + std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()) + ".txt");
  Require(!std::filesystem::exists(path), "policy fixture owns a fresh exact path");
  const auto path_text = path.string(); w.bindings.candidate_options.runtime_policy_path = path_text;
  const auto write_policy = [&path](std::string_view value) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    stream << value; Require(bool(stream), "write policy fixture");
  };
  for (const auto &[policy, expected_calls] : std::array<std::pair<std::string_view, int>, 4>{{
           {"shadow-v1\n", 4}, {"cb-first-v1\r\n", 3}, {"full\n", 4}, {"invalid\n", 4}}}) {
    write_policy(policy); const int start = w.evaluations;
    Require(ReadDeclarableWars(w.bindings, candidate) && candidate == baseline &&
            w.evaluations - start == expected_calls, "existing query entry switches mode in same process");
  }
  Require(std::filesystem::remove(path), "remove only owned policy fixture file");
  const int missing_start = w.evaluations;
  Require(ReadDeclarableWars(w.bindings, candidate) && candidate == baseline &&
          w.evaluations - missing_start == 4, "missing runtime policy falls back to full");
}
} // namespace

int main(int argc, char **argv) {
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
  QueryLocalReuseFixture();
  QueryProfileFixture(argc > 1 ? argv[1] : nullptr);
  RealmCandidateLayoutFixture();
  CandidateQueryFixture();
  std::cout << "PASS 1.20.0.2 declarations enumeration, stale choice, validation and native clone ownership fixtures\n";
}
