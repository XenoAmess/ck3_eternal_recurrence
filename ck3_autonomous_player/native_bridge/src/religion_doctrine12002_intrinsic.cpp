#include "xar_bridge/religion_doctrine12002_intrinsic.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template<class T> T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t id) {
  return object && Load<std::uint32_t>(object, kReferenceIdentityOffset) == id;
}
bool CopyKey(const void *native_string, std::string &output) {
  const auto size = Load<std::uint64_t>(native_string, 0x10);
  const auto capacity = Load<std::uint64_t>(native_string, 0x18);
  if (size > capacity || size > 4096) return false;
  const auto *data = capacity < 16 ? static_cast<const char *>(native_string)
                                 : Load<const char *>(native_string, 0);
  if (!data && size) return false;
  output = size ? std::string(data, static_cast<std::size_t>(size)) : std::string{};
  return !output.empty();
}
bool Fail(FaithMainRiteDoctrines &out, const char *reason) {
  out.unavailable_reason = reason;
  return false;
}
bool ReadOnce(const religion::Bindings &b, std::uint64_t epoch,
              FaithMainRiteDoctrines &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Fail(out, "played_character_unavailable");
  if (!frame.clock.paused) return Fail(out, "frame_not_paused");
  auto *actor = ResolveCoreCharacter(b.core, frame.played_character_id);
  if (!actor) return Fail(out, "played_character_unavailable");
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  const auto actor_rite = Load<std::uint32_t>(actor, kCharacterRiteIdOffset);
  if (actor_rite != kAbsentReference) {
    auto *rite = b.character_rite(actor);
    if (!Matches(rite, actor_rite)) return Fail(out, "rite_unavailable");
    out.rite_id = actor_rite;
    const auto faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
    if (faith_id != kAbsentReference) {
      auto *faith = b.rite_faith(rite);
      if (!Matches(faith, faith_id) || b.character_faith(actor) != faith)
        return Fail(out, "faith_unavailable");
      out.faith_id = faith_id;
      const auto main_id = Load<std::uint32_t>(faith, kFaithMainRiteIdOffset);
      if (main_id != kAbsentReference) {
        auto *main = b.faith_main_rite(faith);
        if (!Matches(main, main_id)) return Fail(out, "main_rite_unavailable");
        out.main_rite_id = main_id;
        const auto count = Load<std::int32_t>(main, kMainRiteDoctrineCountOffset);
        const auto capacity = Load<std::int32_t>(main, kMainRiteDoctrineArrayOffset + 8);
        auto **data = Load<const void **>(main, kMainRiteDoctrineArrayOffset);
        if (count < 0 || count > capacity || count > 4096 || (count && !data))
          return Fail(out, "doctrine_collection_unavailable");
        for (std::int32_t i = 0; i < count; ++i) {
          DoctrineRow row{};
          if (!CopyDoctrineDefinition12002(data[i], row))
            return Fail(out, "doctrine_definition_unavailable");
          out.rows.push_back(std::move(row));
        }
      }
    }
  }
  out.available = true;
  out.unavailable_reason.clear();
  return true;
}
bool Same(const FaithMainRiteDoctrines &a, const FaithMainRiteDoctrines &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.rite_id == b.rite_id && a.faith_id == b.faith_id &&
      a.main_rite_id == b.main_rite_id && a.rows == b.rows;
}
std::string Quote(std::string_view v) {
  std::string result = "\"";
  constexpr char hex[] = "0123456789abcdef";
  for (const unsigned char c : v) {
    if (c == '\\' || c == '"') { result += '\\'; result += static_cast<char>(c); }
    else if (c < 32) {
      result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15];
    } else result += static_cast<char>(c);
  }
  return result + '"';
}
std::string Id(const std::optional<std::uint32_t> &v) {
  return v ? std::to_string(*v) : "null";
}
} // namespace

bool CopyDoctrineDefinition12002(const void *definition, DoctrineRow &out) {
  out = {};
  if (!definition) return false;
  const auto *group = Load<const void *>(definition, kDoctrineGroupPointerOffset);
  return group && CopyKey(static_cast<const std::byte *>(definition) + kDoctrineStableKeyOffset,
                         out.doctrine_key) &&
      CopyKey(static_cast<const std::byte *>(group) + kDoctrineGroupStableKeyOffset,
              out.group_key);
}

bool ReadPlayedFaithMainRiteDoctrines12002(const religion::Bindings &b,
    std::uint64_t epoch, FaithMainRiteDoctrines &out) noexcept {
  out = {};
  out.capture_epoch = epoch;
  if (!b.enabled || !b.core.enabled || !b.character_rite || !b.character_faith ||
      !b.rite_faith || !b.faith_main_rite) return false;
  try {
    FaithMainRiteDoctrines a{}, z{};
    if (!ReadOnce(b, epoch, a)) { out.unavailable_reason = a.unavailable_reason; return false; }
    if (!ReadOnce(b, epoch, z)) { out.unavailable_reason = z.unavailable_reason; return false; }
    if (!Same(a, z)) return Fail(out, "state_changed");
    out = std::move(a);
    return true;
  } catch (...) { return Fail(out, "doctrine_copy_failed"); }
}

std::string SerializeFaithMainRiteDoctrines12002(const FaithMainRiteDoctrines &v) {
  std::string rows = "[";
  for (const auto &row : v.rows) {
    if (rows.size() > 1) rows += ',';
    rows += "{\"doctrine_key\":" + Quote(row.doctrine_key) +
        ",\"group_key\":" + Quote(row.group_key) + ",\"source\":" + Quote(row.source) + '}';
  }
  rows += ']';
  return "{\"schema\":\"ck3_12002_faith_main_rite_doctrines_v1\",\"available\":" +
      std::string(v.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (v.available ? "null" : Quote(v.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(v.capture_epoch) +
      ",\"date_raw\":" + std::to_string(v.date_raw) +
      ",\"played_character_id\":" + std::to_string(v.played_character_id) +
      ",\"rite_id\":" + Id(v.rite_id) + ",\"faith_id\":" + Id(v.faith_id) +
      ",\"main_rite_id\":" + Id(v.main_rite_id) + ",\"rows\":" + rows + '}';
}
} // namespace xar::ck3_12002::religion::doctrine12002
