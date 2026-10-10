#include "xar_bridge/prisoner_mode0_scalar_307c340_12004.hpp"

#include <map>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t context = 0x20000000;
constexpr std::uintptr_t definition = 0x30000000;
constexpr std::uintptr_t modifier_rows = 0x60000000;
constexpr std::uintptr_t modifier_receiver = 0x61000000;
constexpr std::uintptr_t modifier_vtable = 0x62000000;
constexpr std::uintptr_t modifier_target = 0x70000000;

struct Fixture {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  int failed_reads = 0;
  PrisonerQuoteSourceFrame12004 frame;
  PrisonerQuoteInternalAliases12004 aliases;

  template <typename T> void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(T); ++i) bytes[address + i] = source[i];
  }
  void Erase(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) bytes.erase(address + i);
  }
  static bool Read(void *opaque, const void *address, void *destination,
                   std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    auto *out = static_cast<std::uint8_t *>(destination);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = f.bytes.find(begin + i);
      if (found == f.bytes.end()) { ++f.failed_reads; return false; }
      out[i] = found->second;
    }
    return true;
  }
  Fixture() {
    frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
    frame.module_base = 0x10000000;
    frame.native_revision = 1; frame.query_sequence = 2; frame.proof_epoch = 3;
    frame.date_raw = 101; frame.jailer_full_id = 0x81000001u;
    frame.prisoner_full_id = 0x82000002u; frame.recipient_full_id = 0x83000003u;
    frame.definition_identity = definition;
    frame.interaction_context_identity = context;
    frame.original_scope_identity = context + 8;
    frame.roles_verified_in_owned_context = true; frame.same_frame_confirmed = true;
    // Source-defined copied shape: no fabricated physical clone/internal/support.
    aliases.secondary_scope = std::uintptr_t{0};
    aliases.evaluation_flag_raw_u8 = std::uint8_t{0}; aliases.primary_scope_root_word = std::uint16_t{4};
    Put(context, definition);
    Put(context + 0x2E8, std::uint32_t{0x80000002u});
    Put(context + 0x2D8, std::uint32_t{0x80000003u});
    Put(frame.module_base + 0x5D1DADC, std::uint8_t{0});
    Put(definition + 0x18C8 + 0x28, std::int64_t{-9});
    Put(definition + 0x18C8 + 0x30, std::uintptr_t{0});
    Put(definition + 0x18C8 + 0x3C, std::int32_t{0});
    Put(definition + 0x1918 + 0x28, std::int64_t{7654321});
  }
  PrisonerMode0ScalarInputs12004 Inputs() {
    return ReadPrisonerMode0ScalarInputs12004({this, Read, 4096}, frame, aliases);
  }
  PrisonerMode0ScalarPostWitness12004 Post(const PrisonerMode0ScalarInputs12004 &input,
                                          std::uint64_t bits) {
    PrisonerMode0ScalarPostWitness12004 w{};
    w.frame = frame; w.actual_helper_rva = kPrisonerMode0ScalarHelperRva12004;
    w.actual_parent_callsite_rva = kPrisonerMode0ScalarParentCallRva12004;
    w.context_identity = context; w.definition_identity = definition;
    w.score_block_identity = definition + 0x18C8;
    w.clone_source_identity = context + 8;
    w.cloned_scope_root_word = std::uint16_t{4}; w.cloned_scope_payload_u64 = input.cloned_scope_payload_u64;
    w.score_internal_aliases = aliases; w.final_qword_bits = bits;
    w.source_equivalent_clone_shape_ready = true;
    return w;
  }
  void OneModifier() {
    Put(definition + 0x18C8 + 0x30, modifier_rows);
    Put(definition + 0x18C8 + 0x3C, std::int32_t{1});
    Put(modifier_rows, modifier_receiver); Put(modifier_receiver, modifier_vtable);
    Put(modifier_vtable + 0x30, modifier_target);
  }
};
} // namespace

// Authored own-source cases only. Synthetic current frames and post witnesses
// validate binding/unknown behavior, never native scope or cleanup acceptance.
// Father35 includes this no-main function in the sole connected10 compound.
int RunPrisonerMode0Scalar307C34012004NewCases() {
  int failures = 0;
  const auto require = [&](bool value) { if (!value) ++failures; };
  {
    Fixture f;
    f.Put(context + 0x2E8, std::uint32_t{0xFFFFFFFFu});
    f.Erase(context + 0x2D8, sizeof(std::uint32_t)); f.Erase(context, sizeof(std::uintptr_t));
    const auto input = f.Inputs(); const auto out = ProjectPrisonerMode0Scalar12004(input);
    require(out.numeric_source_ready && out.reached_effects_source_ready &&
            out.returned_qword_bits == std::uint64_t{10000000} && f.failed_reads == 0 &&
            !input.context_2d8_raw_u32);
  }
  {
    Fixture f;
    f.Put(context + 0x2D8, std::uint32_t{0x80000002u});
    f.Erase(context, sizeof(std::uintptr_t));
    const auto out = ProjectPrisonerMode0Scalar12004(f.Inputs());
    require(out.numeric_source_ready && out.returned_qword_bits == std::uint64_t{10000000} &&
            f.failed_reads == 0);
  }
  {
    Fixture f;
    const auto input = f.Inputs(); const auto score = ProjectPrisonerMode0Score12004(input);
    const auto out = ProjectPrisonerMode0Scalar12004(input);
    require(input.score_block_identity == definition + 0x18C8 &&
            input.cloned_scope_payload_u64 == std::uint64_t{0x80000002u} &&
            score.returned_q64 == std::int64_t{-9} &&
            out.projected_score_q64 == std::int64_t{-9} && !out.returned_qword_bits &&
            !out.numeric_source_ready);
  }
  {
    Fixture f;
    const auto input = f.Inputs(); auto post = f.Post(input, ~std::uint64_t{8});
    post.complete_reached_post_effects_source_ready = true;
    const auto out = ProjectPrisonerMode0Scalar12004(input, {}, post);
    require(out.numeric_source_ready && out.reached_effects_source_ready &&
            out.returned_qword_bits == ~std::uint64_t{8} && !out.actual_native_output_observed);
  }
  {
    Fixture f;
    const auto input = f.Inputs(); auto post = f.Post(input, ~std::uint64_t{8});
    post.native_clone_observed = true;
    const auto out = ProjectPrisonerMode0Scalar12004(input, {}, post);
    require(out.projected_score_source_ready && !out.numeric_source_ready &&
            !out.returned_qword_bits && !out.actual_native_output_observed);
  }
  {
    Fixture f;
    const auto input = f.Inputs(); auto post = f.Post(input, ~std::uint64_t{8});
    post.complete_reached_post_effects_source_ready = true; ++post.frame.query_sequence;
    const auto out = ProjectPrisonerMode0Scalar12004(input, {}, post);
    require(!out.returned_qword_bits && !out.numeric_source_ready);
  }
  {
    Fixture f;
    const auto input = f.Inputs(); auto post = f.Post(input, ~std::uint64_t{8});
    post.complete_reached_post_effects_source_ready = true; post.cloned_scope_payload_u64 = 2;
    require(!ProjectPrisonerMode0Scalar12004(input, {}, post).returned_qword_bits);
  }
  {
    Fixture f;
    const auto input = f.Inputs(); auto post = f.Post(input, 7654321);
    post.complete_reached_post_effects_source_ready = true;
    require(!ProjectPrisonerMode0Scalar12004(input, {}, post).returned_qword_bits);
  }
  {
    Fixture f;
    f.OneModifier();
    const auto input = f.Inputs();
    require(input.raw_score.raw_inputs_complete &&
            !ProjectPrisonerMode0Score12004(input).returned_q64 &&
            !ProjectPrisonerMode0Scalar12004(input).returned_qword_bits);
  }
  {
    Fixture f;
    f.OneModifier(); const auto input = f.Inputs();
    PrisonerRecipientScoreModifierTransition12004 t{};
    t.frame = f.frame; t.internal_aliases = f.aliases;
    t.receiver_identity = modifier_receiver; t.vtable_identity = modifier_vtable;
    t.slot30_target_identity = modifier_target; t.actual_callsite_rva = kPrisonerRecipientScoreModifierCallRva12004;
    t.incoming_q64 = -9; t.returned_q64 = 0; t.source_result_ready = true;
    const auto score = ProjectPrisonerMode0Score12004(input, {t});
    require(score.numeric_source_ready && score.returned_q64 == std::int64_t{0} &&
            score.applied_transition_count == 1);
  }
  {
    Fixture f;
    auto input = f.Inputs(); input.score_block_identity = definition + 0x1918;
    require(!ProjectPrisonerMode0Score12004(input).returned_q64);
  }
  {
    Fixture f;
    auto input = f.Inputs(); input.branch = PrisonerMode0ScalarBranch12004::equal_ids_constant;
    require(!ProjectPrisonerMode0Scalar12004(input).returned_qword_bits);
  }
  return failures;
}
} // namespace xar::ck3_12004
