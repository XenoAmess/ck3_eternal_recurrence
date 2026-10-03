#include "xar_bridge/ck3_12003_mercenary_hire_action.hpp"

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
    std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
                sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

struct NativeOwnedSource {
  void *value = nullptr;
  ~NativeOwnedSource() { ck3_12002::DestroyOwnedCommand(value); }
};

template <typename T>
void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(T));
}

HireActionStatus Finish(HireActionResult &out, HireActionStatus status,
                        const char *reason) {
  out.status = status;
  out.unavailable_reason = reason;
  return status;
}

} // namespace

HireActionBindings BindMercenaryHireActionImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  HireActionBindings b{};
  if (base == 0 || sha != kHireActionExecutableSha256) return b;
  b.candidates = BindMercenaryCandidatesImage12003(base, sha);
  b.final_terms = BindMercenaryFinalTermsImage12003(base, sha);
  // The exact .3 core review reuses this byte-identical command manager,
  // hidden-result clone ABI and native ownership path from the .2 adapter.
  b.commands = ck3_12002::BindCommandImage(
      base, ck3_12002::kExecutableSha256);
  b.create_default = reinterpret_cast<HireCommandFactory>(
      base + kHireCommandFactoryRva);
  b.validate_source = reinterpret_cast<HireCommandValidator>(
      base + kHireCommandValidatorRva);
  b.enabled = b.candidates.enabled && b.final_terms.enabled && b.commands.enabled;
  return b;
}

HireActionStatus ApplyMercenaryHire12003(
    const HireActionBindings &b, void *actor, std::int32_t actor_id,
    std::uint32_t company_id, HireActionResult &out) noexcept {
  out = {};
  out.actor_character_id = actor_id;
  out.company_id = company_id;
  if (!b.enabled || !b.commands.enabled || b.create_default == nullptr ||
      b.validate_source == nullptr || actor == nullptr) {
    return Finish(out, HireActionStatus::unavailable,
                  "mercenary_hire_bindings_or_current_actor_unavailable");
  }
  void *company = ResolveMercenaryCompany12003(b.candidates, company_id);
  if (company == nullptr) {
    return Finish(out, HireActionStatus::rejected,
                  "mercenary_company_not_resolved_from_current_manager");
  }
  out.company_resolved = true;
  std::uint32_t employer_id = UINT32_MAX;
  if (!Read(company, 0x48, employer_id)) {
    return Finish(out, HireActionStatus::unavailable,
                  "mercenary_current_employer_unavailable");
  }
  if (employer_id != UINT32_MAX) {
    out.prior_employer_character_id = employer_id;
    if (employer_id == static_cast<std::uint32_t>(actor_id)) {
      // This is a current employer observation, independent of command ACK.
      return Finish(out, HireActionStatus::already_hired, "");
    }
  }
  // Fresh normal-mode native evaluation. Cost/CanAfford are copied context;
  // CanAfford=false does not prevent native permitted-debt payment status 1.
  (void)ReadMercenaryFinalTerms12003(b.final_terms, company, actor,
                                   out.final_terms);
  if (!out.final_terms.can_hire.has_value() ||
      !out.final_terms.payment_status.has_value()) {
    return Finish(out, HireActionStatus::unavailable,
                  "mercenary_native_hire_or_payment_evaluation_unavailable");
  }
  if (!*out.final_terms.can_hire) {
    return Finish(out, HireActionStatus::rejected,
                  "native_mercenary_can_hire_false");
  }
  if (*out.final_terms.payment_status == 0) {
    return Finish(out, HireActionStatus::rejected,
                  "native_mercenary_payment_outside_allowance");
  }
  NativeOwnedSource source{b.create_default()};
  if (source.value == nullptr) {
    return Finish(out, HireActionStatus::unavailable,
                  "native_mercenary_command_factory_unavailable");
  }
  // Write only IDs into game-allocated owning command storage. The actual
  // native default factory supplied interfaces, metadata and normal mode 1.
  Store(source.value, 0x20, actor_id);
  Store(source.value, 0x24, company_id);
  out.native_command_validation_observable = true;
  out.native_command_valid = b.validate_source(source.value, nullptr);
  if (!out.native_command_valid) {
    return Finish(out, HireActionStatus::rejected,
                  "native_mercenary_command_validator_false");
  }
  const auto submitted = ck3_12002::SubmitCommandCopy(
      b.commands, source.value, kHireCommandChannelFlags);
  if (submitted != ck3_12002::CommandSubmitResult::submitted) {
    return Finish(out,
        submitted == ck3_12002::CommandSubmitResult::rejected
            ? HireActionStatus::rejected : HireActionStatus::unavailable,
        submitted == ck3_12002::CommandSubmitResult::rejected
            ? "native_mercenary_queue_rejected"
            : "native_mercenary_queue_unavailable");
  }
  out.command_submitted = true;
  out.verification_pending = true;
  return Finish(out, HireActionStatus::submitted, "");
}

} // namespace xar::ck3_12003::mercenary
