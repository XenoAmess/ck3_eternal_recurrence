#pragma once

#include "xar_bridge/ck3_12002_context.hpp"

#include <string>

namespace xar::ck3_12002 {

// Diagnostic sampling only. The bridge's existing owning-thread callback may
// call this once and persist the returned JSON to its selected artifact path.
// This entry does not register callbacks, submit commands or operate a process.
// An unavailable native query is retained in JSON and returns false.
bool CollectMarriageProbe12002(const ContextBindings &bindings,
                              std::string &artifact_json) noexcept;

} // namespace xar::ck3_12002
