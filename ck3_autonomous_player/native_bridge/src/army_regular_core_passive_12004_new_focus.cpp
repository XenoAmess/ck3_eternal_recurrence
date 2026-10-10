#include "xar_bridge/army_regular_core_passive_12004.hpp"
#include "xar_bridge/army_regular_core_passive_12004_new_focus.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004 {
namespace {
void Check(bool value, const char *reason) { if (!value) throw std::runtime_error(reason); }
constexpr std::uintptr_t image = 0x10000000, manager = 0x20000000, state = 0x20100000;
constexpr std::uintptr_t persistent = 0x30001000, fallback = 0x30000000;
constexpr std::uintptr_t army = 0x40000000, arrg = 0x50001000, invalid_arrg = 0x50000000;
constexpr std::uintptr_t province = 0x60000000, definition = 0x60100000;
constexpr std::uintptr_t persistent_ids = 0x70000000, army_ids = 0x70001000, arrg_ids = 0x70002000;
constexpr std::uintptr_t persistent_registry = 0x71000000, persistent_table = 0x71001000;
constexpr std::uintptr_t arrg_registry = 0x71002000, arrg_table = 0x71003000, data = 0x72000000;
constexpr std::uintptr_t opaque_return = 0xFEDCBA9876543210ULL;
struct Region { std::uintptr_t address; std::vector<std::byte> bytes; };
struct Memory {
  std::vector<Region> regions;
  std::size_t reads = 0, original_calls = 0;
  bool block_entry_prepared = false, change_date = false;
  std::uintptr_t caller = kArmyRegularCoreCallerReturnRva12004;
  ArmyRegularCoreBindings12004 bindings;
  ArmyRegularCoreObservation12004 observation;
  void Add(std::uintptr_t address, std::size_t count) { regions.push_back({address, std::vector<std::byte>(count)}); }
  template<class T> void Put(std::uintptr_t address, T value) {
    for (auto &region : regions) if (address >= region.address && address - region.address <= region.bytes.size() &&
        sizeof value <= region.bytes.size() - (address - region.address)) {
      std::memcpy(region.bytes.data() + (address - region.address), &value, sizeof value); return;
    }
    throw std::runtime_error("fixture write exceeds owned region");
  }
  void Slot(std::uintptr_t rva, std::uintptr_t value) { Add(image + rva, 8); Put(image + rva, value); }
  static bool Read(void *context, std::uintptr_t address, void *out, std::size_t count) noexcept {
    auto &m = *static_cast<Memory *>(context); ++m.reads;
    if (m.block_entry_prepared && address == persistent + 0x148) return false;
    for (const auto &region : m.regions) if (address >= region.address && address - region.address <= region.bytes.size() &&
        count <= region.bytes.size() - (address - region.address)) {
      std::memcpy(out, region.bytes.data() + (address - region.address), count); return true;
    }
    return false;
  }
  void Seed() {
    Add(manager, 0x100); Add(state, 0x100);
    Add(persistent, 0x160); Add(fallback, 0x160); Add(army, 0x200);
    Add(arrg, 0x160); Add(invalid_arrg, 0x160); Add(province, 0x800); Add(definition, 0x40);
    Add(persistent_ids, 16); Add(army_ids, 8); Add(arrg_ids, 8); Add(data, 32);
    Add(persistent_registry, 0x40); Add(persistent_table, 48); Add(arrg_registry, 0x40); Add(arrg_table, 32);
    Put(manager + 0x30, persistent_ids); Put<std::int32_t>(manager + 0x3C, 4);
    Put(manager + 0x50, army_ids); Put<std::int32_t>(manager + 0x5C, 2);
    Put<std::int32_t>(persistent_ids, 2); Put<std::int32_t>(persistent_ids + 4, 0x1000001);
    Put<std::int32_t>(persistent_ids + 8, 0x2000001); Put<std::int32_t>(persistent_ids + 12, 2);
    Put<std::int32_t>(army_ids, 0x1000001); Put<std::int32_t>(army_ids + 4, 0x2000001);
    Put<std::uint64_t>(state + 8, 0x123456789ULL); Put<std::uint32_t>(state + 0x9C, 1234);
    Put<std::uint8_t>(state + 0xC0, 2);
    Slot(0x5D1EB68, persistent_registry); Slot(0x5D1EB58, fallback);
    Put(persistent_registry + 0x20, persistent_table); Put<std::int32_t>(persistent_registry + 0x2C, 3);
    Put(persistent_table + 2 * 16 + 8, persistent);
    Slot(0x5D1DE48, 0); Slot(0x5D1DE50, army);
    Slot(0x5D1F340, arrg_registry); Slot(0x5D1F338, invalid_arrg);
    Put(arrg_registry + 0x20, arrg_table); Put<std::int32_t>(arrg_registry + 0x2C, 2);
    Put(arrg_table + 16 + 8, arrg);
    Put<std::int32_t>(persistent + 0x10, 2); Put<std::uint32_t>(persistent + 0x14, 0x52656769);
    Put<std::int32_t>(fallback + 0x10, -1); Put<std::uint32_t>(fallback + 0x14, 0x52656769);
    Put<std::int64_t>(persistent + 0x148, 10000); Put<std::int64_t>(fallback + 0x148, 20000);
    Put(persistent + 0x118, definition); Put(persistent + 0x120, province);
    Put<std::int32_t>(persistent + 0x138, 1);
    Put<std::int32_t>(province + 0x10, 900); Put<std::int32_t>(province + 0x788, -1);
    Put<std::int32_t>(province + 0x73C, -1); Put<std::uint32_t>(definition + 0x38, 0);
    for (const auto object : {persistent, fallback}) for (std::int32_t i = 0; i < 7; ++i) {
      const auto chunk = object + 0x18 + static_cast<std::size_t>(i) * 0x24;
      Put<std::int32_t>(chunk, i ? 0 : 100); Put<std::int32_t>(chunk + 4, i ? 0 : (object == persistent ? 80 : 20));
      Put<std::int32_t>(chunk + 8, 2); Put<std::int32_t>(chunk + 0xC, i);
      Put<std::int32_t>(chunk + 0x10, -1); Put<std::uint8_t>(chunk + 0x14, 1);
      Put<std::int32_t>(chunk + 0x18, i ? 0 : 3);
    }
    Put<std::int32_t>(invalid_arrg + 0x10, -1); Put<std::uint32_t>(invalid_arrg + 0x14, 0);
    Put<std::int32_t>(army + 0x10, -1); Put(army + 0x38, arrg_ids); Put<std::int32_t>(army + 0x44, 2);
    Put<std::int32_t>(arrg_ids, 1); Put<std::int32_t>(arrg_ids + 4, 1);
    Put<std::int32_t>(arrg + 0x10, 1); Put<std::uint32_t>(arrg + 0x14, 0x41725267);
    Put<std::int32_t>(arrg + 0x148, -1); Put(arrg + 0x20, data); Put<std::int32_t>(arrg + 0x2C, 2);
    Put<std::int32_t>(data + 8, 2); Put<std::int32_t>(data + 12, 0);
    Put<std::int32_t>(data + 24, 2); Put<std::int32_t>(data + 28, 0);
    bindings = BindArmyRegularCoreImage12004(image, kExecutableSha256);
    bindings.read_context = this; bindings.read = &Read;
  }
};
Memory *active = nullptr;
std::uintptr_t __fastcall Original(void *) {
  ++active->original_calls;
  active->block_entry_prepared = false;
  active->Put<std::int32_t>(persistent + 0x1C, 99);
  active->Put<std::int32_t>(persistent + 0x30, 4);
  active->Put<std::int32_t>(manager + 0x3C, 1); active->Put<std::int32_t>(manager + 0x5C, 1);
  if (active->change_date) active->Put<std::uint64_t>(state + 8, 0x12345678AULL);
  return opaque_return;
}
std::uintptr_t __fastcall ParentOriginal(void *secondary) {
  active->observation = InvokeArmyRegularCorePassive12004(active->bindings, &Original,
      reinterpret_cast<void *>(reinterpret_cast<std::uintptr_t>(secondary) - 8), active->caller);
  return active->observation.raw_return_bits;
}
ArmyNaturalPhaseRecord12004 Connected(Memory &memory) {
  active = &memory;
  ArmyNaturalPhaseBindings12004 parent;
  parent.read_context = &memory; parent.read = &Memory::Read; parent.game_state_identity = state;
  return InvokeArmyNaturalPhaseScope12004(parent, &ParentOriginal, reinterpret_cast<void *>(manager + 8),
      ArmyNaturalPhaseKind12004::post_date, 0xAA001);
}
const ArmyRegularCorePersistent12004 &Physical(const ArmyRegularCoreFrame12004 &frame, std::uintptr_t token) {
  const auto found = std::find_if(frame.persistent_objects.begin(), frame.persistent_objects.end(),
      [&](const auto &item) { return item.physical_token == token; });
  Check(found != frame.persistent_objects.end(), "expected owned physical object absent"); return *found;
}
} // namespace

void RunArmyRegularCoreNaturalFocus12004() {
  ClearArmyRegularCoreJournal12004();
  Memory complete; complete.Seed();
  const auto parent = Connected(complete); const auto &event = complete.observation;
  Check(complete.original_calls == 1 && event.original_called && event.original_returned &&
      event.raw_return_bits == opaque_return && parent.raw_return_bits == opaque_return, "original/opaque RAX contract");
  Check(event.observed && event.entry_provenance_complete && event.return_provenance_complete &&
      event.entry.capture_complete && event.returned.capture_complete, "connected natural frame not complete");
  Check(event.parent_scope.saved_mask02_admitted == true && !event.parent_scope.saved_c0_raw,
      "literal mask admission manufactured full saved C0");
  Check(event.entry_event.clock_identity == parent.scope.entry_event.clock_identity &&
      parent.scope.entry_event.sequence < event.entry_event.sequence && event.entry_event.sequence < event.returned_event.sequence,
      "shared real clock/TLS parent order lost");
  Check(event.entry.persistent_occurrences.size() == 4 && event.entry.army_refresh_occurrences.size() == 2 &&
      event.entry.persistent_occurrences[1].physical_token == fallback && event.entry.persistent_occurrences[2].physical_token == fallback &&
      event.entry.persistent_occurrences[1].used_fallback == true && event.entry.persistent_occurrences[2].raw_full_id == 0x2000001,
      "ALL original occurrence/fallback alias contract");
  Check(Physical(event.entry, persistent).prepared_fraction_raw == 10000 &&
      Physical(event.entry, persistent).chunks[0].current_soldiers == 80 &&
      Physical(event.returned, persistent).chunks[0].current_soldiers == 99, "entry and return physical frames mixed");
  Check(event.entry.army_objects.size() == 1 && event.entry.army_objects[0].arrg_occurrences.size() == 2 &&
      event.entry.army_objects[0].arrg_occurrences[0].records.size() == 2 &&
      event.entry.army_objects[0].arrg_occurrences[0].records[0].state_raw == 3 &&
      event.returned.army_objects[0].arrg_occurrences[0].records[0].state_raw == 4 &&
      event.returned.persistent_occurrences.size() == 1 && event.returned.army_refresh_occurrences.size() == 1,
      "owned DATA state/independent roster contract");
  const auto reads = complete.reads;
  auto journal = ReadArmyRegularCoreJournal12004();
  Check(complete.reads == reads && journal.events.size() == 1, "query performed a live read");
  journal.events[0].entry.persistent_occurrences.clear();
  Check(ReadArmyRegularCoreJournal12004().events[0].entry.persistent_occurrences.size() == 4, "journal owned-copy isolation");

  Memory partial; partial.Seed(); partial.block_entry_prepared = true; Connected(partial);
  Check(partial.original_calls == 1 && partial.observation.entry_provenance_complete &&
      !partial.observation.entry.capture_complete && partial.observation.returned.capture_complete &&
      !Physical(partial.observation.entry, persistent).prepared_fraction_raw &&
      Physical(partial.observation.returned, persistent).prepared_fraction_raw == 10000,
      "returned prepared148 filled an absent entry value");
  Memory date; date.Seed(); date.change_date = true; Connected(date);
  Check(date.observation.entry.capture_complete && !date.observation.return_provenance_complete &&
      !date.observation.returned.capture_complete && date.original_calls == 1, "date change accepted as same return frame");
  Memory wrong; wrong.Seed(); wrong.caller = kArmyRegularCoreCallerReturnRva12004 + 1; Connected(wrong);
  Check(wrong.original_calls == 1 && !wrong.observation.entry_provenance_complete && !wrong.observation.entry.capture_complete,
      "wrong literal caller acquired genuine frame");
  Memory absent; absent.Seed(); active = &absent;
  const auto outside = InvokeArmyRegularCorePassive12004(absent.bindings, &Original,
      reinterpret_cast<void *>(manager), kArmyRegularCoreCallerReturnRva12004);
  Check(absent.original_calls == 1 && !outside.entry_provenance_complete && outside.raw_return_bits == opaque_return,
      "absent parent suppressed original or supplied history");
  journal = ReadArmyRegularCoreJournal12004();
  Check(journal.events.size() == kArmyRegularCoreJournalCapacity12004 && journal.overwritten_events == 1,
      "bounded journal retention contract");
  const auto before_clear = NextArmyNaturalPhaseEvent12004(); ClearArmyRegularCoreJournal12004();
  const auto after_clear = NextArmyNaturalPhaseEvent12004();
  Check(before_clear.clock_identity == after_clear.clock_identity && before_clear.sequence < after_clear.sequence &&
      ReadArmyRegularCoreJournal12004().events.empty(), "journal clear reset real process clock");

  std::array<std::uint8_t, kArmyRegularCorePatchBytes12004> target{
    0x40,0x53,0x57,0x48,0x83,0xEC,0x48,0x48,0x8B,0x59,0x30,0x48,0x63,0x41,0x3C};
  const auto original_bytes = target;
  ArmyRegularCoreDetourState12004 detour;
  ArmyRegularCoreInstallEnvironment12004 environment;
  environment.bindings = complete.bindings; environment.target_override = reinterpret_cast<std::uintptr_t>(target.data());
  Check(!InstallArmyRegularCorePassive12004(detour, environment, kExecutableSha256) && target == original_bytes,
      "installer accepted missing quiescence");
  environment.primary_thread_suspended_proven = true;
  Check(!InstallArmyRegularCorePassive12004(detour, environment, "wrong-sha") && target == original_bytes,
      "installer accepted wrong build");
  target[0] = 0x90;
  Check(!InstallArmyRegularCorePassive12004(detour, environment, kExecutableSha256), "installer accepted wrong anchor");
  target = original_bytes;
  Check(InstallArmyRegularCorePassive12004(detour, environment, kExecutableSha256) && detour.installed.load() &&
      target[0] == 0xFF && target[1] == 0x25 && target[14] == 0x90 && detour.trampoline,
      "installer failed exact complete-instruction prefix");
  Check(std::memcmp(detour.trampoline, original_bytes.data(), original_bytes.size()) == 0,
      "trampoline did not retain original prefix");
  Check(!UninstallArmyRegularCorePassive12004(detour, false) && detour.installed.load(), "unproved uninstall accepted");
  Check(UninstallArmyRegularCorePassive12004(detour, true) && target == original_bytes && !detour.trampoline,
      "quiescent restoration failed");
  active = nullptr;
}
} // namespace xar::ck3_12004
