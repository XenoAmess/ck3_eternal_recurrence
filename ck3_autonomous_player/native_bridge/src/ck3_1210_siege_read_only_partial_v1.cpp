#include "xar_bridge/ck3_1210_siege_read_only_partial_v1.hpp"
#include <cstring>
#include <limits>
#include <type_traits>
#include <vector>

namespace xar::ck3_1210::siege_read_only_partial_v1 {
namespace {
constexpr std::uintptr_t kGameSlot = 0x68B1D58, kJominiSlot = 0x68B3800;
constexpr std::uintptr_t kCharactersSlot = 0x68A8628, kSiegeRegistrySlot = 0x6A67198;
constexpr std::uintptr_t kManagerVt = 0x4E4B000, kRegistryVt = 0x4E4AE18;
constexpr std::uintptr_t kSiegeVt = 0x4E4AF40;
constexpr std::uint32_t kCharTag = 0x43686172, kProvTag = 0x50726F76, kSigeTag = 0x53696765;
bool ValidRequest(const Request &r) noexcept {
  return r.frame.native_revision != 0 && r.frame.query_sequence != 0 &&
      r.frame.played_character_id != -1 && r.province_id > 0 &&
      r.province_id < kProvinceTableBound;
}
bool Selection(const ProvinceSelection &p, const Request &r) noexcept {
  return p.province_id == r.province_id && p.validated_province_count > 1 &&
      p.validated_province_count <= kProvinceTableBound &&
      p.province_id < p.validated_province_count;
}
struct Pass {
  const Bindings &bindings;
  const Request &request;
  ReadAccess access;
  std::vector<std::uint64_t> words;
  Target target = UnknownTarget{};
  bool Add(std::uint64_t value) {
    if (words.size() == 512) return false;
    words.push_back(value); return true;
  }
  template <class T> bool Read(std::uintptr_t base, std::size_t off, T &v) {
    static_assert(std::is_trivially_copyable_v<T> && sizeof(T) <= 8);
    constexpr auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
    if (!base || off > maximum - base || sizeof(T) - 1 > maximum - (base + off) ||
        !access.copy(access.context, reinterpret_cast<const void *>(base + off), &v, sizeof v)) return false;
    std::uint64_t value{}; std::memcpy(&value, &v, sizeof v);
    return Add(base + off) && Add(sizeof v) && Add(value);
  }
  bool Frame(FrameEvidence &e) {
    if (!access.read_frame(access.context, e) || e.source != request.frame ||
        !e.main_scope_held || !e.map_ready || !e.paused || !e.has_live_played_character ||
        !e.scope_epoch || !e.game_state || !e.jomini_state || !e.played_character ||
        e.local_player_id == -1) return false;
    return Add(e.source.native_revision) && Add(e.source.query_sequence) &&
        Add(static_cast<std::uint32_t>(e.source.game_date_raw)) &&
        Add(static_cast<std::uint32_t>(e.source.played_character_id)) &&
        Add(e.scope_epoch) && Add(e.game_state) && Add(e.jomini_state) &&
        Add(e.played_character) && Add(static_cast<std::uint32_t>(e.local_player_id));
  }
  bool Actor(const FrameEvidence &e) {
    std::uintptr_t store{}, slots{}, character{}, death{};
    std::int32_t capacity{}, id{}; std::uint32_t tag{};
    if (!Read(bindings.image_base, kCharactersSlot, store) ||
        !Read(store, 0x20, slots) || !Read(store, 0x2C, capacity) ||
        capacity <= 0 || capacity > kProvinceTableBound || !slots) return false;
    const auto index = static_cast<std::uint32_t>(request.frame.played_character_id) & 0xFFFFFFU;
    return index < static_cast<std::uint32_t>(capacity) &&
        Read(slots, std::size_t(index) * 0x10 + 8, character) &&
        character == e.played_character && Read(character, 0x18, id) &&
        Read(character, 0x1C, tag) && Read(character, 0x1D0, death) &&
        id == request.frame.played_character_id && tag == kCharTag && !death;
  }
  bool ReadTarget(std::uintptr_t data) {
    std::uintptr_t array{}, province{};
    std::int32_t count{}, province_id{}; std::uint32_t province_tag{};
    if (!Read(data, 0x4140, array) || !Read(data, 0x414C, count) ||
        count <= request.province_id || count > kProvinceTableBound || !array ||
        !Read(array, std::size_t(request.province_id) * 8, province) ||
        !Read(province, 0x10, province_id) || province_id != request.province_id ||
        !Read(province, 0xB24, province_tag) || province_tag != kProvTag) return false;
    std::uintptr_t manager_type{}, owned{}, registry{}, registry_type{}, slots{};
    std::int32_t capacity{}, reference{};
    if (!Read(data, 0x3F130, manager_type) || manager_type != bindings.image_base + kManagerVt ||
        !Read(data, 0x3F158, owned) || !Read(bindings.image_base, kSiegeRegistrySlot, registry) ||
        !registry || registry != owned || !Read(registry, 0, registry_type) ||
        registry_type != bindings.image_base + kRegistryVt ||
        !Read(registry, 0x20, slots) || !Read(registry, 0x2C, capacity) ||
        capacity < 0 || capacity > kProvinceTableBound || (capacity && !slots) ||
        !Read(province, 0xA20, reference)) return false;
    const ProvinceSelection selection{province_id, count};
    if (reference == -1) target = AbsentTarget{selection};
    else {
      const auto index = static_cast<std::uint32_t>(reference) & 0xFFFFFFU;
      std::uintptr_t siege{}, type{}, backlink{}; std::int32_t id{};
      std::uint32_t tag{}; std::int64_t work{};
      if (index >= static_cast<std::uint32_t>(capacity) ||
          !Read(slots, std::size_t(index) * 0x10 + 8, siege) || !siege ||
          !Read(siege, 0, type) || type != bindings.image_base + kSiegeVt ||
          !Read(siege, 8, id) || id != reference ||
          !Read(siege, 0xC, tag) || tag != kSigeTag ||
          !Read(siege, 0x210, backlink) || backlink != province ||
          !Read(siege, 0x3F0, work) || work < 0) return false;
      target = IdentityOnlyTarget{selection, reference, work};
    }
    return true;
  }
  bool Capture() {
    FrameEvidence before{}, after{};
    if (!Frame(before)) return false;
    std::uintptr_t game{}, jomini{}, data{};
    std::int32_t date{}, speed{}; std::uint8_t paused{};
    if (!Read(bindings.image_base, kGameSlot, game) || game != before.game_state ||
        !Read(bindings.image_base, kJominiSlot, jomini) || jomini != before.jomini_state ||
        !Read(game, 8, date) || date != request.frame.game_date_raw ||
        !Read(game, 0x70, speed) || !Read(jomini, 0x20, paused) || paused != 1 ||
        !Read(game, 0xA0, data) || !data || !Actor(before)) return false;
    if (!ReadTarget(data)) target = UnknownTarget{};
    return Frame(after) && before == after;
  }
};
} // namespace

Bindings BindImage(std::uintptr_t base, std::string_view sha) noexcept {
  constexpr auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (!base || base > maximum - kSiegeRegistrySlot - 7 || sha != kExecutableSha256) return {};
  return {true, base};
}
bool CopyTarget(const Bindings &b, const Request &r, Captured &out, ReadAccess access) noexcept {
  const Request expected = r;
  const Bindings admitted = b;
  out = {}; out.request = expected;
  if (!admitted.exact_build_admitted || !admitted.image_base || !ValidRequest(expected)) return false;
  constexpr auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (admitted.image_base > maximum - kSiegeRegistrySlot - 7) return false;
  out.source_identity_admitted = true;
  if (!access.copy || !access.read_frame) return false;
  try {
    Pass first{admitted, expected, access, {}, UnknownTarget{}},
        second{admitted, expected, access, {}, UnknownTarget{}};
    if (!first.Capture() || !second.Capture() || first.words != second.words) return false;
    out.target = second.target;
    out.source_frame_verified = true;
    return true;
  } catch (...) { out.target = UnknownTarget{}; return false; }
}
bool AppendJson(const Captured &v, std::string &output) noexcept {
  if (!v.source_identity_admitted || !v.source_frame_verified || !ValidRequest(v.request)) return false;
  if (const auto *absent = std::get_if<AbsentTarget>(&v.target)) {
    if (!Selection(absent->province, v.request)) return false;
  } else if (const auto *identity = std::get_if<IdentityOnlyTarget>(&v.target)) {
    if (!Selection(identity->province, v.request) || identity->siege_full_id == -1 || identity->current_work_raw < 0)
      return false;
  } else if (!std::holds_alternative<UnknownTarget>(v.target)) return false;
  try {
    std::string body = "{\"schema\":\"";
    body += kSchema;
    body += "\",\"source_frame\":{\"game_version\":\"1.21.0\",\"steam_build_id\":\"26622941\",\"executable_sha256\":\"";
    body += kExecutableSha256;
    body += "\",\"native_revision\":\"" + std::to_string(v.request.frame.native_revision);
    body += "\",\"game_date_raw\":" + std::to_string(v.request.frame.game_date_raw);
    body += ",\"query_sequence\":\"" + std::to_string(v.request.frame.query_sequence);
    body += "\",\"played_character_id\":" + std::to_string(v.request.frame.played_character_id);
    body += "},\"requested_province_id\":" + std::to_string(v.request.province_id);
    body += ",\"partial\":true,\"full_snapshot_available\":false,\"live_qualified\":false,\"target\":{";
    if (const auto *absent = std::get_if<AbsentTarget>(&v.target)) {
      body += "\"state\":\"ABSENT\",\"province_id\":" + std::to_string(absent->province.province_id);
      body += ",\"validated_province_count\":" + std::to_string(absent->province.validated_province_count);
    } else if (const auto *identity = std::get_if<IdentityOnlyTarget>(&v.target)) {
      body += "\"state\":\"IDENTITY_ONLY\",\"province_id\":" + std::to_string(identity->province.province_id);
      body += ",\"validated_province_count\":" + std::to_string(identity->province.validated_province_count);
      body += ",\"siege_full_id\":" + std::to_string(identity->siege_full_id);
      body += ",\"current_work_raw\":\"" + std::to_string(identity->current_work_raw) + "\"";
    } else body += "\"state\":\"UNKNOWN\"";
    body += "},\"holder\":{\"state\":\"UNAVAILABLE\",\"reason\":\"holder_getter_unclosed\"}";
    body += ",\"subrealm\":{\"state\":\"UNAVAILABLE\",\"reason\":\"subrealm_getter_unclosed\"}";
    body += ",\"progress\":{\"state\":\"UNAVAILABLE\",\"reason\":\"progress_dependency_graph_unclosed\"}}";
    output += body;
    return true;
  } catch (...) { return false; }
}
} // namespace xar::ck3_1210::siege_read_only_partial_v1
