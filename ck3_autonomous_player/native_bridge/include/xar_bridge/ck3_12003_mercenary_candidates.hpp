#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::mercenary {

inline constexpr std::string_view kCandidateExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
using CurrentMercenarySoldiers = std::int32_t (*)(void *company);

struct CandidateBindings {
  bool enabled = false;
  void **manager_slot = nullptr;
  void **fallback_slot = nullptr;
  CurrentMercenarySoldiers current_soldiers = nullptr;
};

struct Candidate {
  std::uint32_t company_id = UINT32_MAX;
  std::uint32_t manager_slot_index = UINT32_MAX;
  std::optional<std::uint32_t> employer_id;
  bool troop_strength_available = false;
  std::optional<std::int32_t> current_soldiers;
  std::string troop_strength_unavailable_reason =
      "native_current_soldiers_unavailable";
};

// Company is temporary owner-thread input only. The visitor must copy values;
// no company pointer is stored in Candidate or retained after this call.
using CandidateVisitor = bool (*)(void *company, const Candidate &candidate,
                                 void *user);

CandidateBindings BindMercenaryCandidatesImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool VisitMercenaryCandidates12003(const CandidateBindings &bindings,
    CandidateVisitor visitor, void *user, std::string &unavailable_reason) noexcept;

} // namespace xar::ck3_12003::mercenary
