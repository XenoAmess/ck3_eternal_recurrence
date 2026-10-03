#include "xar_bridge/ck3_12003_confession_rite_permission.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"

#include <cstring>

namespace xar::ck3_12003::religion::confession_permission {
namespace {
namespace current_religion = ck3_12002::religion;
namespace tenet_rows = ck3_12002::religion::doctrine12002;

template <typename T> T Load(const void *source, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(source) + offset, sizeof(value));
  return value;
}

bool Fail(Terms &out, const char *reason) {
  out.available = false;
  out.unavailable_reason = reason;
  out.current_rite_status.reset();
  out.has_at_least_permitted.reset();
  return false;
}

bool ReadOnce(const Bindings &b, const current_religion::Bindings &religion,
    void *actor, const CurrentContext &current, Terms &out) {
  if (!b.enabled || b.tenet_database_global == nullptr ||
      b.source_main_rite_status == nullptr || !religion.enabled ||
      religion.character_rite == nullptr)
    return Fail(out, "bindings_unavailable");
  if (!current.available) return Fail(out, "current_context_unavailable");
  if (actor == nullptr || current.played_character_id <= 0 ||
      Load<std::int32_t>(actor, 0x18) != current.played_character_id)
    return Fail(out, "played_character_mismatch");
  if (!current.rite_id.has_value() ||
      Load<std::uint32_t>(actor, current_religion::kCharacterRiteIdOffset) != *current.rite_id)
    return Fail(out, "rite_unavailable");
  auto *rite = religion.character_rite(actor);
  if (rite == nullptr ||
      Load<std::uint32_t>(rite, current_religion::kReferenceIdentityOffset) != *current.rite_id)
    return Fail(out, "rite_unavailable");

  const auto *database = *b.tenet_database_global;
  if (database == nullptr) return Fail(out, "tenet_database_unavailable");
  // The existing TenetSources producer's loaded definition array, independent
  // of whether an actual Rite creation draft exists.
  const auto *array = static_cast<const std::byte *>(database) + 0xEF0;
  const auto *definitions = Load<const std::byte *>(array);
  const auto count = Load<std::int32_t>(array, 0xC);
  const auto capacity = Load<std::int32_t>(array, 8);
  if (count < 0 || count > 8192 || count > capacity ||
      (count != 0 && definitions == nullptr))
    return Fail(out, "tenet_definitions_unavailable");

  const void *confession = nullptr;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto *definition = Load<const void *>(definitions,
        static_cast<std::size_t>(i) * sizeof(void *));
    std::string key;
    if (!tenet_rows::CopyTenetDefinitionKey12002(definition, key))
      return Fail(out, "tenet_definition_key_unavailable");
    if (key == kTenetKey) {
      confession = definition;
      break;
    }
  }
  if (confession == nullptr) return Fail(out, "tenet_definition_unavailable");
  // This existing member names the draft's receiver, but binds the same
  // GetTenetStatus(Rite*, definition) used by TenetRows. Here the receiver is
  // explicitly the actual player's current Rite, not the Faith main Rite.
  const auto state = b.source_main_rite_status(rite, confession);
  if (state > 4) return Fail(out, "tenet_state_unavailable");

  if (*b.tenet_database_global != database ||
      Load<const std::byte *>(array) != definitions ||
      Load<std::int32_t>(array, 0xC) != count ||
      Load<std::int32_t>(actor, 0x18) != current.played_character_id ||
      Load<std::uint32_t>(actor, current_religion::kCharacterRiteIdOffset) != *current.rite_id ||
      Load<std::uint32_t>(rite, current_religion::kReferenceIdentityOffset) != *current.rite_id)
    return Fail(out, "state_changed");
  out.current_rite_status = state;
  out.has_at_least_permitted = state == 3 || state == 4;
  out.available = true;
  out.unavailable_reason.clear();
  return true;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      out += '\\';
      out += static_cast<char>(byte);
    } else if (byte < 0x20) {
      out += "\\u00";
      out += hex[byte >> 4];
      out += hex[byte & 0x0F];
    } else {
      out += static_cast<char>(byte);
    }
  }
  return out + '"';
}

template <typename T> std::string Number(const std::optional<T> &value) {
  return value.has_value() ? std::to_string(*value) : "null";
}
std::string Bool(const std::optional<bool> &value) {
  return value.has_value() ? (*value ? "true" : "false") : "null";
}
} // namespace

bool ReadPlayerConfessionRitePermission12003(const Bindings &b,
    const current_religion::Bindings &religion, void *actor,
    const CurrentContext &current, Terms &out) noexcept {
  out = {};
  out.capture_epoch = current.capture_epoch;
  out.date_raw = current.date_raw;
  out.played_character_id = current.played_character_id;
  out.rite_id = current.rite_id;
  try {
#if defined(_WIN32) && defined(_MSC_VER)
    auto guarded = [](const Bindings &bindings,
        const current_religion::Bindings &r, void *actual_actor,
        const CurrentContext &context, Terms &terms) -> bool {
      __try { return ReadOnce(bindings, r, actual_actor, context, terms); }
      __except (1) { return Fail(terms, "tenet_native_read_unavailable"); }
    };
    return guarded(b, religion, actor, current, out);
#else
    return ReadOnce(b, religion, actor, current, out);
#endif
  } catch (...) {
    return Fail(out, "tenet_native_read_unavailable");
  }
}

std::string SerializePlayerConfessionRitePermission12003(const Terms &t) {
  return std::string{"{\"schema\":"} + Quote(kSchema) +
      ",\"read_only\":true,\"available\":" + (t.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (t.available ? std::string{"null"} : Quote(t.unavailable_reason)) +
      ",\"capture_epoch\":" + std::to_string(t.capture_epoch) +
      ",\"date_raw\":" + std::to_string(t.date_raw) +
      ",\"played_character_id\":" + std::to_string(t.played_character_id) +
      ",\"rite_id\":" + Number(t.rite_id) +
      ",\"tenet_key\":" + Quote(kTenetKey) +
      ",\"current_rite_status\":" + (t.available ? Number(t.current_rite_status) : "null") +
      ",\"has_at_least_permitted\":" + (t.available ? Bool(t.has_at_least_permitted) : "null") + "}";
}

} // namespace xar::ck3_12003::religion::confession_permission
