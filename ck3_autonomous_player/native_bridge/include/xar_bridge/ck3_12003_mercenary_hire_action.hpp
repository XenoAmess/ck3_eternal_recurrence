#pragma once

#include "xar_bridge/ck3_12002_commands.hpp"
#include "xar_bridge/ck3_12003_mercenary_candidates.hpp"
#include "xar_bridge/ck3_12003_mercenary_final_terms.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::mercenary {

inline constexpr std::string_view kHireActionExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::uintptr_t kHireCommandFactoryRva = 0x29958F0;
inline constexpr std::uintptr_t kHireCommandValidatorRva = 0x29942E0;
inline constexpr std::uint32_t kHireCommandChannelFlags = 0x0E;

// Game-allocated owning default CHireMercenaryCompanyCommand, sizeof=0x30.
// The factory initializes both vtables, metadata, absent IDs and normal mode 1.
using HireCommandFactory = void *(*)();
using HireCommandValidator = bool (*)(const void *source_command,
                                     void *native_reason);

struct HireActionBindings {
  bool enabled = false;
  CandidateBindings candidates;
  FinalTermsBindings final_terms;
  ck3_12002::CommandBindings commands;
  HireCommandFactory create_default = nullptr;
  HireCommandValidator validate_source = nullptr;
};

enum class HireActionStatus { unavailable, rejected, submitted, already_hired };

struct HireActionResult {
  HireActionStatus status = HireActionStatus::unavailable;
  std::string unavailable_reason = "not_sampled";
  std::int32_t actor_character_id = -1;
  std::uint32_t company_id = UINT32_MAX;
  bool company_resolved = false;
  std::optional<std::uint32_t> prior_employer_character_id;
  FinalTerms final_terms;
  bool native_command_validation_observable = false;
  bool native_command_valid = false;
  bool command_submitted = false;
  bool verification_pending = false;
};

HireActionBindings BindMercenaryHireActionImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Application-main action owner supplies the actual current played character
// resolved from its paused mailbox envelope. Re-resolves the complete company
// ID from the current manager; a query's retained company pointer is not input.
// Native queue AL is only submission acceptance. This result never credits a
// payment, employer change, newly raised army or fulfilled reinforcement goal.
HireActionStatus ApplyMercenaryHire12003(
    const HireActionBindings &, void *actual_current_played_character,
    std::int32_t actor_character_id, std::uint32_t full_company_id,
    HireActionResult &) noexcept;

} // namespace xar::ck3_12003::mercenary
