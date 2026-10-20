#include "ghw_variable_bindings_12004.hpp"

namespace xar::ck3_12004::religion::ghw_variables_candidate {
namespace {
bool Memory(void *p, std::uintptr_t address, void *out,
            std::size_t bytes) noexcept {
  auto &b = *static_cast<BindingState *>(p);
  return b.owner_read_memory &&
      b.owner_read_memory(b.owner_context, address, out, bytes);
}
bool Frame(void *p, BoundFrame &out) noexcept {
  auto &b = *static_cast<BindingState *>(p);
  return b.owner_read_frame && b.owner_read_frame(b.owner_context, out);
}
bool Identifier(void *p, std::string_view key, std::int32_t &out) noexcept {
  auto &b = *static_cast<BindingState *>(p);
  // Reuse the actual .4 table/lookup/name factories and exact key round-trip.
  // Lookup3F8A660 is the read-lock wrapper around non-inserting lookup3F8A380;
  // it does not create a missing identifier. See IDENTIFIER-LOOKUP.actual.json.
  return ck3_12002::ResolvePhaseVariableIdentifier(b.identifiers, key, out);
}
bool Context(void *p, Scope scope, std::uint32_t id,
             std::uintptr_t &out) noexcept {
  out = 0;
  auto &b = *static_cast<BindingState *>(p);
  if (scope == Scope::global) {
    if (id != 0 || !b.global.enabled || !b.global.global_accessor_slot)
      return false;
    ck3_12002::SettlementGlobalAccessor getter = nullptr;
    if (!Memory(p, reinterpret_cast<std::uintptr_t>(b.global.global_accessor_slot),
                &getter, sizeof(getter)) || !getter) return false;
    out = reinterpret_cast<std::uintptr_t>(getter());
  } else {
    if (id == kNullReference || !b.identifiers.enabled ||
        !b.identifiers.variable_context) return false;
    ck3_12002::PhaseVariableTarget target{};
    if (scope == Scope::faith) target.kind = kFaithScopeKind;
    else if (scope == Scope::religion) target.kind = kReligionScopeKind;
    else return false;
    target.payload = static_cast<std::int64_t>(id);
    out = reinterpret_cast<std::uintptr_t>(
        b.identifiers.variable_context(&target));
  }
  return out != 0;
}
} // namespace

Access BindGhwVariableAccess12004(BindingState &state, std::uintptr_t base,
    std::string_view sha, void *owner, ReadMemory memory,
    ReadBoundFrame frame) noexcept {
  state = {};
  if (!base || sha != kExactSha || !memory || !frame) return {};
  state.owner_context = owner;
  state.owner_read_memory = memory;
  state.owner_read_frame = frame;
  state.identifiers = ck3_12004::BindFamilyBreakIdentifiersImage(base, sha);
  state.global = ck3_12004::BindSnapshotSettlementImage(base, sha);
  if (!state.identifiers.enabled || !state.global.enabled) return {};
  return {&state, Memory, Frame, Identifier, Context, kExactSha};
}
} // namespace xar::ck3_12004::religion::ghw_variables_candidate
