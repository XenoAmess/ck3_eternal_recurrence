#pragma once

#include <array>
#include <cstdint>

namespace xar::bridge {

// Private, one-callback reader for CK3 1.19.0.6. The caller must resolve
// character and law pointers in the same paused application-main frame.
// No native pointer or legality result may be kept for a later frame.
inline constexpr std::uint32_t kRealmLawFinalTerms11906CostScale = 100'000;
inline constexpr std::uint32_t kRealmLawFinalTerms11906CostSlots = 10;

enum class RealmLawFinalTerms11906Status : std::uint8_t {
  unavailable,
  candidate_kind_rejected,
  already_active,
  engine_blocked,
  can_enact,
};

struct RealmLawFinalTerms11906Input {
  const void *law = nullptr;
  const void *actor = nullptr;
  std::uint32_t full_actor_id = 0;
};

// Exact native signatures are frozen by realm_law_final_terms_11906_abi.json.
// The cost function returns its caller-provided 80-byte output buffer.
struct RealmLawFinalTerms11906Operations {
  bool (*candidate_kind_allowed)(const void *law) = nullptr;
  bool (*is_active)(const void *actor, const void *law) = nullptr;
  bool (*engine_final_can_enact)(const void *law, const void *actor,
                                 void *error_sink) = nullptr;
  std::int64_t *(*read_cost_q100000)(std::int64_t *out10,
                                     const void *compiled_cost_block,
                                     std::uint32_t full_actor_id) = nullptr;
};

struct RealmLawFinalTerms11906Result {
  RealmLawFinalTerms11906Status status =
      RealmLawFinalTerms11906Status::unavailable;
  bool cost_available = false;
  // Native order: gold, prestige, piety, renown, influence, herd,
  // treasury, treasury_or_gold, merit, barter_goods. Slot 7 is routed by
  // the engine affordability check; it is not an independent balance.
  std::array<std::int64_t, kRealmLawFinalTerms11906CostSlots> cost_raw{};
};

RealmLawFinalTerms11906Result ReadRealmLawFinalTerms11906(
    const RealmLawFinalTerms11906Input &input,
    const RealmLawFinalTerms11906Operations &operations) noexcept;

} // namespace xar::bridge
