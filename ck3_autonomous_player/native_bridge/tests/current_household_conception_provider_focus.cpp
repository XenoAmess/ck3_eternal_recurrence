#include "xar_bridge/ck3_12004_first_heir_conception_candidate_inputs.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>

extern "C" int RunConceptionPairProviderScenario12004();
extern "C" unsigned ConceptionPairProviderScenarioCheckCount12004();
extern "C" unsigned ConceptionPairProviderScenarioCount12004();

namespace xar::ck3_12004::secondary_membership_producer_focus {

struct OwnedMemory {
  std::array<std::byte, 0x20> first{};
  std::array<std::byte, 0x1B0> second{};
  std::array<std::byte, 0x30> family{};
  std::array<std::uint32_t, 4> ids{};
  std::uintptr_t denied = 0;
};

template <std::size_t N, typename T>
inline void Put(std::array<std::byte, N> &block, std::size_t offset, T value) {
  std::memcpy(block.data() + offset, &value, sizeof(T));
}
template <typename T, std::size_t N>
inline bool Contains(const std::array<T, N> &block,
                     std::uintptr_t address, std::size_t bytes) {
  const auto begin = reinterpret_cast<std::uintptr_t>(block.data());
  const auto length = sizeof(T) * N;
  return address >= begin && address - begin <= length &&
      bytes <= length - (address - begin);
}
inline bool Copy(void *opaque, const void *address, void *output,
                 std::size_t bytes) noexcept {
  auto &memory = *static_cast<OwnedMemory *>(opaque);
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  if (raw == memory.denied ||
      !(Contains(memory.first, raw, bytes) || Contains(memory.second, raw, bytes) ||
        Contains(memory.family, raw, bytes) || Contains(memory.ids, raw, bytes)))
    return false;
  std::memcpy(output, address, bytes);
  return true;
}
inline void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

inline void RunSecondaryFamilyMembershipProducerFocus12004() {
  OwnedMemory memory;
  const auto first = reinterpret_cast<std::uintptr_t>(memory.first.data());
  const auto second = reinterpret_cast<std::uintptr_t>(memory.second.data());
  const auto family = reinterpret_cast<std::uintptr_t>(memory.family.data());
  const auto data = reinterpret_cast<std::uintptr_t>(memory.ids.data());
  constexpr std::uint32_t first_id = 0xAB000007U, second_id = 0x05000002U;
  Put(memory.first, 0x18, first_id);
  Put(memory.first, 0x1C, std::uint32_t{0x43686172U});
  Put(memory.second, 0x18, second_id);
  Put(memory.second, 0x1C, std::uint32_t{0x43686172U});
  Put(memory.second, 0x1A8, family);
  Put(memory.family, 0x20, data);
  Put(memory.family, 0x2C, std::int32_t{4});
  memory.ids = {0xCD000007U, first_id, first_id, 0xFFFFFFFFU};
  const auto binding = BindConceptionSecondaryFamilyMembership12004(
      kGameVersion, kExecutableSha256, Copy, &memory);
  const auto run = [&]() {
    const auto before_first = memory.first;
    const auto before_second = memory.second;
    const auto before_family = memory.family;
    const auto before_ids = memory.ids;
    auto read = ReadConceptionSecondaryFamilyMembershipForPair12004(
        binding, second, second_id, first, first_id);
    Require(before_first == memory.first && before_second == memory.second &&
        before_family == memory.family && before_ids == memory.ids,
        "secondary membership observer changed source bytes");
    return read;
  };
  auto read = run();
  Require(read.status == "available" && read.second_family_present == true &&
      read.list_count_raw_i32 == 4 && read.list_span_bytes == 16 &&
      read.first_match_index == 1 && read.second_family20_contains_first == true &&
      read.ordered_full_ids == std::vector<std::uint32_t>(memory.ids.begin(), memory.ids.end()),
      "secondary membership lost ordered duplicate complete-generation IDs");
  memory.ids.fill(0xCD000007U);
  read = run();
  Require(read.status == "available" && read.second_family20_contains_first == false,
      "secondary membership compared low24 instead of full32 IDs");
  Put(memory.family, 0x20, std::uintptr_t{0});
  Put(memory.family, 0x2C, std::int32_t{0});
  memory.denied = data;
  read = run();
  Require(read.status == "available" && read.list_data_present == false &&
      read.list_span_bytes == 0 && read.second_family20_contains_first == false,
      "known empty null-data list became unavailable");
  Put(memory.second, 0x1A8, std::uintptr_t{0});
  memory.denied = family + 0x20;
  read = run();
  Require(read.status == "available" && read.second_family_present == false &&
      !read.second_family20_contains_first && !read.list_count_raw_i32,
      "null Family bypass consulted or fabricated membership");
  Put(memory.second, 0x1A8, family);
  memory.denied = 0;
  Put(memory.family, 0x2C, std::int32_t{1});
  read = run();
  Require(read.status == "unavailable" && !read.second_family20_contains_first,
      "positive-count null data became empty false");
  Put(memory.family, 0x20, data);
  Put(memory.family, 0x2C, std::int32_t{-1});
  read = run();
  Require(read.status == "unavailable" && read.list_count_raw_i32 == -1 &&
      !read.second_family20_contains_first,
      "negative signed list count became empty false");
  Put(memory.family, 0x2C, std::int32_t{4});
  memory.ids = {first_id, first_id, first_id, first_id};
  memory.denied = data + 8;
  read = run();
  Require(read.status == "unavailable" && !read.second_family20_contains_first &&
      read.ordered_full_ids.size() == 2,
      "partial raw list exposed an aggregate membership Boolean");
}

} // namespace xar::ck3_12004::secondary_membership_producer_focus

namespace {
using namespace xar::ck3_12004;
using namespace xar::ck3_11906;
struct Memory {
  std::array<std::byte, 0x1D0> first{}, second{};
  std::array<std::byte, 0x30> family{};
  std::array<std::uint32_t, 4> ids{0x01000002U, 2U, 2U, 0xFFFFFFFFU};
  std::array<std::int64_t, 7> scalars{25000, 0, 0, 100000, 150000, 100000, 200000};
  std::uintptr_t denied = 0;
  unsigned id_reads = 0, copies = 0;
  bool wrong_post_id = false, denied_post_id = false;
  std::optional<std::size_t> denied_scalar;
};
template <std::size_t N, typename T>
void Put(std::array<std::byte, N> &block, std::size_t offset, T value) {
  assert(offset <= N && sizeof(T) <= N - offset);
  std::memcpy(block.data() + offset, &value, sizeof(T));
}
template <typename T, std::size_t N>
bool Contains(const std::array<T, N> &block, std::uintptr_t address, std::size_t bytes) {
  const auto start = reinterpret_cast<std::uintptr_t>(block.data());
  constexpr auto length = sizeof(T) * N;
  return address >= start && address - start <= length && bytes <= length - (address - start);
}
bool Copy(void *opaque, const void *address, void *output, std::size_t bytes) noexcept {
  auto &m = *static_cast<Memory *>(opaque);
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  ++m.copies;
  if (raw == m.denied) return false;
  for (std::size_t index = 0; index < m.scalars.size(); ++index)
    if (raw == 0x10000000ULL + conception_pair_value_inputs::kLoadedNumericSlotRvas[index]) {
      if (bytes != sizeof(std::int64_t) || m.denied_scalar == index) return false;
      std::memcpy(output, &m.scalars[index], bytes);
      return true;
    }
  if (raw == reinterpret_cast<std::uintptr_t>(m.second.data()) + 0x18) {
    ++m.id_reads;
    if (m.id_reads > 1 && m.denied_post_id) return false;
    if (m.id_reads > 1 && m.wrong_post_id) {
      const std::uint32_t changed = 0x01000003U;
      std::memcpy(output, &changed, sizeof(changed));
      return true;
    }
  }
  if (!(Contains(m.first, raw, bytes) || Contains(m.second, raw, bytes) ||
        Contains(m.family, raw, bytes) || Contains(m.ids, raw, bytes))) return false;
  std::memcpy(output, address, bytes);
  return true;
}
Memory *current_memory = nullptr;
unsigned normal_calls = 0, reverse_calls = 0;
bool normal_return = false, reverse_return = false, change_after_normal = false;
bool NormalGetter(void *first, void *second) {
  assert(first == current_memory->first.data() && second == current_memory->second.data());
  ++normal_calls;
  if (change_after_normal) Put(current_memory->first, 0x18, std::uint32_t{0x01000002U});
  return normal_return;
}
bool ReverseGetter(void *second, void *first) {
  assert(second == current_memory->second.data() && first == current_memory->first.data());
  ++reverse_calls;
  return reverse_return;
}
void Reset(Memory &m) {
  m = {};
  m.scalars = {25000, 0, 0, 100000, 150000, 100000, 200000};
  m.ids = {0x01000002U, 2U, 2U, 0xFFFFFFFFU};
  Put(m.first, 0x18, std::uint32_t{2}); Put(m.second, 0x18, std::uint32_t{3});
  Put(m.first, 0x1C, std::uint32_t{0x43686172U});
  Put(m.second, 0x1C, std::uint32_t{0x43686172U});
  Put(m.second, 0x1A8, reinterpret_cast<std::uintptr_t>(m.family.data()));
  Put(m.family, 0x20, reinterpret_cast<std::uintptr_t>(m.ids.data()));
  Put(m.family, 0x2C, std::int32_t{4});
  current_memory = &m;
  normal_calls = reverse_calls = 0;
  normal_return = reverse_return = change_after_normal = false;
}
void NewReaderCases() {
  Memory m; Reset(m);
  const auto second = reinterpret_cast<std::uintptr_t>(m.second.data());
  const auto first = reinterpret_cast<std::uintptr_t>(m.first.data());
  const auto title_binding = BindConceptionSecondTitleState12004("1.20.0.4", xar::ck3_12004::kExecutableSha256, Copy, &m);
  auto title = [&]() { m.id_reads = 0; return ReadConceptionSecondTitleStatePresenceForCharacter12004(title_binding, second, 3); };
  assert(title().second_title_state_present == false);
  Put(m.second, 0x1C0, std::uint64_t{0x8000000000000000ULL});
  auto high = title(); assert(high.second_1c0_raw_u64 == 0x8000000000000000ULL && high.second_title_state_present == true);
  m.denied = second + 0x1C0; assert(!title().second_title_state_present); m.denied = 0;
  Put(m.second, 0x18, std::uint32_t{0x01000003U}); assert(!title().second_title_state_present); Put(m.second, 0x18, std::uint32_t{3});
  Put(m.second, 0x1C, std::uint32_t{0}); assert(!title().second_title_state_present); Put(m.second, 0x1C, std::uint32_t{0x43686172U});
  m.denied = second + 0x18; assert(!title().second_title_state_present); m.denied = 0;
  m.wrong_post_id = true; assert(!title().second_title_state_present); m.wrong_post_id = false;
  m.denied_post_id = true; assert(!title().second_title_state_present); m.denied_post_id = false;
  m.copies = 0;
  assert(!ReadConceptionSecondTitleStatePresenceForCharacter12004(title_binding, std::numeric_limits<std::uintptr_t>::max() - 0x10, 3).second_title_state_present && m.copies == 0);
  assert(!ReadConceptionSecondTitleStatePresenceForCharacter12004(BindConceptionSecondTitleState12004("wrong", xar::ck3_12004::kExecutableSha256, Copy, &m), second, 3).second_title_state_present);
  assert(!ReadConceptionSecondTitleStatePresenceForCharacter12004(BindConceptionSecondTitleState12004("1.20.0.4", "wrong", Copy, &m), second, 3).second_title_state_present);
  assert(!ReadConceptionSecondTitleStatePresenceForCharacter12004(BindConceptionSecondTitleState12004("1.20.0.4", xar::ck3_12004::kExecutableSha256, nullptr, &m), second, 3).second_title_state_present);
  Put(m.first, 0x1C0, std::uint64_t{1}); Put(m.second, 0x1C0, std::uint64_t{0}); assert(title().second_title_state_present == false);
  Put(m.first, 0x1C0, std::uint64_t{0}); Put(m.second, 0x1C0, std::uint64_t{1}); assert(title().second_title_state_present == true);
  ConceptionNormalCloseFamily12004Bindings normal{true, NormalGetter, Copy, &m};
  m.id_reads = 0;
  auto n = ReadConceptionNormalCloseFamilyForPair12004(normal, first, 2, second, 3, false, false);
  assert(n.normal_close_family == false && n.native_call_attempted && normal_calls == 1);
  normal_return = true; m.id_reads = 0;
  assert(ReadConceptionNormalCloseFamilyForPair12004(normal, first, 2, second, 3, false, false).normal_close_family == true);
  auto skip = ReadConceptionNormalCloseFamilyForPair12004(normal, first, 2, second, 3, true, std::nullopt);
  assert(skip.status == "not_required" && !skip.normal_close_family && !skip.native_call_attempted);
  auto unknown = ReadConceptionNormalCloseFamilyForPair12004(normal, first, 2, second, 3, std::nullopt, true);
  assert(unknown.status == "unavailable" && !unknown.normal_close_family && !unknown.native_call_attempted);
  assert(!ReadConceptionNormalCloseFamilyForPair12004(normal, first, 0x01000002U, second, 3, false, false).normal_close_family);
  change_after_normal = true; m.id_reads = 0;
  auto changed = ReadConceptionNormalCloseFamilyForPair12004(normal, first, 2, second, 3, false, false);
  assert(!changed.normal_close_family && changed.native_return_value == true && changed.native_call_attempted);
  change_after_normal = false; Put(m.first, 0x18, std::uint32_t{2});
  ConceptionReverseCloseOrExtended12004Bindings reverse{true, 0x10000000ULL, ReverseGetter, Copy, &m};
  m.id_reads = 0;
  assert(ReadConceptionReverseCloseOrExtended12004(reverse, second, 3, first, 2).alternate_close_or_extended == false);
  reverse_return = true; m.id_reads = 0;
  assert(ReadConceptionReverseCloseOrExtended12004(reverse, second, 3, first, 2).alternate_close_or_extended == true);
  assert(reverse_calls == 2);
  assert(!ReadConceptionReverseCloseOrExtended12004(reverse, second, 0x01000003U, first, 2).alternate_close_or_extended);
  m.wrong_post_id = true; m.id_reads = 0;
  assert(!ReadConceptionReverseCloseOrExtended12004(reverse, second, 3, first, 2).alternate_close_or_extended);
}
CurrentFirstHeirRelationshipReadV1 Household() {
  CurrentFirstHeirRelationshipReadV1 read{};
  read.failure = CurrentFirstHeirRelationshipFailureV1::none; read.heir_character_id = 2;
  read.relationship.primary_spouse_character_id = 3; read.relationship.spouse_character_ids = {3};
  read.reproductive_inputs.emplace();
  auto &r = *read.reproductive_inputs;
  r.status = "available"; r.unavailable_reason = {}; r.played_character_id = 1; r.heir_character_id = 2; r.date_raw = 123;
  for (const auto id : {2, 3}) {
    CurrentFirstHeirReproductiveRowV1 row{}; row.character_id = id;
    row.roles = id == 2 ? std::vector<std::string_view>{"heir"} : std::vector<std::string_view>{"primary_spouse", "spouse"};
    row.available = true; row.unavailable_reason = {}; row.age_measure_raw = std::int16_t{32}; row.sex_selector_raw = static_cast<std::uint8_t>(id == 2 ? 0 : 1);
    row.fertility.available = true; row.fertility.extension_present = true; row.fertility.native_gate_evaluated = true; row.fertility.native_gate_allows = true; row.fertility.effective_raw = 40000;
    row.native_pregnancy.status = "available"; row.native_pregnancy.unavailable_reason = {}; row.native_pregnancy.is_pregnant = false;
    r.rows.push_back(row);
  }
  return read;
}
CurrentFirstHeirConceptionCandidateInputsReadV1 Companion() {
  CurrentFirstHeirConceptionCandidateInputsReadV1 c{}; c.status = "available"; c.unavailable_reason = {};
  for (const auto id : {2, 3}) {
    CurrentCharacterConceptionCandidateRowV1 row{}; row.character_id = id;
    row.secondary_context.status = "available"; row.secondary_context.unavailable_reason = {}; row.secondary_context.context_7d8_raw_i32 = 0; row.secondary_context.selects_alternate_relation_path = false;
    c.rows.push_back(row);
  }
  auto &f = c.rows[0].first_value; f.status = "available"; f.unavailable_reason = {}; f.seed_after_children_raw = 30000; f.adjusted_age_raw = 32; f.selected_age_band_index = 0; f.age_product_raw = 30000; f.first_output_raw = 30000;
  auto &s = c.rows[1].second_value; s.ready = true; s.adjusted_age_raw = 32; s.selected_band_index = 0; s.prefinal_raw = 40000; s.value_raw = 40000;
  CurrentHouseholdConceptionPairInputsV1 p{}; p.first_character_id = 2; p.second_character_id = 3;
  p.first_title_state_present = false; p.selected_character_id = 3;
  p.offspring_count.status = "available"; p.offspring_count.unavailable_reason = {}; p.offspring_count.native_count = 1;
  p.child_limit.status = "complete"; p.child_limit.unavailable_reason = {}; p.child_limit.value.child_limit_raw = 5;
  p.last_child_date.status = "family_absent_bypass"; p.last_child_date.date_inputs_available = true; p.last_child_date.unavailable_reason = {}; p.last_child_date.source.first_family_present = false; p.last_child_date.recent_child_branch_passed = true;
  p.list_bonus.status = "available"; p.list_bonus.unavailable_reason = {}; p.list_bonus.primary_relation_match = false; p.list_bonus.apply_relation_bonus = false; p.list_bonus.apply_land_state_bonus = false;
  p.related_pair.status = "available"; p.related_pair.unavailable_reason = {}; p.related_pair.related_pair_predicate = false;
  p.short_circuit.status = "available"; p.short_circuit.reason = "continue"; p.short_circuit.first_evaluated = p.short_circuit.second_evaluated = true; p.short_circuit.short_circuits_to_zero = false;
  for (auto *predicate : {&p.short_circuit.first, &p.short_circuit.second}) { predicate->status = "available"; predicate->reason = "continue"; predicate->predicate_true = false; }
  c.pairs.push_back(p); return c;
}
void CollectNewInputs(Memory &m, CurrentFirstHeirConceptionCandidateInputsReadV1 &c) {
  auto &p = c.pairs[0];
  const auto first = reinterpret_cast<std::uintptr_t>(m.first.data()), second = reinterpret_cast<std::uintptr_t>(m.second.data());
  auto title = ReadConceptionSecondTitleStatePresenceForCharacter12004(BindConceptionSecondTitleState12004("1.20.0.4", xar::ck3_12004::kExecutableSha256, Copy, &m), second, 3);
  p.second_title_state_status = title.status; p.second_title_state_unavailable_reason = title.unavailable_reason; p.second_1c0_raw_u64 = title.second_1c0_raw_u64; p.second_title_state_present = title.second_title_state_present;
  m.id_reads = 0;
  p.secondary_family_membership = ReadConceptionSecondaryFamilyMembershipForPair12004(BindConceptionSecondaryFamilyMembership12004("1.20.0.4", xar::ck3_12004::kExecutableSha256, Copy, &m), second, 3, first, 2);
  m.id_reads = 0;
  p.normal_close_family = ReadConceptionNormalCloseFamilyForPair12004({true, NormalGetter, Copy, &m}, first, 2, second, 3, c.rows[0].secondary_context.selects_alternate_relation_path, c.rows[1].secondary_context.selects_alternate_relation_path);
  if (change_after_normal) { change_after_normal = false; Put(m.first, 0x18, std::uint32_t{2}); }
  m.id_reads = 0;
  p.reverse_close_or_extended = ReadConceptionReverseCloseOrExtended12004({true, 0x10000000ULL, ReverseGetter, Copy, &m}, second, 3, first, 2);
  NativeConceptionCandidateBindingsV1 b{}; b.enabled = true; b.module_base = 0x10000000ULL; b.read_memory = Copy; b.read_context = &m;
  p.provider_numeric = ReadProviderNumericInputsV1(b);
  if (!m.denied_scalar) {
    p.loaded_numeric.status = conception_pair_value_inputs::LoadedReadStatus::available;
    p.loaded_numeric.inputs = conception_pair_value_inputs::LoadedNumericInputs{m.scalars[0],m.scalars[1],m.scalars[2],m.scalars[3],m.scalars[4],m.scalars[5],m.scalars[6]};
  } else {
    p.loaded_numeric.status = conception_pair_value_inputs::LoadedReadStatus::slot_read_failed;
    p.loaded_numeric.failed_slot_rva = conception_pair_value_inputs::kLoadedNumericSlotRvas[*m.denied_scalar];
  }
  p.base_stage = conception_pair_value_inputs::EvaluateBaseStage(c.rows[0].first_value.first_output_raw, c.rows[1].second_value.value_raw, p.loaded_numeric.inputs ? std::optional<std::int64_t>{p.loaded_numeric.inputs->base_average_floor} : std::nullopt);
  p.alternate_relation_path = SelectConceptionSecondaryRelationPath12004(c.rows[0].secondary_context.selects_alternate_relation_path,c.rows[1].secondary_context.selects_alternate_relation_path);
  p.provider_inputs = BuildConceptionProviderInputsV1(p, &c.rows[0], &c.rows[1], false);
  p.provider_result = EvaluateConceptionPairProvider12004(p.provider_inputs);
}
void Emit(std::string_view name, const CurrentFirstHeirRelationshipReadV1 &h, const CurrentFirstHeirConceptionCandidateInputsReadV1 *c) {
  std::cout << CurrentFirstHeirRelationshipResultJsonV1(name, 7, 2, h, {}, nullptr, nullptr, c) << '\n';
}
} // namespace
int main(int argc, const char **argv) {
  const bool wire_only = argc == 2 && std::string_view(argv[1]) == "--wire-only";
  assert(argc == 1 || wire_only);
  if (!wire_only) {
    assert(RunConceptionPairProviderScenario12004() == 0);
    NewReaderCases();
    xar::ck3_12004::secondary_membership_producer_focus::RunSecondaryFamilyMembershipProducerFocus12004();
  }
  Memory m; auto household = Household();
  Reset(m); auto c = Companion(); CollectNewInputs(m, c);
  assert(c.pairs[0].provider_result.first_output_raw == 35000); Emit("normal_complete", household, &c);
  Reset(m); c = Companion(); m.denied_scalar = 6; CollectNewInputs(m, c);
  assert(c.pairs[0].provider_result.first_output_raw == 35000 && !c.pairs[0].loaded_numeric.inputs); Emit("unused_scalar_missing", household, &c);
  Reset(m); c = Companion(); Put(m.second, 0x1C0, std::uint64_t{0x8000000000000000ULL}); c.rows[0].secondary_context.selects_alternate_relation_path = true; c.rows[0].secondary_context.context_7d8_raw_i32 = 1; reverse_return = true; CollectNewInputs(m, c);
  assert(c.pairs[0].provider_result.first_output_raw == 70000 && normal_calls == 0 && c.pairs[0].normal_close_family.status == "not_required"); Emit("alternate_directed_true", household, &c);
  Reset(m); c = Companion(); c.rows[0].secondary_context.selects_alternate_relation_path = true; c.rows[0].secondary_context.context_7d8_raw_i32 = 1; m.denied = reinterpret_cast<std::uintptr_t>(m.ids.data()) + 8; CollectNewInputs(m, c);
  assert(!c.pairs[0].provider_result.first_output_raw && c.pairs[0].provider_result.unavailable_input == "second_family20_contains_first"); Emit("partial_membership", household, &c);
  Reset(m); c = Companion(); normal_return = true; change_after_normal = true; CollectNewInputs(m, c);
  assert(!c.pairs[0].provider_result.first_output_raw && c.pairs[0].normal_close_family.native_return_value == true); Emit("normal_identity_changed", household, &c);
  c = Companion(); c.pairs[0].short_circuit.first.predicate_true = true; c.pairs[0].short_circuit.second_evaluated = false; c.pairs[0].short_circuit.second = {}; c.pairs[0].short_circuit.short_circuits_to_zero = true; c.pairs[0].short_circuit.first_output_raw = 0;
  c.pairs[0].provider_inputs = BuildConceptionProviderInputsV1(c.pairs[0], nullptr, nullptr, std::nullopt); c.pairs[0].provider_result = EvaluateConceptionPairProvider12004(c.pairs[0].provider_inputs);
  assert(c.pairs[0].provider_result.first_output_raw == 0 && c.pairs[0].provider_result.reached_stages == 1); Emit("known_early_zero", household, &c);
  c = {}; c.unavailable_reason = "current_household_conception_frame_changed"; Emit("changed_frame", household, &c);
  Emit("legacy_absent", household, nullptr);
  std::cout << "{\"new_provider_scenarios\":" << ConceptionPairProviderScenarioCount12004() << ",\"new_provider_checks\":" << ConceptionPairProviderScenarioCheckCount12004() << ",\"new_wire_cases\":8,\"original_provider_calls\":false,\"native_rng_calls\":false}" << '\n';
}
