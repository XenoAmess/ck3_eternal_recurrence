#pragma once

#include "player_construction_view_probe_v1_mailbox.hpp"
#include "xar_bridge/ck3_12004_construction.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

namespace xar::ck3_12004 {
// The query member is the existing receipt DTO. Its legacy native Bindings and
// HoldingView cache are not consumed by the actual .4 executor.
struct ConstructionMailboxContext12004 final {
  ck3_12002::QueryMailboxEnvelope envelope{};
  ConstructionBindings12004 bindings{};
  ck3_11906::PlayerConstructionViewProbeMailboxContextV1 query{};
};

// Submit &context.envelope as the executor_context. The envelope's typed_context
// points to context; its game points directly to the selected actual .4 adapter.
bool ExecuteConstructionMailbox12004(
    void *context, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
std::string HandleConstruction12004(const ConstructionMailboxContext12004 &context);
} // namespace xar::ck3_12004
