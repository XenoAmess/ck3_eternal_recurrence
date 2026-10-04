#include "xar_bridge/ck3_12003_mercenary_composition.hpp"

#include <algorithm>
#include <cstddef>
#include <cstring>
#include <limits>
#include <sstream>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::mercenary {
namespace {
template <typename T>
bool Read(const void *object, std::size_t offset, T &value) noexcept {
  if (object == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool ReadHolder(CompanyHolder getter, void *company, void *&holder) noexcept {
  if (getter == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    holder = getter(company);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void *ResolvePersistent(const CompositionBindings &b, std::uint32_t id) noexcept {
  if (id == UINT32_MAX) return nullptr;
  void *storage = nullptr, *fallback = nullptr;
  const void *slots = nullptr;
  std::int32_t capacity = -1;
  if (!Read(b.persistent_regiment_storage_slot, 0, storage) || storage == nullptr ||
      !Read(b.persistent_regiment_fallback_slot, 0, fallback) ||
      !Read(storage, 0x20, slots) || slots == nullptr ||
      !Read(storage, 0x2C, capacity) || capacity < 0 ||
      (id & 0xFFFFFFU) >= static_cast<std::uint32_t>(capacity)) return nullptr;
  void *regiment = nullptr;
  std::uint32_t actual = UINT32_MAX, tag = 0;
  if (!Read(slots, static_cast<std::size_t>(id & 0xFFFFFFU)*0x10+8, regiment) ||
      regiment == nullptr || regiment == fallback ||
      !Read(regiment, 0x10, actual) || actual != id ||
      !Read(regiment, 0x14, tag) || tag != 0x52656769U) return nullptr;
  return regiment;
}

bool ReadTypeKey(const void *type, std::string &key) {
  const auto *text = static_cast<const std::byte *>(type) + 0x18;
  std::size_t size = 0, capacity = 0;
  if (!Read(text, 0x10, size) || !Read(text, 0x18, capacity) ||
      size == 0 || size > capacity) return false;
  const char *data = reinterpret_cast<const char *>(text);
  if (capacity >= 16 && (!Read(text, 0, data) || data == nullptr)) return false;
  key.clear();
  key.reserve(size);
  for (std::size_t index = 0; index < size; ++index) {
    char value = 0;
    if (!Read(data, index, value)) return false;
    key.push_back(value);
  }
  return true;
}

bool ReadRegiment(void *regiment, CompanyRegimentComposition &row,
                  std::string &reason) {
  reason = "mercenary_regiment_counts_unavailable";
  if (!Read(regiment, 0x128, row.maximum_soldiers) || row.maximum_soldiers < 0)
    return false;
  std::int64_t current = row.maximum_soldiers;
  // Exact 2625720 current-count branch, including native state3/current0=max.
  // A company-wide native soldier count also includes the holder's knights.
  for (std::size_t index = 0; index < 7; ++index) {
    const std::size_t chunk = 0x18 + index*0x24;
    std::int32_t maximum = 0, raw_current = 0, state = 0;
    if (!Read(regiment, chunk, maximum) || maximum < 0) return false;
    if (maximum == 0) continue;
    if (!Read(regiment, chunk+4, raw_current) || raw_current < 0 ||
        !Read(regiment, chunk+0x18, state)) return false;
    const std::int32_t effective = state == 3 && raw_current == 0
        ? maximum : raw_current;
    current += static_cast<std::int64_t>(effective)-maximum;
  }
  if (current < 0 || current > std::numeric_limits<std::int32_t>::max()) return false;
  row.current_soldiers = static_cast<std::int32_t>(current);

  reason = "mercenary_regiment_type_unavailable";
  const void *type = nullptr;
  std::uint32_t tag = 0;
  if (!Read(regiment, 0x118, type)) return false;
  if (type == nullptr) return false;
  if (!Read(type, 0x38, tag)) return false;
  if (tag != 0x4744624FU) return true;
  std::string key;
  reason = "mercenary_regiment_type_key_unavailable";
  if (!ReadTypeKey(type, key)) return false;
  std::int32_t tier = 0;
  reason = "mercenary_regiment_siege_tier_unavailable";
  if (!Read(type, 0x2A0, tier)) return false;
  row.type_status = "available";
  row.maa_type_key = std::move(key);
  row.siege_tier_raw = tier;
  return true;
}

void Quote(std::ostream &out, std::string_view text) {
  constexpr char hex[] = "0123456789abcdef";
  out << '"';
  for (const unsigned char value : text) {
    if (value == '"' || value == '\\') out << '\\' << static_cast<char>(value);
    else if (value < 0x20) out << "\\u00" << hex[value >> 4] << hex[value & 15];
    else out << static_cast<char>(value);
  }
  out << '"';
}
template <typename T>
void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::string> &value) {
  if (value) Quote(out, *value);
  else out << "null";
}
} // namespace

CompositionBindings BindMercenaryCompositionImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  CompositionBindings b{};
  if (base == 0 || sha != kCompositionExecutableSha256) return b;
  b.enabled = true;
  b.persistent_regiment_storage_slot = reinterpret_cast<void **>(base+0x5D1EB68);
  b.persistent_regiment_fallback_slot = reinterpret_cast<void **>(base+0x5D1EB58);
  b.company_holder = reinterpret_cast<CompanyHolder>(base+0x2626430);
  return b;
}

bool ReadMercenaryComposition12003(const CompositionBindings &b, void *company,
    std::uint32_t expected_id, CompanyComposition &out) noexcept {
  out = {};
  out.company_id = expected_id;
  out.unavailable_reason = "mercenary_composition_bindings_unavailable";
  if (!b.enabled || b.persistent_regiment_storage_slot == nullptr ||
      b.persistent_regiment_fallback_slot == nullptr || b.company_holder == nullptr)
    return false;
  try {
    std::uint32_t actual = UINT32_MAX, tag = 0;
    out.unavailable_reason = "mercenary_composition_identity_unavailable";
    if (expected_id == UINT32_MAX || !Read(company, 0x10, actual) || actual != expected_id ||
        !Read(company, 0x14, tag) || tag != 0x4D657263U) return false;

    void *holder = nullptr;
    std::uint32_t holder_id = UINT32_MAX, holder_tag = 0;
    out.holder_unavailable_reason = "mercenary_company_holder_unavailable";
    if (ReadHolder(b.company_holder, company, holder) && holder != nullptr &&
        Read(holder, 0x18, holder_id) && holder_id != UINT32_MAX &&
        Read(holder, 0x1C, holder_tag) && holder_tag == 0x43686172U) {
      out.holder_character_id = holder_id;
      out.holder_available = true;
      out.holder_unavailable_reason.clear();
    }

    const void *ids = nullptr;
    std::int32_t count = -1;
    out.unavailable_reason = "mercenary_company_regiment_collection_unavailable";
    if (!Read(company, 0x30, ids) || !Read(company, 0x3C, count) || count < 0 ||
        (count != 0 && ids == nullptr)) return false;
    out.regiment_count = static_cast<std::uint32_t>(count);
    std::int64_t current = 0, maximum = 0, positive_current = 0;
    std::int32_t maximum_tier = 0;
    for (std::int32_t index = 0; index < count; ++index) {
      CompanyRegimentComposition row{};
      row.ordinal = static_cast<std::uint32_t>(index);
      out.unavailable_reason = "mercenary_company_regiment_reference_unavailable";
      if (!Read(ids, static_cast<std::size_t>(index)*4, row.persistent_regiment_id))
        return false;
      void *regiment = ResolvePersistent(b, row.persistent_regiment_id);
      out.unavailable_reason = "mercenary_company_regiment_identity_unavailable";
      if (regiment == nullptr || !ReadRegiment(regiment, row, out.unavailable_reason))
        return false;
      current += row.current_soldiers;
      maximum += row.maximum_soldiers;
      if (row.siege_tier_raw) {
        maximum_tier = std::max(maximum_tier, *row.siege_tier_raw);
        if (*row.siege_tier_raw >= 1) positive_current += row.current_soldiers;
      }
      out.regiments.push_back(std::move(row));
      ++out.covered_regiment_count;
    }
    out.current_regiment_soldiers = current;
    out.maximum_regiment_soldiers = maximum;
    out.maximum_siege_tier_raw = maximum_tier;
    out.positive_siege_tier_current_soldiers = positive_current;
    out.available = true;
    out.unavailable_reason.clear();
    return true;
  } catch (...) {
    out.available = false;
    out.unavailable_reason = "mercenary_composition_copy_exception";
    return false;
  }
}

std::string SerializeMercenaryComposition12003(const CompanyComposition &value) {
  std::ostringstream out;
  out << std::boolalpha << "{\"available\":" << value.available
      << ",\"unavailable_reason\":";
  if (value.available) out << "null";
  else Quote(out, value.unavailable_reason);
  out << ",\"company_id\":" << value.company_id
      << ",\"holder_available\":" << value.holder_available
      << ",\"holder_unavailable_reason\":";
  if (value.holder_available) out << "null";
  else Quote(out, value.holder_unavailable_reason);
  out << ",\"holder_character_id\":"; Optional(out, value.holder_character_id);
  out << ",\"regiment_count\":"; Optional(out, value.regiment_count);
  out << ",\"covered_regiment_count\":" << value.covered_regiment_count;
  out << ",\"current_regiment_soldiers\":"; Optional(out, value.current_regiment_soldiers);
  out << ",\"maximum_regiment_soldiers\":"; Optional(out, value.maximum_regiment_soldiers);
  out << ",\"maximum_siege_tier_raw\":"; Optional(out, value.maximum_siege_tier_raw);
  out << ",\"positive_siege_tier_current_soldiers\":";
  Optional(out, value.positive_siege_tier_current_soldiers);
  out << ",\"regiments\":[";
  for (std::size_t index = 0; index < value.regiments.size(); ++index) {
    if (index != 0) out << ',';
    const auto &row = value.regiments[index];
    out << "{\"ordinal\":" << row.ordinal
        << ",\"persistent_regiment_id\":" << row.persistent_regiment_id
        << ",\"type_status\":"; Quote(out, row.type_status);
    out << ",\"maa_type_key\":"; Optional(out, row.maa_type_key);
    out << ",\"siege_tier_raw\":"; Optional(out, row.siege_tier_raw);
    out << ",\"current_soldiers\":" << row.current_soldiers
        << ",\"maximum_soldiers\":" << row.maximum_soldiers << '}';
  }
  out << "]}";
  return out.str();
}

} // namespace xar::ck3_12003::mercenary
