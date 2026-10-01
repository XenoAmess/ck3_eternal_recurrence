#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {
struct Query {
  QueryMailboxEnvelope envelope{};
  CoreBindings bindings{};
  std::uintptr_t module_base = 0;
  RealmLawReadback12002 readback{};
};
bool ReadMemory(void *, std::uintptr_t address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != 0 && output != nullptr && ReadProcessMemory(
      GetCurrentProcess(), reinterpret_cast<const void *>(address), output,
      size, &read) != 0 && read == size;
}
}

bool ExecuteRealmLawPausedPrivateQuery12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteRealmLawPausedPrivateQuery12002)) return true;
  auto &query = *static_cast<Query *>(envelope->typed_context);
  private_law::RealmLawActiveCollectionAccess access{};
  access.admitted_executable_sha256 = private_law::kRealmLawActiveCollectionExeSha25612002;
  access.played_character_address = reinterpret_cast<std::uintptr_t>(
      ResolveCoreCharacter(query.bindings, envelope->expected_snapshot.played_character_id));
  access.read_memory = &ReadMemory;
  const RealmLawReadbackFrame12002 frame{envelope->expected_snapshot_revision,
      envelope->expected_snapshot.date_raw, envelope->expected_snapshot.played_character_id};
  (void)CaptureRealmLawReadback12002(access, query.module_base, frame,
      private_law::BindRealmLawFinalTermsImage12002(query.module_base,
          private_law::kRealmLawFinalTermsExecutableSha256), query.readback);
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bool ReadRealmLawOnApplicationMain12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string &serialized, std::string &failure) noexcept {
  serialized.clear(); failure.clear();
  if (xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
      xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != private_law::kRealmLawFinalTermsExecutableSha256 ||
      revision == 0 || !published.paused || !published.map_ready ||
      !published.has_played_character || !published.played_character_alive) {
    failure = "native_law_paused_actor_unavailable"; return false;
  }
  try {
    Query query{};
    query.envelope.game = &NativeAdapter12002(adapter);
    query.envelope.mailbox = &mailbox;
    query.envelope.expected_snapshot = published;
    query.envelope.expected_snapshot_revision = revision;
    query.envelope.typed_context = &query;
    query.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    query.bindings = BindCoreImage(query.module_base, xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()));
    if (!query.bindings.enabled || ck3_11906::TrySubmitMainThreadQueryV1(mailbox,
        &ExecuteRealmLawPausedPrivateQuery12002, &query.envelope,
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
    serialized = SerializeRealmLawReadback12002(query.readback);
    return !serialized.empty();
  } catch (...) {
    failure = "native_law_mailbox_exception"; return false;
  }
}
} // namespace xar::ck3_12002
