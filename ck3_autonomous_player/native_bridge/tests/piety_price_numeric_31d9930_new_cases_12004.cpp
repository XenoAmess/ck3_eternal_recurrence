#include "xar_bridge/piety_price_numeric_31d9930_12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

struct NumericFixture {
  std::array<std::uint8_t, 0x81C> definition{};
  std::array<std::uintptr_t, 4> reads{};
  std::size_t read_count = 0;
  bool deny_mode = false;
  bool deny_value = false;

  std::uintptr_t pointer() const noexcept {
    return reinterpret_cast<std::uintptr_t>(definition.data());
  }

  void set_mode(std::int32_t mode) noexcept {
    std::memcpy(definition.data() + 0x818, &mode, sizeof(mode));
  }

  void set_value(std::int32_t value) noexcept {
    std::memcpy(definition.data() + 0x7F8, &value, sizeof(value));
  }
};

bool ReadFixture(void *context, const void *source, void *out,
                 std::size_t size) noexcept {
  auto &fixture = *static_cast<NumericFixture *>(context);
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  if (fixture.read_count < fixture.reads.size())
    fixture.reads[fixture.read_count] = address;
  ++fixture.read_count;
  const auto mode_address = fixture.pointer() + 0x818;
  const auto value_address = fixture.pointer() + 0x7F8;
  if (size != sizeof(std::int32_t) ||
      (address != mode_address && address != value_address) ||
      (address == mode_address && fixture.deny_mode) ||
      (address == value_address && fixture.deny_value)) return false;
  std::memcpy(out, source, size);
  return true;
}

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

} // namespace

// New connected source-model cases only. No main and no independent execution.
std::size_t RunPietyPriceNumeric31D9930NewCases12004() {
  constexpr std::uint64_t revision = 0xF123456789ABCDEFULL;
  constexpr std::uintptr_t unreadable_rite = 0xDEAD;
  NumericFixture fixture;
  fixture.set_mode(std::int32_t{0});
  fixture.set_value(std::int32_t{-2147483647} - std::int32_t{1});
  Numeric31D9930Bindings12004 bindings;
  bindings.context = &fixture;
  bindings.guarded_read = ReadFixture;
  bindings.exact_12004_bound = true;

  const auto literal = ReadPietyPriceNumeric31D993012004(
      bindings, fixture.pointer(), unreadable_rite, revision);
  Require(literal.source_ready && literal.native_eax_raw &&
              *literal.native_eax_raw ==
                  (std::int32_t{-2147483647} - std::int32_t{1}),
          "31D9930 literal signed32 EAX did not traverse 11/40");
  Require(literal.definition_pointer == fixture.pointer() &&
              literal.current_rite_pointer == unreadable_rite &&
              literal.frame_key == revision && literal.evaluator &&
              literal.evaluator->unchanged_snapshot_revision == revision &&
              literal.evaluator->expression_identity == fixture.pointer() + 0x760 &&
              !literal.actual_original_consumed_values,
          "31D9930 input/revision/source projection identity changed");
  Require(fixture.read_count == std::size_t{4} &&
              fixture.reads[0] == fixture.pointer() + 0x818 &&
              fixture.reads[1] == fixture.pointer() + 0x7F8 &&
              fixture.reads[2] == fixture.pointer() + 0x818 &&
              fixture.reads[3] == fixture.pointer() + 0x7F8 &&
              literal.evaluator->mode_after_raw_i32 == std::int32_t{0} &&
              literal.evaluator->eax_after_raw_i32 == literal.native_eax_raw,
          "Mode0 consumed an unneeded Rite/name/frame/global input");

  fixture.read_count = 0;
  fixture.set_mode(std::int32_t{1});
  std::int32_t adapter_out = 73;
  construction_owner_mode3::RawReceiverAccessV1 raw_access;
  raw_access.context = &fixture;
  raw_access.read_memory = ReadFixture;
  raw_access.exact_12004_bound = true;
  Require(!ReadPietyPriceNumeric31D9930Adapter12004(
              nullptr, raw_access, fixture.pointer(), unreadable_rite,
              revision, adapter_out) && adapter_out == std::int32_t{73} &&
              fixture.read_count == std::size_t{1},
          "Reached dynamic frontier fabricated EAX or changed adapter output");

  fixture.read_count = 0;
  fixture.set_mode(std::int32_t{0});
  fixture.deny_value = true;
  const auto missing = ReadPietyPriceNumeric31D993012004(
      bindings, fixture.pointer(), unreadable_rite, std::uint64_t{0});
  Require(!missing.source_ready && !missing.native_eax_raw && missing.evaluator &&
              missing.evaluator->mode_raw_i32 == std::int32_t{0} &&
              missing.frame_key == std::uint64_t{0} &&
              missing.reason == "piety_numeric_static_eax_raw_unavailable",
          "Missing raw EAX was substituted or zero revision gated");
  return std::size_t{3};
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
