#include "xar_bridge/piety_price_numeric_31d9930_dynamic_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

struct DynamicFixture {
  std::array<std::uint8_t, 0x81C> definition{};
  std::array<std::uint8_t, 0x7B> named_definition{};
  std::size_t reads = 0;

  std::uintptr_t definition_pointer() const noexcept {
    return reinterpret_cast<std::uintptr_t>(definition.data());
  }

  std::uintptr_t named_pointer() const noexcept {
    return reinterpret_cast<std::uintptr_t>(named_definition.data());
  }
};

template <class T, std::size_t N>
void Write(std::array<std::uint8_t, N> &bytes, std::size_t offset, T value) {
  if (offset > N || sizeof(value) > N - offset)
    throw std::runtime_error("Dynamic fixture write outside source field");
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

template <std::size_t N>
bool Copy(const std::array<std::uint8_t, N> &bytes, std::uintptr_t address,
          void *out, std::size_t size) noexcept {
  const auto base = reinterpret_cast<std::uintptr_t>(bytes.data());
  if (address < base || address - base > N || size > N - (address - base))
    return false;
  std::memcpy(out, bytes.data() + (address - base), size);
  return true;
}

bool ReadFixture(void *context, const void *source, void *out,
                 std::size_t size) noexcept {
  auto &fixture = *static_cast<DynamicFixture *>(context);
  ++fixture.reads;
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  return Copy(fixture.definition, address, out, size) ||
      Copy(fixture.named_definition, address, out, size);
}

bool CopyWrongSelectedExpression(
    void *, const PietyPriceNumericAccess12004 &, std::uintptr_t,
    std::uintptr_t, std::uint64_t, PietyPriceA0F0B0DynamicInputs12004 &out) noexcept {
  out.expression_identity += 8;
  return true;
}

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

} // namespace

// First new22f dynamic scalar seam only. No old static cases and no main.
std::size_t RunPietyPriceNumeric31D9930DynamicNewCases12004() {
  constexpr std::uint64_t revision = 0xF23456789ABCDEF1ULL;
  constexpr std::uintptr_t unreadable_rite = 0xDEAD;
  DynamicFixture fixture;
  Write(fixture.definition, 0x818, std::int32_t{1});
  Write(fixture.definition, 0x810, std::uintptr_t{0});
  Write(fixture.definition, 0x800, fixture.named_pointer());
  Write(fixture.named_definition, 0x70, std::uintptr_t{0});
  Write(fixture.named_definition, 0x7A, std::uint8_t{1});
  Write(fixture.named_definition, 0x60, std::int32_t{-17});
  Numeric31D9930DynamicBindings12004 bindings;
  bindings.access.context = &fixture;
  bindings.access.guarded_read = ReadFixture;
  bindings.access.exact_12004_bound = true;
  const auto result = ReadPietyPriceNumeric31D9930Dynamic12004(
      bindings, fixture.definition_pointer(), unreadable_rite, revision);
  Require(result.source_ready && result.native_eax_raw == std::int32_t{-17} &&
              result.evaluator && result.evaluator->named_source &&
              result.evaluator->expression_identity == fixture.definition_pointer() + 0x760 &&
              result.frame_key == revision && result.current_rite_pointer == unreadable_rite &&
              !result.dynamic_input_copy.callback_attempted &&
              !result.evaluator->copied_pack.physical_pack_identity &&
              result.evaluator->original_named_tuple_identity == std::uintptr_t{0} &&
              !result.actual_original_consumed_values,
          "New31D9930 dynamic named constant wrongly demanded pack/R9/Rite");

  fixture.reads = 0;
  bindings.read_dynamic_inputs = CopyWrongSelectedExpression;
  construction_owner_mode3::RawReceiverAccessV1 raw;
  raw.context = &fixture;
  raw.read_memory = ReadFixture;
  raw.exact_12004_bound = true;
  std::int32_t output = 73;
  Require(!ReadPietyPriceNumeric31D9930DynamicAdapter12004(
              &bindings, raw, fixture.definition_pointer(), unreadable_rite,
              revision, output) && output == std::int32_t{73} &&
              fixture.reads == std::size_t{0},
          "Dynamic callback selected another expression or changed unknown output");
  return std::size_t{2};
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
