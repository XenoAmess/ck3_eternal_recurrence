#include "xar_bridge/ck3_12003_holy_order_hire_action.hpp"

#include <utility>

namespace xar::ck3_12003::religion::holy_order {
namespace {
HireActionStatus Finish(HireActionResult &out, HireActionStatus status,
                       const char *reason) {
  out.status = status;
  out.unavailable_reason = reason;
  return status;
}
}

HireActionBindings BindHolyOrderHireActionImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  HireActionBindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.context = BindPlayerHolyOrderImage12003(base, sha);
  // Exact .3 command manager, clone ABI and ownership path reuse the
  // reviewed byte-identical Crozier core implementation.
  b.commands = ck3_12002::BindCommandImage(base, ck3_12002::kExecutableSha256);
  b.primary_vtable = base + kHirePrimaryVtableRva;
  b.secondary_vtable = base + kHireSecondaryVtableRva;
  b.validate_source = reinterpret_cast<HireCommandValidator>(base + kHireCanExecuteRva);
  b.enabled = b.context.enabled && b.commands.enabled;
  return b;
}

HireActionStatus ApplyHolyOrderHire12003(const HireActionBindings &b,
    void *actor, std::int32_t actor_id, std::uint32_t order_id,
    std::int32_t date, std::uint64_t epoch, HireActionResult &out) noexcept {
  out = {};
  out.actor_character_id = actor_id;
  out.holy_order_id = order_id;
  if (!b.enabled || !b.commands.enabled || b.primary_vtable == 0 ||
      b.secondary_vtable == 0 || b.validate_source == nullptr || actor == nullptr)
    return Finish(out, HireActionStatus::unavailable,
                  "holy_order_hire_bindings_or_current_actor_unavailable");
  try {
    // Reuse the existing native observation; no new pricing/strength formula.
    // Only copied current manager rows survive this owning-thread invocation.
    if (!ReadPlayerHolyOrderContext12003(b.context, actor, actor_id, date, epoch,
                                       out.prior_context))
      return Finish(out, HireActionStatus::unavailable,
                    "holy_order_hire_current_context_unavailable");
    auto &rows = out.prior_context.rows;
    const Row *selected = nullptr;
    for (const auto &row : rows)
      if (row.holy_order_id == order_id) { selected = &row; break; }
    if (selected == nullptr)
      return Finish(out, HireActionStatus::rejected,
                    "holy_order_not_resolved_from_current_manager");
    Row row = *selected;
    rows.clear();
    rows.push_back(std::move(row));
    const auto &current = rows.front();
    out.holy_order_resolved = true;
    out.prior_employer_character_id = current.employer_id;
    if (!current.is_military)
      return Finish(out, HireActionStatus::rejected, "holy_order_is_not_military");
    if (current.employer_id == static_cast<std::uint32_t>(actor_id))
      return Finish(out, HireActionStatus::already_hired, "");
    if (!current.military_terms || !current.military_terms->can_hire.has_value())
      return Finish(out, HireActionStatus::unavailable,
                    "holy_order_native_can_hire_unavailable");
    if (!*current.military_terms->can_hire)
      return Finish(out, HireActionStatus::rejected, "native_holy_order_can_hire_false");
    HireMode3Source source{};
    source.primary_vtable = b.primary_vtable;
    source.secondary_vtable = b.secondary_vtable;
    source.played_character_full_id = static_cast<std::uint32_t>(actor_id);
    source.holy_order_full_id = order_id;
    // CanExecute is the native final authority. Independent CanAfford/reasons
    // and ten-slot quote remain observations, not an invented Python gate.
    out.native_command_validation_observable = true;
    out.native_command_valid = b.validate_source(&source, nullptr);
    if (!out.native_command_valid)
      return Finish(out, HireActionStatus::rejected,
                    "native_holy_order_command_validator_false");
    const auto submitted = ck3_12002::SubmitCommandCopy(b.commands, &source,
                                                       kHireChannelFlags);
    if (submitted != ck3_12002::CommandSubmitResult::submitted)
      return Finish(out, submitted == ck3_12002::CommandSubmitResult::rejected
          ? HireActionStatus::rejected : HireActionStatus::unavailable,
          submitted == ck3_12002::CommandSubmitResult::rejected
          ? "native_holy_order_queue_rejected" : "native_holy_order_queue_unavailable");
    out.command_submitted = true;
    out.verification_pending = true;
    return Finish(out, HireActionStatus::submitted, "");
  } catch (...) {
    return Finish(out, HireActionStatus::unavailable, "holy_order_hire_native_copy_exception");
  }
}

} // namespace xar::ck3_12003::religion::holy_order
