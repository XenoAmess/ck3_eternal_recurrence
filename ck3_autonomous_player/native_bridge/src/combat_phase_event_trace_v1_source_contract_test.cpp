#include "xar_bridge/combat_phase_event_trace_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace {

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(stream),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

template <std::size_t N>
bool ContainsAll(std::string_view haystack,
                 const std::array<std::string_view, N> &needles) {
  for (const auto needle : needles) {
    if (!Contains(haystack, needle)) {
      return false;
    }
  }
  return true;
}

std::int32_t SignedLow32(std::int64_t value) {
  const auto low = static_cast<std::uint32_t>(value);
  if (low <=
      static_cast<std::uint32_t>(std::numeric_limits<std::int32_t>::max())) {
    return static_cast<std::int32_t>(low);
  }
  return static_cast<std::int32_t>(static_cast<std::int64_t>(low) -
                                   0x1'0000'0000LL);
}

std::int32_t QuantizeRandomListWeight(std::int64_t raw) {
  auto quotient = raw / 100'000;
  const auto remainder = raw - quotient * 100'000;
  if (raw > 0 && remainder != 0) {
    ++quotient;
  }
  return SignedLow32(quotient);
}

std::vector<std::int32_t>
TailSwapFilter(std::vector<std::int32_t> candidates,
               const std::vector<std::int32_t> &shared_reject,
               const std::vector<std::int32_t> &source_reject,
               std::vector<std::string> &evaluation_log) {
  std::size_t index = 0;
  while (index < candidates.size()) {
    const auto candidate = candidates[index];
    evaluation_log.push_back("shared:" + std::to_string(candidate));
    const bool shared_pass =
        std::find(shared_reject.begin(), shared_reject.end(), candidate) ==
        shared_reject.end();
    bool source_pass = false;
    if (shared_pass) {
      evaluation_log.push_back("source:" + std::to_string(candidate));
      source_pass = std::find(source_reject.begin(), source_reject.end(),
                              candidate) == source_reject.end();
    }
    if (shared_pass && source_pass) {
      ++index;
      continue;
    }
    candidates[index] = candidates.back();
    candidates.pop_back();
  }
  return candidates;
}

std::int32_t SelectRandomListIndex(const std::vector<std::int32_t> &weights,
                                   std::uint32_t draw31) {
  if (weights.empty()) {
    return -1;
  }
  std::uint32_t total_bits = 0;
  for (const auto weight : weights) {
    total_bits += static_cast<std::uint32_t>(weight);
  }
  const auto total = SignedLow32(total_bits);
  if (total <= 0) {
    return static_cast<std::int32_t>(draw31 % weights.size());
  }
  auto remainder =
      static_cast<std::int32_t>(draw31 % static_cast<std::uint32_t>(total));
  for (std::size_t index = 0; index < weights.size(); ++index) {
    remainder = SignedLow32(static_cast<std::uint32_t>(remainder) -
                            static_cast<std::uint32_t>(weights[index]));
    if (remainder < 0) {
      return static_cast<std::int32_t>(index);
    }
  }
  return 0;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 6) {
    return 1;
  }
  const auto source = ReadFile(argv[1]);
  const auto header = ReadFile(argv[2]);
  const auto abi = ReadFile(argv[3]);
  const auto fixture = ReadFile(argv[4]);
  const auto documentation = ReadFile(argv[5]);
  if (source.empty() || header.empty() || abi.empty() || fixture.empty() ||
      documentation.empty()) {
    return 2;
  }

  if (xar::ck3_11906::kCombatPhaseEventTraceV1CapabilityAdvertised ||
      xar::ck3_11906::kCombatPhaseEventTraceV1RowCount != 13 ||
      xar::ck3_11906::kCombatPhaseEventTraceV1FixedScale != 100'000) {
    return 3;
  }
  constexpr std::array<std::string_view, 13> expected_keys{
      "commander_none",
      "commander_wounded",
      "commander_maimed",
      "commander_killed",
      "knight_none",
      "knight_berserker_attack",
      "knight_become_berserker",
      "knight_shieldmaiden_attack",
      "knight_becomes_incapable",
      "knight_wounded",
      "knight_maimed",
      "knight_killed",
      "knight_qualify_for_accolade",
  };
  if (xar::ck3_11906::kCombatPhaseEventTraceV1StockKeys != expected_keys) {
    return 4;
  }

  constexpr std::array<std::string_view, 33> required_source{
      "kPhaseEventDatabaseSlotRva = 0x57C7930",
      "kNullPhaseEventSlotRva = 0x57C7940",
      "kCombatSideScopeKeyIdRva = 0x57EB630",
      "kCurrentDateSlotRva = 0x570E068",
      "kCombatEventDaysRva = 0x570EF9C",
      "kGlobalRngWrapperSlotRva = 0x4FEB1C8",
      "kBattleResultStorageSlotRva = 0x57C0328",
      "kBattleResultFallbackSlotRva = 0x57C0320",
      "kBattleEventVtableRva = 0x41461A0",
      "kConstructEventTargetScopeRva = 0x81F190",
      "kInsertNamedEventTargetRva = 0x3358160",
      "kEvaluateTriggerRva = 0x334C510",
      "kEvaluateValueRva = 0x337B210",
      "kDestroyEventTargetTailRva = 0x81E900",
      "kDestroyEventTargetRows48Rva = 0x81E980",
      "kEventTargetScopeSize = 0x168",
      "kCombatBattleResultIdOffset = 0x708",
      "kBattleEventRowsOffset = 0x188",
      "kBattleEventRowStride = 0x38",
      "kCharacterEventTargetKind = 4",
      "kCombatSideEventTargetKind = 11",
      "LoadAt<void *>(side, kSideCombatBackPointerOffset) != combat",
      "storage_.data() + kEventTargetNamedRowsOffset",
      "chance_raw / kCombatPhaseEventTraceV1FixedScale",
      "PopulateCharacterStatesAndRows",
      "ReadRetainedBattleEvents",
      "battle_events_after == battle_events",
      "characters_after == characters",
      "rng_after != rng_before",
      "SamePausedSnapshot(before, after)",
      "production_trace_gates_not_closed",
      "evaluator_probe_available",
  };
  if (!ContainsAll(source, required_source)) {
    return 5;
  }
  constexpr std::array<std::string_view, 7> forbidden_source{
      "0x2E1C570",
      "0x23C8750",
      "0x23C9900",
      "0x3380310",
      "0x356A0A0",
      "0x356B770",
      "kPhaseEventDatabaseGetter",
  };
  for (const auto forbidden : forbidden_source) {
    if (Contains(source, forbidden)) {
      return 6;
    }
  }

  constexpr std::array<std::string_view, 18> required_header{
      "game.command.query-combat-phase-event-trace-v1-N",
      "query-combat-phase-event-trace-v1-",
      "kCombatPhaseEventTraceV1CapabilityAdvertised = false",
      "std::array<CombatPhaseEventNativeRowV1, 13>",
      "retained_row_occurrence_requires_managed_before_after",
      "transition_state_complete = false",
      "ccombat_side_knight_source_then_tail_swap_remove_v1",
      "rejected_row_replaced_by_current_tail_then_same_index_rechecked",
      "CombatPhaseBattleEventLedgerV1",
      "native_daily_phase_event_boundaries_v1",
      "native_capture_before_side0_schedule_call_0x27FB58F",
      "native_capture_after_side1_schedule_return_0x27FB5AC",
      "native_capture_before_side0_phase_fire_entry_0x23C9900",
      "native_capture_after_side0_phase_fire_return_0x2309EF7",
      "native_capture_before_side1_phase_fire_entry_0x23C9900",
      "native_capture_after_side1_phase_fire_return_0x2309EFF",
      "production_trace_ready = false",
      "ReadCombatPhaseEventTraceV1Probe",
  };
  if (!ContainsAll(header, required_header)) {
    return 7;
  }

  constexpr std::array<std::string_view, 23> required_abi{
      "\"advertised\": false",
      "\"calls_weighted_selector\": false",
      "\"calls_effect_executor\": false",
      "\"calls_global_rng_draw\": false",
      "0x334C510(event+0x38, scope)",
      "0x337B210(event+0x118, int64_out, scope)",
      "0x81E900(scope+0x118)",
      "0x19DD670",
      "0x19F4760",
      "tail_swap_remove",
      "0x57C0328",
      "BattleEvent+0x10",
      "native_daily_phase_event_boundaries_v1",
      "0x27FB58F",
      "0x27FB5AC",
      "0x2309EF7",
      "0x2309EFF",
      "preallocated query-owned ring buffer",
      "schedule-local RNG state/counter",
      "only the seventh record is a normal paused query",
      "retained_schedule_warning",
      "phase_event_origin_association_for_retained_battle_event_delta",
      "\"production_trace_ready\": false",
  };
  if (!ContainsAll(abi, required_abi)) {
    return 8;
  }
  constexpr std::array<std::string_view, 20> required_fixture{
      "\"fixture_kind\": \"offline_source_contract_only\"",
      "\"live_observation\": false",
      "\"contains_fake_combat_id\": false",
      "\"contains_fake_rng_state\": false",
      "\"contains_fake_effect_transition\": false",
      "\"capability_advertised\": false",
      "retained_schedule_and_generic_battle_event_rows_only",
      "ccombat_side_knight_source_then_tail_swap_remove_v1",
      "generic_battle_ledger_not_phase_origin_without_boundary_delta",
      "native_daily_phase_event_boundaries_v1",
      "tail_swap_remove_nonstable",
      "shared_short_circuits_source",
      "signed_negative_weight_not_clamped",
      "total_nonpositive_uniform_draw",
      "native_capture_before_side0_schedule_call_0x27FB58F",
      "native_capture_after_side1_schedule_return_0x27FB5AC",
      "native_capture_before_side0_phase_fire_entry_0x23C9900",
      "native_capture_before_side1_phase_fire_entry_0x23C9900",
      "preallocated_query_owned_ring_buffer_no_pause_no_bridge_reentry",
      "ui_date_polling_admissible\": false",
  };
  if (!ContainsAll(fixture, required_fixture) ||
      Contains(fixture, "\"live_observation\": true")) {
    return 9;
  }
  constexpr std::array<std::string_view, 18> required_documentation{
      "```mermaid",
      "kind-11",
      "evaluator_probe_available",
      "production capability",
      "retained schedule",
      "managed before/after",
      "tail-swap-remove",
      "0x19DD670",
      "retained BattleEvent",
      "native-boundary",
      "132/132",
      "没有启动、注入、暂停、恢复或操作 CK3",
      "0x27FB58F",
      "0x27FB5AC",
      "0x2309EF7",
      "0x2309EFF",
      "query-owned ring buffer",
      "只有最后一个是正常 paused query",
  };
  if (!ContainsAll(documentation, required_documentation)) {
    return 10;
  }

  std::vector<std::string> evaluation_log;
  const auto post_filter =
      TailSwapFilter({101, 102, 103, 104}, {}, {102}, evaluation_log);
  const std::vector<std::int32_t> expected_post_filter{101, 104, 103};
  const std::vector<std::string> expected_log{
      "shared:101", "source:101", "shared:102", "source:102",
      "shared:104", "source:104", "shared:103", "source:103",
  };
  if (post_filter != expected_post_filter || evaluation_log != expected_log) {
    return 11;
  }
  evaluation_log.clear();
  const auto shared_short_circuit =
      TailSwapFilter({201, 202, 203}, {202}, {}, evaluation_log);
  if (shared_short_circuit != std::vector<std::int32_t>{201, 203} ||
      evaluation_log != std::vector<std::string>{"shared:201", "source:201",
                                                 "shared:202", "shared:203",
                                                 "source:203"}) {
    return 12;
  }
  const std::vector<std::int32_t> signed_weights{
      QuantizeRandomListWeight(100'001),
      QuantizeRandomListWeight(-100'000),
      QuantizeRandomListWeight(200'000),
  };
  if (signed_weights != std::vector<std::int32_t>{2, -1, 2} ||
      SelectRandomListIndex(signed_weights, 2) != 2 ||
      SelectRandomListIndex({0, -1, 1}, 5) != 2) {
    return 13;
  }
  const xar::game::CombatPhaseEventManagedBoundaryContractV1 boundaries;
  const std::array<std::string, 7> expected_boundaries{
      "native_capture_before_side0_schedule_call_0x27FB58F",
      "native_capture_after_side1_schedule_return_0x27FB5AC",
      "native_capture_before_side0_phase_fire_entry_0x23C9900",
      "native_capture_after_side0_phase_fire_return_0x2309EF7",
      "native_capture_before_side1_phase_fire_entry_0x23C9900",
      "native_capture_after_side1_phase_fire_return_0x2309EFF",
      "paused_next_day_stable_query",
  };
  if (boundaries.required_snapshot_sequence != expected_boundaries ||
      boundaries.capture_transport !=
          "preallocated_query_owned_ring_buffer_no_pause_no_bridge_reentry") {
    return 14;
  }
  return 0;
}
