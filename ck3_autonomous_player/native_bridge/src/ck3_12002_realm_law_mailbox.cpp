#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/crown_authority_cooldown_turn_tick_12004.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"
#include "xar_bridge/realm_law_12004_native.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {
bool ReadMemory(void *, std::uintptr_t address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && ReadProcessMemory(
      GetCurrentProcess(), reinterpret_cast<const void *>(address), output,
      size, &read) != 0 && read == size;
}
}

namespace {
bool ExecuteRealmLawQuery(QueryMailboxEnvelope &envelope,
    RealmLawReadbackQuery12002 &query,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    ck3_11906::MainThreadQueryExecutorV1 execute,
    ck3_12004::crown_cooldown::turn_tick::Observation *turn_tick) noexcept {
  if (!EnterQueryMailbox(envelope, stamp, execute)) return true;
  private_law::RealmLawActiveCollectionAccess access{};
  const bool actual_12004 =
      query.actual_executable_sha256 == ck3_12004::kExecutableSha256;
  if (query.collection_access_override != nullptr) {
    access = *query.collection_access_override;
  } else {
    access.admitted_executable_sha256 = actual_12004
        ? ck3_12004::kExecutableSha256
        : private_law::kRealmLawActiveCollectionExeSha25612002;
    access.played_character_address = reinterpret_cast<std::uintptr_t>(
        actual_12004
            ? ck3_12004::ResolveCoreCharacter(
                  query.bindings, envelope.expected_snapshot.played_character_id)
            : ResolveCoreCharacter(
                  query.bindings, envelope.expected_snapshot.played_character_id));
    access.read_memory = &ReadMemory;
  }
  const RealmLawReadbackFrame12002 frame{envelope.expected_snapshot_revision,
      envelope.expected_snapshot.date_raw, envelope.expected_snapshot.played_character_id};
  const auto operations = query.final_operations_override != nullptr
          ? *query.final_operations_override
          : actual_12004
          ? ck3_12004::private_law::BindRealmLawFinalTermsImage12004(
                query.module_base, query.actual_executable_sha256)
          : private_law::BindRealmLawFinalTermsImage12002(query.module_base,
                private_law::kRealmLawFinalTermsExecutableSha256);
  if (actual_12004 && turn_tick != nullptr) {
    (void)CaptureRealmLawReadbackWithTurnTick12004(access, query.module_base,
        frame, operations, query.readback, *turn_tick,
        query.actual_executable_sha256, query.cooldown_bindings_override);
  } else {
    (void)CaptureRealmLawReadback12002(access, query.module_base, frame,
        operations, query.readback, query.actual_executable_sha256,
        query.cooldown_bindings_override);
  }
  (void)FinishQueryMailbox(envelope);
  return true;
}
} // namespace

bool ExecuteRealmLawPausedPrivateQuery12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return true;
  auto &query = *static_cast<RealmLawReadbackQuery12002 *>(envelope->typed_context);
  return ExecuteRealmLawQuery(*envelope, query, stamp,
      &ExecuteRealmLawPausedPrivateQuery12002, nullptr);
}

bool ExecuteRealmLawPausedPrivateQueryWithTurnTick12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return true;
  auto &owner = *static_cast<RealmLawTurnTickQuery12004 *>(envelope->typed_context);
  return ExecuteRealmLawQuery(*envelope, owner.query, stamp,
      &ExecuteRealmLawPausedPrivateQueryWithTurnTick12004, &owner.turn_tick);
}

bool ReadRealmLawOnApplicationMain12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  const bool actual_12004 = game::IsCk3_12004Descriptor(adapter.descriptor());
  const bool reviewed_12002 =
      game::ReviewedCrozierAbiVersion(adapter.descriptor()) == "1.20.0.2" &&
      game::ReviewedCrozierAbiSha256(adapter.descriptor()) ==
          private_law::kRealmLawFinalTermsExecutableSha256;
  if ((!actual_12004 && !reviewed_12002) ||
      revision == 0 || !published.paused || !published.map_ready ||
      !published.has_played_character || !published.played_character_alive) {
    failure = "native_law_paused_actor_unavailable"; return false;
  }
  try {
    RealmLawTurnTickQuery12004 owner{};
    auto &query = owner.query;
    query.actual_executable_sha256 = adapter.descriptor().executable_sha256;
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = actual_12004
        ? static_cast<void *>(&owner) : static_cast<void *>(&query);
    query.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    query.bindings = actual_12004
        ? ck3_12004::BindCoreImage(query.module_base, query.actual_executable_sha256)
        : BindCoreImage(query.module_base,
              game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    const auto execute = actual_12004
        ? &ExecuteRealmLawPausedPrivateQueryWithTurnTick12004
        : &ExecuteRealmLawPausedPrivateQuery12002;
    if (!query.bindings.enabled || ck3_11906::TrySubmitMainThreadQueryV1(mailbox,
        execute, &query.envelope,
        query.envelope.ticket) != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "native_law_mailbox_submit_unavailable"; return false;
    }
    auto wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 5000);
    while (wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running)
      wait = ck3_11906::WaitForMainThreadQueryV1(mailbox, query.envelope.ticket, 100);
    const auto reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
    if (wait != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaim != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !query.envelope.frame_stable || !query.readback.available) {
      failure = query.readback.failure.empty() ? "native_law_paused_capture_unavailable" : query.readback.failure;
      return false;
    }
    serialized = actual_12004
        ? SerializeRealmLawReadbackWithTurnTick12004(query.readback, owner.turn_tick)
        : SerializeRealmLawReadback12002(query.readback);
    return !serialized.empty();
  } catch (...) {
    failure = "native_law_mailbox_exception"; return false;
  }
}
} // namespace xar::ck3_12002
