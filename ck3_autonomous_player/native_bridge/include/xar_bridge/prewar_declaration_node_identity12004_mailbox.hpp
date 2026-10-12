#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_declarations.hpp"
#include "xar_bridge/prewar_declaration_node_identity12004.hpp"
#include "xar_bridge/prewar_force_coalition12004.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

inline constexpr std::string_view kPrewarDeclarationNodeIdentityStep12004 =
    "query-prewar-declaration-node-identity-v1";
inline constexpr std::string_view kPrewarDeclarationNodeIdentityDomain12004 =
    "prewar_declaration_node_identity_v1";
inline constexpr std::size_t kPrewarDeclarationNodeWireLimit12004 = 8192;
inline constexpr bool kPrewarDeclarationNodeCapabilityAdvertised12004 = false;

// Private database/index/key equality witness; never serialized.
struct PrewarDeclarationNodeDatabaseWitness12004 {
  std::uintptr_t database = 0;
  std::uintptr_t types = 0;
  std::uintptr_t descriptor = 0;
  std::uintptr_t key_data = 0;
  std::int32_t count = -1;
  std::array<std::byte, 32> key_storage{};
  std::string key;
  bool operator==(const PrewarDeclarationNodeDatabaseWitness12004 &) const = default;
};

struct PrewarDeclarationNodeRound12004 {
  PrewarDeclarationNodeDatabaseWitness12004 database;
  PrewarDeclarationNodeIdentity12004 directory;
  bool operator==(const PrewarDeclarationNodeRound12004 &) const = default;
};

struct PrewarDeclarationNodeIdentityMailbox12004 {
  ck3_12002::QueryMailboxEnvelope envelope{};
  PrewarForceCoalitionRequest12004 request{};
  ck3_12002::DeclarationsBindings declarations{};
  PrewarDeclarationNodeIdentityBindings12004 bindings{};
  PrewarDeclarationNodeRound12004 observation{};
  std::uint64_t capture_epoch = 0;
  std::uint64_t query_sequence = 0;
  std::uint32_t executor_invocations = 0;
  bool completed = false;
  ck3_11906::MainThreadQueryWaitResultV1 wait_result =
      ck3_11906::MainThreadQueryWaitResultV1::ticket_mismatch;
  ck3_11906::MainThreadQueryReclaimResultV1 reclaim_result =
      ck3_11906::MainThreadQueryReclaimResultV1::not_terminal;
  std::string failure;

  PrewarDeclarationNodeIdentityMailbox12004() = default;
  PrewarDeclarationNodeIdentityMailbox12004(
      const PrewarDeclarationNodeIdentityMailbox12004 &) = delete;
  PrewarDeclarationNodeIdentityMailbox12004 &operator=(
      const PrewarDeclarationNodeIdentityMailbox12004 &) = delete;
};

bool IsPrewarDeclarationNodeIdentityStep12004(std::string_view step) noexcept;
bool ExecutePrewarDeclarationNodeIdentityMailbox12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;
bool RunPrewarDeclarationNodeIdentityMailbox12004(
    PrewarDeclarationNodeIdentityMailbox12004 &query,
    std::string &serialized, std::string &failure) noexcept;

// This separate PRIVATE research response never changes formal v2's schema or
// war admission. Binding retains the entire requested tuple; only the current
// database CB index/key and actor/target identities are independently read.
// Finalized primary roles remain unobserved. The complete escaped outer result
// must fit 8192 bytes; oversize is rejected, never truncated or paged.
bool HandlePrewarDeclarationNodeIdentity12004(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t native_revision,
    const PrewarForceCoalitionRequest12004 &request,
    std::string_view request_id,
    std::string &serialized, std::string &failure) noexcept;

} // namespace xar::ck3_12004
