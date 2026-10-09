#include "xar_bridge/crown_authority_cooldown_observer_12004.hpp"
#include "xar_bridge/crown_authority_cooldown_turn_tick_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

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

template <typename T>
bool ReadMemory(const turn_tick::Access &access, std::uintptr_t address,
                T &output) noexcept {
  return access.read_memory != nullptr && address != 0 &&
      access.read_memory(access.context, address, &output, sizeof(output));
}

bool ReadTurnTickContext(const turn_tick::Access &access,
                        const void *context,
                        turn_tick::Observation &output) noexcept {
  output = {};
  output.unavailable_reason = "turn_tick_game_data_unavailable";
  std::uintptr_t game_state = 0;
  std::uintptr_t game_data = 0;
  if (!ReadMemory(access, access.game_state_slot_address, game_state) ||
      game_state == 0 ||
      !ReadMemory(access, game_state + kGameStateDataOffset, game_data) ||
      game_data == 0) return false;

  // Actual named UpdateTurnTick: GameData+98 -> bucket pointers -> full
  // context pointers (2AA5060/2AA4010). Count every exact pointer match.
  std::uintptr_t buckets = 0;
  std::int32_t bucket_count = 0;
  output.unavailable_reason = "turn_tick_manager_unavailable";
  if (!ReadMemory(access, game_data + 0x98, buckets) ||
      !ReadMemory(access, game_data + 0xA4, bucket_count) ||
      bucket_count < 0 || bucket_count > 65536 ||
      (bucket_count != 0 && buckets == 0)) return false;
  std::uint64_t matches = 0;
  const auto current = reinterpret_cast<std::uintptr_t>(context);
  for (std::int32_t bucket_index = 0; bucket_index < bucket_count;
       ++bucket_index) {
    std::uintptr_t bucket = 0;
    std::uintptr_t contexts = 0;
    std::int32_t context_count = 0;
    output.unavailable_reason = "turn_tick_bucket_unavailable";
    if (!ReadMemory(access, buckets + static_cast<std::uintptr_t>(bucket_index) * 8,
                    bucket) || bucket == 0 ||
        !ReadMemory(access, bucket, contexts) ||
        !ReadMemory(access, bucket + 0x0C, context_count) ||
        context_count < 0 || context_count > 65536 ||
        (context_count != 0 && contexts == 0)) return false;
    for (std::int32_t index = 0; index < context_count; ++index) {
      std::uintptr_t entry = 0;
      output.unavailable_reason = "turn_tick_context_entry_unavailable";
      if (!ReadMemory(access, contexts + static_cast<std::uintptr_t>(index) * 8,
                      entry)) return false;
      if (entry != 0 && entry == current) ++matches;
    }
  }

  std::uintptr_t scalar_rows = 0;
  std::int32_t scalar_count = 0;
  output.unavailable_reason = "turn_tick_scalar_tail_unavailable";
  if (!ReadMemory(access, current + 0x1C, scalar_count) ||
      scalar_count < 0 || scalar_count > 65536) return false;
  bool tail_allows_tick = false;
  if (scalar_count != 0) {
    std::int32_t tail_expiry = 0;
    if (!ReadMemory(access, current + 0x10, scalar_rows) || scalar_rows == 0 ||
        !ReadMemory(access, scalar_rows +
                static_cast<std::uintptr_t>(scalar_count - 1) * 0x20 + 0x0C,
            tail_expiry)) return false;
    // Actual2AA4088..4090: a nonnegative scalar tail reaches clock+28 INC.
    tail_allows_tick = tail_expiry >= 0;
  }
  output.read_available = true;
  output.manager_match_count = matches;
  output.manager_contains_context = matches != 0;
  output.scalar_tail_allows_tick = tail_allows_tick;
  output.context_tick_eligible = matches != 0 && tail_allows_tick;
  output.unavailable_reason = {};
  return true;
}

bool ReadImpl(const Bindings &bindings, std::int32_t character_id,
              std::int64_t frame_date_raw, Observation &output,
              const turn_tick::Access *turn_tick_access,
              turn_tick::Observation *turn_tick_output) noexcept {
  output = {};
  if (turn_tick_output != nullptr) *turn_tick_output = {};
  const auto &identifiers = bindings.identifiers;
  if (!identifiers.enabled || !identifiers.variable_context || character_id < 0) {
    if (turn_tick_output != nullptr)
      turn_tick_output->unavailable_reason = "turn_tick_kind4_binding_unavailable";
    return false;
  }

  std::int32_t token = -1;
  if (!ck3_12002::ResolvePhaseVariableIdentifier(
          identifiers, "crown_authority_cooldown", token)) {
    if (turn_tick_output != nullptr)
      turn_tick_output->unavailable_reason = "turn_tick_identifier_unavailable";
    return false;
  }

  const ck3_12002::PhaseVariableTarget target{4, {}, character_id};
  const void *context = identifiers.variable_context(&target);
  if (!context) {
    if (turn_tick_output != nullptr)
      turn_tick_output->unavailable_reason = "turn_tick_kind4_context_unavailable";
    return false;
  }
  if (turn_tick_output != nullptr && turn_tick_access != nullptr)
    (void)ReadTurnTickContext(*turn_tick_access, context, *turn_tick_output);

  // Actual full VariableContext: remaining helper3727530, complete kind4
  // return225DFE0 -> already-held getter1D671E0 and genuine list consumer.
  const auto *rows = Load<const std::byte *>(context, 0x10);
  const auto count = Load<std::int32_t>(context, 0x1C);
  if (count < 0 || count > 65536 || (count != 0 && !rows)) return false;
  const auto clock = Load<std::int32_t>(context, 0x28);

  std::optional<std::int32_t> expiry;
  std::int32_t expiry_index = -1;
  for (std::int32_t index = 0; index < count; ++index) {
    const std::size_t offset = static_cast<std::size_t>(index) * 0x20;
    if (Load<std::int32_t>(rows, offset + 8) != token) continue;
    // The native helper selects the first matching scalar row.
    expiry = Load<std::int32_t>(rows, offset + 0x0C);
    expiry_index = index;
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
  // Actual date+24 -> UpdateTurnTick, with one increment per matching eligible
  // context pointer. Normalizer887360 rebases the timed suffix and clock
  // together, preserving the positive remaining of a surviving suffix row.
  if (turn_tick_output != nullptr && turn_tick_output->read_available &&
      turn_tick_output->context_tick_eligible.value_or(false) &&
      turn_tick_output->manager_match_count.value_or(0) != 0 &&
      *output.remaining_raw > 0) {
    bool queried_row_in_timed_suffix = false;
    for (std::int32_t index = count; index != 0; --index) {
      const auto row_index = index - 1;
      const std::size_t offset = static_cast<std::size_t>(row_index) * 0x20;
      if (Load<std::int32_t>(rows, offset + 0x0C) < 0) break;
      if (row_index == expiry_index) {
        queried_row_in_timed_suffix = true;
        break;
      }
    }
    if (queried_row_in_timed_suffix) {
      const auto remaining = static_cast<std::uint64_t>(*output.remaining_raw);
      const auto matches = *turn_tick_output->manager_match_count;
      const auto whole_steps = remaining / matches +
          static_cast<std::uint64_t>(remaining % matches != 0);
      const std::uint32_t future_bits = static_cast<std::uint32_t>(frame_date_raw) +
          static_cast<std::uint32_t>(whole_steps * 24U);
      std::int32_t future_raw = 0;
      std::memcpy(&future_raw, &future_bits, sizeof(future_raw));
      output.retry_date_raw = static_cast<std::int64_t>(future_raw);
      output.remaining_unit = "scalar_clock_step_calendar_projected";
    }
  }
  return true;
}

} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha256) noexcept {
  Bindings result;
  result.identifiers = BindFamilyBreakIdentifiersImage(base, sha256);
  return result;
}

bool Read(const Bindings &bindings, std::int32_t character_id,
          std::int64_t frame_date_raw, Observation &output) noexcept {
  return ReadImpl(bindings, character_id, frame_date_raw, output, nullptr, nullptr);
}

bool turn_tick::ReadWithTurnTick(const crown_cooldown::Bindings &bindings,
    std::int32_t character_id, std::int64_t frame_date_raw,
    crown_cooldown::Observation &cooldown, const turn_tick::Access &access,
    turn_tick::Observation &turn_tick_output) noexcept {
  return ReadImpl(bindings, character_id, frame_date_raw, cooldown,
      &access, &turn_tick_output);
}

} // namespace xar::ck3_12004::crown_cooldown
