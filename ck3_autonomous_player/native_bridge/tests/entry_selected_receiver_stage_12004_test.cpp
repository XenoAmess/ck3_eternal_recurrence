#include "xar_bridge/entry_selected_receiver_stage_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"

#include <iostream>
#include <stdexcept>

namespace native4 = xar::ck3_12004;
namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Fixture {
  native4::PersonSixStageCapture12004DTO capture;
  native4::KnightConsumedContext12004 consumed;
  native4::EntrySelectedReceiverCall12004 call;
  Fixture() {
    capture.build_version = "1.20.0.4";
    capture.executable_sha256 = std::string(native4::kExecutableSha256);
    capture.configured = capture.capture_observed = capture.capture_complete = true;
    capture.raw_counts_ready = true;
    capture.capture_sequence = 17;
    capture.capture_thread_id = capture.query_thread_id = 42;
    capture.character_id = 0x07000002U;
    capture.character_identity = 0x30000;
    capture.context_identity = 0x50010;
    capture.source_return_rva = native4::kPersonSixStageReturnRva12004;
    auto &model = capture.preparation_model;
    model.observed = model.ready = true;
    model.model_identity = 0x50000;
    model.owner_character_identity = capture.character_identity;
    model.owner_character_id = capture.character_id;
    model.owner_matches_capture = true;
    for (std::size_t index = 0; index < capture.stages.size(); ++index) {
      capture.stages[index].index = static_cast<std::uint32_t>(index);
      capture.stages[index].observed = true;
      capture.stages[index].raw_count_i32 = static_cast<std::int32_t>(index);
    }
    capture.post_six_aggregate.observed = true;
    auto &pc = capture.post_six_aggregate.pc;
    pc.ready = true;
    pc.admitted = true;
    pc.identity = 0x50078;
    pc.count_i32 = 3;
    pc.properties = native4::PersonCarrierDirect12004Properties{};
    pc.properties->keys_u16 = std::vector<std::uint16_t>{0xC1, 0xC5, 0xC9};
    pc.properties->values_q64 = std::vector<std::int64_t>{0, -15000, 2500};
    pc.weight_q100000 = 0;
    consumed.property_key = 0xC5;
    consumed.caller_return_rva = native4::kKnightStatContextReturns12004[4];
    consumed.selected_character_id = capture.character_id;
    consumed.selected_character_identity = capture.character_identity;
    consumed.context_identity = capture.context_identity;
    consumed.preparation_capture_sequence = capture.capture_sequence;
    consumed.preparation_model_identity = model.model_identity;
    consumed.preparation_context_identity = capture.context_identity;
    consumed.preparation_owner_character_id = model.owner_character_id;
    consumed.context_matches_preparation = consumed.owner_matches_preparation = true;
    consumed.pc_matches_preparation_post = true;
    consumed.consumed_pc = pc;
    consumed.operand_raw = -300000;
    call.linked_character_id = 0x03000005U;
    call.linked_character_identity = 0x10000;
    call.consumption_thread_id = 42;
  }
  native4::EntrySelectedReceiverStage12004 Observe() const {
    return native4::ObserveEntrySelectedReceiverStage12004(capture, consumed, call);
  }
};

void FocusedProof() {
  const Fixture original;
  const auto positive = original.Observe();
  Require(positive.completed_preparation_lineage_proven && positive.reason.empty() &&
      positive.preparation_stage == "paused_same_thread_six_stage_completion" &&
      positive.preparation_stage_observed_mask == 0x3F &&
      positive.linked_character_id == original.call.linked_character_id &&
      positive.selected_character_id == original.capture.character_id &&
      positive.linked_character_id != positive.selected_character_id &&
      positive.linked_character_identity != positive.selected_character_identity,
      "completed actual selected receiver did not preserve distinct linked Character");

  auto world = original;
  world.capture.preparation_model.owner_character_identity = 0x90000;
  auto leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven &&
      leaf.selected_matches_model_owner_id == true &&
      leaf.selected_matches_model_owner_identity == false,
      "same full ID substituted for the actual preparation owner pointer");

  world = original;
  world.capture.capture_complete = false;
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven &&
      leaf.preparation_stage == "open_native_six_stage_capture" &&
      !leaf.preparation_completion_thread_id && !leaf.completion_on_consumption_thread &&
      !leaf.completed_post_pc_matches_consumed && leaf.getter_matches_capture_context == true,
      "all six observed counts or same receiver relabelled an open capture as complete");

  world = original;
  world.call.consumption_thread_id = 43;
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven &&
      leaf.completion_on_consumption_thread == false &&
      leaf.preparation_capture_thread_id == std::uint32_t{42},
      "different consumption thread adopted historical same-thread completion");

  world = original;
  world.consumed.caller_return_rva = native4::kKnightStatContextReturns12004[3];
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven && !leaf.exact_consumed_callsite &&
      leaf.selected_matches_capture_identity == true,
      "a matching current selected object replaced the exact Ci callsite");

  world = original;
  world.capture.capture_sequence = 18;
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven && leaf.capture_sequence_matches_record == false,
      "a newer same-owner capture replaced the consumed record's retained sequence");

  world = original;
  world.capture.post_six_aggregate.pc.properties->values_q64->at(1) = 15000;
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven &&
      leaf.completed_post_pc_matches_consumed == false &&
      world.consumed.pc_matches_preparation_post == true,
      "the old comparison boolean replaced an independent complete post-PC comparison");

  world = original;
  world.capture.preparation_model.owner_character_identity.reset();
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven &&
      !leaf.selected_matches_model_owner_identity && leaf.selected_matches_model_owner_id == true,
      "unread owner pointer became a positive identity match");

  world = original;
  world.capture.stages[2].observed = false;
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven && leaf.preparation_stage_observed_mask == 0x3B,
      "partial callback observation became a completed six-stage lineage");

  world = original;
  world.capture.source_return_rva.reset();
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven && !leaf.exact_preparation_source_return,
      "missing historical native source return became exact-build evidence");

  world = original;
  world.capture.build_version = "1.20.0.3";
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven && !leaf.exact_capture_build,
      "old-build capture was accepted as actual4 lineage");

  world = original;
  world.consumed.context_identity = 0x80010;
  leaf = world.Observe();
  Require(!leaf.completed_preparation_lineage_proven &&
      leaf.getter_matches_capture_context == false &&
      leaf.getter_matches_preparation_model_inline == false &&
      leaf.selected_matches_model_owner_identity == true,
      "same selected Character associated a different getter context with historical preparation");

  const auto capture_before = original.capture;
  const auto consumed_before = original.consumed;
  static_cast<void>(original.Observe());
  Require(original.capture == capture_before && original.consumed == consumed_before &&
      original.consumed.operand_raw == -300000,
      "derived observer changed the historical capture, consumed PC or signed operand");
}
} // namespace

extern "C"
#if defined(_WIN32)
__declspec(dllexport)
#endif
int EntrySelectedReceiverStageFocusedTest12004() {
  try {
    FocusedProof();
    std::cout << "entry selected receiver stage: positive lineage and eleven distinct non-equivalence cases GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}

int main() {
  return EntrySelectedReceiverStageFocusedTest12004();
}
