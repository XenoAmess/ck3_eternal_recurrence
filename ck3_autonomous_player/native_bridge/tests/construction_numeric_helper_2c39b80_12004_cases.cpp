#include "xar_bridge/construction_numeric_helper_2c39b80_12004.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <stdexcept>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {
constexpr std::uintptr_t kOwnedImage = 0x180000000ULL;
constexpr std::uint64_t kCapturedFrame = 0xFFFFFFFF00000017ULL;
struct OwnedInputs {
  std::array<std::byte, 0x720> province{};
  std::array<std::byte, 0x850> context{};
  std::array<std::byte, 0x390> receiver{};
  std::array<std::byte, 0x1D8> resolved_character{};
  std::array<std::byte, 0x90> resolved_context{};
  std::array<std::byte, 0x48> returned_object{};
  std::int64_t scalar = 100000;
  bool deny_scalar = false, change_receiver = false;
  bool child_globals_ready = false, deny_child_value = false;
  std::uint32_t receiver_reads = 0, child_value_reads = 0;
};
template <std::size_t N, typename T>
void Store(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
template <typename T>
bool Contains(const T &memory, std::uintptr_t raw, std::size_t count) {
  const auto begin = reinterpret_cast<std::uintptr_t>(&memory);
  return raw >= begin && raw - begin <= sizeof(memory) &&
      count <= sizeof(memory) - static_cast<std::size_t>(raw - begin);
}
bool ReadOwned(void *context, const void *address, void *output, std::size_t count) {
  auto &owned = *static_cast<OwnedInputs *>(context);
  const auto raw = reinterpret_cast<std::uintptr_t>(address);
  if (raw == kOwnedImage + kConstructionNumeric2C39B80ScalarRva12004 && count == 8) {
    if (owned.deny_scalar) return false;
    std::memcpy(output, &owned.scalar, count);
    return true;
  }
  if (owned.child_globals_ready && count == 8) {
    std::optional<std::uintptr_t> pointer;
    if (raw == kOwnedImage + 0x5D1DAF8 || raw == kOwnedImage + 0x5D1DAE0 ||
        raw == kOwnedImage + 0x5C67568) pointer = 0;
    if (raw == kOwnedImage + 0x5C67570)
      pointer = reinterpret_cast<std::uintptr_t>(owned.resolved_character.data());
    if (raw == kOwnedImage + 0x5D1E2A8)
      pointer = reinterpret_cast<std::uintptr_t>(owned.returned_object.data());
    if (pointer) {
      std::memcpy(output, &*pointer, count);
      return true;
    }
  }
  if (raw == reinterpret_cast<std::uintptr_t>(owned.context.data()) + 0x848 && count == 8) {
    ++owned.receiver_reads;
    if (owned.change_receiver && owned.receiver_reads == 2) {
      const std::uintptr_t changed = 0;
      std::memcpy(output, &changed, count);
      return true;
    }
  }
  if (raw == reinterpret_cast<std::uintptr_t>(owned.receiver.data()) + 0x38C) {
    ++owned.child_value_reads;
    if (owned.deny_child_value) return false;
  }
  if (!(Contains(owned.province, raw, count) || Contains(owned.context, raw, count) ||
        Contains(owned.receiver, raw, count) || Contains(owned.resolved_character, raw, count) ||
        Contains(owned.resolved_context, raw, count) || Contains(owned.returned_object, raw, count)))
    return false;
  std::memcpy(output, address, count);
  return true;
}
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
}

void VerifyConstructionNumericHelper2C39B80OwnedCases12004() {
  OwnedInputs owned;
  const auto province = reinterpret_cast<std::uintptr_t>(owned.province.data());
  const auto context = reinterpret_cast<std::uintptr_t>(owned.context.data());
  const auto receiver = reinterpret_cast<std::uintptr_t>(owned.receiver.data());
  Store(owned.province, 0x10, std::int32_t{51});
  Store(owned.province, 0x620 + 0xF0, context);
  Store(owned.context, 0x848, receiver);
  Store(owned.receiver, 0x38C, std::uint32_t{999999});
  const LoadedInputAccessV1 access{&owned, ReadOwned, true};
  auto inputs = ReadLoadedNumericHelper2C39B80InputsV1(
      access, province, 51, kOwnedImage, kCapturedFrame);
  Require(inputs.observed && inputs.failure == Numeric2C39B80InputFailureV1::none &&
      inputs.frame_key == kCapturedFrame && inputs.province_pointer == province &&
      inputs.slots_pointer == province + 0x620 && inputs.context_pointer == context &&
      inputs.receiver_pointer == receiver && inputs.scalar_raw == 100000 &&
      inputs.scalar_address == kOwnedImage + 0x5C69450 &&
      !inputs.actual_original_consumed_values && owned.child_value_reads == 0,
      "19c raw parent inputs lost source/frame binding or bypassed child gate");
  // The owned reader deliberately has no registry slots. A readable38C is
  // insufficient to replace the source-owned child's missing lookup/gate.
  auto joined = ReadConstructionNumericHelper2C39B80V1(
      access, province, 51, kOwnedImage, kCapturedFrame);
  Require(!joined.observed &&
      joined.failure == Numeric2C39B80ObservationFailureV1::child_inputs &&
      joined.inputs_before.observed && !joined.child.observed &&
      !joined.conditional_arithmetic && owned.child_value_reads == 0,
      "19c synthesized child or computed output from a readable ungated38C");
  // One connected positive path: the child's real source-defined lazy roots
  // choose its fallback Character,04 resolves1D0->88, and bit35 admits the
  // original receiver's signed DWORD. Parent scalar/frame bookends surround it.
  owned.child_globals_ready = true;
  Store(owned.resolved_character, 0x18, std::uint32_t{0xAB000001U});
  Store(owned.resolved_character, 0x1C, std::uint32_t{0x43686172U});
  Store(owned.resolved_character, 0x1D0,
      reinterpret_cast<std::uintptr_t>(owned.resolved_context.data()));
  Store(owned.resolved_context, 0x88,
      reinterpret_cast<std::uintptr_t>(owned.returned_object.data()));
  Store(owned.returned_object, 0x40, std::uint64_t{1ULL << 35});
  Store(owned.receiver, 0x38C, std::uint32_t{0xFFFFFFF3U});
  joined = ReadConstructionNumericHelper2C39B80V1(
      access, province, 51, kOwnedImage, kCapturedFrame);
  Require(joined.observed && joined.conditional_arithmetic &&
      joined.child.observed && joined.child.frame_key == kCapturedFrame &&
      joined.child.receiver_pointer == receiver && joined.child.eax_signed_i32 == -13 &&
      joined.child.gate_bit35 == true && joined.conditional_arithmetic->output_raw == 87000 &&
      joined.inputs_before.context_pointer == joined.inputs_after_child.context_pointer &&
      !joined.actual_original_consumed_values,
      "19c connected child/scalar result lost gate, signedness or same-frame binding");
  Store(owned.returned_object, 0x40, std::uint64_t{0});
  owned.deny_child_value = true;
  owned.child_value_reads = 0;
  joined = ReadConstructionNumericHelper2C39B80V1(
      access, province, 51, kOwnedImage, kCapturedFrame);
  Require(joined.observed && joined.child.gate_bit35 == false &&
      joined.child.eax_signed_i32 == 0 && joined.conditional_arithmetic &&
      joined.conditional_arithmetic->output_raw == 100000 && owned.child_value_reads == 0,
      "19c connected clear gate read38C or lost source-defined zero contribution");
  owned.deny_scalar = true;
  inputs = ReadLoadedNumericHelper2C39B80InputsV1(access, province, 51, kOwnedImage, kCapturedFrame);
  Require(!inputs.observed && inputs.failure == Numeric2C39B80InputFailureV1::scalar_read &&
      !inputs.scalar_raw, "19c missing scalar became zero input");
  owned.deny_scalar = false;
  owned.change_receiver = true;
  owned.receiver_reads = 0;
  inputs = ReadLoadedNumericHelper2C39B80InputsV1(access, province, 51, kOwnedImage, kCapturedFrame);
  Require(!inputs.observed && inputs.failure == Numeric2C39B80InputFailureV1::source_changed,
      "19c changed receiver was joined to old scalar/child provenance");
  owned.change_receiver = false;
  Store(owned.context, 0x848, std::uintptr_t{0});
  inputs = ReadLoadedNumericHelper2C39B80InputsV1(access, province, 51, kOwnedImage, kCapturedFrame);
  Require(inputs.observed && inputs.receiver_pointer == 0 && inputs.scalar_raw == 100000,
      "19c copied null receiver lost its independent raw identity");

  auto value = EvaluateNumericHelper2C39B80V1(-1, 12345);
  Require(value.child_scaled100000_raw == -100000 && value.first_stage_raw == -12345 &&
      value.second_stage_raw == -123 && value.output_raw == 99877 && !value.second_stage_slow,
      "19c signed32/truncation fast path differs from actual source");
  value = EvaluateNumericHelper2C39B80V1(std::numeric_limits<std::int32_t>::min(), 100000);
  Require(value.first_stage_raw == -214748364800000LL && value.second_stage_slow &&
      value.second_stage_raw == -2147483648000LL && value.output_raw == -2147483548000LL,
      "19c negative signed32/decomposed slow path differs from source");
  value = EvaluateNumericHelper2C39B80V1(1, std::numeric_limits<std::int64_t>::max());
  Require(value.first_stage_raw == std::numeric_limits<std::int64_t>::max() &&
      value.second_stage_slow && value.second_stage_raw == 92233720368547758LL &&
      value.output_raw == 92233720368647758LL,
      "19c high Q64 input was narrowed before native slow arithmetic");
  value = EvaluateNumericHelper2C39B80V1(2, std::numeric_limits<std::int64_t>::max());
  Require(value.first_stage_raw == -2 && value.second_stage_raw == 0 &&
      value.output_raw == 100000 && !value.second_stage_slow,
      "19c wrapped first-stage product was promoted to unbounded arithmetic");
}
} // namespace xar::ck3_12004::construction_owner_mode3
