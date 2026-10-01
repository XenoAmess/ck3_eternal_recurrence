#include "xar_bridge/ck3_12002_realm_law_final_terms.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_12002::private_law {

RealmLawFinalTerms12002Operations BindRealmLawFinalTermsImage12002(
    std::uintptr_t base, std::string_view sha) noexcept {
  RealmLawFinalTerms12002Operations out{};
  if (base == 0 || sha != kRealmLawFinalTermsExecutableSha256) return out;
  out.terms.candidate_kind_allowed =
      reinterpret_cast<decltype(out.terms.candidate_kind_allowed)>(base + kRealmLawCandidateKindRva);
  out.terms.is_active = reinterpret_cast<decltype(out.terms.is_active)>(base + kRealmLawAlreadyActiveRva);
  out.terms.engine_final_can_enact =
      reinterpret_cast<decltype(out.terms.engine_final_can_enact)>(base + kRealmLawFinalCanEnactRva);
  out.terms.read_cost_q100000 =
      reinterpret_cast<decltype(out.terms.read_cost_q100000)>(base + kRealmLawNumericCostRva);
  out.full_can_enact_with_reason =
      reinterpret_cast<decltype(out.full_can_enact_with_reason)>(base + kRealmLawFinalCanEnactReasonRva);
  out.destroy_native_reason =
      reinterpret_cast<decltype(out.destroy_native_reason)>(base + kRealmLawReasonDestructorRva);
  return out;
}

RealmLawFinalTerms12002Result ReadRealmLawFinalTerms12002(
    const RealmLawFinalTerms12002Input &input,
    const RealmLawFinalTerms12002Operations &operations) noexcept {
  RealmLawFinalTerms12002Result result{};
  const auto &op = operations.terms;
  if (input.law == nullptr || input.actor == nullptr ||
      input.full_actor_id == 0xFFFFFFFFu || op.candidate_kind_allowed == nullptr ||
      op.is_active == nullptr || op.engine_final_can_enact == nullptr ||
      op.read_cost_q100000 == nullptr ||
      operations.full_can_enact_with_reason == nullptr ||
      operations.destroy_native_reason == nullptr) return result;
  try {
    const bool kind = op.candidate_kind_allowed(input.law);
    const bool active = kind && op.is_active(input.actor, input.law);
    const bool can_enact = kind && !active &&
        op.engine_final_can_enact(input.law, input.actor, nullptr);
    const auto *cost = static_cast<const std::byte *>(input.law) + kRealmLawCompiledCostOffset;
    if (op.read_cost_q100000(result.terms.cost_raw.data(), cost, input.full_actor_id) !=
        result.terms.cost_raw.data()) return {};
    result.terms.cost_available = true;
    result.terms.status = !kind ? RealmLawFinalTerms12002Status::candidate_kind_rejected
        : active ? RealmLawFinalTerms12002Status::already_active
        : can_enact ? RealmLawFinalTerms12002Status::can_enact
                    : RealmLawFinalTerms12002Status::engine_blocked;

    // The engine expects its 32-byte MSVC string in empty inline mode.
    alignas(8) std::array<std::byte, 32> reason{};
    const std::uint64_t inline_capacity = 15;
    std::memcpy(reason.data() + 0x18, &inline_capacity, sizeof(inline_capacity));
    const bool full_can_enact = operations.full_can_enact_with_reason(input.law, input.actor, reason.data());
    std::uint64_t size = 0, capacity = 0;
    std::memcpy(&size, reason.data() + 0x10, sizeof(size));
    std::memcpy(&capacity, reason.data() + 0x18, sizeof(capacity));
    const char *characters = reinterpret_cast<const char *>(reason.data());
    if (capacity > 15) std::memcpy(&characters, reason.data(), sizeof(characters));
    const bool valid = size <= 4096 && capacity >= size && characters != nullptr;
    try {
      if (valid) result.native_reason.assign(characters, static_cast<std::size_t>(size));
    } catch (...) {
      operations.destroy_native_reason(reason.data());
      return {};
    }
    operations.destroy_native_reason(reason.data());
    if (!valid || full_can_enact != can_enact) return {};
    result.native_reason_available = true;
    return result;
  } catch (...) {
    return {};
  }
}

} // namespace xar::ck3_12002::private_law
