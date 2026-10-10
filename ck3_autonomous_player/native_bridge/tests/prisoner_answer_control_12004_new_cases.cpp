#include "xar_bridge/prisoner_answer_control_inputs_12004.hpp"

#include <initializer_list>
#include <map>
#include <stdexcept>

namespace xar::ck3_12004 {
namespace {
struct CopiedMemory {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::size_t reads = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(T); ++index)
      bytes[address + index] = data[index];
  }
  static bool Read(void *context, const void *address, void *out,
                   std::size_t count) noexcept {
    auto &memory = *static_cast<CopiedMemory *>(context);
    ++memory.reads;
    auto *target = static_cast<std::uint8_t *>(out);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (std::size_t index = 0; index < count; ++index) {
      const auto found = memory.bytes.find(begin + index);
      if (found == memory.bytes.end()) return false;
      target[index] = found->second;
    }
    return true;
  }
};
PrisonerQuoteSourceFrame12004 Frame() {
  PrisonerQuoteSourceFrame12004 frame;
  frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.module_base = 0x140000000ULL;
  frame.native_revision = 91;
  frame.query_sequence = 12;
  frame.proof_epoch = 900000;
  frame.date_raw = 53290008;
  frame.jailer_full_id = 0x81012345;
  frame.prisoner_full_id = 0x82012345;
  frame.recipient_full_id = 0x83012345;
  frame.definition_identity = 0x220000;
  frame.interaction_context_identity = 0x230000;
  frame.original_scope_identity = 0x240000;
  frame.roles_verified_in_owned_context = frame.same_frame_confirmed = true;
  return frame;
}
struct Fixture {
  CopiedMemory memory;
  PrisonerQuoteSourceFrame12004 frame = Frame();
  static constexpr std::uintptr_t instance = 0x300000, object = 0x400000,
      list = 0x500000;
  PrisonerQuoteReadOnlyAccess12004 Access(std::size_t cap = 4096) {
    return {&memory, &CopiedMemory::Read, cap};
  }
  void List(std::int32_t count, std::initializer_list<std::uint32_t> values) {
    memory.Put(frame.module_base + kPrisonerControlCollectionSlotRva12004, instance);
    memory.Put(instance + 0xA0, object);
    memory.Put(object + 0x22358, count == 0 ? std::uintptr_t{0} : list);
    memory.Put(object + 0x22364, count);
    std::size_t index = 0;
    for (const auto value : values) memory.Put(list + 4 * index++, value);
  }
  void Flags(std::int32_t guard, std::uint8_t first,
             std::optional<std::uint8_t> second = std::uint8_t{0}) {
    memory.Put(frame.module_base + kPrisonerControlDebugGuardRva12004, guard);
    memory.Put(frame.module_base + kPrisonerControlDebugObjectRva12004, first);
    if (second) memory.Put(frame.module_base + kPrisonerControlDebugObjectRva12004 + 1, *second);
  }
  PrisonerControlTlsEpoch12004 Epoch(std::int32_t value) {
    return {frame, value, true};
  }
};
void Require(bool okay, const char *case_name) {
  if (!okay) throw std::runtime_error(case_name);
}
PrisonerAnswerHelperResult12004 JoinMode(
    const PrisonerAnswerControlPackage12004 &packet, std::uint32_t key,
    std::uint8_t argument2 = 1) {
  PrisonerAnswerHelperRaw12004 raw;
  raw.frame = packet.membership_raw.frame;
  raw.frame_ready = PrisonerQuoteSourceFrameReady12004(raw.frame);
  raw.context_2d8_raw_u32 = key;
  raw.definition_2727_raw_u8 = std::uint8_t{0};
  PrisonerAnswerQueryArguments12004 arguments{argument2, std::uint8_t{1},
      std::uintptr_t{0}, std::uintptr_t{0}};
  PrisonerAnswerModeChildren12004 children;
  children.id_2baa6f0 = packet.id_2baa6f0;
  children.debug_a75d00 = packet.debug_a75d00;
  // This copied child fixture covers parent selection only. Missing reporter
  // evidence must remain separate from the numerical AL in the joined result.
  children.scope = PrisonerAnswerScopeChild12004{raw.frame, 0x307C340,
      raw.frame.interaction_context_identity, std::uint64_t{0}, true};
  return ProjectPrisonerAnswerModeBranch12004(raw, arguments, 0, children);
}
} // namespace

// No main and no native calls. 35 includes this once in its connected query
// source compound, and 10 performs the first compile/run.
int RunPrisonerAnswerControl12004NewCases() {
  int cases = 0;
  {
    Fixture f; f.List(1, {0x01012345});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 0x81012345);
    Require(p.id_2baa6f0.raw_al == std::uint8_t{0} &&
        p.id_2baa6f0.full_id_argument == std::uint32_t{0x81012345} &&
        !p.debug_a75d00.byte0_raw_u8, "generation_bits_are_complete_dword"); ++cases;
  }
  {
    Fixture f; f.List(3, {0xFFFFFFFF}); // Later list bytes deliberately absent.
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 0xFFFFFFFF);
    Require(p.id_2baa6f0.raw_al == std::uint8_t{1} &&
        p.membership_raw.copied_prefix.size() == 1, "first_full_match_needs_no_tail"); ++cases;
  }
  {
    Fixture f; f.List(3, {7, 7, 8});
    const auto raw = ReadPrisonerControlMembershipRaw12004(f.Access(), f.frame, 8);
    Require(raw.copied_prefix == std::vector<std::uint32_t>({7, 7, 8}) &&
        ProjectPrisonerControlMembership12004(raw).raw_al == std::uint8_t{1},
        "order_and_duplicates_are_preserved"); ++cases;
  }
  {
    Fixture f; f.List(0, {}); f.Flags(0, 1, std::uint8_t{1});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 0, f.Epoch(0));
    Require(p.id_2baa6f0.raw_al == std::uint8_t{0} && f.memory.reads == 4 &&
        !p.debug_raw.initialization_guard_i32, "known_empty_skips_unreached_debug"); ++cases;
  }
  {
    Fixture f; f.List(1, {0});
    const auto missing = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, std::nullopt);
    const auto zero = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, std::uint32_t{0});
    Require(!missing.id_2baa6f0.raw_al && zero.id_2baa6f0.raw_al == std::uint8_t{1},
        "missing_argument_is_distinct_from_present_zero"); ++cases;
  }
  {
    Fixture f; f.List(-1, {});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7);
    Require(!p.id_2baa6f0.raw_al && !p.membership_raw.unavailable_reason.empty(),
        "negative_signed_count_is_unavailable"); ++cases;
  }
  {
    Fixture f; f.List(2, {7, 8});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(1), f.frame, 7);
    Require(!p.id_2baa6f0.raw_al && p.membership_raw.copied_prefix.empty(),
        "bounded_read_cap_does_not_mean_no_match"); ++cases;
  }
  {
    Fixture f; f.List(2, {7});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 8);
    Require(!p.id_2baa6f0.raw_al && p.membership_raw.copied_prefix.size() == 1,
        "unread_required_element_is_not_false"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.frame.same_frame_confirmed = false;
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7);
    Require(!p.id_2baa6f0.raw_al && f.memory.reads == 0,
        "current_frame_proof_is_required_before_memory"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.Flags(1, 1, std::uint8_t{1});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7);
    Require(p.debug_raw.initialization_guard_i32 == std::int32_t{1} &&
        p.debug_raw.observed_byte0 == std::uint8_t{1} &&
        !p.debug_a75d00.byte0_raw_u8 && !JoinMode(p, 7).raw_al,
        "proof_epoch_does_not_supply_literal_tls_epoch"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.Flags(-2, 0, std::uint8_t{0});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7, f.Epoch(-1));
    Require(p.debug_a75d00.byte0_raw_u8 == std::uint8_t{0} &&
        p.debug_a75d00.byte1_raw_u8 == std::uint8_t{0} &&
        p.debug_a75d00.reached_effects_source_ready, "tls_guard_uses_signed_comparison"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.Flags(0, 1);
    auto epoch = f.Epoch(1); ++epoch.frame.interaction_context_identity;
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7, epoch);
    Require(!p.debug_a75d00.byte0_raw_u8,
        "same_revision_with_different_context_is_not_same_frame"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.Flags(2, 1, std::uint8_t{1});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7, f.Epoch(1));
    Require(!p.debug_a75d00.byte0_raw_u8 && !p.debug_a75d00.byte1_raw_u8,
        "initialization_route_is_not_reproduced_by_raw_static_bytes"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.Flags(0, 3, std::nullopt);
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7, f.Epoch(0));
    const auto joined = JoinMode(p, 7);
    Require(p.debug_a75d00.byte0_raw_u8 == std::uint8_t{3} &&
        !p.debug_a75d00.byte1_raw_u8 && joined.raw_al == std::uint8_t{0} &&
        joined.branch == "debug_byte0_nonzero" && !joined.reached_effects_source_ready,
        "joined_byte0_path_keeps_reporter_effects_separate"); ++cases;
  }
  {
    Fixture f; f.List(1, {7}); f.Flags(0, 0, std::uint8_t{5});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 7, f.Epoch(0));
    const auto joined = JoinMode(p, 7);
    Require(joined.raw_al == std::uint8_t{2} && joined.branch == "debug_byte1_nonzero" &&
        !joined.reached_effects_source_ready && !JoinMode(p, 8).raw_al,
        "joined_byte1_and_actual_full_id_operand_binding"); ++cases;
  }
  {
    Fixture f; f.List(1, {0x01012345});
    const auto p = ReadPrisonerAnswerControlPackage12004(f.Access(), f.frame, 0x81012345);
    const auto joined = JoinMode(p, 0x81012345);
    Require(joined.raw_al == std::uint8_t{2} && joined.branch == "signed_scope_nonpositive" &&
        !joined.reached_effects_source_ready && !p.debug_a75d00.byte0_raw_u8,
        "joined_nonmember_needs_no_debug_or_tls_input"); ++cases;
  }
  return cases;
}
} // namespace xar::ck3_12004
