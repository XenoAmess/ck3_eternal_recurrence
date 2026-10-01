#pragma once
#include "player_construction_view_probe_v1_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"
namespace xar::ck3_12002 {
// The old member is a shared pointer-free receipt DTO; its old native Bindings
// member is never consumed by this executor.
struct ConstructionMailboxContextV1 final {
  ck3_11906::PlayerConstructionViewProbeMailboxContextV1 query;
  CoreBindings core;
};
bool ExecuteConstructionMailboxV1(
    void* context,const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;
std::string SerializeConstructionMailboxV1(const ConstructionMailboxContextV1& context);
} // namespace xar::ck3_12002
