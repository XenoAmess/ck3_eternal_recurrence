#include "xar_bridge/ck3_12002_realm_law_components.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_12002::private_law {
namespace {

template <typename Value>
Value Load(const void *source, std::size_t offset) noexcept {
  Value value{};
  std::memcpy(&value, static_cast<const std::byte *>(source) + offset,
              sizeof(value));
  return value;
}

using ReleaseNativeRows = void (*)(void *, void *, std::uint32_t);

void ReleaseRows(void *scope, std::size_t data_offset,
                 std::size_t count_offset, std::size_t allocator_offset,
                 void (*destroy_rows)(void *)) noexcept {
  void *data = Load<void *>(scope, data_offset);
  if (data == nullptr) return;
  auto *part = static_cast<std::byte *>(scope) + data_offset;
  if (destroy_rows != nullptr) destroy_rows(part);
  const std::int32_t zero = 0;
  std::memcpy(static_cast<std::byte *>(scope) + count_offset, &zero,
              sizeof(zero));
  void *allocator = Load<void *>(scope, allocator_offset);
  const void *table = Load<void *>(allocator, 0);
  const auto release = Load<ReleaseNativeRows>(table, 0x10);
  release(allocator, data, 8);
}

void AssignKey(std::string_view key,
                bridge::RealmLawGovernanceKeyV1 &output) noexcept {
  output = {};
  output.size = static_cast<std::uint16_t>(key.size());
  std::memcpy(output.bytes.data(), key.data(), key.size());
}

template <std::size_t Count>
bool AssignOptionalSelector(
    std::uint8_t index, const std::array<std::string_view, Count> &keys,
    bridge::RealmLawGovernanceOptionalKeyV1 &output) noexcept {
  output = {};
  if (index > Count) return false;
  output.presence = index == Count
      ? bridge::RealmLawGovernancePresenceV1::absent
      : bridge::RealmLawGovernancePresenceV1::present;
  if (index < Count) AssignKey(keys[index], output.value);
  return true;
}
} // namespace

RealmLawComponentBindings12002 BindRealmLawComponentsImage12002(
    std::uintptr_t module, std::string_view hash) noexcept {
  RealmLawComponentBindings12002 output{};
  if (module == 0 || hash != kExecutableSha256) return output;
  output.enabled = true;
  output.construct_actor_scope = reinterpret_cast<decltype(
      output.construct_actor_scope)>(module + kRealmLawConstructActorScopeRva);
  output.evaluate_trigger = reinterpret_cast<decltype(output.evaluate_trigger)>(
      module + kRealmLawEvaluateCompiledTriggerRva);
  output.destroy_scope_tail = reinterpret_cast<decltype(output.destroy_scope_tail)>(
      module + 0x889700);
  output.destroy_scope_rows = reinterpret_cast<decltype(output.destroy_scope_rows)>(
      module + 0x889780);
  return output;
}

RealmLawComponents12002 ReadRealmLawComponents12002(
    const void *law, const void *actor,
    const RealmLawComponentBindings12002 &bindings) noexcept {
  RealmLawComponents12002 output{};
  if (!bindings.enabled || law == nullptr || actor == nullptr ||
      bindings.construct_actor_scope == nullptr ||
      bindings.evaluate_trigger == nullptr ||
      bindings.destroy_scope_tail == nullptr ||
      bindings.destroy_scope_rows == nullptr) return output;
  alignas(16) std::array<std::byte, kRealmLawActorScopeSize> scope{};
  if (bindings.construct_actor_scope(scope.data(), actor) != scope.data())
    return output;
  const auto *bytes = static_cast<const std::byte *>(law);
  output.can_have = bindings.evaluate_trigger(bytes + kRealmLawCanHaveOffset,
                                               scope.data());
  output.can_pass = bindings.evaluate_trigger(bytes + kRealmLawCanPassOffset,
                                               scope.data());
  output.can_keep = bindings.evaluate_trigger(bytes + kRealmLawCanKeepOffset,
                                               scope.data());
  bindings.destroy_scope_tail(scope.data() + 0x118);
  ReleaseRows(scope.data(), 0x100, 0x108, 0x110,
               bindings.destroy_scope_rows);
  ReleaseRows(scope.data(), 0x18, 0x24, 0x28, nullptr);
  output.complete = true;
  return output;
}

bool ReadRealmLawSuccessionShape12002(
    const void *law, bridge::RealmLawGovernanceSuccessionShapeV1 &output) noexcept {
  output = {};
  if (law == nullptr) return false;
  const auto *policy = static_cast<const std::byte *>(law) +
      kRealmLawSuccessionPolicyOffset;
  const auto order = Load<std::uint8_t>(policy, 0);
  const auto traversal = Load<std::uint8_t>(policy, 1);
  const auto rank = Load<std::uint8_t>(policy, 3);
  const auto division = Load<std::uint8_t>(policy, 4);
  const auto share = Load<std::int64_t>(policy, 0x60);
  constexpr std::array<std::string_view, 9> orders{
      "inheritance", "election", "appointment", "theocratic", "company",
      "generate", "generate_from_template", "player_heir", "noble_family"};
  constexpr std::array<std::string_view, 3> traversals{
      "children", "dynasty_house", "dynasty"};
  constexpr std::array<std::string_view, 2> ranks{"oldest", "youngest"};
  constexpr std::array<std::string_view, 2> divisions{"single_heir", "partition"};
  if (order == orders.size() && traversal == traversals.size() &&
      rank == ranks.size() && division == divisions.size() && share == 0) {
    output.presence = bridge::RealmLawGovernancePresenceV1::absent;
    output.title_division.presence = bridge::RealmLawGovernancePresenceV1::absent;
    output.traversal_order.presence = bridge::RealmLawGovernancePresenceV1::absent;
    output.rank.presence = bridge::RealmLawGovernancePresenceV1::absent;
    output.primary_heir_minimum_share.presence =
        bridge::RealmLawGovernancePresenceV1::absent;
    return true;
  }
  if (order >= orders.size() ||
      !AssignOptionalSelector(traversal, traversals, output.traversal_order) ||
      !AssignOptionalSelector(rank, ranks, output.rank) ||
      !AssignOptionalSelector(division, divisions, output.title_division)) {
    output = {};
    return false;
  }
  output.presence = bridge::RealmLawGovernancePresenceV1::present;
  AssignKey(orders[order], output.order_of_succession);
  output.primary_heir_minimum_share.presence =
      bridge::RealmLawGovernancePresenceV1::present;
  output.primary_heir_minimum_share.value_raw = share;
  return true;
}
} // namespace xar::ck3_12002::private_law
