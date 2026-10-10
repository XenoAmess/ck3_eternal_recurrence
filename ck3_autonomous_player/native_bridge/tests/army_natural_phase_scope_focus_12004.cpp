#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include "xar_bridge/army_natural_phase_json_12004.hpp"

#include <array>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <thread>

namespace {
using namespace xar::ck3_12004;
std::array<std::byte, 0x200> manager{};
std::array<std::byte, 0xD0> state{};
std::array<std::uint32_t, 4> ids{0xAB000001U, 0U, 0xAB000001U, 0xFFFFFFFFU};
unsigned calls = 0;
bool deny_read = false;
ArmyNaturalPhaseBindings12004 bindings;
constexpr std::uintptr_t kRawReturn = 0xFEDCBA9876543210ULL;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template<class T> void Store(std::array<std::byte, 0xD0> &storage,
    std::size_t offset, T value) { std::memcpy(storage.data() + offset, &value, sizeof value); }
bool Read(void *, std::uintptr_t address, void *output, std::size_t bytes) noexcept {
  if (deny_read) return false;
  const auto in = [&](const auto &storage) {
    const auto begin = reinterpret_cast<std::uintptr_t>(storage.data());
    return address >= begin && address - begin <= sizeof storage &&
        bytes <= sizeof storage - static_cast<std::size_t>(address - begin);
  };
  if (!in(manager) && !in(state) && !in(ids)) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), bytes);
  return true;
}
void Setup() {
  manager.fill(std::byte{0}); state.fill(std::byte{0}); calls = 0; deny_read = false;
  const auto roster = reinterpret_cast<std::uintptr_t>(ids.data());
  const std::int32_t count = 4;
  std::memcpy(manager.data() + 0x50, &roster, sizeof roster);
  std::memcpy(manager.data() + 0x5C, &count, sizeof count);
  Store(state, 8, std::uint64_t{0x11223344032D2400ULL});
  Store(state, 0x9C, std::uint32_t{42}); Store(state, 0xC0, std::uint8_t{0x80});
  bindings = {};
  bindings.read = Read;
  bindings.next_event = NextArmyNaturalPhaseEvent12004;
  bindings.game_state_identity = reinterpret_cast<std::uintptr_t>(state.data());
  bindings.session_identity = reinterpret_cast<std::uintptr_t>(&bindings);
}
std::uintptr_t __fastcall Plain(void *) { ++calls; return kRawReturn; }
std::uintptr_t __fastcall Pre(void *secondary) {
  ++calls;
  const auto before = CopyActiveArmyNaturalPhaseScope12004();
  Require(before.observed && before.phase == ArmyNaturalPhaseKind12004::pre_date, "pre parent TLS");
  Require(before.original_army_roster.boundary == ArmyNaturalRosterBoundary12004::parent_entry,
      "entry snapshot must remain earlier");
  const auto primary = reinterpret_cast<std::uintptr_t>(secondary) - 8;
  Require(!ObserveArmyNaturalPhaseOriginalRoster12004(primary, 0x2A99E77), "wrong prefix boundary");
  Require(ObserveArmyNaturalPhaseOriginalRoster12004(primary, 0x2A99E76,
      std::uint64_t{0x11223344032D2418ULL}), "literal roster boundary");
  const auto exact = CopyActiveArmyNaturalPhaseScope12004();
  Require(exact.original_army_roster.ordered_full_ids == std::vector<std::uint32_t>(ids.begin(), ids.end()),
      "raw full generations and repeated occurrences");
  Require(exact.original_army_roster.boundary == ArmyNaturalRosterBoundary12004::pre_date_prefix_return,
      "real prefix boundary retained");
  bool other_thread_active = true;
  std::thread other([&] { other_thread_active = CopyActiveArmyNaturalPhaseScope12004().observed; });
  other.join(); Require(!other_thread_active, "parent TLS must not cross threads");
  Store(state, 8, std::uint64_t{0x11223344032D2418ULL});
  Store(state, 0x9C, std::uint32_t{43});
  return kRawReturn;
}
std::uintptr_t __fastcall Post(void *secondary) {
  ++calls;
  const auto incoming = CopyActiveArmyNaturalPhaseScope12004();
  Require(incoming.entry_c0_raw == std::uint8_t{0x80} && !incoming.saved_mask02_admitted,
      "entry C0 is not later saved mask");
  Require(ObserveArmyNaturalPhaseSavedMask12004(reinterpret_cast<std::uintptr_t>(secondary),
      0x2A9A67D, std::uint8_t{0}), "unconditional due saved false mask");
  Require(!ObserveArmyNaturalPhaseSavedMask12004(reinterpret_cast<std::uintptr_t>(secondary),
      0x2A9A8E2, std::uint8_t{0}), "guarded core cannot certify false");
  Require(!ObserveArmyNaturalPhaseSavedMask12004(reinterpret_cast<std::uintptr_t>(secondary),
      0x2A9A8EA, std::uint8_t{2}), "contradictory later mask rejected");
  const auto outer = CopyActiveArmyNaturalPhaseScope12004();
  const auto nested = InvokeArmyNaturalPhaseScope12004(bindings, Plain, secondary,
      ArmyNaturalPhaseKind12004::pre_date, 0x123);
  Require(nested.original_called && nested.original_returned && nested.raw_return_bits == kRawReturn,
      "nested original once/RAX");
  const auto restored = CopyActiveArmyNaturalPhaseScope12004();
  Require(restored.entry_event.sequence == outer.entry_event.sequence &&
      restored.phase == ArmyNaturalPhaseKind12004::post_date, "restore outer TLS");
  Store(state, 0xC0, std::uint8_t{0x82});
  return kRawReturn;
}
} // namespace

void RunArmyNaturalPhaseScopeFocus12004() {
  using namespace xar::ck3_12004;
  Setup(); ClearArmyNaturalPhaseJournal12004();
  auto *secondary = manager.data() + 8;
  const auto pre = InvokeArmyNaturalPhaseScope12004(bindings, Pre, secondary,
      ArmyNaturalPhaseKind12004::pre_date, 0xA1);
  Require(calls == 1U && pre.original_called && pre.original_returned && pre.raw_return_bits == kRawReturn,
      "pre original once opaque RAX");
  Require(pre.scope.date_raw != pre.returned_date_raw && pre.scope.absolute_day_raw != pre.returned_absolute_day_raw,
      "pre and returned frames remain separate");
  Require(pre.same_clock_thread_order == true && !CopyActiveArmyNaturalPhaseScope12004().observed,
      "completed shared clock and inactive TLS");
  Require(ArmyNaturalPhaseCurrentContextMatches12004(pre.scope,
      pre.scope.primary_manager_identity, pre.scope.game_state_identity, pre.scope.entry_event.clock_identity),
      "owned actual process/context qualification");
  Require(!ArmyNaturalPhaseSessionMatches12004(pre.scope, std::nullopt).has_value(),
      "missing session remains independent unknown");
  Require(ArmyNaturalPhaseSessionMatches12004(pre.scope, bindings.session_identity) == true,
      "source supplied same session");
  Require(!ArmyNaturalPhaseCurrentContextMatches12004(pre.scope,
      pre.scope.primary_manager_identity + 8, pre.scope.game_state_identity, pre.scope.entry_event.clock_identity),
      "other manager rejected");
  const auto post = InvokeArmyNaturalPhaseScope12004(bindings, Post, secondary,
      ArmyNaturalPhaseKind12004::post_date, 0xA2);
  Require(calls == 3U && post.scope.saved_mask02_admitted == false && !post.scope.saved_c0_raw &&
      post.returned_c0_raw == std::uint8_t{0x82}, "saved mask survives later C0 writes");
  Require(post.scope.actual_entry_rva == kArmyNaturalPostDateRva12004 &&
      post.scope.entry_event.clock_identity == pre.scope.entry_event.clock_identity &&
      post.scope.entry_event.sequence > pre.returned_event.sequence, "one process monotonic clock");
  const auto journal = ReadArmyNaturalPhaseJournal12004();
  Require(journal.size() == std::size_t{3}, "nested and complete parent journal");
  std::ostringstream json; AppendArmyNaturalPhaseJournal12004(json, journal);
  Require(json.str().find("\"saved_c0_raw\":null") != std::string::npos &&
      json.str().find("\"boundary\":\"pre_date_prefix_return\"") != std::string::npos,
      "honest scope serialization");
  deny_read = true;
  const auto partial = InvokeArmyNaturalPhaseScope12004(bindings, Plain, secondary,
      ArmyNaturalPhaseKind12004::pre_date, 0xA3);
  Require(calls == 4U && partial.original_returned && !partial.scope.date_raw &&
      !partial.scope.original_army_roster.complete, "failed observation still original once");
  const auto count_before = ReadArmyNaturalPhaseJournal12004().size();
  const auto absent = InvokeArmyNaturalPhaseScope12004(bindings, nullptr, secondary,
      ArmyNaturalPhaseKind12004::post_date, 0xA4);
  Require(!absent.scope.observed && !absent.original_called &&
      ReadArmyNaturalPhaseJournal12004().size() == count_before, "no fake original or journal");
  const auto event_before_clear = NextArmyNaturalPhaseEvent12004();
  ClearArmyNaturalPhaseJournal12004();
  const auto event_after_clear = NextArmyNaturalPhaseEvent12004();
  Require(event_after_clear.clock_identity == event_before_clear.clock_identity &&
      event_after_clear.sequence > event_before_clear.sequence, "journal clear never resets clock");
}
