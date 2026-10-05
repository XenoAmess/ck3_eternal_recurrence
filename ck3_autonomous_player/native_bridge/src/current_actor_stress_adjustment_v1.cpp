#include "xar_bridge/current_actor_stress_adjustment_v1.hpp"
#include "xar_bridge/current_actor_stress_adjustment_v1_pins.hpp"

#include <windows.h>
#include <array>
#include <charconv>
#include <cstring>
#include <limits>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}

void *ResolveCurrentActor(void **storage_slot, std::int32_t id) noexcept {
  if (storage_slot == nullptr || *storage_slot == nullptr || id <= 0)
    return nullptr;
  const auto storage = *storage_slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto slots = Load<void *>(storage, 0x20);
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFF;
  if (slots == nullptr || capacity <= 0 || capacity > 1'000'000 ||
      index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const auto actor = Load<void *>(slots, index * 0x10ULL + 8);
  return actor != nullptr && Load<std::int32_t>(actor, 0x18) == id &&
      Load<std::uint32_t>(actor, 0x1C) == 0x43686172U &&
      Load<void *>(actor, 0x1D0) == nullptr &&
      Load<void *>(actor, 0x1B0) != nullptr ? actor : nullptr;
}

struct NativeSample {
  void *actor = nullptr;
  void *resource_extension = nullptr;
  std::int32_t stress = 0;
  std::int64_t gain = 0;
  std::int64_t loss = 0;
  std::int32_t adjusted_delta = 0;
};

bool GuardedNativeSample(const CurrentActorStressAdjustmentNativeBindingsV1 &b,
                        const CurrentActorStressAdjustmentRequestV1 &r,
                        NativeSample &sample) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    sample.actor = ResolveCurrentActor(b.character_storage_slot,
                                      r.expected_player_character_id);
    if (sample.actor == nullptr) return false;
    sample.resource_extension = Load<void *>(sample.actor, 0x1B0);
    sample.stress = Load<std::int32_t>(sample.resource_extension, 0x2F8);
    if (sample.stress < 0) return false;
    void *aggregator = b.get_character_modifier_aggregator(sample.actor);
    if (aggregator == nullptr) return false;
    auto map = static_cast<std::byte *>(aggregator) + 0x68;
    if (b.read_character_modifier(map, &sample.gain, 143) != &sample.gain ||
        b.read_character_modifier(map, &sample.loss, 144) != &sample.loss)
      return false;
    sample.adjusted_delta =
        b.read_adjusted_stress_delta(sample.actor, r.base_amount);
    return ResolveCurrentActor(b.character_storage_slot,
                              r.expected_player_character_id) == sample.actor &&
        Load<void *>(sample.actor, 0x1B0) == sample.resource_extension &&
        Load<std::int32_t>(sample.resource_extension, 0x2F8) == sample.stress;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool SampleMatches(const NativeSample &left, const NativeSample &right) noexcept {
  return left.actor == right.actor &&
      left.resource_extension == right.resource_extension &&
      left.stress == right.stress && left.gain == right.gain &&
      left.loss == right.loss && left.adjusted_delta == right.adjusted_delta;
}

bool FrameReady(const game::Snapshot &f,
                const CurrentActorStressAdjustmentRequestV1 &r) noexcept {
  return r.expected_revision != 0 && r.expected_game_pid != 0 &&
      r.expected_connection_generation != 0 &&
      r.expected_player_character_id > 0 && r.base_amount >= -300 &&
      r.base_amount <= 300 && f.paused && f.map_ready &&
      f.has_played_character && f.played_character_alive &&
      f.played_character_stress_points >= 0 &&
      f.played_character_id == r.expected_player_character_id;
}

bool Space(char c) noexcept {
  return c == ' ' || c == '\n' || c == '\r' || c == '\t';
}

void SkipSpace(std::string_view s, std::size_t &at) noexcept {
  while (at < s.size() && Space(s[at])) ++at;
}

bool StringLiteral(std::string_view s, std::size_t &at,
                   std::string_view &value) noexcept {
  if (at >= s.size() || s[at] != '"') return false;
  const auto begin = ++at;
  while (at < s.size() && s[at] != '"') {
    if (static_cast<unsigned char>(s[at]) < 0x20 || s[at] == '\\') return false;
    ++at;
  }
  if (at == s.size()) return false;
  value = s.substr(begin, at - begin); ++at;
  return true;
}

template <class T> bool Integer(std::string_view token, T &out) noexcept {
  if (token.empty()) return false;
  const auto digit = token.front() == '-' ? 1U : 0U;
  if (digit == token.size() || token[digit] < '0' || token[digit] > '9' ||
      (token[digit] == '0' && digit + 1 < token.size())) return false;
  const auto parsed = std::from_chars(token.data(), token.data() + token.size(), out);
  return parsed.ec == std::errc{} && parsed.ptr == token.data() + token.size();
}

std::string Quote(std::string_view s) {
  std::string out = "\"";
  for (char c : s) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  return out + '"';
}
std::string Bool(bool b) { return b ? "true" : "false"; }
template <class T> std::string Nullable(const std::optional<T> &v, bool ready) {
  return ready && v ? std::to_string(*v) : "null";
}

} // namespace

bool ParseCurrentActorStressAdjustmentRequestV1(
    std::string_view wire, CurrentActorStressAdjustmentRequestV1 &out) noexcept {
  out = {};
  if (wire.empty() || wire.size() > 4096) return false;
  constexpr std::array<std::string_view, 9> keys{
      "base_amount", "expected_revision", "expected_player_character_id",
      "expected_game_pid", "expected_connection_generation", "type",
      "request_id", "step", "protocol_version"};
  std::array<bool, keys.size()> seen{};
  std::array<std::string_view, keys.size()> values{};
  std::array<bool, keys.size()> strings{};
  std::size_t at = 0;
  SkipSpace(wire, at);
  if (at >= wire.size() || wire[at++] != '{') return false;
  for (;;) {
    SkipSpace(wire, at);
    std::string_view key;
    if (!StringLiteral(wire, at, key)) return false;
    std::size_t index = 0;
    while (index < keys.size() && keys[index] != key) ++index;
    if (index == keys.size() || seen[index]) return false;
    seen[index] = true;
    SkipSpace(wire, at);
    if (at >= wire.size() || wire[at++] != ':') return false;
    SkipSpace(wire, at);
    if (at < wire.size() && wire[at] == '"') {
      strings[index] = true;
      if (!StringLiteral(wire, at, values[index])) return false;
    } else {
      const auto begin = at;
      while (at < wire.size() && !Space(wire[at]) && wire[at] != ',' &&
             wire[at] != '}') ++at;
      values[index] = wire.substr(begin, at - begin);
    }
    SkipSpace(wire, at);
    if (at >= wire.size()) return false;
    if (wire[at] == '}') { ++at; break; }
    if (wire[at++] != ',') return false;
  }
  SkipSpace(wire, at);
  if (at != wire.size()) return false;
  for (std::size_t i = 0; i < 5; ++i)
    if (!seen[i] || strings[i]) return false;
  for (std::size_t i = 5; i < 8; ++i)
    if (seen[i] && (!strings[i] || values[i].empty())) return false;
  std::uint32_t version = 0;
  if (seen[8] && (strings[8] || !Integer(values[8], version) || version != 1))
    return false;
  if ((seen[5] && values[5] != "execute_step") ||
      (seen[7] && values[7] != kCurrentActorStressAdjustmentV1Step)) return false;
  CurrentActorStressAdjustmentRequestV1 parsed{};
  if (!Integer(values[0], parsed.base_amount) ||
      !Integer(values[1], parsed.expected_revision) ||
      !Integer(values[2], parsed.expected_player_character_id) ||
      !Integer(values[3], parsed.expected_game_pid) ||
      !Integer(values[4], parsed.expected_connection_generation) ||
      parsed.base_amount < -300 || parsed.base_amount > 300 ||
      parsed.expected_revision == 0 || parsed.expected_player_character_id <= 0 ||
      parsed.expected_game_pid == 0 || parsed.expected_connection_generation == 0)
    return false;
  out = parsed;
  return true;
}

bool VerifyCurrentActorStressAdjustmentCodePinsV1(
    std::uintptr_t image_base) noexcept {
  if (image_base == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    for (const auto &pin : kCurrentActorStressAdjustmentCodePinsV1)
      if (std::memcmp(reinterpret_cast<const void *>(image_base + pin.rva),
                      pin.bytes, pin.length) != 0) return false;
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

CurrentActorStressAdjustmentNativeBindingsV1
BindCurrentActorStressAdjustmentImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  CurrentActorStressAdjustmentNativeBindingsV1 out{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return out;
  out.enabled = true;
  out.image_base = image_base;
  out.executable_sha256 = executable_sha256;
  out.character_storage_slot = reinterpret_cast<void **>(
      image_base + kCharacterStorageSlotRva);
  out.verify_code_pins = &VerifyCurrentActorStressAdjustmentCodePinsV1;
  out.get_character_modifier_aggregator =
      reinterpret_cast<decltype(out.get_character_modifier_aggregator)>(
          image_base + 0x28C3AE0);
  out.read_character_modifier =
      reinterpret_cast<decltype(out.read_character_modifier)>(
          image_base + 0x2303700);
  out.read_adjusted_stress_delta =
      reinterpret_cast<decltype(out.read_adjusted_stress_delta)>(
          image_base + 0x28BC800);
  return out;
}

void MakeCurrentActorStressAdjustmentUnavailableV1(
    CurrentActorStressAdjustmentObservationV1 &out,
    std::string_view reason) noexcept {
  out.available = false;
  out.current_stress_points.reset();
  out.stress_gain_modifier_raw.reset();
  out.stress_loss_modifier_raw.reset();
  out.adjusted_delta_points.reset();
  out.frame_verified = false;
  out.unavailable_reason = reason.empty() ? "internal_error" : reason;
}

bool ReadCurrentActorStressAdjustmentV1(
    const CurrentActorStressAdjustmentNativeBindingsV1 &b,
    const CurrentActorStressAdjustmentAccessV1 &a,
    const CurrentActorStressAdjustmentRequestV1 &r,
    const game::Snapshot &expected,
    CurrentActorStressAdjustmentObservationV1 &out) noexcept {
  const bool owner_verified = out.owner_thread_verified;
  const bool tls_verified = out.tls_verified;
  const auto owner_id = out.owner_thread_id;
  const auto pump_epoch = out.owner_pump_epoch;
  out = {};
  out.owner_thread_verified = owner_verified;
  out.tls_verified = tls_verified;
  out.owner_thread_id = owner_id;
  out.owner_pump_epoch = pump_epoch;
  out.snapshot_revision = r.expected_revision;
  out.date_raw = expected.date_raw;
  out.game_pid = r.expected_game_pid;
  out.connection_generation = r.expected_connection_generation;
  out.player_character_id = r.expected_player_character_id;
  out.base_amount = r.base_amount;
  const auto fail = [&out](std::string_view reason) {
    MakeCurrentActorStressAdjustmentUnavailableV1(out, reason); return false;
  };
  if (!b.enabled || b.image_base == 0 ||
      b.executable_sha256 != kExecutableSha256 ||
      b.verify_code_pins == nullptr || b.character_storage_slot == nullptr ||
      b.get_character_modifier_aggregator == nullptr ||
      b.read_character_modifier == nullptr ||
      b.read_adjusted_stress_delta == nullptr)
    return fail("exact_source_binding_unavailable");
  if (!owner_verified || !tls_verified || owner_id == 0 || pump_epoch == 0 ||
      a.is_owning_thread == nullptr || a.capture_frame == nullptr ||
      !a.is_owning_thread(a.context)) return fail("owner_thread_unavailable");
  if (!FrameReady(expected, r)) return fail("actor_frame_not_ready");
  if (!b.verify_code_pins(b.image_base)) return fail("source_code_pins_changed");
  out.source_code_pins_verified = true;
  game::Snapshot before{}, after{};
  if (!a.capture_frame(a.context, before) || before != expected ||
      !FrameReady(before, r)) return fail("before_frame_changed");
  NativeSample first{}, second{};
  if (!GuardedNativeSample(b, r, first) ||
      first.stress != before.played_character_stress_points)
    return fail("native_actor_or_modifier_read_unavailable");
  out.actor_binding_verified = true;
  if (!a.is_owning_thread(a.context) ||
      !a.capture_frame(a.context, after) || after != before ||
      !FrameReady(after, r)) return fail("after_frame_changed");
  if (!GuardedNativeSample(b, r, second) || !SampleMatches(first, second))
    return fail("native_stress_values_changed");
  if (!a.is_owning_thread(a.context) ||
      !a.capture_frame(a.context, after) || after != before)
    return fail("completion_frame_changed");
  out.current_stress_points = first.stress;
  out.stress_gain_modifier_raw = first.gain;
  out.stress_loss_modifier_raw = first.loss;
  out.adjusted_delta_points = first.adjusted_delta;
  out.available = true;
  out.frame_verified = true;
  out.unavailable_reason = {};
  return true;
}

std::string SerializeCurrentActorStressAdjustmentV1(
    const CurrentActorStressAdjustmentObservationV1 &out,
    std::uint64_t query_sequence) {
  const bool ready = query_sequence > 0 && out.available && out.source_code_pins_verified &&
      out.actor_binding_verified && out.owner_thread_verified && out.tls_verified &&
      out.frame_verified && out.owner_thread_id > 0 && out.owner_pump_epoch > 0 &&
      out.snapshot_revision > 0 && out.game_pid > 0 && out.connection_generation > 0 &&
      out.player_character_id > 0 && out.base_amount >= -300 && out.base_amount <= 300 &&
      out.current_stress_points && *out.current_stress_points >= 0 &&
      out.stress_gain_modifier_raw && out.stress_loss_modifier_raw &&
      out.adjusted_delta_points && out.unavailable_reason.empty();
  const std::string status = ready ? "available" : "unavailable";
  const std::string scope =
      "\"snapshot_revision\":" + std::to_string(out.snapshot_revision) +
      ",\"date_raw\":" + std::to_string(out.date_raw) +
      ",\"game_pid\":" + std::to_string(out.game_pid) +
      ",\"connection_generation\":" + std::to_string(out.connection_generation);
  return "{\"step\":" + Quote(kCurrentActorStressAdjustmentV1Step) +
      ",\"accepted\":true,\"status\":" + Quote(status) +
      ",\"read_only\":true,\"query_sequence\":" + std::to_string(query_sequence) +
      ',' + scope + ",\"current_actor_stress_adjustment\":{\"schema\":" +
      Quote(kCurrentActorStressAdjustmentV1Schema) + ",\"status\":" + Quote(status) +
      ",\"source\":\"native_current_actor_stress_consumer_1.20.0.3\","
      "\"read_only\":true,\"exact_build\":\"1.20.0.3\",\"executable_sha256\":" +
      Quote(kExecutableSha256) + ',' + scope +
      ",\"player_character_id\":" + std::to_string(out.player_character_id) +
      ",\"base_amount\":" + std::to_string(out.base_amount) +
      ",\"current_stress_points\":" + Nullable(out.current_stress_points, ready) +
      ",\"stress_gain_modifier_raw\":" + Nullable(out.stress_gain_modifier_raw, ready) +
      ",\"stress_loss_modifier_raw\":" + Nullable(out.stress_loss_modifier_raw, ready) +
      ",\"modifier_scale\":100000,\"modifier_semantics\":\"additive_increment\","
      "\"adjusted_delta_points\":" + Nullable(out.adjusted_delta_points, ready) +
      ",\"stress_gain_consumer_index\":143,\"stress_loss_consumer_index\":144,"
      "\"native_aggregator_getter_rva\":\"0x28C3AE0\","
      "\"native_modifier_reader_rva\":\"0x2303700\","
      "\"native_adjuster_rva\":\"0x28BC800\",\"source_code_pins_verified\":" +
      Bool(out.source_code_pins_verified) + ",\"actor_binding_verified\":" +
      Bool(out.actor_binding_verified) + ",\"owner_thread_verified\":" +
      Bool(out.owner_thread_verified) + ",\"tls_verified\":" + Bool(out.tls_verified) +
      ",\"frame_verified\":" + Bool(ready && out.frame_verified) +
      ",\"owner_thread_id\":" + std::to_string(out.owner_thread_id) +
      ",\"owner_pump_epoch\":" + std::to_string(out.owner_pump_epoch) +
      ",\"unavailable_reason\":" +
      (ready ? "null" : Quote(out.unavailable_reason.empty()
          ? std::string_view("typed_result_inconsistent") : out.unavailable_reason)) +
      ",\"final_after_stress_prediction_ready\":false,\"option_cost_binding_ready\":false,"
      "\"business_postcondition_verified\":false},\"backend_id\":\"native-headless\"}";
}

} // namespace xar::ck3_12003
