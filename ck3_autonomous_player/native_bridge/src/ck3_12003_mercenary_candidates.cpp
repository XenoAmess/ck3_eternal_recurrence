#include "xar_bridge/ck3_12003_mercenary_candidates.hpp"

#include <cstddef>
#include <cstring>

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
bool ReadCurrentSoldiers(CurrentMercenarySoldiers getter, void *company,
                         std::int32_t &value) noexcept {
  if (getter == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    value = getter(company);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}
} // namespace

CandidateBindings BindMercenaryCandidatesImage12003(std::uintptr_t base,
    std::string_view sha) noexcept {
  CandidateBindings b{};
  if (base == 0 || sha != kCandidateExecutableSha256) return b;
  b.enabled = true;
  b.manager_slot = reinterpret_cast<void **>(base + 0x5D1DF08);
  b.fallback_slot = reinterpret_cast<void **>(base + 0x5D1DEF8);
  b.current_soldiers = reinterpret_cast<CurrentMercenarySoldiers>(base + 0x2625720);
  return b;
}

void *ResolveMercenaryCompany12003(const CandidateBindings &b,
                                  std::uint32_t full_company_id) noexcept {
  if (!b.enabled || b.manager_slot == nullptr || b.fallback_slot == nullptr ||
      full_company_id == UINT32_MAX) return nullptr;
  void *manager = nullptr, *fallback = nullptr;
  if (!Read(b.manager_slot, 0, manager) || manager == nullptr ||
      !Read(b.fallback_slot, 0, fallback)) return nullptr;
  const void *entries = nullptr;
  std::int32_t range_bound = -1;
  const std::uint32_t index = full_company_id & 0xFFFFFFU;
  if (!Read(manager, 0x20, entries) || entries == nullptr ||
      !Read(manager, 0x2C, range_bound) || range_bound < 0 ||
      index >= static_cast<std::uint32_t>(range_bound)) return nullptr;
  void *company = nullptr;
  std::uint32_t actual_id = UINT32_MAX, type = 0;
  if (!Read(entries, static_cast<std::size_t>(index) * 0x10 + 8, company) ||
      company == nullptr || company == fallback ||
      !Read(company, 0x10, actual_id) || actual_id != full_company_id ||
      !Read(company, 0x14, type) || type != 0x4D657263U) return nullptr;
  return company;
}

bool VisitMercenaryCandidates12003(const CandidateBindings &b,
    CandidateVisitor visitor, void *user, std::string &reason) noexcept {
  reason = "mercenary_bindings_unavailable";
  if (!b.enabled || b.manager_slot == nullptr || b.fallback_slot == nullptr ||
      visitor == nullptr) return false;
  void *manager = nullptr, *fallback = nullptr;
  if (!Read(b.manager_slot, 0, manager) || manager == nullptr ||
      !Read(b.fallback_slot, 0, fallback)) {
    reason = "mercenary_manager_unavailable";
    return false;
  }
  const void *entries = nullptr;
  std::int32_t range_bound = -1;
  if (!Read(manager, 0x20, entries) || !Read(manager, 0x2C, range_bound) ||
      range_bound < 0 || (range_bound != 0 && entries == nullptr)) {
    reason = "mercenary_entries_unavailable";
    return false;
  }
  try {
    // +2C is the complete slot range, not the active-company count. Null holes
    // and the native missing-object fallback are expected and omitted.
    for (std::int32_t i = 0; i < range_bound; ++i) {
      void *company = nullptr;
      if (!Read(entries, static_cast<std::size_t>(i) * 0x10 + 8, company)) {
        reason = "mercenary_entry_unavailable";
        return false;
      }
      if (company == nullptr || company == fallback) continue;
      Candidate row{};
      std::uint32_t type = 0, employer = UINT32_MAX;
      if (!Read(company, 0x10, row.company_id) || row.company_id == UINT32_MAX ||
          (row.company_id & 0xFFFFFFU) != static_cast<std::uint32_t>(i) ||
          !Read(company, 0x14, type) || type != 0x4D657263U ||
          !Read(company, 0x48, employer)) {
        reason = "mercenary_identity_unavailable";
        return false;
      }
      row.manager_slot_index = static_cast<std::uint32_t>(i);
      if (employer != UINT32_MAX) row.employer_id = employer;
      std::int32_t soldiers = 0;
      if (ReadCurrentSoldiers(b.current_soldiers, company, soldiers)) {
        row.current_soldiers = soldiers;
        row.troop_strength_available = true;
        row.troop_strength_unavailable_reason.clear();
      }
      if (!visitor(company, row, user)) {
        reason = "mercenary_visitor_failed";
        return false;
      }
    }
    reason.clear();
    return true;
  } catch (...) {
    reason = "mercenary_native_copy_exception";
    return false;
  }
}
} // namespace xar::ck3_12003::mercenary
