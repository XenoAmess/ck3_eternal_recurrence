#include "xar_bridge/ck3_12004_prisoner_retained_target_state.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
// Actual4 cached jailer_getter 0x289E810, complete 88B body.
constexpr std::size_t kCharacterExtensionOffset = 0x1B0;
constexpr std::size_t kExtensionPrisonRelationOffset = 0x288;

struct Sample {
  void *actor = nullptr;
  void *target = nullptr;
  void *jailer = nullptr;
  std::uintptr_t death_data = 0;
  std::uintptr_t extension = 0;
  std::uintptr_t relation = 0;
  std::uint32_t jailer_id = 0;
  friend bool operator==(const Sample &, const Sample &) = default;
};

template <class T>
bool Read(const bridge::PlayerPrisonerCollectionAccessV1 &access,
          std::uintptr_t base, std::size_t offset, T &value) noexcept {
  return base != 0 && offset <=
      (std::numeric_limits<std::uintptr_t>::max)() - base &&
      access.read_memory(access.context, base + offset, &value, sizeof(value));
}

bool ReadSample(const RetainedTargetStateBindings12004 &bindings,
                const bridge::PlayerPrisonerCollectionAccessV1 &access,
                std::uint32_t actor_id, std::uint32_t target_id,
                Sample &sample, const char *&reason) noexcept {
  sample = {};
  sample.actor = ResolveCoreCharacter(bindings.core, static_cast<std::int32_t>(actor_id));
  sample.target = ResolveCoreCharacter(bindings.core, static_cast<std::int32_t>(target_id));
  if (!sample.actor || !sample.target) {
    reason = "retained_target_identity_unavailable"; return false;
  }
  const auto target = reinterpret_cast<std::uintptr_t>(sample.target);
  if (!Read(access, target, kCharacterDeathDataOffset, sample.death_data)) {
    reason = "retained_target_memory_unavailable"; return false;
  }
  if (sample.death_data == 0) {
    if (!Read(access, target, kCharacterExtensionOffset, sample.extension) ||
        (sample.extension != 0 && !Read(access, sample.extension,
            kExtensionPrisonRelationOffset, sample.relation))) {
      reason = "retained_target_memory_unavailable"; return false;
    }
    if (sample.relation != 0) {
      if (!Read(access, sample.relation, 0, sample.jailer_id)) {
        reason = "retained_target_memory_unavailable"; return false;
      }
      if (sample.jailer_id == 0 || sample.jailer_id == UINT32_MAX ||
          !(sample.jailer = ResolveCoreCharacter(bindings.core,
              static_cast<std::int32_t>(sample.jailer_id)))) {
        reason = "retained_target_jailer_identity_unavailable"; return false;
      }
    }
  }
  if (ResolveCoreCharacter(bindings.core, static_cast<std::int32_t>(actor_id)) != sample.actor ||
      ResolveCoreCharacter(bindings.core, static_cast<std::int32_t>(target_id)) != sample.target ||
      (sample.jailer != nullptr && ResolveCoreCharacter(bindings.core,
          static_cast<std::int32_t>(sample.jailer_id)) != sample.jailer)) {
    reason = "retained_target_identity_changed"; return false;
  }
  return true;
}

bool Fail(RetainedTargetState12004 &out, const char *reason) {
  out.available = false; out.unavailable_reason = reason;
  out.target_alive.reset(); out.is_imprisoned.reset();
  out.jailer_character_id.reset(); out.custody_state = "unavailable";
  return false;
}

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) {
      out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15];
    } else out += static_cast<char>(ch);
  }
  return out + '"';
}
std::string Bool(const std::optional<bool> &value) {
  return value.has_value() ? (*value ? "true" : "false") : "null";
}
} // namespace

RetainedTargetStateBindings12004 BindRetainedTargetStateImage12004(
    std::uintptr_t module, std::string_view sha256) noexcept {
  RetainedTargetStateBindings12004 bindings{};
  bindings.core = BindCoreImage(module, sha256);
  bindings.enabled = bindings.core.enabled;
  bindings.module_base = module;
  return bindings;
}

bool ReadRetainedTargetState12004(
    const RetainedTargetStateBindings12004 &bindings,
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    const bridge::PlayerPrisonerFrameV1 &expected,
    std::uint32_t target_id, RetainedTargetState12004 &out) noexcept {
  out = {}; out.frame = expected; out.target_character_id = target_id;
  if (!bindings.enabled || !bindings.core.enabled || !access.capture_frame ||
      !access.read_memory || !access.exact_build_admitted ||
      access.admitted_executable_sha256 != kExecutableSha256 ||
      access.module_base != bindings.module_base)
    return Fail(out, "retained_target_bindings_unavailable");
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id)
    return Fail(out, "retained_target_application_main_required");
  if (!expected.paused || !expected.map_ready || !expected.played_character_alive ||
      !expected.played_character_identity_round_trip || expected.played_character_id <= 0 ||
      expected.public_revision == 0 || expected.native_revision == 0 ||
      expected.proof_epoch == 0 || target_id == 0 || target_id == UINT32_MAX ||
      target_id == static_cast<std::uint32_t>(expected.played_character_id))
    return Fail(out, "retained_target_paused_pair_unavailable");
  try {
    bridge::PlayerPrisonerFrameV1 before{}, after{};
    if (!access.capture_frame(access.context, before) || before != expected)
      return Fail(out, "retained_target_frame_changed");
    const auto actor_id = static_cast<std::uint32_t>(expected.played_character_id);
    Sample first{}, second{}; const char *reason = "retained_target_source_unavailable";
    if (!ReadSample(bindings, access, actor_id, target_id, first, reason) ||
        !ReadSample(bindings, access, actor_id, target_id, second, reason))
      return Fail(out, reason);
    if (first != second) return Fail(out, "retained_target_sample_changed");
    if (!access.capture_frame(access.context, after) || after != expected)
      return Fail(out, "retained_target_frame_changed");
    out.available = true; out.unavailable_reason.clear();
    out.target_alive = second.death_data == 0;
    if (second.death_data != 0) out.custody_state = "dead";
    else {
      out.is_imprisoned = second.relation != 0;
      if (second.relation == 0) out.custody_state = "free";
      else {
        out.jailer_character_id = second.jailer_id;
        out.custody_state = second.jailer_id == actor_id ? "held_by_player" : "held_by_other";
      }
    }
    return true;
  } catch (...) { return Fail(out, "retained_target_internal_error"); }
}

std::string SerializeRetainedTargetState12004(const RetainedTargetState12004 &row) {
  std::string out = "{\"schema\":\"xar.ck3.prisoner-retained-target-state-12004-v1\","
      "\"build_version\":" + Quote(kGameVersion) + ",\"executable_sha256\":" +
      Quote(kExecutableSha256) + ",\"available\":" +
      (row.available ? "true" : "false") + ",\"unavailable_reason\":" +
      Quote(row.unavailable_reason) + ",\"snapshot_revision\":" +
      std::to_string(row.frame.native_revision) + ",\"date_raw\":" +
      std::to_string(row.frame.date_raw) + ",\"actor_character_id\":" +
      std::to_string(row.frame.played_character_id) + ",\"target_character_id\":" +
      std::to_string(row.target_character_id) + ",\"target_alive\":" + Bool(row.target_alive) +
      ",\"is_imprisoned\":" + Bool(row.is_imprisoned) + ",\"jailer_character_id\":";
  out += row.jailer_character_id.has_value() ?
      std::to_string(*row.jailer_character_id) : "null";
  return out + ",\"custody_state\":" + Quote(row.custody_state) + "}";
}

} // namespace xar::ck3_12004
