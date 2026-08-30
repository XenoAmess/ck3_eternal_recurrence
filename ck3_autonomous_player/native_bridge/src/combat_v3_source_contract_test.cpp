#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>
#include <vector>

namespace {

bool Fail(std::string_view message) {
  std::cerr << message << '\n';
  return false;
}

bool ContainsAll(std::string_view source,
                 const std::vector<std::string_view> &needles) {
  for (const auto needle : needles) {
    if (source.find(needle) == std::string_view::npos) {
      std::cerr << "missing production combat-v3 source contract token: "
                << needle << '\n';
      return false;
    }
  }
  return true;
}

bool AppearsInOrder(std::string_view source,
                    const std::vector<std::string_view> &needles) {
  std::size_t position = 0;
  for (const auto needle : needles) {
    position = source.find(needle, position);
    if (position == std::string_view::npos) {
      std::cerr << "missing or reordered production combat-v3 token: "
                << needle << '\n';
      return false;
    }
    position += needle.size();
  }
  return true;
}

bool ReadSource(const char *path, std::string &output) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    std::cerr << "could not open production source: " << path << '\n';
    return false;
  }
  output.assign(std::istreambuf_iterator<char>(input),
                std::istreambuf_iterator<char>());
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 6) {
    return Fail("usage: combat_v3_source_contract_test <combat_v3.cpp> "
                "<game_adapter.cpp> <ck3_adapter.cpp> <bridge.cpp> "
                "<combat_v3_mailbox.cpp>")
               ? 0
               : 1;
  }
  std::string source;
  std::string game_adapter_source;
  std::string ck3_adapter_source;
  std::string bridge_source;
  std::string mailbox_source;
  if (!ReadSource(argv[1], source) ||
      !ReadSource(argv[2], game_adapter_source) ||
      !ReadSource(argv[3], ck3_adapter_source) ||
      !ReadSource(argv[4], bridge_source) ||
      !ReadSource(argv[5], mailbox_source)) {
    return 1;
  }
  const std::string_view view(source);

  if (!ContainsAll(
          view,
          {
              "kCombatShellSize = 0x718",
              "kConstructCombatSideRva = 0x23C7D30",
              "kPopulateCombatSideRva = 0x23C9100",
              "kSelectBattleCommanderRva = 0x23C8A60",
              "kRefreshCombatSideStrengthRva = 0x23CB840",
              "kReadCombatSideStrengthRva = 0x23CC340",
              "kResolveCombatAdvantageRva = 0x2308D50",
              "kReadSideDynamicAdvantageRva = 0x2307CB0",
              "kReadCommanderDynamicAdvantageRva = 0x2307680",
              "kReadSideModifierAdvantageRva = 0x2307230",
              "kReadCombatRelationKindRva = 0x2307080",
              "kDestroyCombatSideRva = 0x2303B00",
              "kCombatSideKnightEntriesOffset = 0x40",
              "kCombatSideKnightEntriesCountOffset = 0x4C",
              "kCombatSideKnightEntryStride = 0x60",
              "kCombatSideKnightRegimentIdOffset = 0x08",
              "ccombat_side_commanders_then_knights_native_source_"
              "equivalence_v1",
              "ReadNativeCandidateSourceRowsV3(",
              "SealCandidateSourceProofV3(",
              "ValidateCandidateSourceProofV3(",
              "proof.ordered_sources != native_rows",
              "output.constructor_sources.size() != 15",
              "ValidateEffectLedgerV3(local.side(0), ledgers[0])",
              "ValidateEffectLedgerV3(local.side(1), ledgers[1])",
          })) {
    return 1;
  }

  for (const auto forbidden : {
           std::string_view{"0x2303CF0"},
           std::string_view{"0x23043F0"},
           std::string_view{"0x23044F0"},
           std::string_view{"0x356B770"},
       }) {
    if (view.find(forbidden) != std::string_view::npos) {
      std::cerr << "forbidden mutating/RNG helper entered production v3: "
                << forbidden << '\n';
      return 1;
    }
  }

  const auto reader = view.find("bool ReadAdvantageModel(");
  if (reader == std::string_view::npos) {
    return Fail("ReadAdvantageModel is missing") ? 0 : 1;
  }
  const auto reader_view = view.substr(reader);
  if (!AppearsInOrder(
          reader_view,
          {
              "construct_side(side, local.shell())",
              "populate_side(side, army.army)",
              "ReadNativeCandidateSourceRowsV3(",
              "SealCandidateSourceProofV3(",
              "select_commander(side)",
              "refresh_strength(side)",
              "\"attacker_adjacency\"",
              "\"defender_adjacency\"",
              "\"attacker_terrain\"",
              "\"defender_terrain\"",
              "\"supply_0\"",
              "\"supply_1\"",
              "\"holding_defender_1\"",
              "\"gathering_army_0\"",
              "\"gathering_army_1\"",
              "\"debt_0_owner\"",
              "\"debt_1_owner\"",
              "\"debt_0_treasury\"",
              "\"debt_1_treasury\"",
              "\"unreformed_faith_0\"",
              "\"unreformed_faith_1\"",
              "AllocateEffectLedgerV3(local.side(0), ledgers[0])",
              "resolve_advantage(local.shell())",
              "read_relation(local.shell()",
              "read_side_total(local.shell()",
              "read_commander(local.shell()",
              "read_side_modifier(",
              "resolved != original_total",
              "revalidated_sources !=",
              "candidate_source_proof.ordered_sources",
              "local.CleanupChecked()",
              "original_total_helper_match = true",
              "output.available = true",
          })) {
    return 1;
  }

  const auto cleanup = view.find("bool CleanupChecked() noexcept");
  if (cleanup == std::string_view::npos ||
      !AppearsInOrder(view.substr(cleanup),
                      {
                          "destroy_(side(index))",
                          "NativeFreeBufferV3(population_allocators[index]",
                      })) {
    return Fail("local combat teardown order is not destructor-then-aux-free")
               ? 0
               : 1;
  }

  if (!ContainsAll(
          game_adapter_source,
          {
              "bool ParseCombatSimulationInputsV3Step(",
              "game.command.query-combat-simulation-inputs-v3-N",
              "ParseCombatSimulationInputsV3Step(step, request)",
          }) ||
      game_adapter_source.find("ParseCombatSimulationInputsV3TestStep") !=
          std::string::npos) {
    return Fail("production v3 parser/capability dispatch is not frozen") ? 0
                                                                           : 1;
  }
  if (!ContainsAll(
          ck3_adapter_source,
          {
              "constexpr std::array<std::string_view, 65> kCapabilities",
              "game.command.query-battle-reinforcement-assignment-v1-N",
              "game.command.query-combat-simulation-inputs-v3-N",
              "read_combat_simulation_inputs_v3(",
              "ck3_11906::ReadCombatSimulationInputsV3(bindings_",
          })) {
    return 1;
  }
  if (!ContainsAll(
          bridge_source,
          {
              "void AppendCombatSimulationInputsV3(",
              "production_exact_132_refs",
              "xar::ck3_11906::SerializeCombatPhaseInputsV3(",
              "std::string CombatSimulationInputsV3ResultFrame(",
              "query-combat-simulation-inputs-v3-",
              "ParseCombatSimulationInputsV3Step(",
              "ParseCombatSimulationInputsV3ExpectedRevision(",
              "CombatSimulationInputsV3MailboxContext query{}",
              "ExecuteCombatSimulationInputsV3MailboxQuery",
              "TrySubmitMainThreadQueryV1(",
              "WaitForMainThreadQueryV1(",
              "phase_inputs_unavailable",
          }) ||
      !AppearsInOrder(
          bridge_source,
          {
              "query-combat-simulation-inputs-v3-",
              "ParseCombatSimulationInputsV3Step(",
              "ParseCombatSimulationInputsV3ExpectedRevision(",
              "CombatSimulationInputsV3MailboxContext query{}",
              "TrySubmitMainThreadQueryV1(",
              "WaitForMainThreadQueryV1(",
              "phase_inputs_unavailable",
              "CombatSimulationInputsV3ResultFrame(",
          }) ||
      bridge_source.find("xar::game::ReadCombatSimulationInputsV3(") !=
          std::string::npos) {
    return Fail("production v3 bridge dispatch/frame contract is incomplete")
               ? 0
               : 1;
  }
  if (!ContainsAll(
          mailbox_source,
          {
              "kCombatSimulationInputsV3AccoladeScriptedRulesSingletonSlotRva",
              "kCombatSimulationInputsV3AccoladeTypeDatabaseSlotRva",
              "kCombatSimulationInputsV3AccoladeOwnerNamedKeyIdRva",
              "PhaseRuntimeReady(",
              "ReadBaseOnlyPhaseUnavailable(",
              "ReadCombatSimulationInputsV3(query->bindings",
              "ReadSnapshot(query->bindings, before)",
              "ReadSnapshot(query->bindings, after)",
              "after != before",
              "snapshot == query.expected_snapshot",
              "GenerationBoundEncounterMatchesExpectedSnapshot(",
              "SnapshotContainsFullGenerationArmyId(",
              "query.expected_snapshot_revision == 0",
          }) ||
      !AppearsInOrder(
          mailbox_source,
          {
              "PhaseRuntimeReady(query->module_base",
              "ReadSnapshot(query->bindings, before)",
              "ReadCombatSimulationInputsV3(query->bindings",
              "ReadSnapshot(query->bindings, after)",
          })) {
    return Fail("production v3 application-main mailbox contract is incomplete")
               ? 0
               : 1;
  }
  constexpr std::string_view crash_disabled_exit_v2_capability =
      "game.command.query-war-termination-exit-terms-v2-N";
  constexpr std::string_view crash_disabled_exit_v2_prefix =
      "query-war-termination-exit-terms-v2-";
  for (const auto production_source : {std::string_view{game_adapter_source},
                                       std::string_view{ck3_adapter_source},
                                       std::string_view{bridge_source}}) {
    if (production_source.find(crash_disabled_exit_v2_capability) !=
            std::string_view::npos ||
        production_source.find(crash_disabled_exit_v2_prefix) !=
            std::string_view::npos) {
      return Fail("crash-disabled exit-v2 leaked into production dispatch")
                 ? 0
                 : 1;
    }
  }
  return 0;
}
