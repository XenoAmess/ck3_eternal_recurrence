#include "xar_bridge/ck3_12003_prisoner_negotiated_collection.hpp"
#include "xar_bridge/ck3_12003_prisoner_native_kinship.hpp"
// Reuse fixture-owned memory helpers only. Neither the original release
// main/RunCase nor the separate kinship six-case source is invoked.
#define main PrisonerReleaseFixtureNotExecutedForNegotiated12003
#include "ck3_12003_prisoner_release_preview_test.cpp"
#undef main

namespace {
enum class NegotiatedCase {
  gain_hook_accepted, gain_hook_refused, gain_hook_native_false,
  gain_hook_mask_changed, renounce_claims_gain_hook, change_prison_auto_accept
};
NegotiatedCase negotiated_case{};
unsigned selected_calls = 0, score_calls = 0, answer_calls = 0;
unsigned close_control_calls = 0, extended_control_calls = 0;

std::uint32_t RequestMask(NegotiatedCase kind) {
  if (kind == NegotiatedCase::renounce_claims_gain_hook) return 10;
  if (kind == NegotiatedCase::change_prison_auto_accept) return 32;
  return 8;
}
std::int64_t NativeScoreValue() {
  if (negotiated_case == NegotiatedCase::gain_hook_refused) return -5000002;
  if (negotiated_case == NegotiatedCase::renounce_claims_gain_hook) return 2500003;
  return 5000001;
}
std::uint8_t NativeAnswerValue() {
  if (negotiated_case == NegotiatedCase::gain_hook_refused) return 2;
  if (negotiated_case == NegotiatedCase::renounce_claims_gain_hook) return 1;
  return 0;
}
void SelectNegotiatedOption(void *context, std::int32_t ordinal) {
  Require(context == active->context && ordinal >= 0 && ordinal < 13,
          "native setter owns actual thirteen-option context");
  active->selected[static_cast<std::size_t>(ordinal)] = 1;
  ++selected_calls;
}
void FinalizeNegotiated(void *context) {
  Finalize(context);
  if (negotiated_case == NegotiatedCase::gain_hook_mask_changed)
    active->selected.fill(0);
}
bool NegotiatedAutoAccept(void *trigger, const void *scope) {
  Require(trigger == &active->trigger_token &&
          scope == static_cast<std::byte *>(active->context) + 8,
          "native autoaccept trigger uses finalized selected context");
  ++active->auto_accepts;
  return negotiated_case == NegotiatedCase::change_prison_auto_accept;
}
std::int64_t *NegotiatedScore(void *context, std::int64_t *output) {
  Require(context == active->context && output != nullptr,
          "native recipient score uses owned finalized context");
  Require(active->selected[3] == 1,
          "gain-hook score reads actual native-selected bytes");
  *output = NativeScoreValue();
  ++score_calls;
  return output;
}
std::uint8_t NegotiatedAnswer(void *context, std::uint8_t mode,
    std::uint8_t flag, void *error_a, void *error_b) {
  Require(context == active->context && mode == 1 && flag == 1 &&
          error_a == nullptr && error_b == nullptr,
          "actual current native answer signature and owned context");
  ++answer_calls;
  return NativeAnswerValue();
}
bool KinshipControl(void *subject, void *target, unsigned &calls) {
  Require(reinterpret_cast<std::uintptr_t>(subject) ==
              kPrisonerBase + kSelectedOrdinal * 0x1000 &&
          reinterpret_cast<std::uintptr_t>(target) == kPlayer,
          "same-wire kinship control uses actual full-ID subject and jailer");
  ++calls;
  return false;
}
bool CloseControl(void *subject, void *target) {
  return KinshipControl(subject, target, close_control_calls);
}
bool ExtendedControl(void *subject, void *target) {
  return KinshipControl(subject, target, extended_control_calls);
}

void RunNegotiated(NegotiatedCase kind, std::string_view name,
                   const std::filesystem::path &directory) {
  negotiated_case = kind;
  selected_calls = score_calls = answer_calls = 0;
  close_control_calls = extended_control_calls = 0;
  Fixture fixture(kind == NegotiatedCase::gain_hook_native_false ?
                  Case::gate_false : Case::gate_true);
  fixture.Prepare();
  bridge::PlayerPrisonerCollectionAccessV1 ca{};
  ca.exact_build_admitted = true;
  ca.admitted_executable_sha256 = old::kExecutableSha256;
  ca.module_base = kModule;
  ca.current_thread_id = ca.application_main_thread_id = 8;
  ca.read_lineage = ca.read_child_relation = ca.read_title_tier = ca.read_dread = true;
  ca.context = &fixture;
  ca.capture_frame = CaptureFrame;
  ca.read_memory = ReadMemory;
  ca.get_primary_title = PrimaryTitle;
  bridge::PlayerPrisonerCollectionSnapshotV1 collection{};
  Require(old::ReadPlayerPrisonerCollectionV1(ca, collection) &&
          collection.collection_complete && collection.returned_count == 4,
          "actual native complete collection source");
  for (std::size_t i = 0; i < kPrisonerIds.size(); ++i)
    Require(collection.rows[i].full_character_id == kPrisonerIds[i] &&
            collection.rows[i].source_ordinal == i &&
            collection.rows[i].jailer_character_id == kPlayerId,
            "actual complete full IDs, source ordinals and player custody");

  leaf::PrisonerNegotiatedBindings12003 bindings{};
  bindings.release = BindFixture(fixture);
  bindings.release.gift.interaction.finalize = FinalizeNegotiated;
  bindings.release.gift.interaction.evaluate_trigger = NegotiatedAutoAccept;
  bindings.release.gift.interaction.recipient_answer_score = NegotiatedScore;
  bindings.select_local_option = SelectNegotiatedOption;
  bindings.evaluate_answer = NegotiatedAnswer;
  const leaf::PrisonerReleasePreviewAccess12003 access{
      8, 8, &fixture, CaptureFrame, ReadMemory};
  const auto requested = RequestMask(kind);
  const std::string request_payload =
      "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":1,\"step\":"
      "\"query-player-prisoner-collection-private-v1-ransom-ordinal-2\","
      "\"expected_revision\":1014,\"release_option_mask_bits\":" +
      std::to_string(requested) + "}";
  std::uint32_t parsed_mask = 0;
  Require(leaf::ParsePrisonerNegotiatedRequestMask12003(request_payload, parsed_mask) &&
          parsed_mask == requested,
          "production parser consumes actual numeric request mask");
  std::array<leaf::PrisonerNegotiatedPreview12003,
      bridge::kPlayerPrisonerMaximumRowsV1> negotiated{};
  const bool ok = leaf::ReadPrisonerNegotiatedCollectionRow12003(
      bindings, access, collection, kSelectedOrdinal, parsed_mask, negotiated);
  const auto &result = negotiated[kSelectedOrdinal];
  const auto &o = result.observation;
  const bool retained = kind != NegotiatedCase::gain_hook_mask_changed;
  Require(ok == retained && o.available == retained,
          "actual selected-row native observation availability");
  for (std::uint32_t i = 0; i < collection.returned_count; ++i)
    Require(negotiated[i].requested_option_mask_bits == parsed_mask &&
            (i == kSelectedOrdinal ||
             negotiated[i].observation.unavailable_reason == "not_evaluated"),
            "every returned row binds request mask; only actual ordinal evaluated");
  if (retained) {
    const bool sendable = kind != NegotiatedCase::gain_hook_native_false;
    const bool auto_accept = kind == NegotiatedCase::change_prison_auto_accept;
    Require(o.selected_option_mask_bits == parsed_mask &&
            o.observed_definition_option_count == 13 &&
            o.observed_context_option_count == 13 &&
            o.actor_character_id == kPlayerId &&
            o.recipient_character_id == kPrisonerIds[kSelectedOrdinal] &&
            o.jailer_character_id == kPlayerId &&
            o.prisoner_character_id == kPrisonerIds[kSelectedOrdinal] &&
            o.puppet_or_actor_character_id == kPlayerId &&
            o.frame == collection.frame &&
            o.can_send == sendable && o.auto_accept == auto_accept &&
            o.send_costs_raw == kCosts &&
            o.definition_key == leaf::kPrisonerReleaseDefinitionKey12003 &&
            o.definition_stable_hash == static_cast<std::uint32_t>(kDefinitionHash) &&
            o.definition_ordinal == kDefinitionOrdinal,
            "roles, actual selection, final gate and costs originate in native leaf");
    const bool answered = sendable && !auto_accept;
    Require(result.recipient_answer_available == answered &&
            score_calls == (answered ? 2U : 0U) &&
            answer_calls == (answered ? 2U : 0U),
            "native answer callbacks only run for sendable conditional context");
    if (answered)
      Require(result.recipient_acceptance_score_raw == NativeScoreValue() &&
              result.recipient_answer_status_raw == NativeAnswerValue(),
              "leaf copies actual score and native answer, without probability inference");
    Require(fixture.constructed == 2 && fixture.destroyed == 2 &&
            fixture.flags == 26 && fixture.refreshed == 2 && fixture.finalized == 2 &&
            fixture.gates == 2 && fixture.costs == 2 && fixture.auto_accepts == 2 &&
            selected_calls == (requested == 10 ? 4U : 2U),
            "two actual finalized native samples with ten costs each");
  } else {
    Require(o.unavailable_reason == "requested_release_options_not_retained" &&
            o.selected_option_mask_bits == 0 &&
            fixture.constructed == 1 && fixture.destroyed == 1 &&
            fixture.flags == 13 && fixture.refreshed == 1 && fixture.finalized == 1 &&
            selected_calls == 1 && fixture.gates == 0 && fixture.costs == 0 &&
            fixture.auto_accepts == 0 && score_calls == 0 && answer_calls == 0,
            "actual finalizer-cleared mask0 diagnostic precedes gate evaluation");
  }
  Require(fixture.context == nullptr, "every native owned context destroyed");

  // Stable same-wire control, not the old kinship scenario matrix.
  leaf::PrisonerNativeKinshipBindings12003 kb{};
  kb.enabled = true;
  kb.module_base = kModule;
  kb.close_family = CloseControl;
  kb.close_or_extended_family = ExtendedControl;
  const leaf::PrisonerNativeKinshipAccess12003 ka{
      8, 8, &fixture, CaptureFrame, ReadMemory};
  std::array<leaf::PrisonerNativeKinship12003,
      bridge::kPlayerPrisonerMaximumRowsV1> kinship{};
  Require(leaf::ReadPrisonerNativeKinship12003(kb, ka, kPlayerId,
              collection.rows[kSelectedOrdinal].full_character_id,
              kSelectedOrdinal, kinship[kSelectedOrdinal]) &&
          kinship[kSelectedOrdinal].frame == collection.frame &&
          close_control_calls == 2 && extended_control_calls == 2,
          "actual schema7 kinship union control is frame-bound");

  // Existing unrelated leaf fields are explicit typed controls. This FIRST
  // claims no ordinary-ransom/all-options-off or kinship matrix qualification.
  std::array<old::PlayerPrisonerRansomQuoteV1,
      bridge::kPlayerPrisonerMaximumRowsV1> quotes{};
  for (auto &quote : quotes)
    quote.failure = old::PlayerPrisonerRansomQuoteFailureV1::not_evaluated;
  quotes[kSelectedOrdinal].failure = old::PlayerPrisonerRansomQuoteFailureV1::role_unavailable;
  std::array<leaf::PrisonerReleasePreview12003,
      bridge::kPlayerPrisonerMaximumRowsV1> releases{};
  const auto value = old::SerializePlayerPrisonerCollectionPrivateV1(
      collection, collection.frame.native_revision, quotes, true,
      &releases, &kinship, &negotiated);
  Require(!value.empty() &&
          value.find("\"schema_version\":7") != std::string::npos &&
          value.find("\"native_kinship\"") != std::string::npos &&
          value.find("\"negotiated_release_preview\"") != std::string::npos,
          "actual whole serializer emits schema7 requested negotiated plus kinship union");
  const auto wire = std::string{
      "{\"step\":\"query-player-prisoner-collection-private-v1-ransom-ordinal-2\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":"} +
      std::to_string(static_cast<unsigned>(kind) + 1U) +
      ",\"observation_revision\":" + std::to_string(collection.frame.proof_epoch) +
      ",\"snapshot_revision\":" + std::to_string(collection.frame.native_revision) +
      ",\"player_prisoner_collection\":" + value +
      ",\"private_build\":true,\"read_only\":true,\"advertised\":false,"
      "\"backend_id\":\"native-headless\"}";
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  Require(stream.is_open(), "open new negotiated whole wire");
  stream << wire << '\n';
  Require(stream.good(), "write new negotiated whole wire");
  std::cout << "FIRST negotiated " << name << " collection=4 request_mask="
            << parsed_mask << " available=" << (retained ? "true" : "false") << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: ck3_12003_prisoner_negotiated_preview_test OUTPUT_DIRECTORY");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    RunNegotiated(NegotiatedCase::gain_hook_accepted, "gain_hook_accepted", directory);
    RunNegotiated(NegotiatedCase::gain_hook_refused, "gain_hook_refused", directory);
    RunNegotiated(NegotiatedCase::gain_hook_native_false, "gain_hook_native_false", directory);
    RunNegotiated(NegotiatedCase::gain_hook_mask_changed, "gain_hook_mask_changed", directory);
    RunNegotiated(NegotiatedCase::renounce_claims_gain_hook, "renounce_claims_gain_hook", directory);
    RunNegotiated(NegotiatedCase::change_prison_auto_accept, "change_prison_auto_accept", directory);
    std::cout << "FIRST negotiated cases=6 complete\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST negotiated RED " << error.what() << '\n';
    return 1;
  }
}
