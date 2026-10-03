#include "xar_bridge/ck3_12003_repentance_recovery_inputs.hpp"

#include <windows.h>
#include <array>
#include <bit>
#include <cstring>
#include <sstream>

namespace xar::ck3_12003::religion::repentance_recovery_inputs {
namespace {
constexpr std::string_view kExactSha = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
template<typename T> bool Read(const void* p, std::size_t offset, T& value) noexcept {
  SIZE_T copied = 0;
  return p && ReadProcessMemory(GetCurrentProcess(),
      static_cast<const std::byte*>(p) + offset, &value, sizeof(value), &copied) && copied == sizeof(value);
}
template<typename F, typename R, typename... A> bool Call(F fn, R& result, A... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try { result = fn(args...); return true; }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  result = fn(args...); return true;
#endif
}
void Known(BoolObservation& value, bool actual) noexcept {
  value.available = true; value.reason = "none"; value.value = actual;
}
bool Matches(const void* actor, std::int32_t expected) noexcept {
  std::int32_t id = -1; std::uint32_t tag = 0;
  return expected >= 0 && Read(actor, 0x18, id) && id == expected &&
      Read(actor, 0x1C, tag) && tag == 0x43686172;
}
void PopeFlag(const Bindings& b, void* actor, BoolObservation& out) noexcept {
  out.reason = "flag_pool_unavailable";
  const void* atom_rows = nullptr; std::int32_t atom_count = -1;
  if (!b.existing_atom || !Read(b.atom_pool, 0x10, atom_rows) || !atom_rows ||
      !Read(b.atom_pool, 0x1C, atom_count) || atom_count < 0) return;
  constexpr char key[] = "pope_excom";
  NativeStringView view{key, static_cast<std::int32_t>(sizeof(key)-1), 1, {}};
  std::uint32_t atom = 0xFFFFFFFFU; std::uint32_t* returned = nullptr;
  if (!Call(b.existing_atom, returned, b.atom_pool, &atom, &view) || returned != &atom) return;
  std::uint8_t dummy = 0; void* script_data = nullptr;
  out.reason = "character_flag_data_unavailable";
  if (!Read(actor, 0x1A5, dummy) || !Read(actor, 0x1B0, script_data)) return;
  if (atom == 0xFFFFFFFFU || dummy || !script_data) { Known(out, false); return; }
  std::int32_t index = -2;
  if (!Read(script_data, 0, index) || index < -1) return;
  if (index == -1) { Known(out, false); return; }
  void* flags = nullptr;
  out.reason = "flag_collection_unavailable";
  if (!Call(b.character_flag_collection, flags, script_data) || !flags) return;
  const std::byte* rows = nullptr; std::int32_t count = -1;
  if (!Read(flags, 0x10, rows) || !Read(flags, 0x1C, count) || count < 0 || (count && !rows)) return;
  for (std::int32_t i=0; i<count; ++i) {
    std::uint32_t actual = 0xFFFFFFFFU;
    if (!Read(rows, static_cast<std::size_t>(i)*0x20 + 0x08, actual)) return;
    if (actual == atom) { Known(out, true); return; }
  }
  Known(out, false);
}
bool KeyMatches(const void* definition, std::string_view key) noexcept {
  std::uint64_t size = 0, capacity = 0;
  const auto* native = static_cast<const std::byte*>(definition) + 0x18;
  if (!Read(native, 0x10, size) || !Read(native, 0x18, capacity) || size != key.size() || capacity < size) return false;
  const void* chars = native;
  if (capacity >= 0x10 && !Read(native, 0, chars)) return false;
  std::array<char, 64> actual{}; SIZE_T copied = 0;
  return size <= actual.size() && chars &&
      ReadProcessMemory(GetCurrentProcess(), chars, actual.data(), static_cast<SIZE_T>(size), &copied) &&
      copied == size && std::memcmp(actual.data(), key.data(), static_cast<std::size_t>(size)) == 0;
}
std::int64_t DayCounter(std::int32_t raw) noexcept {
  return (static_cast<std::int64_t>(raw) - 0x29C55C0) / 24;
}
void Modifier(const Bindings& b, void* actor, std::string_view key, std::int32_t date,
    ModifierObservation& out) noexcept {
  out.reason = "modifier_definition_unavailable";
  void* database = nullptr; void* fallback = nullptr;
  if (!Call(b.modifier_database, database) || !database || !Read(b.modifier_fallback_slot, 0, fallback)) return;
  std::uint32_t hash = 0;
  if (!Call(b.stable_key_hash, hash, database, key.data(), static_cast<std::uint32_t>(key.size()))) return;
  void* definition = nullptr;
  if (!Call(b.modifier_lookup, definition, database, std::bit_cast<std::int32_t>(hash)) ||
      !definition || definition == fallback || !KeyMatches(definition, key)) return;
  out.reason = "modifier_rows_unavailable";
  void* script = nullptr;
  if (!Read(actor, 0x1B0, script)) return;
  const std::byte* rows = nullptr; std::int32_t count = 0;
  if (script && (!Read(script, 0x188, rows) || !Read(script, 0x194, count) || count < 0 || (count && !rows))) return;
  for (std::int32_t i=0; i<count; ++i) {
    const auto offset = static_cast<std::size_t>(i)*0x48;
    const void* actual = nullptr;
    if (!Read(rows, offset, actual)) return;
    if (actual == definition) {
      std::int32_t expiry = 0;
      if (!Read(rows, offset + 0x08, expiry)) return;
      out.present = true; out.expiry_date_raw = expiry;
      out.remaining_calendar_days = DayCounter(expiry) - DayCounter(date);
      out.available = true; out.reason = "none"; return;
    }
  }
  out.present = false; out.available = true; out.reason = "none";
}
void ClericalHeld(const Bindings& b, std::int32_t actor, BoolObservation& out) noexcept {
  out.reason = "title_storage_unavailable";
  void* storage = nullptr; const std::byte* rows = nullptr; std::uint32_t count = 0;
  if (!Read(b.title_storage_slot, 0, storage) || !Read(storage, 0x20, rows) ||
      !Read(storage, 0x2C, count) || (count && !rows)) return;
  bool any = false;
  for (std::uint32_t i=0; i<count; ++i) {
    const void* title = nullptr;
    if (!Read(rows, static_cast<std::size_t>(i)*0x10 + 8, title)) return;
    if (!title) continue;
    std::int32_t id = -1, holder = -1, clerical_type = 0;
    out.reason = "held_title_unavailable";
    if (!Read(title, 0x10, id)) return;
    if (id == -1 || (static_cast<std::uint32_t>(id)&0xFFFFFFU) != i) continue;
    if (!Read(title, 0x128, holder)) return;
    if (holder != actor) continue;
    if (!Read(title, 0x328, clerical_type)) return;
    any = any || clerical_type == 4;
  }
  Known(out, any);
}
template<typename T> void Number(std::ostringstream& stream, const std::optional<T>& value) {
  if (value) stream << *value; else stream << "null";
}
void Boolean(std::ostringstream& stream, const std::optional<bool>& value) {
  if (value) stream << (*value ? "true" : "false"); else stream << "null";
}
void Serialize(std::ostringstream& stream, const BoolObservation& out) {
  stream << "{\"available\":" << (out.available ? "true" : "false") << ",\"reason\":\"" << out.reason << "\",\"value\":";
  Boolean(stream, out.value); stream << '}';
}
void Serialize(std::ostringstream& stream, const NumberObservation& out) {
  stream << "{\"available\":" << (out.available ? "true" : "false") << ",\"reason\":\"" << out.reason << "\",\"value\":";
  Number(stream, out.value); stream << '}';
}
void Serialize(std::ostringstream& stream, const ModifierObservation& out) {
  stream << "{\"available\":" << (out.available ? "true" : "false") << ",\"reason\":\"" << out.reason << "\",\"present\":";
  Boolean(stream, out.present); stream << ",\"expiry_date_raw\":"; Number(stream, out.expiry_date_raw);
  stream << ",\"remaining_calendar_days\":"; Number(stream, out.remaining_calendar_days); stream << '}';
}
} // namespace
Bindings BindPlayerRepentanceRecoveryInputsImage12003(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExactSha) return b;
  b.enabled = true;
  b.existing_atom = reinterpret_cast<ExistingAtomLookup>(base + 0x3F8A3A0);
  b.atom_pool = reinterpret_cast<void*>(base + 0x5DC1390);
  b.character_flag_collection = reinterpret_cast<ObjectGetter>(base + 0x1D67200);
  b.highest_held_tier = reinterpret_cast<HighestHeldTier>(base + 0x28AC6B0);
  b.title_storage_slot = reinterpret_cast<void**>(base + 0x5D1DAF8);
  b.modifier_database = reinterpret_cast<ModifierDatabase>(base + 0x8FD4E0);
  b.stable_key_hash = reinterpret_cast<StableKeyHash>(base + 0x3F7E240);
  b.modifier_lookup = reinterpret_cast<ModifierLookup>(base + 0xAB8D20);
  b.modifier_fallback_slot = reinterpret_cast<void**>(base + 0x5D1E0B0);
  return b;
}
bool ReadPlayerRepentanceRecoveryInputs12003(const Bindings& b, void* actor,
    std::int32_t expected, std::int32_t date, std::uint64_t epoch, Context& out) noexcept {
  out = {}; out.played_character_id = expected; out.date_raw = date; out.capture_epoch = epoch;
  if (!b.enabled || !Matches(actor, expected)) return false;
  PopeFlag(b, actor, out.pope_excom);
  Modifier(b, actor, "recent_excommunication", date, out.recent_excommunication);
  Modifier(b, actor, "promised_pilgrimage_to_clergy_modifier", date, out.promised_pilgrimage_to_clergy);
  std::int32_t tier = -1;
  out.highest_held_title_tier.reason = "highest_held_tier_unavailable";
  if (Call(b.highest_held_tier, tier, actor)) {
    out.highest_held_title_tier = {true, "none", tier};
  }
  ClericalHeld(b, expected, out.any_held_title_has_clerical_region);
  out.available = out.pope_excom.available && out.recent_excommunication.available &&
      out.promised_pilgrimage_to_clergy.available && out.highest_held_title_tier.available &&
      out.any_held_title_has_clerical_region.available;
  return out.available;
}
std::string SerializePlayerRepentanceRecoveryInputs12003(const Context& out) {
  std::ostringstream stream;
  stream << "{\"schema\":\"ck3_12003_repentance_recovery_inputs_v1\",\"available\":" << (out.available ? "true" : "false")
      << ",\"played_character_id\":" << out.played_character_id << ",\"date_raw\":" << out.date_raw << ",\"capture_epoch\":" << out.capture_epoch
      << ",\"pope_excom\":"; Serialize(stream, out.pope_excom);
  stream << ",\"recent_excommunication\":"; Serialize(stream, out.recent_excommunication);
  stream << ",\"promised_pilgrimage_to_clergy\":"; Serialize(stream, out.promised_pilgrimage_to_clergy);
  stream << ",\"highest_held_title_tier\":"; Serialize(stream, out.highest_held_title_tier);
  stream << ",\"any_held_title_has_clerical_region\":"; Serialize(stream, out.any_held_title_has_clerical_region);
  stream << ",\"clerical_observation_source\":\"complete_loaded_title_holder_scan\",\"modifier_expiry_unit\":\"native_date_raw\",\"read_only\":true}";
  return stream.str();
}
} // namespace xar::ck3_12003::religion::repentance_recovery_inputs
