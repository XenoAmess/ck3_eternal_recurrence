#include "entry_final_side_fixture_12004.hpp"
#include "xar_bridge/ck3_12004_physical_entry_writeback.hpp"
#include "xar_bridge/entry_final_getter_capture_12004.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace xar::ck3_12004;

bool RunEntryPrecedingCapture12004NewCases();
bool RunEntryFinalGetterCapture12004NewCases();

namespace {
constexpr std::uintptr_t kSideReturn = 0xFEDCBA9876543210;
EntryFinalSideCaptureOriginal12004 g_fixture_original = nullptr;
std::size_t g_side_original_calls = 0;
std::filesystem::path g_wire_output_directory;

template <class Callback> bool Guard(Callback callback) noexcept {
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <class T> void Put(void *base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::uint8_t *>(base) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::uint8_t *>(base) + offset, sizeof(value));
  return value;
}
PersonInstalledTransferEvent12004 SharedClock(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}
PersonInstalledTransferEvent12004 ForeignCompletionClock(void *context) noexcept {
  auto event = NextPersonNaturalLineageEvent12004();
  auto &calls = *static_cast<std::size_t *>(context);
  if (++calls == 2) event.clock_identity ^= 0x10;
  return event;
}
std::optional<EntryPrecedingRecord12004> NoFixturePreceding(
    std::uint32_t, std::uintptr_t, std::uintptr_t, std::uintptr_t,
    const PersonInstalledTransferEvent12004 &) noexcept { return std::nullopt; }

std::uintptr_t __fastcall FixtureBody(void *side, void *province) {
  ++g_side_original_calls;
  return g_fixture_original(side, province);
}

struct NativeTarget {
  void *allocation = nullptr;
  NativeTarget() {
    allocation = VirtualAlloc(nullptr, 64, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    Require(allocation != nullptr, "fixture target allocation");
    std::array<std::uint8_t, 64> code{};
    std::memcpy(code.data(), kEntryFinalSidePrologue12004.data(), 20);
    // Exact source prologue, then an ABI-preserving synthetic original body.
    // RSP has the original 32-byte shadow area and native call alignment.
    code[20] = 0x48; code[21] = 0xB8;
    const auto body = reinterpret_cast<std::uintptr_t>(&FixtureBody);
    std::memcpy(code.data() + 22, &body, sizeof(body));
    code[30] = 0xFF; code[31] = 0xD0;
    const std::array<std::uint8_t, 6> epilogue{0x48,0x83,0xC4,0x20,0x5F,0xC3};
    std::memcpy(code.data() + 32, epilogue.data(), epilogue.size());
    std::memcpy(allocation, code.data(), code.size());
    DWORD old = 0;
    Require(VirtualProtect(allocation, code.size(), PAGE_EXECUTE_READ, &old) != FALSE,
            "fixture target executable");
    Require(FlushInstructionCache(GetCurrentProcess(), allocation, code.size()) != FALSE,
            "fixture target flush");
  }
  ~NativeTarget() { if (allocation) (void)VirtualFree(allocation, 0, MEM_RELEASE); }
  NativeTarget(const NativeTarget &) = delete;
  NativeTarget &operator=(const NativeTarget &) = delete;
};

std::optional<EntryFinalSideCaptureRecord12004> RunFixture(
    EntryFinalSideCaptureOriginal12004 original,
    std::span<EntryFinalCacheImage12004> levy,
    std::span<EntryFinalCacheImage12004> maa, void *province,
    PersonInstalledTransferRead12004 reader, void *context,
    std::size_t bucket_budget = 1024 * 1024,
    EntryFinalSideCaptureClock12004 fixture_clock = SharedClock,
    void *event_context = nullptr) {
  if (!original || !province || g_fixture_original) return std::nullopt;
  NativeTarget target;
  std::array<std::uint8_t, 0x60> side{};
  Put(side.data(), 0x28, reinterpret_cast<std::uintptr_t>(levy.data()));
  Put(side.data(), 0x34, static_cast<std::int32_t>(levy.size()));
  Put(side.data(), 0x40, reinterpret_cast<std::uintptr_t>(maa.data()));
  Put(side.data(), 0x4C, static_cast<std::int32_t>(maa.size()));
  EntryFinalSideCaptureInstall12004 environment;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = kEntryFinalSideFixtureImageBase12004;
  environment.target_override = reinterpret_cast<std::uintptr_t>(target.allocation);
  environment.bindings.read = reader ? reader : EntryFinalSideFixtureRead12004;
  environment.bindings.read_context = context;
  environment.bindings.next_event = fixture_clock;
  environment.bindings.event_context = event_context;
  environment.bindings.claim_preceding = NoFixturePreceding;
  environment.bindings.maximum_bucket_payload_bytes = bucket_budget;
  EntryFinalSideCaptureState12004 state;
  const auto previous = ReadEntryFinalSideCapture12004().latest_record_sequence;
  Require(InstallEntryFinalSideCapture12004(state, environment,
      kEntryFinalSideCaptureExeSha12004), "fixture Side installation");
  g_fixture_original = original;
  g_side_original_calls = 0;
  try {
    const auto installed = reinterpret_cast<EntryFinalSideCaptureOriginal12004>(target.allocation);
    const auto result = installed(side.data(), province);
    Require(g_side_original_calls == 1, "Side original exactly once");
    const auto query = ReadEntryFinalSideCapture12004();
    Require(query.latest_record_sequence == previous + 1 && !query.records.empty(),
            "one retained Side occurrence");
    auto record = query.records.back();
    Require(record.raw_return_bits == result, "opaque Side RAX preserved");
    Require(UninstallEntryFinalSideCapture12004(state, true), "fixture Side uninstall");
    g_fixture_original = nullptr;
    Require(PeekActiveEntryFinalSideScope12004() == nullptr &&
            PeekActiveEntryFinalSideWriterScope12004() == nullptr &&
            PeekActiveEntryFinalWriterScope12004() == nullptr, "lexical scopes restored");
    return record;
  } catch (...) {
    g_fixture_original = nullptr;
    (void)UninstallEntryFinalSideCapture12004(state, true);
    throw;
  }
}

struct Connected {
  std::array<std::uint8_t, 0x40> regiment{};
  std::array<std::uint8_t, 0x40> returned{};
  std::array<std::uint8_t, 0x40> output{};
  EntryFinalGetterCaptureBindings12004 getter;
  std::size_t writer_calls = 0, getter_calls = 0;
  bool deny_damage = false, deny_entry_image = false, wrong_writer_return = false;
  bool duplicate_getter = false;
  std::uintptr_t deny_entry = 0;
};
Connected *g_connected = nullptr;
bool ConnectedRead(void *opaque, std::uintptr_t address, void *out,
                   std::size_t bytes) noexcept {
  auto &c = *static_cast<Connected *>(opaque);
  if (address == kEntryFinalSideFixtureImageBase12004 + kEntryFinalFallbackSlotRva12004 &&
      bytes == sizeof(std::uintptr_t)) {
    const auto pointer = reinterpret_cast<std::uintptr_t>(c.regiment.data());
    std::memcpy(out, &pointer, sizeof(pointer));
    return true;
  }
  if (c.deny_damage && address == reinterpret_cast<std::uintptr_t>(c.returned.data()) + 0x18)
    return false;
  if (c.deny_entry_image && bytes == 0x60 && address == c.deny_entry) return false;
  return EntryFinalSideFixtureRead12004(nullptr, address, out, bytes);
}
bool ConnectedConstRead(void *opaque, const void *address, void *out,
                        std::size_t bytes) noexcept {
  return ConnectedRead(opaque, reinterpret_cast<std::uintptr_t>(address), out, bytes);
}
void *ConnectedGetter(void *regiment, void *output, void *province) {
  auto &c = *g_connected;
  ++c.getter_calls;
  Require(regiment == c.regiment.data() && output == c.output.data() && province != nullptr,
          "actual getter ABI arguments");
  return c.returned.data(); // Deliberately distinct from actual output argument.
}
std::uint64_t __fastcall ConnectedWriter(void *entry, void *province) {
  auto &c = *g_connected;
  ++c.writer_calls;
  auto *returned = CaptureNaturalEntryFinalGetterReturn12004(c.getter, ConnectedGetter,
      c.regiment.data(), c.output.data(), province,
      kEntryFinalSideFixtureImageBase12004 + kEntryFinalGetterWriterReturn12004);
  if (c.duplicate_getter)
    (void)CaptureNaturalEntryFinalGetterReturn12004(c.getter, ConnectedGetter,
        c.regiment.data(), c.output.data(), province,
        kEntryFinalSideFixtureImageBase12004 + kEntryFinalGetterWriterReturn12004);
  // Test original writes six literal raw fields; it performs no stat arithmetic.
  Put(entry, 0x30, Get<std::uint32_t>(returned, 0x08));
  for (std::size_t i = 0; i != 5; ++i)
    Put(entry, 0x38 + i * 8, Get<std::uint64_t>(returned, 0x10 + i * 8));
  return Get<std::uint64_t>(returned, 0x30);
}
std::uintptr_t __fastcall ConnectedSide(void *side, void *province) {
  auto &c = *g_connected;
  Require(PeekActiveEntryFinalSideScope12004() != nullptr, "actual Side scope published");
  Require(InitializePhysicalEntryWritebackFixture12004(ConnectedWriter,
      BindEntryFinalWriterCapture12004(kEntryFinalSideFixtureImageBase12004,
          kEntryFinalSideCaptureExeSha12004, &c, ConnectedConstRead)), "single writer fixture original");
  for (const auto offset : {0x28U, 0x40U}) {
    const auto pointer = Get<std::uintptr_t>(side, offset);
    const auto count = Get<std::int32_t>(side, offset + 0xC);
    for (std::int32_t i = 0; i < count; ++i) {
      const auto rva = c.wrong_writer_return ? 0x265108EU :
          (offset == 0x28 ? 0x265108DU : 0x26510BBU);
      (void)InvokePhysicalEntryWriter12004(reinterpret_cast<void *>(pointer +
          static_cast<std::size_t>(i) * 0x60), province,
          kEntryFinalSideFixtureImageBase12004 + rva);
    }
  }
  return kSideReturn;
}
std::uintptr_t __fastcall EmptySide(void *, void *) { return kSideReturn; }

void Prepare(Connected &c) {
  Put(c.regiment.data(), 0x10, std::uint32_t{0xAB000123});
  Put(c.returned.data(), 0x08, std::uint32_t{0xFFFFFFFF});
  const std::array<std::uint64_t, 5> bits{
      0x8000000000000000ULL,0xFFFFFFFFFFFFFFFFULL,0,0x0123456789ABCDEFULL,
      0xFEDCBA9876543210ULL};
  for (std::size_t i = 0; i != bits.size(); ++i) Put(c.returned.data(), 0x10 + i * 8, bits[i]);
  c.getter = BindEntryFinalGetterCapture12004("1.20.0.4", kEntryFinalSideCaptureExeSha12004,
      kEntryFinalSideFixtureImageBase12004, ConnectedRead, &c, SharedClock, nullptr);
}
EntryFinalSideCaptureQuery12004 SingleQuery(const EntryFinalSideCaptureRecord12004 &record) {
  EntryFinalSideCaptureQuery12004 query;
  query.latest_record_sequence = record.record_sequence;
  query.records.push_back(record);
  return query;
}

void NewConnectedCases() {
  std::array<std::uint8_t, 0x40> province{};
  Put(province.data(), 0x10, std::int32_t{-1234});
  std::array<EntryFinalCacheImage12004, 2> levy{};
  std::array<EntryFinalCacheImage12004, 1> maa{};
  Put(levy[0].data(), 0x08, std::uint32_t{0xCD000123});
  Put(levy[1].data(), 0x08, std::uint32_t{0xEE000123});
  Put(maa[0].data(), 0x08, std::uint32_t{0xDD000123});
  // Zero and negative opaque row patterns remain members without admission.
  Put(levy[0].data(), 0x10, std::int32_t{0});
  Put(levy[1].data(), 0x10, std::int32_t{-1});
  Connected c; Prepare(c); g_connected = &c;
  auto record = RunFixture(ConnectedSide, levy, maa, province.data(), ConnectedRead, &c);
  Require(record && record->offline_fixture && record->original_called && record->original_returned,
          "real installed Side fixture captured");
  Require(c.writer_calls == 3 && c.getter_calls == 3, "full physical native occurrence count");
  Require(record->scope.copy_complete && record->scope.physical_slots.size() == 3 &&
          record->writer_records.size() == 3 && record->writer_occurrences_cover_copied_slots == true,
          "full levy then MAA physical order");
  Require(record->scope.physical_slots[0].bucket == EntryFinalSideBucket12004::levy &&
          record->scope.physical_slots[1].bucket_index == 1 &&
          record->scope.physical_slots[2].bucket == EntryFinalSideBucket12004::men_at_arms &&
          record->scope.physical_slots[2].traversal_ordinal == 2,
          "bucket identity and order retained");
  for (const auto &writer : record->writer_records) {
    Require(writer.side_slot_six_cache_writeback_observed && writer.returned_record &&
            writer.child_records_accepted == 1 && writer.original_called && writer.original_returned,
            "actual child six-cache postimage");
    Require(writer.original_return_bits == kSideReturn &&
            writer.original_return_matches_returned_screen == true,
            "writer original screen RAX bits preserved through both observers");
    Require(writer.actual_resolved_regiment_full_id == 0xAB000123 &&
            writer.resolved_full_id_matches_requested == false &&
            writer.resolved_identity_matches_copied_fallback == true,
            "full generation and copied fallback independent");
    Require(writer.returned_record->actual_output_identity != writer.returned_record->raw_return_bits &&
            writer.entry_cache_after.siege_bits == 0x8000000000000000ULL &&
            writer.entry_cache_after.damage_bits == 0xFFFFFFFFFFFFFFFFULL,
            "returned RAX and high raw bits retained");
  }
  Require(!record->preceding && !record->outer_invocation, "no inferred outer invocation");
  const auto frozen_wire = SerializeEntryFinalSideCapture12004(SingleQuery(*record));
  if (!g_wire_output_directory.empty()) {
    std::ofstream wire(g_wire_output_directory / "entry-side-connected-full.json", std::ios::binary);
    wire << frozen_wire << '\n';
    Require(static_cast<bool>(wire), "connected owned wire artifact");
  }
  levy[0].fill(0x11); maa[0].fill(0x22); c.returned.fill(0x33);
  Require(SerializeEntryFinalSideCapture12004(SingleQuery(*record)) == frozen_wire,
          "immutable retained wire after live mutation");
  std::cout << "PASS side_connected_full_order_raw_bits_generation_immutable\n";

  std::array<EntryFinalCacheImage12004, 1> one{};
  Put(one[0].data(), 8, std::uint32_t{0xCD000123});
  Prepare(c); c.deny_damage = true;
  record = RunFixture(ConnectedSide, one, {}, province.data(), ConnectedRead, &c);
  Require(record && record->writer_records.size() == 1, "partial child retained");
  const auto &partial = record->writer_records[0];
  Require(partial.returned_record && !partial.returned_fields_match_entry_after[2] &&
          partial.returned_fields_match_entry_after[0] == true &&
          partial.returned_fields_match_entry_after[1] == true &&
          partial.returned_fields_match_entry_after[3] == true &&
          partial.returned_fields_match_entry_after[4] == true &&
          partial.returned_fields_match_entry_after[5] == true &&
          !partial.all_returned_fields_match_entry_after && !partial.six_cache_writeback_observed,
          "one unread field preserves five independent comparisons");
  std::cout << "PASS side_connected_independent_partial_returned_field\n";

  c.deny_damage = false; c.deny_entry_image = true;
  c.deny_entry = reinterpret_cast<std::uintptr_t>(one[0].data());
  record = RunFixture(ConnectedSide, one, {}, province.data(), ConnectedRead, &c);
  Require(record && !record->scope.copy_complete && !record->writer_occurrences_cover_copied_slots &&
          record->writer_records.size() == 1 &&
          !record->writer_records[0].entry_images_copy_complete &&
          record->writer_records[0].six_cache_writeback_observed,
          "bulk copy unknown with independent six cache copies");
  std::cout << "PASS side_connected_bulk_image_partial_independent_cache\n";

  c.deny_entry_image = false; c.wrong_writer_return = true;
  record = RunFixture(ConnectedSide, one, {}, province.data(), ConnectedRead, &c);
  Require(record && record->writer_records.size() == 1 &&
          !record->writer_records[0].side_slot_associated &&
          record->writer_records[0].six_cache_writeback_observed &&
          !record->writer_records[0].side_slot_six_cache_writeback_observed &&
          record->writer_occurrences_cover_copied_slots == false,
          "wrong source slot retains unqualified actual writer");
  std::cout << "PASS side_connected_wrong_writer_boundary\n";

  c.wrong_writer_return = false; c.duplicate_getter = true;
  record = RunFixture(ConnectedSide, one, {}, province.data(), ConnectedRead, &c);
  Require(record && record->writer_records[0].child_records_accepted == 1 &&
          record->writer_records[0].child_records_rejected == 1,
          "first getter child retained and duplicate rejected");
  std::cout << "PASS side_connected_duplicate_child\n";

  c.duplicate_getter = false;
  record = RunFixture(ConnectedSide, one, {}, province.data(), ConnectedRead, &c, 0);
  Require(record && record->scope.levy_header.count_i32 == 1 &&
          record->scope.physical_slots.empty() && !record->scope.copy_complete &&
          record->writer_records.size() == 1 && !record->writer_records[0].side_slot_associated,
          "observer budget preserves native count and natural original");
  std::cout << "PASS side_connected_budget_no_native_quantity_limit\n";

  record = RunFixture(EmptySide, {}, {}, province.data(), EntryFinalSideFixtureRead12004, nullptr);
  Require(record && record->scope.copy_complete && record->scope.physical_slots.empty() &&
          record->writer_occurrences_cover_copied_slots == true,
          "empty physical traversal complete");
  std::cout << "PASS side_connected_empty_physical_buckets\n";
  std::size_t events = 0;
  record = RunFixture(EmptySide, {}, {}, province.data(), EntryFinalSideFixtureRead12004,
      nullptr, 1024 * 1024, ForeignCompletionClock, &events);
  Require(record && events == 2 && record->scope.copy_complete &&
          record->writer_occurrences_cover_copied_slots == false,
          "empty traversal cannot bypass completed clock boundary");
  std::cout << "PASS side_connected_foreign_completion_clock\n";
  g_connected = nullptr;
}

void NewInstallGuardCases() {
  NativeTarget target;
  EntryFinalSideCaptureInstall12004 environment;
  environment.offline_fixture = true;
  environment.module_base = kEntryFinalSideFixtureImageBase12004;
  environment.target_override = reinterpret_cast<std::uintptr_t>(target.allocation);
  environment.bindings.read = EntryFinalSideFixtureRead12004;
  EntryFinalSideCaptureState12004 state;
  Require(!InstallEntryFinalSideCapture12004(state, environment, "wrong pin") &&
          state.failure_flags == side_capture_exact_build, "exact build guard");
  Require(!InstallEntryFinalSideCapture12004(state, environment, kEntryFinalSideCaptureExeSha12004) &&
          state.failure_flags == side_capture_quiescence, "suspended proof guard");
  environment.primary_thread_suspended_proven = true;
  auto *bytes = static_cast<std::uint8_t *>(target.allocation);
  DWORD old = 0;
  Require(VirtualProtect(bytes, 64, PAGE_EXECUTE_READWRITE, &old) != FALSE, "fixture anchor writable");
  bytes[0] ^= 1;
  Require(!InstallEntryFinalSideCapture12004(state, environment, kEntryFinalSideCaptureExeSha12004) &&
          state.failure_flags == side_capture_anchor && state.trampoline == nullptr,
          "exact complete prologue guard");
  std::cout << "PASS side_install_exact_pin_quiescence_prologue_guards\n";
}
} // namespace

bool EntryFinalSideFixtureRead12004(void *, std::uintptr_t address, void *out,
                                  std::size_t bytes) noexcept {
  if (!address || !out || address > std::numeric_limits<std::uintptr_t>::max() - bytes)
    return false;
  return Guard([&]() noexcept {
    std::memcpy(out, reinterpret_cast<const void *>(address), bytes);
    return true;
  });
}

std::optional<EntryFinalSideCaptureRecord12004>
RunEntryFinalSideFixtureForOriginal12004(EntryFinalSideCaptureOriginal12004 original,
    PersonInstalledTransferRead12004 read, void *read_context) {
  std::array<EntryFinalCacheImage12004, 1> levy{};
  std::array<std::uint8_t, 0x40> province{};
  Put(levy[0].data(), 8, std::uint32_t{0xCD000123});
  Put(province.data(), 0x10, std::int32_t{-1234});
  return RunFixture(original, levy, {}, province.data(), read, read_context);
}

int main(int argc, char **argv) {
  try {
    Require(argc == 1 || argc == 2, "optional sole argument is new wire output directory");
    if (argc == 2) {
      g_wire_output_directory = argv[1];
      std::filesystem::create_directories(g_wire_output_directory);
    }
    NewInstallGuardCases();
    NewConnectedCases();
    Require(RunEntryPrecedingCapture12004NewCases(), "new preceding exported cases");
    Require(RunEntryFinalGetterCapture12004NewCases(), "new getter exported cases");
    std::cout << "PASS entry_connected_new_compound\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
