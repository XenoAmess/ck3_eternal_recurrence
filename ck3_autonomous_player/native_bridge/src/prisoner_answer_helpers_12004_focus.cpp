#include "xar_bridge/prisoner_answer_helpers_12004.hpp"

#include <array>
#include <cstring>
#include <stdexcept>
#include <utility>

namespace {
using namespace xar::ck3_12004;
struct OwnedAnswerFixture {
  std::array<std::uint8_t, 0x300> context{};
  std::array<std::uint8_t, 0x2740> definition{};
};
bool ReadOwned(void *opaque, const void *address, void *out, std::size_t size) noexcept {
  const auto &f = *static_cast<OwnedAnswerFixture *>(opaque);
  const auto p = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &region : std::array<std::pair<const void *, std::size_t>, 2>{{
      {f.context.data(), f.context.size()}, {f.definition.data(), f.definition.size()}}}) {
    const auto begin = reinterpret_cast<std::uintptr_t>(region.first);
    if (p >= begin && p - begin <= region.second && size <= region.second - (p - begin)) {
      std::memcpy(out, address, size); return true;
    }
  }
  return false;
}
template <class T, std::size_t N> void Put(std::array<std::uint8_t, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
void Require(bool value, const char *why) {
  if (!value) throw std::runtime_error(why);
}
PrisonerAnswerByteChild12004 IdChild(const PrisonerAnswerHelperRaw12004 &raw, std::uint8_t al) {
  PrisonerAnswerByteChild12004 out{}; out.frame = raw.frame; out.actual_callee_rva = 0x2BAA6F0;
  out.full_id_argument = raw.context_2d8_raw_u32; out.raw_al = al; out.reached_effects_source_ready = true; return out;
}
PrisonerAnswerModeChildren12004 ScopeChildren(const PrisonerAnswerHelperRaw12004 &raw,
    std::uint32_t mode, std::uint64_t bits) {
  PrisonerAnswerModeChildren12004 out{}; out.id_2baa6f0 = IdChild(raw, 0);
  PrisonerAnswerScopeChild12004 scope{}; scope.frame = raw.frame;
  scope.actual_callee_rva = mode == 0 ? 0x307C340 : 0x307C440;
  scope.context_identity = raw.frame.interaction_context_identity;
  scope.returned_qword_bits = bits; scope.reached_effects_source_ready = true; out.scope = scope;
  PrisonerAnswerReporterEffects12004 reporter{}; reporter.frame = raw.frame;
  reporter.actual_callee_rva = 0x307BAF0; reporter.null_null_output_effects_source_ready = true;
  out.reporter_307baf0 = reporter; return out;
}
} // namespace

// Called only by father35's connected compound. Child values below are explicit
// conditional fixture inputs; they are not observed native callback returns.
void RunPrisonerAnswerHelpersSourceFocus12004() {
  OwnedAnswerFixture fixture{};
  const auto context = reinterpret_cast<std::uintptr_t>(fixture.context.data());
  const auto definition = reinterpret_cast<std::uintptr_t>(fixture.definition.data());
  Put(fixture.context, 0, definition);
  Put(fixture.context, 0x2D8, std::uint32_t{0xF1234567});
  Put(fixture.context, 0x2DC, std::uint32_t{0xE1234567});
  Put(fixture.context, 0x2E8, std::uint32_t{0xFFFFFFFF});
  PrisonerQuoteSourceFrame12004 frame{};
  frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.module_base = 0x100000; frame.native_revision = 101; frame.query_sequence = 102;
  frame.proof_epoch = 103; frame.date_raw = 0; frame.jailer_full_id = 0xF1234567;
  frame.prisoner_full_id = 0x81234567; frame.recipient_full_id = 0xE1234567;
  frame.definition_identity = definition; frame.interaction_context_identity = context;
  frame.original_scope_identity = context + 8; frame.roles_verified_in_owned_context = true;
  frame.same_frame_confirmed = true;
  PrisonerQuoteReadOnlyAccess12004 access{}; access.context = &fixture; access.read_memory = ReadOwned;
  auto raw = ReadPrisonerAnswerHelperRaw12004(access, frame);
  Require(raw.frame_ready && raw.context_2d8_raw_u32 == 0xF1234567u &&
      raw.context_2dc_raw_u32 == 0xE1234567u && raw.context_2e8_raw_u32 == 0xFFFFFFFFu,
      "readonly answer source must retain full DWORD identities and sentinel");
  const PrisonerAnswerQueryArguments12004 args{std::uint8_t{1}, std::uint8_t{1}, std::uintptr_t{0}, std::uintptr_t{0}};
  auto initial = ProjectPrisonerAnswerInitialGate12004(raw, args, {});
  Require(!initial.raw_al && !initial.numeric_source_ready, "different IDs cannot invent predicate");
  PrisonerAnswerByteChild12004 predicate{}; predicate.frame = frame; predicate.actual_callee_rva = 0x3148BB0;
  predicate.receiver_identity = definition; predicate.second_argument_identity = context + 8;
  predicate.raw_al = std::uint8_t{0}; predicate.reached_effects_source_ready = true;
  initial = ProjectPrisonerAnswerInitialGate12004(raw, args, predicate);
  Require(initial.raw_al == 3 && initial.reached_effects_source_ready, "zero predicate gives raw3");
  predicate.raw_al = std::uint8_t{0x80};
  Require(ProjectPrisonerAnswerInitialGate12004(raw, args, predicate).raw_al == 0,
      "all nonzero predicate bytes give raw0");
  predicate.frame.query_sequence++;
  Require(!ProjectPrisonerAnswerInitialGate12004(raw, args, predicate).raw_al, "different query cannot join child");
  auto equal = raw; equal.context_2dc_raw_u32 = equal.context_2d8_raw_u32;
  Require(ProjectPrisonerAnswerInitialGate12004(equal, args, {}).raw_al == 0,
      "equal full IDs bypass predicate");
  auto unknown_output = args; unknown_output.argument4_pointer.reset();
  Require(!ProjectPrisonerAnswerInitialGate12004(equal, unknown_output, {}).raw_al,
      "missing output pointer is not null");

  raw.definition_2727_raw_u8 = std::uint8_t{1};
  for (const auto &item : std::array<std::pair<std::uint64_t, std::uint8_t>, 7>{{
      {0, std::uint8_t{2}}, {1, std::uint8_t{1}}, {9999999, std::uint8_t{1}}, {10000000, std::uint8_t{0}}, {0xFFFFFFFFFFFFFFFFull, std::uint8_t{2}},
      {0x8000000000000000ull, std::uint8_t{2}}, {0x7FFFFFFFFFFFFFFFull, std::uint8_t{0}}}}) {
    const auto children = ScopeChildren(raw, 0, item.first);
    const auto result = ProjectPrisonerAnswerModeBranch12004(raw, args, 0, children);
    Require(result.raw_al == item.second && result.numeric_source_ready && result.reached_effects_source_ready,
        "mode0 must use unsigned decrement range and signed QWORD positivity");
  }
  raw.definition_2728_raw_u8 = std::uint8_t{0}; raw.definition_2725_raw_u8 = std::uint8_t{1};
  auto children = ScopeChildren(raw, 1, 0);
  Require(ProjectPrisonerAnswerModeBranch12004(raw, args, 1, children).raw_al == 1,
      "mode1 flag2725 overrides zero scope");
  raw.definition_2725_raw_u8 = std::uint8_t{0}; raw.definition_2728_raw_u8 = std::uint8_t{1};
  children = ScopeChildren(raw, 1, 9999999);
  Require(ProjectPrisonerAnswerModeBranch12004(raw, args, 1, children).raw_al == 1,
      "mode1 flag2728 uses finite inclusive range");
  children.scope->actual_callee_rva = 0x307C340;
  Require(!ProjectPrisonerAnswerModeBranch12004(raw, args, 1, children).raw_al,
      "actor and recipient scope callees cannot interchange");
  children = ScopeChildren(raw, 1, 1); children.scope->returned_qword_bits.reset();
  Require(!ProjectPrisonerAnswerModeBranch12004(raw, args, 1, children).raw_al,
      "known scope function address is not a returned QWORD");
  children = ScopeChildren(raw, 1, 1); children.reporter_307baf0.reset();
  const auto effects_missing = ProjectPrisonerAnswerModeBranch12004(raw, args, 1, children);
  Require(effects_missing.raw_al == 1 && !effects_missing.reached_effects_source_ready,
      "numeric branch cannot claim unresolved reporter effects");
  auto flag0 = args; flag0.argument3_raw_u8 = std::uint8_t{0};
  Require(!ProjectPrisonerAnswerModeBranch12004(raw, flag0, 1, children).raw_al,
      "generic zero argument3 branch stays unavailable");

  children = {}; children.id_2baa6f0 = IdChild(raw, 1);
  PrisonerAnswerDebugFlags12004 debug{}; debug.frame = frame; debug.actual_callee_rva = 0xA75D00;
  debug.byte0_raw_u8 = std::uint8_t{1}; debug.reached_effects_source_ready = true; children.debug_a75d00 = debug;
  PrisonerAnswerReporterEffects12004 reporter{}; reporter.frame = frame; reporter.actual_callee_rva = 0x307B910;
  reporter.null_null_output_effects_source_ready = true; children.reporter_307b910 = reporter;
  Require(ProjectPrisonerAnswerModeBranch12004(raw, args, 1, children).raw_al == 0,
      "byte0 override does not require unused byte1 or scope");
  children.debug_a75d00->byte0_raw_u8 = std::uint8_t{0}; children.debug_a75d00->byte1_raw_u8 = std::uint8_t{1};
  Require(ProjectPrisonerAnswerModeBranch12004(raw, args, 0, children).raw_al == 2,
      "byte1 plus incoming argument2 returns raw2 before scope");
  children.debug_a75d00->byte1_raw_u8.reset();
  Require(!ProjectPrisonerAnswerModeBranch12004(raw, args, 0, children).raw_al,
      "missing reached debug byte1 is not zero");
}
