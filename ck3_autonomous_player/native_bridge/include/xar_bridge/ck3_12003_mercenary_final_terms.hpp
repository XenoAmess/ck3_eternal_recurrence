#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003::mercenary {

inline constexpr std::string_view kFinalTermsExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::int64_t kFinalTermsResourceScale = 100000;
inline constexpr std::uint32_t kNormalHireMode = 1;

using CanHire = bool (*)(void *company, void *actor, std::uint32_t mode,
                        void *native_reason);
using Cost = std::int64_t *(*)(void *company, std::int64_t *out10,
                             void *actor, std::int32_t current_landstate_value);
using PaymentStatus = std::int32_t (*)(void *company, void *actor,
                                     std::uint32_t mode);
using CanAfford = bool (*)(const std::int64_t *cost10, void *actor,
                          void *native_reason);
using HireDuration = std::int64_t (*)(void *company, void *actor);
using ReasonDestroy = void (*)(void *native_reason);

struct FinalTermsBindings {
  bool enabled = false;
  CanHire can_hire = nullptr;
  Cost cost = nullptr;
  PaymentStatus payment_status = nullptr;
  CanAfford can_afford = nullptr;
  HireDuration hire_duration = nullptr;
  ReasonDestroy reason_destroy = nullptr;
};

struct FinalTerms {
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::optional<bool> can_hire;
  std::optional<bool> can_afford;
  // Native normal hire may be allowed through debt even when CanAfford=false.
  // 0: outside native payment allowance; 1: permitted debt; 2: full funds.
  std::optional<std::int32_t> payment_status;
  // Native order: gold, prestige, piety, renown, influence, herd,
  // treasury, treasury_or_gold, merit, barter_goods. All signed Q100000.
  std::optional<std::array<std::int64_t, 10>> resource_costs_raw;
  std::optional<std::int64_t> hire_duration_months;
  bool can_hire_reasons_available = false;
  std::optional<std::string> can_hire_reason_literal;
  bool can_afford_reasons_available = false;
  std::optional<std::string> can_afford_reason_literal;
};

FinalTermsBindings BindMercenaryFinalTermsImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
// Called by the paused application-main owner. The provider supplies its actual
// current played character and a validated company; only copied terms escape.
// This does not create or submit a command, mutate cash, or choose a company.
bool ReadMercenaryFinalTerms12003(const FinalTermsBindings &, void *company,
                                void *current_played_character,
                                FinalTerms &) noexcept;
std::string SerializeMercenaryFinalTerms12003(const FinalTerms &);

} // namespace xar::ck3_12003::mercenary
