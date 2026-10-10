#include "xar_bridge/prisoner_cost_variant_3755500_readonly_12004.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar::ck3_12004;
struct Range { std::uintptr_t begin; std::size_t size; };
struct Memory {
  std::vector<Range> ranges;
  std::uintptr_t denied = 0, count_address = 0;
  bool change_count_on_second_read = false;
  int reads = 0, count_reads = 0;
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    ++memory.reads;
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    if (begin == memory.denied) return false;
    for (const auto &range : memory.ranges) {
      if (begin >= range.begin && begin - range.begin <= range.size &&
          size <= range.size - (begin - range.begin)) {
        if (begin == memory.count_address && size == sizeof(std::int32_t)) {
          ++memory.count_reads;
          if (memory.change_count_on_second_read && memory.count_reads == 2) {
            const std::int32_t changed = 1;
            std::memcpy(output, &changed, sizeof(changed));
            return true;
          }
        }
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
  template <typename T> void Allow(T &value) {
    ranges.push_back({reinterpret_cast<std::uintptr_t>(&value), sizeof(value)});
  }
};
template <typename T, std::size_t N>
void Put(std::array<std::uint8_t, N> &buffer, std::size_t offset, T value) {
  if (offset > N || sizeof(value) > N - offset) throw std::runtime_error("fixture buffer range");
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <typename T> std::uintptr_t Address(T &value) {
  return reinterpret_cast<std::uintptr_t>(&value);
}
struct Fixture {
  std::array<std::uint8_t, 0x90> list{};
  std::array<std::uint8_t, 16> root{}, row{};
  std::array<std::uint8_t, 8> receiver{};
  std::array<std::uint8_t, 0x38> vtable{};
  std::array<std::uint8_t, 32> descriptor{};
  Memory memory;
  PrisonerQuoteReadOnlyAccess12004 access{};
  PrisonerCostVariant3755500Arguments12004 arguments{};
  Fixture() {
    memory.Allow(list); memory.Allow(root); memory.Allow(row);
    memory.Allow(receiver); memory.Allow(vtable); memory.Allow(descriptor);
    memory.count_address = Address(list) + 0xC;
    access.context = &memory; access.read_memory = &Memory::Read;
    auto &frame = arguments.frame;
    frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
    frame.module_base = 0x100000; frame.native_revision = 2;
    frame.query_sequence = 3; frame.proof_epoch = 4; frame.date_raw = 5;
    frame.jailer_full_id = 0x81000001u; frame.prisoner_full_id = 0x82000002u;
    frame.recipient_full_id = 0x83000003u; frame.definition_identity = 0x101;
    frame.interaction_context_identity = 0x102; frame.original_scope_identity = Address(root);
    frame.roles_verified_in_owned_context = true; frame.same_frame_confirmed = true;
    arguments.receiver_identity = Address(list);
    arguments.descriptor_identity = Address(descriptor);
    auto &aliases = arguments.internal_aliases;
    aliases.primary_scope = Address(root); aliases.secondary_scope = 0;
    aliases.tertiary_scope = 0; aliases.support118_identity = 0;
    aliases.evaluation_flag_raw_u8 = std::uint8_t{0};
    // Source-defined copied internal shape: no invented physical stack address.
    aliases.physical_aliases_copied = false;
    Put(root, 0, std::uint16_t{1}); Put(root, 8, std::int64_t{-123456789});
    Put(list, 0, Address(row)); Put(row, 0, Address(receiver));
    Put(receiver, 0, Address(vtable));
    // These are unread executable witnesses. Calling either would be invalid.
    Put(vtable, 0x30, std::uintptr_t{0x700030});
    Put(vtable, 0x20, std::uintptr_t{0x700020});
  }
  void Count(std::int32_t count) { Put(list, 0xC, count); }
  auto Read() { return ReadPrisonerCostVariant3755500Readonly12004(access, arguments); }
};
}

// Linked into the one new parent quote compound. This file has no main and
// never runs any old Army journal, native method, Game, or prior fixture.
int RunPrisonerCostVariant3755500Readonly12004Cases() {
  int checks = 0;
  const auto check = [&](bool value, const char *message) {
    ++checks;
    if (!value) throw std::runtime_error(message);
  };
  {
    Fixture fixture; fixture.arguments.frame.same_frame_confirmed = false;
    const auto result = fixture.Read();
    check(!result.source_result_ready && !result.variant_tag_raw_u16, "frame mismatch remains unknown");
    check(fixture.memory.reads == 0, "invalid frame reads no native data");
  }
  {
    Fixture fixture; fixture.Count(0); fixture.arguments.internal_aliases = {};
    const auto result = fixture.Read();
    check(result.source_result_ready && result.variant_tag_raw_u16 == 0, "zero count is known tag0");
    check(result.variant_payload_raw_q64 == 0 && !result.numeric_raw_q64, "tag0 differs from numeric zero");
    check(!result.incoming_root_raw && fixture.memory.reads == 2, "zero count does not read scope");
  }
  {
    Fixture fixture; fixture.Count(-2); const auto result = fixture.Read();
    check(result.source_result_ready && result.variant_tag_raw_u16 == 1, "negative count preserves root tag");
    check(result.numeric_raw_q64 == -123456789, "negative signed Q64 retained");
    check(result.frame == fixture.arguments.frame && result.internal_aliases == fixture.arguments.internal_aliases,
          "full current frame and source aliases retained");
    check(!result.internal_aliases.internal_identity && !result.internal_aliases.physical_aliases_copied,
          "copied source shape has no invented physical alias");
  }
  {
    Fixture fixture; fixture.Count(-1); Put(fixture.root, 0, std::uint16_t{27});
    const auto result = fixture.Read();
    check(result.source_result_ready && result.variant_tag_raw_u16 == 27, "known nonnumeric raw tag retained");
    check(result.variant_payload_raw_q64 == -123456789 && !result.numeric_raw_q64,
          "nonnumeric tag never maps payload to cost");
  }
  {
    Fixture fixture; fixture.Count(1); const auto result = fixture.Read();
    check(!result.source_result_ready && !result.variant_tag_raw_u16 && !result.variant_payload_raw_q64,
          "dynamic virtual producer stays unknown");
    check(result.expression_type_mask_slot30 == 0x700030 && result.expression_value_slot20 == 0x700020,
          "actual slot identities copied without execution");
    check(result.selected_descriptor_identity == fixture.arguments.descriptor_identity && result.selected_descriptor_raw,
          "zero embedded descriptor selects actual R9 input");
    check(result.callback_identity == fixture.arguments.frame.module_base + 0x3755500 &&
          result.consumer_callsite_rva == 0x9D7252 && result.argument5_raw_u8 == 0 && result.argument6_raw_i32 == 0,
          "literal consumer ABI remains bound");
    check(result.conditional_value_only && !result.native_method_invoked, "no historical/native call credit");
  }
  {
    Fixture fixture; fixture.Count(1); Put(fixture.list, 0x70, std::uintptr_t{0xABC});
    const auto result = fixture.Read();
    check(result.selected_descriptor_identity == Address(fixture.list) + 0x70 && result.selected_descriptor_raw,
          "nonzero embedded first QWORD selects inline descriptor address");
  }
  {
    Fixture fixture; fixture.Count(-1); fixture.memory.denied = Address(fixture.root);
    const auto result = fixture.Read();
    check(!result.source_result_ready && !result.variant_tag_raw_u16, "root read failure remains unknown");
  }
  {
    Fixture fixture; fixture.Count(0); fixture.memory.denied = fixture.memory.count_address;
    const auto result = fixture.Read();
    check(!result.source_result_ready && !result.list_count_raw_i32, "count failure is not zero count");
  }
  {
    Fixture fixture; fixture.Count(0); fixture.memory.change_count_on_second_read = true;
    const auto result = fixture.Read();
    check(!result.source_result_ready && !result.variant_tag_raw_u16 && !result.variant_payload_raw_q64,
          "changing count invalidates conditional result");
    check(result.list_count_raw_i32 == 0 && result.list_count_after_raw_i32 == 1,
          "both mismatched raw counts retained");
  }
  {
    Fixture fixture; fixture.Count(1); fixture.arguments.internal_aliases.support118_identity.reset();
    const auto result = fixture.Read();
    check(!result.source_result_ready && result.unavailable_reason == "cost_variant_internal_alias_shape_unavailable",
          "incomplete internal shape cannot satisfy method input");
  }
  {
    Fixture fixture; fixture.Count(1); fixture.access.maximum_modifier_occurrences = 0;
    const auto result = fixture.Read();
    check(!result.source_result_ready && result.unavailable_reason == "cost_variant_occurrence_ceiling",
          "bounded conditional occurrence policy retained");
  }
  {
    Fixture fixture;
    fixture.arguments.frame.module_base = (std::numeric_limits<std::uintptr_t>::max)();
    const auto result = fixture.Read();
    check(!result.source_result_ready && result.callback_identity == 0 && fixture.memory.reads == 0,
          "callback address overflow rejected before reads");
  }
  return checks;
}
