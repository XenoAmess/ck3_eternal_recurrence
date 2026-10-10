#include "xar_bridge/entry_final_getter_capture_12004.hpp"
#include "xar_bridge/entry_final_writer_capture_12004.hpp"
#include "xar_bridge/ck3_12004_physical_entry_writeback.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"
#include "entry_final_side_fixture_12004.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <optional>

using namespace xar::ck3_12004;

namespace {
constexpr std::string_view kPin =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
enum class GetterCase {
  complete, one_field_unreadable, reader_absent, wrong_caller,
  wrong_province, clock_absent, foreign_begin_clock, foreign_thread,
  foreign_completed_clock, no_active_writer, returned_null
};
struct GetterFixture {
  GetterCase scenario = GetterCase::complete;
  std::array<std::uint8_t, 0x38> returned{}, output{};
  std::array<std::uint8_t, 0x18> regiment{}, other_province{};
  EntryFinalGetterCaptureBindings12004 bindings;
  void *expected_province = nullptr;
  std::uint32_t side_calls = 0, writer_calls = 0, getter_calls = 0;
  std::uint32_t event_calls = 0, returned_field_reads = 0;
  bool forwarded_arguments = true, original_result_preserved = true;
  bool writer_initialized = false;
};
GetterFixture g;
constexpr std::uint32_t kMaxBits = 0xF1234567;
constexpr std::array<std::uint64_t, 5> kRawBits{
    0x8000000000000011ULL, 0xFFFFFFFFFFFFFFE2ULL,
    0xA123456789ABCDE3ULL, 0xB23456789ABCDEF4ULL, 0xC3456789ABCDEF05ULL};

template <class T>
void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::uint8_t *>(object) + offset, &value, sizeof(value));
}
template <class T>
T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::uint8_t *>(object) + offset, sizeof(value));
  return value;
}
bool Reader(void *, std::uintptr_t address, void *output,
            std::size_t size) noexcept {
  const auto returned = reinterpret_cast<std::uintptr_t>(g.returned.data());
  if (address >= returned && address < returned + g.returned.size()) {
    ++g.returned_field_reads;
    if (g.scenario == GetterCase::one_field_unreadable &&
        address == returned + 0x18) return false;
  }
  return EntryFinalSideFixtureRead12004(nullptr, address, output, size);
}
bool WriterReader(void *context, const void *address, void *output,
                  std::size_t size) noexcept {
  return Reader(context, reinterpret_cast<std::uintptr_t>(address), output, size);
}
PersonInstalledTransferEvent12004 Event(void *) noexcept {
  auto event = NextPersonNaturalLineageEvent12004();
  ++g.event_calls;
  if (g.scenario == GetterCase::foreign_begin_clock ||
      (g.scenario == GetterCase::foreign_completed_clock && g.event_calls == 2))
    event.clock_identity ^= 0x100000000ULL;
  if (g.scenario == GetterCase::foreign_thread && event.thread_id)
    *event.thread_id ^= 1U;
  return event;
}
void *NaturalOriginal(void *regiment, void *output, void *province) {
  ++g.getter_calls;
  g.forwarded_arguments = g.forwarded_arguments &&
      regiment == g.regiment.data() && output == g.output.data() &&
      province == g.expected_province;
  return g.scenario == GetterCase::returned_null ? nullptr : g.returned.data();
}
void *Observe(void *province) {
  const auto caller = kEntryFinalSideFixtureImageBase12004 +
      kEntryFinalGetterWriterReturn12004 +
      (g.scenario == GetterCase::wrong_caller ? 1 : 0);
  auto *result = CaptureNaturalEntryFinalGetterReturn12004(g.bindings,
      NaturalOriginal, g.regiment.data(), g.output.data(), province, caller);
  auto *expected = g.scenario == GetterCase::returned_null ? nullptr : g.returned.data();
  g.original_result_preserved = g.original_result_preserved && result == expected;
  return result;
}
std::uint64_t __fastcall NaturalWriter(void *entry, void *) {
  ++g.writer_calls;
  if (g.scenario != GetterCase::no_active_writer) Observe(g.expected_province);
  // Synthetic original writes fixed raw fixture data through the exact source
  // offsets. It performs no mode0 getter computation or old arithmetic.
  Put(entry, 0x30, kMaxBits);
  for (std::size_t i = 0; i < kRawBits.size(); ++i)
    Put(entry, 0x38 + i * 8, kRawBits[i]);
  return kRawBits.back();
}
std::uintptr_t __fastcall NaturalSide(void *, void *province) {
  ++g.side_calls;
  const auto *scope = PeekActiveEntryFinalSideScope12004();
  if (!scope || scope->physical_slots.size() != 1) return 0;
  const auto &slot = scope->physical_slots.front();
  g.expected_province = g.scenario == GetterCase::wrong_province ?
      static_cast<void *>(g.other_province.data()) : province;
  const auto read = g.scenario == GetterCase::reader_absent ? nullptr : Reader;
  const auto event = g.scenario == GetterCase::clock_absent ? nullptr : Event;
  g.bindings = BindEntryFinalGetterCapture12004("1.20.0.4", kPin,
      kEntryFinalSideFixtureImageBase12004, read, nullptr, event, nullptr);
  const auto writer_bindings = BindEntryFinalWriterCapture12004(
      kEntryFinalSideFixtureImageBase12004, kPin, nullptr, WriterReader);
  g.writer_initialized = InitializePhysicalEntryWritebackFixture12004(
      NaturalWriter, writer_bindings);
  if (!g.writer_initialized) return 0;
  if (g.scenario == GetterCase::no_active_writer) Observe(province);
  const auto raw = InvokePhysicalEntryWriter12004(
      reinterpret_cast<void *>(slot.entry_identity), province,
      kEntryFinalSideFixtureImageBase12004 + slot.writer_return_rva);
  return static_cast<std::uintptr_t>(raw);
}
std::optional<EntryFinalWriterCaptureRecord12004> Run(GetterCase scenario) {
  g = {};
  g.scenario = scenario;
  g.output.fill(0x5A);
  Put(g.returned.data(), 0x08, kMaxBits);
  for (std::size_t i = 0; i < kRawBits.size(); ++i)
    Put(g.returned.data(), 0x10 + i * 8, kRawBits[i]);
  Put(g.regiment.data(), 0x10, std::uint32_t{0xA5000007});
  const auto side = RunEntryFinalSideFixtureForOriginal12004(NaturalSide, Reader);
  if (!side || !side->original_called || !side->original_returned ||
      side->writer_records.size() != 1 || g.side_calls != 1 ||
      g.writer_calls != 1 || g.getter_calls != 1 || !g.writer_initialized ||
      !g.forwarded_arguments || !g.original_result_preserved ||
      side->raw_return_bits != kRawBits.back())
    return std::nullopt;
  return side->writer_records.front();
}
bool Metadata(const EntryFinalGetterReturnedRecord12004 &child) {
  return child.original_called && child.original_returned &&
      child.actual_resolved_regiment_identity ==
          reinterpret_cast<std::uintptr_t>(g.regiment.data()) &&
      child.actual_output_identity == reinterpret_cast<std::uintptr_t>(g.output.data()) &&
      child.actual_province_identity == reinterpret_cast<std::uintptr_t>(g.expected_province) &&
      child.caller_return_rva == kEntryFinalGetterWriterReturn12004 &&
      child.begin_event.clock_identity != 0 &&
      child.begin_event.clock_identity == child.completed_event.clock_identity &&
      child.begin_event.sequence < child.completed_event.sequence &&
      child.begin_event.thread_id && child.completed_event.thread_id &&
      child.begin_event.thread_id == child.completed_event.thread_id;
}
bool NoFields(const EntryFinalSixCacheRaw12004 &f) {
  return !f.max_size_bits && !f.siege_bits && !f.damage_bits &&
      !f.toughness_bits && !f.pursuit_bits && !f.screen_bits;
}

bool InstalledHookNewCases() {
  g = {};
  g.expected_province = g.other_province.data();
  auto *target = static_cast<std::uint8_t *>(
      VirtualAlloc(nullptr, 64, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
  if (!target) return false;
  std::memcpy(target, kEntryFinalGetterPrologue12004.data(), 15);
  // Synthetic original restores exactly the actual four-instruction prologue
  // and tail-jumps to the fixture original with all three native args preserved.
  constexpr std::array<std::uint8_t, 15> epilogue{
      0x48,0x83,0xC4,0x60,0x5F,0x48,0x8B,0x74,0x24,0x10,
      0x48,0x8B,0x5C,0x24,0x08};
  std::memcpy(target + 15, epilogue.data(), epilogue.size());
  const std::array<std::uint8_t, 6> jump{0xFF,0x25,0,0,0,0};
  std::memcpy(target + 30, jump.data(), jump.size());
  const auto original = reinterpret_cast<std::uintptr_t>(&NaturalOriginal);
  std::memcpy(target + 36, &original, sizeof(original));
  DWORD old = 0;
  if (!VirtualProtect(target, 64, PAGE_EXECUTE_READ, &old) ||
      !FlushInstructionCache(GetCurrentProcess(), target, 64)) {
    VirtualFree(target, 0, MEM_RELEASE);
    return false;
  }
  EntryFinalGetterCaptureState12004 state;
  EntryFinalGetterCaptureInstall12004 install;
  install.offline_fixture = true;
  install.module_base = kEntryFinalSideFixtureImageBase12004;
  install.target_override = reinterpret_cast<std::uintptr_t>(target);
  install.bindings = BindEntryFinalGetterCapture12004("1.20.0.4", kPin,
      install.module_base, Reader, nullptr, Event, nullptr);
  bool good = !InstallEntryFinalGetterCapture12004(state, install, kPin) &&
      (state.failure_flags.load() & getter_capture_quiescence) != 0 &&
      state.trampoline == nullptr;
  install.primary_thread_suspended_proven = true;
  good = good && !InstallEntryFinalGetterCapture12004(state, install, "wrong") &&
      (state.failure_flags.load() & getter_capture_exact_build) != 0 &&
      state.trampoline == nullptr;
  DWORD ignored = 0;
  if (!VirtualProtect(target, 64, PAGE_EXECUTE_READWRITE, &ignored)) good = false;
  else {
    target[0] ^= 1;
    good = good && !InstallEntryFinalGetterCapture12004(state, install, kPin) &&
        (state.failure_flags.load() & getter_capture_anchor) != 0 &&
        state.trampoline == nullptr;
    target[0] ^= 1;
    if (!VirtualProtect(target, 64, PAGE_EXECUTE_READ, &ignored) ||
        !FlushInstructionCache(GetCurrentProcess(), target, 64)) good = false;
  }
  const bool installed = good &&
      InstallEntryFinalGetterCapture12004(state, install, kPin);
  if (installed) {
    const auto invoked = reinterpret_cast<EntryFinalGetterOriginal12004>(target);
    auto *result = invoked(g.regiment.data(), g.output.data(), g.expected_province);
    good = result == g.returned.data() && g.getter_calls == 1 &&
        g.forwarded_arguments && g.returned_field_reads == 0 &&
        g.event_calls == 0 && state.installed.load() == 1 &&
        !InstallEntryFinalGetterCapture12004(state, install, kPin) &&
        !UninstallEntryFinalGetterCapture12004(state, false);
  } else good = false;
  const bool removed = UninstallEntryFinalGetterCapture12004(state, true);
  good = good && removed && state.trampoline == nullptr &&
      state.installed.load() == 0 &&
      std::memcmp(target, kEntryFinalGetterPrologue12004.data(), 15) == 0;
  // A failed transaction retains backing until the owner can dispose it.
  if (removed) VirtualFree(target, 0, MEM_RELEASE);
  return good;
}

} // namespace

// Called exactly once by the single connected Entry main; no independent main,
// fabricated Peek/Notify implementation, private event clock or native query.
bool RunEntryFinalGetterCapture12004NewCases() {
  if (!InstalledHookNewCases()) return false;
  {
    const auto writer = Run(GetterCase::complete);
    if (!writer || !writer->returned_record ||
        writer->child_records_accepted != 1 || writer->child_records_rejected != 0 ||
        !writer->side_slot_six_cache_writeback_observed) return false;
    const auto child = *writer->returned_record;
    const auto &f = child.returned_fields;
    if (!Metadata(child) ||
        child.raw_return_bits != reinterpret_cast<std::uintptr_t>(g.returned.data()) ||
        child.raw_return_bits == child.actual_output_identity ||
        f.max_size_bits != kMaxBits || f.siege_bits != kRawBits[0] ||
        f.damage_bits != kRawBits[1] || f.toughness_bits != kRawBits[2] ||
        f.pursuit_bits != kRawBits[3] || f.screen_bits != kRawBits[4] ||
        g.returned_field_reads != 6 ||
        !writer->getter_completed_before_writer_return.value_or(false))
      return false;
    const auto owned_json = EntryFinalGetterReturnedRecordJson12004(child);
    g.returned.fill(0);
    if (EntryFinalGetterReturnedRecordJson12004(child) != owned_json ||
        owned_json.find(std::to_string(kRawBits[4])) == std::string::npos ||
        owned_json.find("\"source\":\"native_natural_entry_final_getter_return\"") ==
            std::string::npos) return false;
  }
  {
    const auto writer = Run(GetterCase::one_field_unreadable);
    if (!writer || !writer->returned_record || !Metadata(*writer->returned_record) ||
        writer->returned_fields_copy_complete || writer->six_cache_writeback_observed ||
        writer->returned_record->returned_fields.damage_bits ||
        writer->returned_record->returned_fields.max_size_bits != kMaxBits ||
        writer->returned_record->returned_fields.siege_bits != kRawBits[0] ||
        writer->returned_record->returned_fields.toughness_bits != kRawBits[2] ||
        writer->returned_record->returned_fields.pursuit_bits != kRawBits[3] ||
        writer->returned_record->returned_fields.screen_bits != kRawBits[4] ||
        writer->returned_fields_match_entry_after[2] ||
        !writer->returned_fields_match_entry_after[5].value_or(false) ||
        g.returned_field_reads != 6) return false;
  }
  {
    const auto writer = Run(GetterCase::reader_absent);
    if (!writer || !writer->returned_record || !Metadata(*writer->returned_record) ||
        !NoFields(writer->returned_record->returned_fields) ||
        writer->returned_record->raw_return_bits !=
            reinterpret_cast<std::uintptr_t>(g.returned.data()) ||
        writer->child_records_accepted != 1 || writer->six_cache_writeback_observed ||
        g.returned_field_reads != 0) return false;
    const auto json = EntryFinalGetterReturnedRecordJson12004(*writer->returned_record);
    if (json.find("\"screen_bits\":null") == std::string::npos) return false;
  }
  {
    const auto writer = Run(GetterCase::returned_null);
    if (!writer || !writer->returned_record || !Metadata(*writer->returned_record) ||
        writer->returned_record->raw_return_bits != 0 ||
        !NoFields(writer->returned_record->returned_fields) ||
        writer->six_cache_writeback_observed || g.returned_field_reads != 0)
      return false;
  }
  for (const auto scenario : {
           GetterCase::wrong_caller, GetterCase::wrong_province,
           GetterCase::clock_absent, GetterCase::foreign_begin_clock,
           GetterCase::foreign_thread, GetterCase::foreign_completed_clock,
           GetterCase::no_active_writer}) {
    const auto writer = Run(scenario);
    if (!writer || writer->returned_record || writer->child_records_accepted != 0 ||
        writer->six_cache_writeback_observed || g.returned_field_reads != 0)
      return false;
  }
  const auto wrong_pin = BindEntryFinalGetterCapture12004("1.20.0.4", "wrong",
      kEntryFinalSideFixtureImageBase12004, Reader, nullptr, Event, nullptr);
  const auto wrong_build = BindEntryFinalGetterCapture12004("1.20.0.3", kPin,
      kEntryFinalSideFixtureImageBase12004, Reader, nullptr, Event, nullptr);
  const auto invalid_base = BindEntryFinalGetterCapture12004("1.20.0.4", kPin,
      std::numeric_limits<std::uintptr_t>::max(), Reader, nullptr, Event, nullptr);
  return !wrong_pin.exact_build_admitted && !wrong_build.exact_build_admitted &&
      !invalid_base.exact_build_admitted;
}
