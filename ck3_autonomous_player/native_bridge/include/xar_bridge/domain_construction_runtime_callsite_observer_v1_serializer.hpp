#pragma once

#include "xar_bridge/domain_construction_runtime_callsite_observer_v1.hpp"

#include <string>

namespace xar::bridge {

std::string SerializeDomainConstructionRuntimeObserverV1(
    const DomainConstructionRuntimeObserverDiagnosticsV1 &diagnostics);

} // namespace xar::bridge
