#pragma once
#include "xar_bridge/ck3_12004_holy_site_relic_actions.hpp"
namespace xar::ck3_12004::religion::relic_actions {
// Provider-private synchronous owner-callback stack context. No pointers or
// source qualification flags are accepted from public request parameters.
struct ProductionRelicActionPreviewContext12004 {
 std::uintptr_t image_base=0;
 std::string_view executable_sha256;
};
// Implemented by the separately reviewed source-bound action-context adapter.
// Must leave source_qualified/live_qualified false for injected dependencies.
bool ReadProductionRelicActionPreview12004(void*,const Admission&,const Frame&,
 const Request&,PreviewProof&) noexcept;
}
