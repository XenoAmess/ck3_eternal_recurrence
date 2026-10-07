#include "xar_bridge/crown_authority_cooldown_observer_12004.hpp"

#include "xar_bridge/ck3_12004_family_break_penalty.hpp"

#include <cstddef>
#include <cstring>

namespace xar::ck3_12004::crown_cooldown {
namespace {

template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset,
              sizeof(T));
  return result;
}

std::int32_t NativeSubtract(std::int32_t expiry,
                            std::int32_t clock) noexcept {
  const std::uint32_t bits = static_cast<std::uint32_t>(expiry) -
                             static_cast<std::uint32_t>(clock);
  std::int32_t result{};
  std::memcpy(&result, &bits, sizeof(result));
  return result;
}

} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha256) noexcept {
  Bindings result;
  result.identifiers = BindFamilyBreakIdentifiersImage(base, sha256);
  return result;
}

bool Read(const Bindings &bindings, std::int32_t character_id,
          std::int64_t frame_date_raw, Observation &output) noexcept {
  output = {};
  const auto &identifiers = bindings.identifiers;
  if (!identifiers.enabled || !identifiers.variable_context || character_id < 0)
    return false;

  std::int32_t token = -1;
  if (!ck3_12002::ResolvePhaseVariableIdentifier(
          identifiers, "crown_authority_cooldown", token))
    return false;

  const ck3_12002::PhaseVariableTarget target{4, {}, character_id};
  const void *context = identifiers.variable_context(&target);
  if (!context) return false;

  // Actual full VariableContext: remaining helper3727530, complete kind4
  // return225DFE0 -> already-held getter1D671E0 and genuine list consumer.
  const auto *rows = Load<const std::byte *>(context, 0x10);
  const auto count = Load<std::int32_t>(context, 0x1C);
  if (count < 0 || count > 65536 || (count != 0 && !rows)) return false;
  const auto clock = Load<std::int32_t>(context, 0x28);

  std::optional<std::int32_t> expiry;
  for (std::int32_t index = 0; index < count; ++index) {
    const std::size_t offset = static_cast<std::size_t>(index) * 0x20;
    if (Load<std::int32_t>(rows, offset + 8) != token) continue;
    // The native helper selects the first matching scalar row.
    expiry = Load<std::int32_t>(rows, offset + 0x0C);
    break;
  }

  output.read_available = true;
  output.present = expiry.has_value();
  output.expiry_raw = expiry;
  output.current_clock_raw = clock;
  if (!expiry.has_value()) {
    output.timed = false;
    output.remaining_raw = -1;
    output.retry_date_raw = frame_date_raw;
    return true;
  }

  output.timed = *expiry >= 0;
  output.remaining_raw = *expiry >= 0 ? NativeSubtract(*expiry, clock) : -1;
  // Preserve genuine zero/negative timed values, including computed-1.
  // A raw counter has no positive calendar deadline until cadence is proved.
  return true;
}

} // namespace xar::ck3_12004::crown_cooldown
