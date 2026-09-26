#include "xar_bridge/marriage_native_outcome_classifier_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;

namespace {

constexpr std::uint32_t kSubjectId = 0x01000001U;
constexpr std::uint32_t kCandidateId = 0x02000002U;

template <typename Value, std::size_t Size>
void Write(std::array<std::byte, Size> &bytes, std::size_t offset,
           Value value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x200> subject{};
  std::array<std::byte, 0x200> candidate{};
  std::array<std::byte, 0x340> context{};
  std::int32_t threshold_zero = 10;
  std::int32_t threshold_one = 12;
  std::uint32_t grand_wedding_option_id = 0x01855E2EU;
  bool grand_wedding = false;

  Fixture() {
    Write(subject, bridge::kMarriageCharacterIdOffsetV1, kSubjectId);
    Write(candidate, bridge::kMarriageCharacterIdOffsetV1, kCandidateId);
    Write(subject, bridge::kMarriageCharacterAdultSelectorOffsetV1,
          std::uint8_t{0});
    Write(candidate, bridge::kMarriageCharacterAdultSelectorOffsetV1,
          std::uint8_t{1});
    Write(subject, bridge::kMarriageCharacterAdultMeasureOffsetV1,
          std::int16_t{10});
    Write(candidate, bridge::kMarriageCharacterAdultMeasureOffsetV1,
          std::int16_t{12});
    Write(context, bridge::kMarriageContextSecondaryActorIdOffsetV1,
          kSubjectId);
    Write(context, bridge::kMarriageContextSecondaryRecipientIdOffsetV1,
          kCandidateId);
  }
};

Fixture *g_fixture = nullptr;

bool ReadMemory(void *, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool ReadOption(void *, std::uint32_t option_id) {
  assert(option_id == g_fixture->grand_wedding_option_id);
  return g_fixture->grand_wedding;
}

void Initialize(Fixture &fixture,
                bridge::MarriageNativeOutcomeClassifierStateV1 &state) {
  g_fixture = &fixture;
  auto &env = state.environment;
  env.module_base = 1;
  env.exact_build_admitted = true;
  env.admitted_executable_sha256 =
      bridge::kMarriageProposalNativeBinderExecutableSha256V1;
  env.offline_fixture = true;
  env.read_memory = &ReadMemory;
  env.read_boolean_option = &ReadOption;
  env.grand_wedding_option_id_slot =
      reinterpret_cast<std::uintptr_t>(&fixture.grand_wedding_option_id);
  env.adult_threshold_zero_slot =
      reinterpret_cast<std::uintptr_t>(&fixture.threshold_zero);
  env.adult_threshold_one_slot =
      reinterpret_cast<std::uintptr_t>(&fixture.threshold_one);
}

bridge::MarriagePredictedOutcomeV1 Classify(
    Fixture &fixture,
    bridge::MarriageNativeOutcomeClassifierStateV1 &state) {
  bridge::MarriagePredictedOutcomeV1 output =
      bridge::MarriagePredictedOutcomeV1::unavailable;
  assert(bridge::ClassifyMarriageNativeOutcomeExactV1(
      &state, reinterpret_cast<std::uintptr_t>(fixture.subject.data()),
      reinterpret_cast<std::uintptr_t>(fixture.candidate.data()),
      fixture.context.data(), output));
  return output;
}

bridge::MarriageNativeOutcomeDetailsV1 ReadDetails(
    Fixture &fixture,
    bridge::MarriageNativeOutcomeClassifierStateV1 &state) {
  bridge::MarriageNativeOutcomeDetailsV1 output{};
  assert(bridge::ClassifyMarriageNativeOutcomeDetailsExactV1(
      &state, reinterpret_cast<std::uintptr_t>(fixture.subject.data()),
      reinterpret_cast<std::uintptr_t>(fixture.candidate.data()),
      fixture.context.data(), output));
  return output;
}

void TestExactBindingAndBinderConfiguration() {
  const auto env = bridge::BindMarriageNativeOutcomeClassifierEnvironmentV1(
      0x10000000U, true,
      bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  assert(reinterpret_cast<std::uintptr_t>(env.read_boolean_option) ==
         0x10000000U + bridge::kMarriageReadBooleanOptionRvaV1);
  assert(env.grand_wedding_option_id_slot ==
         0x10000000U + bridge::kMarriageGrandWeddingOptionIdSlotRvaV1);

  Fixture fixture{};
  bridge::MarriageNativeOutcomeClassifierStateV1 state{};
  Initialize(fixture, state);
  bridge::MarriageProposalNativeBinderStateV1 binder{};
  assert(bridge::ConfigureMarriageNativeOutcomeClassifierV1(state, binder));
  assert(binder.environment.outcome_classifier_certified &&
         binder.environment.source_adapter.classify_outcome ==
             &bridge::ClassifyMarriageNativeOutcomeExactV1 &&
         binder.environment.source_adapter.outcome_context == &state);
}

void TestAdultGrandWeddingAndMinorBranches() {
  Fixture fixture{};
  bridge::MarriageNativeOutcomeClassifierStateV1 state{};
  Initialize(fixture, state);
  assert(Classify(fixture, state) ==
         bridge::MarriagePredictedOutcomeV1::marriage);
  auto details = ReadDetails(fixture, state);
  assert(details.subject_is_adult && details.candidate_is_adult &&
         !details.grand_wedding_option_selected &&
         details.predicted_outcome ==
             bridge::MarriagePredictedOutcomeV1::marriage);

  fixture.grand_wedding = true;
  assert(Classify(fixture, state) ==
         bridge::MarriagePredictedOutcomeV1::betrothal);
  details = ReadDetails(fixture, state);
  assert(details.subject_is_adult && details.candidate_is_adult &&
         details.grand_wedding_option_selected &&
         details.predicted_outcome ==
             bridge::MarriagePredictedOutcomeV1::betrothal);

  fixture.grand_wedding = false;
  Write(fixture.candidate, bridge::kMarriageCharacterAdultMeasureOffsetV1,
        std::int16_t{11});
  assert(Classify(fixture, state) ==
         bridge::MarriagePredictedOutcomeV1::betrothal);
  details = ReadDetails(fixture, state);
  assert(details.subject_is_adult && !details.candidate_is_adult &&
         !details.grand_wedding_option_selected);

  Write(fixture.subject, bridge::kMarriageCharacterAdultMeasureOffsetV1,
        std::int16_t{9});
  details = ReadDetails(fixture, state);
  assert(!details.subject_is_adult && !details.candidate_is_adult &&
         details.predicted_outcome ==
             bridge::MarriagePredictedOutcomeV1::betrothal);
}

void TestIdentityAndVersionFailClosed() {
  Fixture fixture{};
  bridge::MarriageNativeOutcomeClassifierStateV1 state{};
  Initialize(fixture, state);
  Write(fixture.context,
        bridge::kMarriageContextSecondaryRecipientIdOffsetV1,
        kSubjectId);
  bridge::MarriagePredictedOutcomeV1 output =
      bridge::MarriagePredictedOutcomeV1::marriage;
  assert(!bridge::ClassifyMarriageNativeOutcomeExactV1(
      &state, reinterpret_cast<std::uintptr_t>(fixture.subject.data()),
      reinterpret_cast<std::uintptr_t>(fixture.candidate.data()),
      fixture.context.data(), output));
  assert(output == bridge::MarriagePredictedOutcomeV1::unavailable);
  assert(bridge::ReadMarriageNativeOutcomeClassifierFailureV1(state) ==
         bridge::MarriageNativeOutcomeClassifierFailureV1::
             secondary_pair_identity_mismatch);

  Write(fixture.context,
        bridge::kMarriageContextSecondaryRecipientIdOffsetV1,
        kCandidateId);
  state.environment.admitted_executable_sha256 = "wrong";
  assert(!bridge::ClassifyMarriageNativeOutcomeExactV1(
      &state, reinterpret_cast<std::uintptr_t>(fixture.subject.data()),
      reinterpret_cast<std::uintptr_t>(fixture.candidate.data()),
      fixture.context.data(), output));
  assert(bridge::ReadMarriageNativeOutcomeClassifierFailureV1(state) ==
         bridge::MarriageNativeOutcomeClassifierFailureV1::
             exact_build_not_admitted);
}

} // namespace

int main() {
  TestExactBindingAndBinderConfiguration();
  TestAdultGrandWeddingAndMinorBranches();
  TestIdentityAndVersionFailClosed();
  std::cout << "marriage native outcome classifier v1 tests passed\n";
  return 0;
}
