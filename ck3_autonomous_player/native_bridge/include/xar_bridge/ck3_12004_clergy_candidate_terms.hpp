#pragma once

#include "xar_bridge/ck3_12003_clergy_candidate_terms.hpp"
#include "xar_bridge/ck3_12004_council_candidates.hpp"
#include "xar_bridge/ck3_12004_council_gates.hpp"

namespace xar::ck3_12004::religion::clergy_candidate_terms {

// Software observations are shared; executable admission and all native
// providers below belong independently to the actual 1.20.0.4 image.
namespace legacy = ck3_12003::religion::clergy_candidate_terms;
using Observation = legacy::Observation;
using Failure = legacy::Failure;

struct Environment {
  bool enabled = false;
  std::string_view executable_sha256{};
  ck3_12004::CouncilCandidatesEnvironmentV1 candidates{};
  ck3_12004::CouncilCandidatesAccessV1 access{};
  ck3_12004::CouncilGatesEnvironment12004 gates{};
};

struct Request {
  ck3_12004::CouncilCandidatesRequestV1 frame{};
  std::int32_t candidate_character_id = -1;
};

// Address calculation only, using the actual4 Council candidate/gate binders.
// Their complete cached bodies and field operands are already source-closed.
Environment BindClergyCandidateTermsImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

// Same-frame explicit candidate membership, learning and replacement terms.
// No appointment, task change, recruitment or submission helper is called.
bool ReadClergyCandidateTerms12004(const Environment &environment,
    const Request &request, std::uint64_t capture_epoch,
    Observation &output) noexcept;
std::string SerializeClergyCandidateTerms12004(const Observation &value);
const char *ClergyCandidateTermsFailureKey12004(Failure failure) noexcept;

} // namespace xar::ck3_12004::religion::clergy_candidate_terms
