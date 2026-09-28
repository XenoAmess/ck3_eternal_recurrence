#include "xar_bridge/realm_law_final_terms_11906.hpp"

#include <cstddef>
#include <cstdint>

namespace xar::bridge {

RealmLawFinalTerms11906Result ReadRealmLawFinalTerms11906(
    const RealmLawFinalTerms11906Input &input,
    const RealmLawFinalTerms11906Operations &operations) noexcept {
  RealmLawFinalTerms11906Result result{};
  if (input.law == nullptr || input.actor == nullptr ||
      input.full_actor_id == 0xFFFFFFFFu ||
      operations.candidate_kind_allowed == nullptr ||
      operations.is_active == nullptr ||
      operations.engine_final_can_enact == nullptr ||
      operations.read_cost_q100000 == nullptr) {
    return result;
  }

  // This reproduces the three GUI gates at 0x3DDF7D8..0x3DDF800.
  // The cost getter is separately called for every candidate, as in the
  // GUI's GetShortCostString path, including a candidate blocked by a gate.
  const bool kind_allowed = operations.candidate_kind_allowed(input.law);
  const bool active = kind_allowed && operations.is_active(input.actor, input.law);
  bool final_allowed = false;
  if (kind_allowed && !active) {
    final_allowed = operations.engine_final_can_enact(
        input.law, input.actor, nullptr);
  }

  const auto *cost_block = static_cast<const std::byte *>(input.law) + 0xCD8;
  if (operations.read_cost_q100000(result.cost_raw.data(), cost_block,
                                  input.full_actor_id) !=
      result.cost_raw.data()) {
    result.cost_raw = {};
    return result;
  }
  result.cost_available = true;
  result.status = !kind_allowed
                      ? RealmLawFinalTerms11906Status::candidate_kind_rejected
                  : active ? RealmLawFinalTerms11906Status::already_active
                  : final_allowed ? RealmLawFinalTerms11906Status::can_enact
                                  : RealmLawFinalTerms11906Status::engine_blocked;
  return result;
}

} // namespace xar::bridge
