#include "xar_bridge/ck3_12004_prisoner_keeper_opinion.hpp"

namespace xar::ck3_12004 {
namespace {
struct Sample {
  void *actor = nullptr;
  void *target = nullptr;
  std::int32_t opinion = 0;
  friend bool operator==(const Sample &, const Sample &) = default;
};

bool ReadSample(const GiftOpinionBindings12004 &bindings,
                std::uint32_t actor_id, std::uint32_t target_id,
                Sample &sample) noexcept {
  sample = {};
  sample.actor = xar::ck3_12004::ResolveCoreCharacter(bindings.core,
      static_cast<std::int32_t>(actor_id));
  sample.target = xar::ck3_12004::ResolveCoreCharacter(bindings.core,
      static_cast<std::int32_t>(target_id));
  if (!sample.actor || !sample.target) return false;
  // Stock release sender: puppet_or_actor opinion toward recipient. The
  // current player collection fixes actor to the played jailer, without a
  // puppet substitution. The reverse material opinion is a separate input.
  sample.opinion = bindings.read_opinion(sample.actor, sample.target);
  return xar::ck3_12004::ResolveCoreCharacter(bindings.core, static_cast<std::int32_t>(actor_id)) ==
      sample.actor && xar::ck3_12004::ResolveCoreCharacter(bindings.core,
      static_cast<std::int32_t>(target_id)) == sample.target;
}

bool Fail(KeeperOpinion12004 &output, const char *reason) {
  output.available = false;
  output.unavailable_reason = reason;
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
} // namespace

KeeperOpinionBindings12004 BindKeeperOpinionImage12004(
    std::uintptr_t module, std::string_view sha256) noexcept {
  KeeperOpinionBindings12004 bindings{};
  bindings.opinion = BindGiftOpinionImage12004(module, sha256);
  return bindings;
}

bool ReadKeeperOpinion12004(
    const KeeperOpinionBindings12004 &bindings,
    const bridge::PlayerPrisonerCollectionAccessV1 &access,
    const bridge::PlayerPrisonerFrameV1 &expected,
    std::uint32_t target_id, KeeperOpinion12004 &output) noexcept {
  output = {};
  output.frame = expected;
  output.target_character_id = target_id;
  const auto &opinion = bindings.opinion;
  if (!opinion.enabled || !opinion.core.enabled || !opinion.read_opinion ||
      !access.capture_frame || !access.exact_build_admitted ||
      access.admitted_executable_sha256 != kExecutableSha256 ||
      access.module_base != opinion.module_base)
    return Fail(output, "keeper_opinion_bindings_unavailable");
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id)
    return Fail(output, "keeper_opinion_application_main_required");
  if (expected.public_revision == 0 || expected.native_revision == 0 ||
      !expected.paused || !expected.map_ready || !expected.played_character_alive ||
      !expected.played_character_identity_round_trip || expected.played_character_id <= 0 ||
      target_id == 0 || target_id == UINT32_MAX ||
      target_id == static_cast<std::uint32_t>(expected.played_character_id))
    return Fail(output, "keeper_opinion_paused_pair_unavailable");
  try {
    bridge::PlayerPrisonerFrameV1 before{}, after{};
    if (!access.capture_frame(access.context, before) || before != expected)
      return Fail(output, "keeper_opinion_frame_changed");
    const auto actor = static_cast<std::uint32_t>(expected.played_character_id);
    Sample first{}, second{};
    if (!ReadSample(opinion, actor, target_id, first) ||
        !ReadSample(opinion, actor, target_id, second) || first != second)
      return Fail(output, "keeper_opinion_source_unavailable_or_changed");
    if (!access.capture_frame(access.context, after) || after != expected)
      return Fail(output, "keeper_opinion_frame_changed");
    output.available = true;
    output.actor_opinion_of_target = second.opinion;
    return true;
  } catch (...) { return Fail(output, "keeper_opinion_internal_error"); }
}

std::string SerializeKeeperOpinion12004(const KeeperOpinion12004 &row) {
  std::string out = "{\"schema\":\"xar.ck3.prisoner-keeper-opinion-12004-v1\","
      "\"build_version\":" + Quote(kGameVersion) + ",\"executable_sha256\":" +
      Quote(kExecutableSha256) + ",\"available\":" +
      (row.available ? "true" : "false") + ",\"unavailable_reason\":" +
      Quote(row.unavailable_reason) + ",\"snapshot_revision\":" +
      std::to_string(row.frame.native_revision) + ",\"date_raw\":" +
      std::to_string(row.frame.date_raw) + ",\"actor_character_id\":" +
      std::to_string(row.frame.played_character_id) + ",\"target_character_id\":" +
      std::to_string(row.target_character_id) + ",\"actor_opinion_of_target\":";
  out += row.actor_opinion_of_target ?
      std::to_string(*row.actor_opinion_of_target) : "null";
  return out + "}";
}

} // namespace xar::ck3_12004
