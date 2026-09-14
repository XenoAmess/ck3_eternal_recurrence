#pragma once

#include "xar_bridge/domain_construction_candidate_observer_v1.hpp"

#include <string>

namespace xar::bridge {

std::string SerializeDomainConstructionCandidateObserverV1(
    const DomainConstructionCandidateObserverDiagnosticsV1 &diagnostics);

} // namespace xar::bridge
