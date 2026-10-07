#include "xar_bridge/ck3_12004_prisoner_release_material_opinion.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12004 {
namespace {
using Access = bridge::PlayerPrisonerCollectionAccessV1;

template <class T>
bool Load(const Access &access, const void *object, std::size_t offset,
          T &value) noexcept {
  value = {};
  return object != nullptr && access.read_memory(access.context,
      reinterpret_cast<std::uintptr_t>(object) + offset, &value, sizeof(value));
}

bool Definition(const Access &access, const GiftOpinionBindings12004 &b,
                const void *definition, std::uint32_t hash) noexcept {
  constexpr auto key = kPrisonerReleaseMaterialOpinionKey12004;
  std::uintptr_t primary = 0, secondary = 0;
  std::uint32_t actual_hash = 0, tag = 0;
  std::uint64_t length = 0, capacity = 0;
  if (!Load(access, definition, 0, primary) || primary != b.modifier_primary_vtable ||
      !Load(access, definition, 0x88, secondary) || secondary != b.modifier_secondary_vtable ||
      !Load(access, definition, 0x14, actual_hash) || actual_hash != hash ||
      !Load(access, definition, 0x38, tag) || tag != 0x4744624FU ||
      !Load(access, definition, 0x28, length) || length != key.size() ||
      !Load(access, definition, 0x30, capacity) || capacity < length) return false;
  const char *text = static_cast<const char *>(definition) + 0x18;
  if (capacity >= 16 && !Load(access, definition, 0x18, text)) return false;
  for (std::size_t i = 0; i < key.size(); ++i) {
    char value = 0;
    if (!Load(access, text, i, value) || value != key[i]) return false;
  }
  return true;
}

struct Sample {
  void *actor = nullptr;
  void *target = nullptr;
  void *database = nullptr;
  void *definition = nullptr;
  std::uint32_t hash = 0;
  std::int32_t opinion = 0;
  bool present = false;
  std::optional<std::int32_t> value;
  friend bool operator==(const Sample &, const Sample &) = default;
};

bool ReadSample(const PrisonerReleaseMaterialOpinionBindings12004 &bindings,
                const Access &access, std::uint32_t actor_id,
                std::uint32_t target_id, Sample &sample) noexcept {
  const auto &b = bindings.opinion;
  sample = {};
  sample.actor = ck3_12004::ResolveCoreCharacter(b.core, static_cast<std::int32_t>(actor_id));
  sample.target = ck3_12004::ResolveCoreCharacter(b.core, static_cast<std::int32_t>(target_id));
  if (!sample.actor || !sample.target ||
      !Load(access, b.modifier_database_slot, 0, sample.database) || !sample.database)
    return false;
  constexpr auto key = kPrisonerReleaseMaterialOpinionKey12004;
  sample.hash = static_cast<std::uint32_t>(bindings.hash_key(
      sample.database, key.data(), static_cast<std::uint32_t>(key.size())));
  sample.definition = b.lookup_modifier(sample.database, sample.hash);
  if (!Definition(access, b, sample.definition, sample.hash)) return false;
  sample.opinion = b.read_opinion(sample.target, sample.actor);
  void *extension = nullptr;
  if (!Load(access, sample.target, 0x1B0, extension)) return false;
  if (extension != nullptr) {
    void *group = b.find_group(extension, actor_id);
    if (group != nullptr) {
      void *rows = nullptr;
      std::int32_t count = 0;
      if (!Load(access, group, 8, rows) || !Load(access, group, 0x14, count) ||
          count < 0 || count > (1 << 20) || (count != 0 && rows == nullptr)) return false;
      for (std::int32_t i = 0; i < count; ++i) {
        void *active = nullptr, *definition = nullptr;
        std::uintptr_t vtable = 0;
        if (!Load(access, rows, static_cast<std::size_t>(i) * 8, active)) return false;
        if (active == nullptr) continue;
        if (!Load(access, active, 0, vtable) ||
            (vtable != b.active_opinion_vtable && vtable != b.temporary_opinion_vtable) ||
            !Load(access, active, 8, definition)) return false;
        if (definition == sample.definition) sample.present = true;
      }
      if (sample.present) sample.value = b.sum_modifier(group, sample.definition);
    }
  }
  void *database_after = nullptr;
  return Load(access, b.modifier_database_slot, 0, database_after) &&
      database_after == sample.database &&
      b.lookup_modifier(database_after, sample.hash) == sample.definition &&
      Definition(access, b, sample.definition, sample.hash) &&
      ck3_12004::ResolveCoreCharacter(b.core, static_cast<std::int32_t>(actor_id)) == sample.actor &&
      ck3_12004::ResolveCoreCharacter(b.core, static_cast<std::int32_t>(target_id)) == sample.target;
}

bool Fail(PrisonerReleaseMaterialOpinion12004 &output, const char *reason) {
  output.available = false;
  output.unavailable_reason = reason;
  return false;
}

std::string Quote(std::string_view value) {
  std::string out = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') { out += '\\'; out += static_cast<char>(ch); }
    else if (ch < 0x20) { out += "\\u00"; out += hex[ch >> 4]; out += hex[ch & 15]; }
    else out += static_cast<char>(ch);
  }
  return out + '"';
}
const char *Boolean(bool value) noexcept { return value ? "true" : "false"; }
} // namespace

PrisonerReleaseMaterialOpinionBindings12004
BindPrisonerReleaseMaterialOpinionImage12004(
    std::uintptr_t module, std::string_view sha256) noexcept {
  PrisonerReleaseMaterialOpinionBindings12004 b{};
  b.opinion = BindGiftOpinionImage12004(module, sha256);
  if (!b.opinion.enabled) return b;
  b.hash_key = reinterpret_cast<PrisonerReleaseMaterialHash12004>(
      module + kOpinionStableKeyHashRva);
  return b;
}

bool ReadPrisonerReleaseMaterialOpinion12004(
    const PrisonerReleaseMaterialOpinionBindings12004 &bindings,
    const Access &access, const bridge::PlayerPrisonerFrameV1 &expected,
    std::uint32_t target_id, PrisonerReleaseMaterialOpinion12004 &output) noexcept {
  output = {};
  output.frame = expected;
  output.target_character_id = target_id;
  const auto &b = bindings.opinion;
  if (!b.enabled || !b.core.enabled || !bindings.hash_key || !b.read_opinion ||
      !b.lookup_modifier || !b.find_group || !b.sum_modifier || !b.modifier_database_slot ||
      !access.capture_frame || !access.read_memory || !access.exact_build_admitted ||
      access.admitted_executable_sha256 != kExecutableSha256 ||
      access.module_base != b.module_base)
    return Fail(output, "release_material_bindings_unavailable");
  if (access.current_thread_id == 0 ||
      access.current_thread_id != access.application_main_thread_id)
    return Fail(output, "release_material_application_main_required");
  if (expected.public_revision == 0 || expected.native_revision == 0 ||
      !expected.paused || !expected.map_ready || !expected.played_character_alive ||
      !expected.played_character_identity_round_trip || expected.played_character_id <= 0 ||
      target_id == 0 || target_id == UINT32_MAX ||
      target_id == static_cast<std::uint32_t>(expected.played_character_id))
    return Fail(output, "release_material_paused_pair_unavailable");
  try {
    bridge::PlayerPrisonerFrameV1 before{}, after{};
    if (!access.capture_frame(access.context, before) || before != expected)
      return Fail(output, "release_material_frame_changed");
    Sample first{}, second{};
    const auto actor = static_cast<std::uint32_t>(expected.played_character_id);
    if (!ReadSample(bindings, access, actor, target_id, first) ||
        !ReadSample(bindings, access, actor, target_id, second) || first != second)
      return Fail(output, "release_material_source_unavailable_or_changed");
    if (!access.capture_frame(access.context, after) || after != expected)
      return Fail(output, "release_material_frame_changed");
    output.available = true;
    output.target_opinion_of_actor = second.opinion;
    output.modifier_observed = true;
    output.modifier_present = second.present;
    output.modifier_value = second.value;
    return true;
  } catch (...) { return Fail(output, "release_material_internal_error"); }
}

std::string SerializePrisonerReleaseMaterialOpinion12004(
    const PrisonerReleaseMaterialOpinion12004 &row) {
  std::string out = "{\"schema\":\"xar.ck3.prisoner-release-material-opinion-12004-v1\","
      "\"build_version\":" + Quote(kGameVersion) + ",\"executable_sha256\":" +
      Quote(kExecutableSha256) + ",\"available\":" + Boolean(row.available) +
      ",\"unavailable_reason\":" + Quote(row.unavailable_reason) +
      ",\"snapshot_revision\":" + std::to_string(row.frame.native_revision) +
      ",\"date_raw\":" + std::to_string(row.frame.date_raw) +
      ",\"actor_character_id\":" + std::to_string(row.frame.played_character_id) +
      ",\"target_character_id\":" + std::to_string(row.target_character_id) +
      ",\"target_opinion_of_actor\":";
  out += row.target_opinion_of_actor ? std::to_string(*row.target_opinion_of_actor) : "null";
  out += ",\"released_from_prison\":{\"observed\":";
  out += Boolean(row.modifier_observed);
  out += ",\"present\":";
  out += Boolean(row.modifier_present);
  out += ",\"value\":";
  out += row.modifier_value ? std::to_string(*row.modifier_value) : "null";
  return out + "},\"release_causation_observed\":false,\"custody_change_observed\":false}";
}

} // namespace xar::ck3_12004
