#pragma once

#include "xar_bridge/ck3_12002_thread_runtime.hpp"

namespace xar::ck3_12002 {

// Version-owned providers retain the master's public/private slot identities.
// Callback contexts are constructed by their corresponding version-owned wire
// handlers; an old provider is never registered merely because its DTO matches.
struct NonwarMailboxExecutorsV1 {
  ck3_11906::MainThreadQueryExecutorV1 lifestyle = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 construction = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 ranked_marriage = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 alliance_projection = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 relationship = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 marriage_submit = nullptr;
};

// This is the production registration seam used before mailbox installation.
// It is pure and can be tested without loading, attaching or querying CK3.
void RegisterNonwarMailboxExecutorsV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &,
    const NonwarMailboxExecutorsV1 &) noexcept;

} // namespace xar::ck3_12002
