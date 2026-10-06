#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12002_government_mailbox.hpp"

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"

#include <windows.h>

namespace xar::ck3_12002 {
namespace {

using namespace bridge::private_observer;

struct GovernmentCallerContext12002 {
  const game::GameAdapter *adapter = nullptr;
  GovernmentRuntimeAdapterBridgeBindingStateV1 *binding = nullptr;
  const game::Snapshot *published = nullptr;
  std::uint64_t revision = 0;
  std::int64_t observed_date_raw = 0;
};

bool CallerIsApplicationMain(void *opaque) noexcept {
  auto *context = static_cast<GovernmentCallerContext12002 *>(opaque);
  if (context == nullptr || context->adapter == nullptr ||
      context->binding == nullptr || context->published == nullptr ||
      !context->binding->execution_active ||
      !context->binding->execution_stamp.paused ||
      context->binding->execution_stamp.thread_id != GetCurrentThreadId()) {
    return false;
  }
  context->observed_date_raw = context->binding->execution_stamp.date_raw;
  return true;
}

bool CallerCaptureSnapshot(GovernmentCallerContext12002 &context,
                           game::Snapshot &snapshot) noexcept {
  if (context.adapter != nullptr &&
      game::IsCk3_12004Descriptor(context.adapter->descriptor())) {
    if (!CallerIsApplicationMain(&context) ||
        !game::ReadCk3_12002TimelineCoreSnapshot(*context.adapter, snapshot)) {
      return false;
    }
    const auto &published = *context.published;
    // Only the eight independently bound .4 core fields are compared. The
    // caller's positive revision is retained without reading advanced families.
    return snapshot.date_raw == published.date_raw &&
           snapshot.speed == published.speed && snapshot.paused == published.paused &&
           snapshot.player_id == published.player_id &&
           snapshot.map_ready == published.map_ready &&
           snapshot.has_played_character == published.has_played_character &&
           snapshot.played_character_id == published.played_character_id &&
           snapshot.played_character_alive == published.played_character_alive &&
           snapshot.paused &&
           snapshot.date_raw == context.binding->execution_stamp.date_raw;
  }
  return CallerIsApplicationMain(&context) &&
         context.adapter->read_snapshot(snapshot) &&
         snapshot == *context.published && snapshot.paused &&
         snapshot.date_raw == context.binding->execution_stamp.date_raw;
}

bool CallerCaptureCampaignFrame(void *opaque,
                               game::CampaignRootFrameV1 &frame) noexcept {
  auto *context = static_cast<GovernmentCallerContext12002 *>(opaque);
  game::Snapshot snapshot{};
  frame = {};
  if (context == nullptr || !CallerCaptureSnapshot(*context, snapshot)) {
    return false;
  }
  frame.snapshot_revision = context->revision;
  frame.date_raw = snapshot.date_raw;
  frame.paused = snapshot.paused;
  frame.map_ready = snapshot.map_ready;
  frame.has_played_character = snapshot.has_played_character;
  frame.played_character_alive = snapshot.played_character_alive;
  frame.played_character_id = snapshot.played_character_id;
  return true;
}

bool CallerCaptureFeatureFrame(void *opaque,
                              game::LoadedFeatureManifestFrameV1 &frame) noexcept {
  auto *context = static_cast<GovernmentCallerContext12002 *>(opaque);
  game::Snapshot snapshot{};
  frame = {};
  if (context == nullptr || !CallerCaptureSnapshot(*context, snapshot)) {
    return false;
  }
  frame.snapshot_revision = context->revision;
  frame.date_raw = snapshot.date_raw;
  frame.paused = snapshot.paused;
  frame.map_ready = snapshot.map_ready;
  return true;
}

bool CallerReadOwnedProcessMemory(void *opaque, const void *address,
                                 void *output, std::size_t size) noexcept {
  SIZE_T copied = 0;
  return CallerIsApplicationMain(opaque) && address != nullptr &&
         output != nullptr && size != 0 &&
         ReadProcessMemory(GetCurrentProcess(), address, output, size, &copied) &&
         copied == size;
}

void AppendCallerJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[character >> 4U]);
      output.push_back(hex[character & 0xfU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

} // namespace

bool IsGovernmentRuntimeAdapterQuery12002(std::string_view step) noexcept {
  return step == kGovernmentRuntimeAdapterV1Step;
}

bool ReadGovernmentRuntimeAdapterOnApplicationMain12002(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept {
  serialized.clear();
  failure.clear();
  try {
    const auto &native = NativeAdapter12002(adapter);
    const bool current_build = game::IsCk3_12004Descriptor(native.descriptor());
    const bool historical_build_unavailable =
        (native.descriptor().adapter_id != "ck3-1.20.0.2-msvc-x64" && !xar::game::IsCk3_12003Descriptor(native.descriptor())) ||
        xar::game::ReviewedCrozierAbiSha256(native.descriptor()) != kExecutableSha256;
    if (!native.enabled() || (!current_build && historical_build_unavailable)) {
      failure = "government runtime adapter exact build is unavailable";
      return false;
    }
    if (revision == 0 || !published.paused || !published.map_ready ||
        !published.has_played_character || !published.played_character_alive) {
      failure = "government runtime adapter published snapshot is not ready";
      return false;
    }

    GovernmentRuntimeAdapterBridgeBindingStateV1 binding{};
    GovernmentCallerContext12002 context{&native, &binding, &published, revision,
                                        published.date_raw};
    GovernmentRuntimeAdapterBridgeBindingEnvironmentV1 environment{};
    environment.binding_enabled = true;
    environment.exact_build_admitted = true;
    environment.admitted_game_version = current_build
        ? xar::ck3_12004::kGameVersion
        : xar::game::ReviewedCrozierAbiVersion(native.descriptor());
    environment.admitted_executable_sha256 = current_build
        ? xar::ck3_12004::kExecutableSha256
        : xar::game::ReviewedCrozierAbiSha256(native.descriptor());
    environment.module_base = reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr));
    environment.campaign_access.context = &context;
    environment.campaign_access.capture_frame = &CallerCaptureCampaignFrame;
    environment.campaign_access.is_main_thread = &CallerIsApplicationMain;
    environment.campaign_access.read_memory = &CallerReadOwnedProcessMemory;
    environment.feature_access.context = &context;
    environment.feature_access.capture_frame = &CallerCaptureFeatureFrame;
    environment.feature_access.is_main_thread = &CallerIsApplicationMain;
    environment.feature_access.read_memory = &CallerReadOwnedProcessMemory;
    GovernmentRuntimeAdapterSourceAccessV1 source_access{};
    if (!BindGovernmentRuntimeAdapterBridgeV1(environment, binding, source_access)) {
      failure = GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(binding.last_failure);
      return false;
    }

    GovernmentRuntimeAdapterPrivateOperationV1 operation{};
    if (!PrepareGovernmentRuntimeAdapterPrivateOperationV1(binding, mailbox,
                                                            revision, operation)) {
      failure = GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(binding.last_failure);
      return false;
    }
    const auto submitted = ck3_11906::TrySubmitMainThreadQueryV1(
        mailbox, &ExecuteGovernmentRuntimeAdapterPrivateOperationV1, &operation,
        operation.ticket);
    if (submitted != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
      failure = "application-main government runtime query is unavailable or busy";
      return false;
    }
    auto waited = ck3_11906::WaitForMainThreadQueryV1(mailbox, operation.ticket, 3'000);
    while (waited == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running) {
      waited = ck3_11906::WaitForMainThreadQueryV1(mailbox, operation.ticket, 250);
    }
    const auto reclaimed = ck3_11906::ReclaimMainThreadQueryV1(mailbox, operation.ticket);
    if (waited != ck3_11906::MainThreadQueryWaitResultV1::completed ||
        reclaimed != ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
        !operation.completed || operation.executor_invocations != 1) {
      failure = "application-main government runtime query did not complete";
      return false;
    }
    operation.result.date_raw = context.observed_date_raw;
    const auto payload = SerializeGovernmentRuntimeAdapterSourceV1(
        operation.result, binding.feature_profile, revision);
    serialized = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
    AppendCallerJsonString(serialized, request_id);
    serialized += ",\"ok\":true,\"result\":{\"step\":";
    AppendCallerJsonString(serialized, kGovernmentRuntimeAdapterV1Step);
    serialized += ",\"accepted\":true,\"private_build\":true,"
                  "\"read_only\":true,\"advertised\":false,\"snapshot_revision\":" + std::to_string(revision) +
                  ",\"government_runtime_adapter\":" + payload + "}}";
    return true;
  } catch (...) {
    serialized.clear();
    failure = "government runtime adapter query failed";
    return false;
  }
}

} // namespace xar::ck3_12002
