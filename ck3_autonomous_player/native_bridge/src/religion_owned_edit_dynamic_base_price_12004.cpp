#include "xar_bridge/religion_owned_edit_dynamic_base_price_12004.hpp"

namespace xar::ck3_12004::piety_price_raw_inputs {

OwnedEditBasePrice12004 ReadOwnedEditDynamicBasePrice2C6471012004(
    const OwnedEditDynamicBasePriceBindings12004 &bindings,
    std::uintptr_t draft, std::uintptr_t current_rite,
    std::uint64_t revision) noexcept {
  // The concrete adapter contexts are local typed copies. No pointer to a
  // temporary returned factory survives this synchronous parent invocation.
  auto first = bindings.first;
  auto second = bindings.second;
  OwnedEditBasePriceBindings12004 parent{};
  parent.access = bindings.access;
  parent.first_scalar_context = &first;
  parent.read_31d9930 = ReadPietyPriceNumeric31D9930DynamicAdapter12004;
  parent.second_scalar_context = &second;
  parent.read_31df3b0 = ReadPietyPriceNumeric31DF3B0DynamicAdapter12004;
  parent.maximum_entries = bindings.maximum_entries;
  // This retains the actual first/second array order, distinct membership
  // readers, post-search endpoint reload, NULLreason and prefix stop rules.
  return ReadOwnedEditBasePrice2C6471012004(parent, draft, current_rite, revision);
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
