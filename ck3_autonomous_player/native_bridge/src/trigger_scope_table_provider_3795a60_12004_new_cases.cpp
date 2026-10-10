#include "xar_bridge/trigger_scope_table_provider_3795a60_12004.hpp"

#include <cstring>
#include <limits>
#include <map>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t image = 0x10000000, data = 0x21000000;
constexpr std::uintptr_t table = image + kTriggerScopeTableInlineRva3795A6012004;
constexpr std::uintptr_t fallback = image + kTriggerScopeFallbackRva3795A6012004;
constexpr std::uintptr_t guard = image + kTriggerScopeTableGuardRva3795A6012004;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  std::map<std::uintptr_t, std::string> bytes;
  std::map<std::uintptr_t, std::size_t> reads;
  bool change_count_on_bookend = false;
  template <typename T> void Put(std::uintptr_t address, T value) {
    bytes[address] = std::string(reinterpret_cast<const char *>(&value), sizeof(T));
  }
};
bool Read(void *opaque, const void *pointer, void *out, std::size_t bytes) noexcept {
  auto &memory = *static_cast<Memory *>(opaque);
  const auto address = reinterpret_cast<std::uintptr_t>(pointer);
  const auto nth = ++memory.reads[address];
  const auto found = memory.bytes.find(address);
  if (found == memory.bytes.end() || found->second.size() != bytes) return false;
  if (address == table + 0xC && nth == 2 && memory.change_count_on_bookend) {
    const std::int32_t changed = 9;
    std::memcpy(out, &changed, sizeof(changed));
    return true;
  }
  std::memcpy(out, found->second.data(), bytes);
  return true;
}
SourceReadFrame12004 Frame() {
  SourceReadFrame12004 frame{};
  frame.executable_sha256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
  frame.module_base = image;
  frame.frame_identity = 17;
  frame.native_revision = 29;
  frame.query_sequence = 31;
  frame.proof_epoch = 37;
  frame.date_raw = 41;
  frame.caller_domain = "lifestyle_current_query";
  frame.caller_snapshot_confirmed = true;
  return frame;
}
Memory Full() {
  Memory memory;
  memory.Put(guard, std::int32_t{-2147483600});
  memory.Put(table, data);
  memory.Put(table + 8, std::int32_t{12});
  memory.Put(table + 0xC, std::int32_t{8});
  memory.Put(data + 4 * 80 + 0x10, std::uintptr_t{0x30001000});
  memory.Put(fallback + 0x10, std::uintptr_t{0});
  return memory;
}
TriggerScopeTableProviderRaw3795A6012004 Observe(Memory &memory,
    std::optional<std::uint16_t> kind = std::uint16_t{4}) {
  return ReadTriggerScopeTableProvider3795A6012004({&memory, &Read}, Frame(), kind);
}
void NoTruth(const TriggerScopeTableProviderRaw3795A6012004 &out) {
  Require(!out.initializer_semantics_source_closed && !out.initialized_state &&
              !out.native_provider_return_observed && !out.native_callback_executed &&
              !out.descriptor_validator_returned_raw_u8 && !out.descriptor_validator_result_source_ready,
          "raw header/pointer facts qualified initializer, native RAX or validator truth");
}
} // namespace

void VerifyTriggerScopeTableProvider3795A60ConnectedCases12004() {
  // 1: Original generic frame and exact stride80 table selection.
  {
    auto memory = Full();
    auto frame = Frame();
    const auto out = ReadTriggerScopeTableProvider3795A6012004({&memory, &Read}, frame, std::uint16_t{4});
    frame.caller_domain = "changed_after_copy";
    Require(out.frame == Frame() && out.query_frame_ready &&
                out.source_return_table_identity == table && out.table_header_copy_complete &&
                out.selected_source_fallback == false && out.selected_descriptor_identity == data + 4 * 80 &&
                out.descriptor_validator_pointer10 == 0x30001000 && out.copied_fields_unchanged == true,
            "source frame or decimal80 descriptor selection was changed");
    NoTruth(out);
  }
  // 2: Equal count selects fallback even when data/capacity are unread.
  {
    auto memory = Full();
    memory.Put(table + 0xC, std::int32_t{4});
    memory.bytes.erase(table);
    memory.bytes.erase(table + 8);
    const auto out = Observe(memory);
    Require(out.selected_source_fallback == true && out.selected_descriptor_identity == fallback &&
                out.descriptor_validator_pointer_copied && !out.table_header_copy_complete,
            "fallback selection required unselected data/capacity or used count>=kind");
    NoTruth(out);
  }
  // 3: Signed negative count is preserved and selects literal fallback.
  {
    auto memory = Full();
    memory.Put(table + 0xC, std::int32_t{-1});
    const auto out = Observe(memory);
    Require(out.count_raw_i32 == -1 && out.selected_source_fallback == true &&
                out.descriptor_validator_pointer10 == 0,
            "signed raw negative count was clamped or treated as unsigned");
    NoTruth(out);
  }
  // 4: Kind0 bypass requires neither header nor callback reads.
  {
    Memory memory;
    const auto out = Observe(memory, std::uint16_t{0});
    Require(out.caller_root_zero_bypasses_descriptor == true && memory.reads.empty() &&
                !out.count_raw_i32 && !out.selected_descriptor_identity,
            "kind0 bypass created unused table dependencies or descriptor selection");
    NoTruth(out);
  }
  // 5: Unknown kind exposes independently copied header, never a selected row.
  {
    auto memory = Full();
    const auto out = Observe(memory, {});
    Require(out.table_header_copy_complete && !out.selected_source_fallback &&
                !out.selected_descriptor_identity && !out.caller_root_zero_bypasses_descriptor,
            "unknown kind was replaced with zero/default/table row");
    NoTruth(out);
  }
  // 6: Unknown count cannot act as count0/fallback.
  {
    auto memory = Full();
    memory.bytes.erase(table + 0xC);
    const auto out = Observe(memory);
    Require(!out.count_raw_i32 && !out.selected_source_fallback && !out.selected_descriptor_identity &&
                out.table_data_identity == data,
            "unread count became a fallback or hid independent data pointer");
    NoTruth(out);
  }
  // 7: Known null data and positive count cannot fabricate a table row.
  {
    auto memory = Full();
    memory.Put(table, std::uintptr_t{0});
    const auto out = Observe(memory);
    Require(out.table_data_identity == 0 && out.selected_source_fallback == false &&
                !out.selected_descriptor_identity && !out.descriptor_validator_pointer10,
            "null table data was replaced by guessed descriptor memory");
    NoTruth(out);
  }
  // 8: Unknown guard remains unknown although header/descriptor are copied.
  {
    auto memory = Full();
    memory.bytes.erase(guard);
    const auto out = Observe(memory);
    Require(!out.initialization_guard_raw_i32 && out.table_header_copy_complete &&
                out.descriptor_validator_pointer_copied && !out.all_attempted_native_reads_complete,
            "unknown guard erased independent copies or was synthesized");
    NoTruth(out);
  }
  // 9: Unknown capacity remains independent of exact caller count/data branch.
  {
    auto memory = Full();
    memory.bytes.erase(table + 8);
    const auto out = Observe(memory);
    Require(!out.capacity_raw_i32 && !out.table_header_copy_complete &&
                out.descriptor_selection_inputs_copied && out.descriptor_validator_pointer_copied,
            "capacity was filled or coupled to a branch which does not consume it");
    NoTruth(out);
  }
  // 10: Unknown validator pointer leaves independently complete header intact.
  {
    auto memory = Full();
    memory.bytes.erase(data + 4 * 80 + 0x10);
    const auto out = Observe(memory);
    Require(out.table_header_copy_complete && out.selected_descriptor_identity == data + 4 * 80 &&
                !out.descriptor_validator_pointer_copied && !out.descriptor_validator_pointer10,
            "unread validator pointer was fabricated or erased its selected descriptor");
    NoTruth(out);
  }
  // 11: WORD maximum uses its literal full kind and decimal80 stride.
  {
    auto memory = Full();
    memory.Put(table + 0xC, std::int32_t{65536});
    memory.Put(data + std::size_t{65535} * 80 + 0x10, std::uintptr_t{0x30002000});
    const auto out = Observe(memory, std::uint16_t{65535});
    Require(out.selected_descriptor_identity == data + std::size_t{65535} * 80 &&
                out.descriptor_validator_pointer10 == 0x30002000,
            "kind WORD was narrowed or its stride confused with0x80");
    NoTruth(out);
  }
  // 12: Changed source keeps first raw values but denies stable-copy fact.
  {
    auto memory = Full();
    memory.change_count_on_bookend = true;
    const auto out = Observe(memory);
    Require(out.count_raw_i32 == 8 && out.descriptor_validator_pointer10 == 0x30001000 &&
                out.copied_fields_unchanged == false &&
                out.unavailable_reason == "copied_source_fields_changed",
            "changed table header became an unchanged source copy");
    NoTruth(out);
  }
  // 13: Wrong exact pin rejects reads and all inferred static addresses.
  {
    auto memory = Full();
    auto frame = Frame();
    frame.executable_sha256 = "other_build";
    const auto out = ReadTriggerScopeTableProvider3795A6012004({&memory, &Read}, frame, std::uint16_t{4});
    Require(!out.query_frame_ready && memory.reads.empty() && !out.source_return_table_identity,
            "wrong build was admitted to image/table identities");
    NoTruth(out);
  }
  // 14: An unconfirmed copied source frame cannot become a new query identity.
  {
    auto memory = Full();
    auto frame = Frame();
    frame.caller_snapshot_confirmed = false;
    const auto out = ReadTriggerScopeTableProvider3795A6012004({&memory, &Read}, frame, std::uint16_t{4});
    Require(!out.query_frame_ready && memory.reads.empty() && out.frame == frame,
            "missing original snapshot confirmation was filled by the leaf");
    NoTruth(out);
  }
  // 15: Source address overflow stays unavailable without a memory read.
  {
    auto memory = Full();
    auto frame = Frame();
    frame.module_base = (std::numeric_limits<std::uintptr_t>::max)() - 2;
    const auto out = ReadTriggerScopeTableProvider3795A6012004({&memory, &Read}, frame, std::uint16_t{4});
    Require(!out.source_return_table_identity && memory.reads.empty(),
            "overflowed module address became a native table pointer");
    NoTruth(out);
  }
  // 16: Raw initializing guard/count0/nullcallback are copies, not completion.
  {
    auto memory = Full();
    memory.Put(guard, std::int32_t{-1});
    memory.Put(table + 0xC, std::int32_t{0});
    const auto out = Observe(memory);
    Require(out.initialization_guard_raw_i32 == -1 && out.count_raw_i32 == 0 &&
                out.selected_descriptor_identity == fallback && out.descriptor_validator_pointer10 == 0 &&
                out.descriptor_validator_pointer_copied && out.copied_fields_unchanged == true,
            "known initializing guard or copied null callback became unknown/default");
    NoTruth(out);
  }
}
} // namespace xar::ck3_12004
