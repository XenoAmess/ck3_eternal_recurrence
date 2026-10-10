#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"

namespace xar::ck3_12004 {
inline constexpr std::uint32_t kPrisonerAnswerInitialHelperRva12004 = 0x307B340;
inline constexpr std::uint32_t kPrisonerAnswerModeHelperRva12004 = 0x307BD70;

struct PrisonerAnswerQueryArguments12004 {
  std::optional<std::uint8_t> argument2_raw_u8, argument3_raw_u8;
  std::optional<std::uintptr_t> argument4_pointer, argument5_pointer;
};

struct PrisonerAnswerHelperRaw12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::optional<std::uintptr_t> context_definition;
  std::optional<std::uint32_t> context_2d8_raw_u32, context_2dc_raw_u32, context_2e8_raw_u32;
  std::optional<std::uint8_t> definition_2725_raw_u8, definition_2727_raw_u8, definition_2728_raw_u8;
  bool frame_ready = false;
};
PrisonerAnswerHelperRaw12004 ReadPrisonerAnswerHelperRaw12004(
    const PrisonerQuoteReadOnlyAccess12004 &, const PrisonerQuoteSourceFrame12004 &);

// These carry a separately reconstructed child result and its actual operands.
// A copied frame joins the same current query; it is not a native return capture.
struct PrisonerAnswerByteChild12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uint32_t actual_callee_rva = 0;
  std::uintptr_t receiver_identity = 0, second_argument_identity = 0;
  std::optional<std::uint32_t> full_id_argument;
  std::optional<std::uint8_t> raw_al;
  bool reached_effects_source_ready = false;
};
struct PrisonerAnswerDebugFlags12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uint32_t actual_callee_rva = 0;
  std::optional<std::uint8_t> byte0_raw_u8, byte1_raw_u8;
  bool reached_effects_source_ready = false;
};
struct PrisonerAnswerScopeChild12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uint32_t actual_callee_rva = 0;
  std::uintptr_t context_identity = 0;
  std::optional<std::uint64_t> returned_qword_bits;
  bool reached_effects_source_ready = false;
};
struct PrisonerAnswerReporterEffects12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uint32_t actual_callee_rva = 0;
  bool null_null_output_effects_source_ready = false;
};
struct PrisonerAnswerModeChildren12004 {
  std::optional<PrisonerAnswerByteChild12004> id_2baa6f0;
  std::optional<PrisonerAnswerDebugFlags12004> debug_a75d00;
  std::optional<PrisonerAnswerScopeChild12004> scope;
  std::optional<PrisonerAnswerReporterEffects12004> reporter_307b910, reporter_307baf0;
};

struct PrisonerAnswerHelperResult12004 {
  std::uint32_t actual_helper_rva = 0;
  std::optional<std::uint8_t> raw_al;
  bool numeric_source_ready = false, reached_effects_source_ready = false;
  std::string branch;
  std::vector<std::string> unavailable;
};
PrisonerAnswerHelperResult12004 ProjectPrisonerAnswerInitialGate12004(
    const PrisonerAnswerHelperRaw12004 &, const PrisonerAnswerQueryArguments12004 &,
    const std::optional<PrisonerAnswerByteChild12004> &predicate_3148bb0);
PrisonerAnswerHelperResult12004 ProjectPrisonerAnswerModeBranch12004(
    const PrisonerAnswerHelperRaw12004 &, const PrisonerAnswerQueryArguments12004 &,
    std::uint32_t mode, const PrisonerAnswerModeChildren12004 &);
} // namespace xar::ck3_12004
