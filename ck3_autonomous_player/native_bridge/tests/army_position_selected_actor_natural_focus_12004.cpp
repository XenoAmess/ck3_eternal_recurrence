#include "xar_bridge/army_position_selected_actor_12004.hpp"

#include <bit>
#include <cstdint>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kImage = 0x140000000;
constexpr std::uintptr_t kActor = 0x210000000;
constexpr std::uintptr_t kHolder = 0x210001000;
constexpr std::uintptr_t kFirst = 0x210002000;
constexpr std::uintptr_t kSecond = 0x210003000;
constexpr std::uintptr_t kContext = 0x210004000;
constexpr std::uintptr_t kContextLink = 0x210005000;
constexpr std::uintptr_t kFallback = 0x210006000;
constexpr std::uintptr_t kRelation = 0x210007000;
constexpr std::uintptr_t kWar = 0x210008000;

struct Memory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::uintptr_t fail_address = 0;
  std::size_t fail_occurrence = 0;
  std::size_t demanded_occurrences = 0;
  template <typename T> void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = source[i];
  }
  static bool Read(void *context, std::uintptr_t address, void *output,
                   std::size_t size) noexcept {
    auto &self = *static_cast<Memory *>(context);
    if (address == self.fail_address &&
        ++self.demanded_occurrences == self.fail_occurrence) return false;
    auto *destination = static_cast<std::uint8_t *>(output);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = self.bytes.find(address + i);
      if (found == self.bytes.end()) return false;
      destination[i] = found->second;
    }
    return true;
  }
  ArmyRegularCoreReadonlyAccess12004 Access(std::size_t maximum = 8) {
    return {kImage, this, Read, maximum};
  }
};

Memory Initial(std::uint32_t candidate_id = 2) {
  Memory m;
  m.Put(kActor + 0x1C0, kContext);
  m.Put(kActor + 0x1B8, std::uintptr_t{0});
  m.Put(kContext + 0x1C0, kContextLink);
  m.Put(kContextLink + 0x28, kFirst);
  m.Put(kFirst + 0x1C, std::uint32_t{0x43686172});
  m.Put(kFirst + 0x18, candidate_id);
  m.Put(kImage + 0x5C67570, kFallback);
  return m;
}

void StableNext(Memory &m) {
  const auto context = kContext + 0x1000;
  const auto link = kContextLink + 0x1000;
  m.Put(kFirst + 0x1C0, context);
  m.Put(kFirst + 0x1B8, std::uintptr_t{0});
  m.Put(context + 0x1C0, link);
  m.Put(link + 0x28, kSecond);
  // A rejected tag retains the current node, before its acceptance gate.
  m.Put(kSecond + 0x1C, std::uint32_t{0});
}

void NoSharedSideOrRelationWar(Memory &m, std::uint32_t holder_id = 3) {
  m.Put(kHolder + 0x18, holder_id);
  m.Put(kHolder + 0x1C0, std::uintptr_t{0});
  m.Put(kImage + 0x5459D38, std::uintptr_t{0});
  m.Put(kImage + 0x5459D38 + 0xC, std::int32_t{0});
  m.Put(kHolder + 0x1B0, std::uintptr_t{0});
  m.Put(kImage + 0x5D27B70, kRelation);
  m.Put(kRelation + 0x20, std::int32_t{-1});
}

void MappedNext(Memory &m) {
  constexpr auto link = kContext + 0x2000;
  constexpr auto registry = kContextLink + 0x4000;
  constexpr auto slots = kContextLink + 0x3000;
  constexpr std::uint32_t full = 0xA1000000;
  m.Put(kFirst + 0x1C0, std::uintptr_t{0});
  m.Put(kFirst + 0x1B8, link);
  m.Put(link + 0xC8, full);
  m.Put(kImage + 0x5C67568, registry);
  m.Put(registry + 0x2C, std::uint32_t{1});
  m.Put(registry + 0x20, slots);
  m.Put(slots + 8, kSecond);
  m.Put(kSecond + 0x18, full);
  m.Put(kSecond + 0x1C0, std::uintptr_t{0});
  m.Put(kSecond + 0x1B8, std::uintptr_t{0});
}
} // namespace

// Exported to the sole new-phase compound executable. No separate main/FIRST.
bool RunArmyPositionSelectedActor12004Cases(std::string &reason,
                                          bool retry_after_mapped_next = false) {
  const auto check = [&](bool condition, const char *name) {
    if (!condition) reason = name;
    return condition;
  };
  if (!retry_after_mapped_next) {
  {
    auto m = Initial(0xFFFFFFFFU);
    // Existing receiver rejects the sentinel and returns original actor;
    // the new selector returns the literal null native fallback. No Model,
    // Title, PC or current_context_getter_identity prerequisite is supplied.
    m.Put(kImage + 0x5C67570, std::uintptr_t{0});
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder, 0);
    if (!check(r.selected_actor_identity == std::optional<std::uintptr_t>{0} &&
               r.path_occurrences == 0 && r.unavailable_reason.empty(),
               "selected_actor_initial_equal_null_fallback")) return false;
  }
  {
    auto m = Initial(); StableNext(m);
    m.Put(kHolder + 0x18, std::uint32_t{2});
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder);
    if (!check(r.selected_actor_identity == kFirst && r.path_occurrences == 1,
               "selected_actor_same_full_id_after_next")) return false;
  }
  {
    auto m = Initial();
    m.Put(kHolder + 0x18, std::uint32_t{2});
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder);
    if (!check(!r.selected_actor_identity && !r.unavailable_reason.empty(),
               "selected_actor_next_read_failure_before_same_id")) return false;
  }
  {
    auto m = Initial(); StableNext(m); NoSharedSideOrRelationWar(m);
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder);
    if (!check(r.selected_actor_identity == kFallback && r.path_occurrences == 1,
               "selected_actor_stable_rejection_returns_global_fallback")) return false;
  }
  {
    auto m = Initial(); StableNext(m); NoSharedSideOrRelationWar(m);
    // Initial receiver, first gate and same-side consumed this ID already;
    // the selector's actual post-call fourth copy must still be demanded.
    m.fail_address = kFirst + 0x18;
    m.fail_occurrence = 4;
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder);
    if (!check(!r.selected_actor_identity &&
               r.unavailable_reason == "selected_actor_relation_full_id_reload_unread",
               "selected_actor_post_same_side_id_reload_failure")) return false;
  }
  }
  {
    auto m = Initial(); MappedNext(m); NoSharedSideOrRelationWar(m, 0xA1000000);
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder);
    if (!check(r.selected_actor_identity == kSecond && r.path_occurrences == 2,
               "selected_actor_mapped_next_generation_and_iteration")) return false;
    const auto bounded = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(1), kActor, kHolder);
    if (!check(!bounded.selected_actor_identity &&
               bounded.unavailable_reason == "selected_actor_path_occurrence_budget_exhausted",
               "selected_actor_path_budget_remains_unknown")) return false;
  }
  {
    auto m = Initial(); StableNext(m); NoSharedSideOrRelationWar(m);
    m.Put(kRelation + 0x20, std::bit_cast<std::int32_t>(std::uint32_t{0xA1000000}));
    m.Put(kImage + 0x5D1DE58, std::uintptr_t{0});
    m.Put(kImage + 0x5D1DE40, kWar);
    m.Put(kWar + 0x358, std::uint8_t{0});
    const auto r = ReadArmyPositionSelectedActor2C0FEC012004(m.Access(), kActor, kHolder, 0);
    if (!check(r.selected_actor_identity == kFirst,
               "selected_actor_active_relation_null_actual_filter")) return false;
  }
  reason.clear();
  return true;
}
} // namespace xar::ck3_12004

void RunArmyPositionSelectedActorNaturalFocus12004() {
  std::string reason;
  if (!xar::ck3_12004::RunArmyPositionSelectedActor12004Cases(reason))
    throw std::runtime_error(reason);
}

// Central retry skips the five scenes already passed by the actual first run.
// The failed mapped-next scene, its budget check and the pending active War
// scene use the same helpers and assertions as the complete future fixture.
void RunArmyPositionSelectedActorNaturalRetryAfterMappedNext12004() {
  std::string reason;
  if (!xar::ck3_12004::RunArmyPositionSelectedActor12004Cases(reason, true))
    throw std::runtime_error(reason);
}
