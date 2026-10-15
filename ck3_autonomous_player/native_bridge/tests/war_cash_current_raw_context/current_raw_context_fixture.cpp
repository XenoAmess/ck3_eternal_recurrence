// Focused production ReadActor/serializer fixture. Compile with the existing
// cash reader and serializer translation units, with the generic-context flag
// both undefined and defined. No game, native wallet callback, or new query.
// This source itself grants no compile, serialization, or runtime credit.
#include "xar_bridge/ck3_12003_war_cash_current_serializer.hpp"
#include "xar_bridge/ck3_12002_war_cash_treasury.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace {
namespace cash = xar::ck3_12003::war_cash_current;
constexpr std::int32_t kActorId = 1741;
constexpr std::string_view kVersion = "1.20.0.4";
constexpr std::string_view kSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

enum class Mode {
  normal, runtime_disabled, zero, failed_value, changed_context,
  null_context, actor_changed, unaligned_context, frame_unqualified
};
struct Memory {
  alignas(16) std::array<std::byte, 0x300> actor{};
  alignas(16) std::array<std::byte, 0x200> living{};
  alignas(16) std::array<std::byte, 0x400> context{};
  alignas(16) std::array<std::byte, 0x400> other_context{};
  Mode mode = Mode::normal;
  std::uintptr_t context_address = 0;
  std::uint32_t pointer_reads = 0;
};

template<class T> void Put(std::uintptr_t address, const T &value) {
  std::memcpy(reinterpret_cast<void *>(address), &value, sizeof(value));
}

std::int64_t *Income(std::int64_t *out, void *, std::int64_t *secondary, void *) {
  *out = 900000; *secondary = 0; return out;
}
void *ExpenseCharacter(void *actor) { return actor; }
std::int64_t *Expenses(std::int64_t *out, void *, void *, std::int64_t,
                       bool, void *) {
  *out = 300000; return out;
}
std::int64_t *Current(std::int64_t *out, void *, void *) {
  for (std::size_t i = 0; i < 10; ++i) out[i] = 0;
  out[0] = 100000; return out;
}
std::int64_t *AllRaised(std::int64_t *out, void *) {
  for (std::size_t i = 0; i < 10; ++i) out[i] = 0;
  out[0] = 200000; return out;
}

bool Read(void *opaque, std::uintptr_t address, void *out,
          std::size_t size) noexcept {
  auto &memory = *static_cast<Memory *>(opaque);
  const auto actor = reinterpret_cast<std::uintptr_t>(memory.actor.data());
  if (address == actor + 0x1C0) {
    ++memory.pointer_reads;
    if (memory.pointer_reads == 2) {
      if (memory.mode == Mode::changed_context) {
        const auto other = reinterpret_cast<std::uintptr_t>(memory.other_context.data());
        Put(actor + 0x1C0, other);
      }
      if (memory.mode == Mode::actor_changed) {
        const std::int32_t changed = kActorId + 1;
        Put(actor + 0x18, changed);
      }
    }
  }
  if (memory.mode == Mode::failed_value &&
      address == memory.context_address + 0x2C8) return false;
  // ReadActor supplies only the two owned actor-pointer reads and four owned
  // context reads. Keep this seam bounded even when a case fails unexpectedly.
  const auto in_range = [address, size](const auto &buffer) {
    const auto start = reinterpret_cast<std::uintptr_t>(buffer.data());
    return address >= start && size <= buffer.size() &&
           address - start <= buffer.size() - size;
  };
  if (!out || !size ||
      (!in_range(memory.actor) && !in_range(memory.context) &&
       !in_range(memory.other_context))) return false;
  std::memcpy(out, reinterpret_cast<const void *>(address), size);
  return true;
}

std::string Run(Mode mode) {
  Memory memory{};
  memory.mode = mode;
  const auto actor = reinterpret_cast<std::uintptr_t>(memory.actor.data());
  const auto living = reinterpret_cast<std::uintptr_t>(memory.living.data());
  memory.context_address = reinterpret_cast<std::uintptr_t>(memory.context.data()) +
      (mode == Mode::unaligned_context ? 1U : 0U);
  Put(actor + 0x18, kActorId);
  Put(actor + 0x1C, std::uint32_t{0x43686172U});
  Put(actor + xar::ck3_12002::kWarCashCharacterLivingExtensionOffset, living);
  Put(living + xar::ck3_12002::kWarCashCharacterGoldOffset, std::int64_t{7000000});
  Put(actor + 0x1C0, mode == Mode::null_context ? std::uintptr_t{0} : memory.context_address);
  const std::array<std::size_t, 4> offsets{0x2C0, 0x2C8, 0x28, 0x30};
  const std::array<std::int64_t, 4> terms{500974, 0, 218610, 0};
  for (std::size_t i = 0; i < offsets.size(); ++i)
    Put(memory.context_address + offsets[i], mode == Mode::zero ? std::int64_t{0} : terms[i]);

  cash::Bindings bindings{};
  bindings.enabled = true;
  bindings.monthly_income = &Income;
  bindings.expense_context_character = &ExpenseCharacter;
  bindings.monthly_total_expenses = &Expenses;
  bindings.current_maintenance = &Current;
  bindings.all_raised_maintenance = &AllRaised;
  bindings.current_raw_context_enabled = mode != Mode::runtime_disabled;
  bindings.current_raw_context_read = &Read;
  bindings.current_raw_context_read_context = &memory;
  cash::ActorResources resources{};
  const bool read_ok = cash::ReadActor(bindings, memory.actor.data(), kActorId, resources);

  xar::game::Snapshot snapshot{};
  snapshot.paused = true;
  snapshot.map_ready = true;
  snapshot.has_played_character = true;
  snapshot.played_character_alive = true;
  snapshot.played_character_id = kActorId;
  snapshot.date_raw = 123456;
  const bool same_frame = mode != Mode::frame_unqualified;
  const auto json = cash::SerializeCurrentResourcesV1(
      resources, snapshot, 42, same_frame, kVersion, kSha);
  const auto has = [&json](std::string_view text) {
    return json.find(text) != std::string::npos;
  };
#if defined(XAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004)
  if (mode == Mode::actor_changed) {
    Require(!read_ok && !resources.current_raw_context, "changed actor retained raw context");
    Require(!has("current_raw_context_v1"), "changed actor serialized a raw leaf");
    Require(resources.unavailable_reason == "war_cash_current_actor_changed_during_raw_context_read",
            "changed actor lost its explicit failure");
  } else {
    Require(read_ok, "unchanged actor failed ReadActor");
    Require(resources.monthly_net_income_raw == 600000, "raw capture changed cash getters");
    if (mode == Mode::runtime_disabled) {
      Require(!resources.current_raw_context && memory.pointer_reads == 0,
              "runtime-disabled read touched context");
      Require(!has("current_raw_context_v1"), "runtime-disabled leaf was serialized");
    } else {
      Require(resources.current_raw_context.has_value(), "raw context was dropped");
      Require(memory.pointer_reads == 2, "context pointer was not read twice");
      const auto &raw = *resources.current_raw_context;
      const auto &values = raw.values;
      Require(raw.character == actor && raw.character_full_id == static_cast<std::uint32_t>(kActorId) &&
              raw.actor_identity_stable, "raw actor identity was not retained");
      Require(has("\"maintenance_attribution\":\"unclosed\""), "raw capture gained attribution");
      if (mode == Mode::failed_value) {
        Require(values.failed_reads == 1 && !values.value_2c8 && !values.capture_complete,
                "failed raw read was not preserved");
      } else if (mode == Mode::changed_context) {
        Require(!values.context_stable && !values.capture_complete && values.value_2c0 == 500974 &&
                values.value_28 == 218610, "changed pointer erased already-read values");
      } else if (mode == Mode::null_context) {
        Require(values.context_identity_before == 0 && values.context_identity_after == 0 &&
                !values.value_2c0 && !values.value_2c8 && !values.value_28 && !values.value_30 &&
                !values.capture_complete, "missing context was replaced by raw zero");
      } else {
        Require(values.capture_complete && values.context_stable && values.failed_reads == 0,
                "complete raw read was not retained");
        if (mode == Mode::zero)
          Require(values.value_2c0 == 0 && values.value_2c8 == 0 && values.value_28 == 0 && values.value_30 == 0,
                  "observed raw zero became unavailable");
      }
      const bool admitted = mode == Mode::normal || mode == Mode::zero;
      Require(has(admitted ? "\"admission_ready\":true" : "\"admission_ready\":false"),
              "wrong raw admission flag");
      if (mode == Mode::unaligned_context)
        Require(has("war_cash_current_raw_context_unaligned_or_overflow"), "unaligned context admitted");
      if (mode == Mode::frame_unqualified)
        Require(has("war_cash_current_raw_context_frame_unqualified"), "unqualified frame admitted");
    }
  }
#else
  Require(read_ok && !resources.current_raw_context && memory.pointer_reads == 0,
          "compile-time feature-OFF touched context");
  Require(!has("current_raw_context_v1"), "compile-time feature-OFF serialized raw context");
#endif
  Require(!has("generic_wallet_context_v1") && !has("caller_return_rva") && !has("amount_raw"),
          "cash raw leaf fabricated a wallet callback");
  return json;
}
} // namespace

int main() {
  try {
    constexpr std::array<std::pair<std::string_view, Mode>, 9> cases{{
      {"normal", Mode::normal}, {"runtime_disabled", Mode::runtime_disabled},
      {"observed_zero", Mode::zero}, {"failed_value", Mode::failed_value},
      {"changed_context", Mode::changed_context}, {"null_context", Mode::null_context},
      {"actor_changed", Mode::actor_changed}, {"unaligned_context", Mode::unaligned_context},
      {"frame_unqualified", Mode::frame_unqualified}}};
    std::cout << '[';
    bool first = true;
    for (const auto &[name, mode] : cases) {
      const auto value = Run(mode);
      if (!first) std::cout << ',';
      first = false;
      std::cout << "{\"case\":\"" << name << "\",\"value\":" << value << '}';
    }
    std::cout << "]\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
