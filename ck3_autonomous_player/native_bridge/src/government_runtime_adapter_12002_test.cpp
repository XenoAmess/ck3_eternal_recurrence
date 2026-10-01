#include "xar_bridge/ck3_12002_campaign.hpp"
#include "xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>

namespace {

namespace observer = xar::bridge::private_observer;
namespace game = xar::game;
using Profile = observer::GovernmentRuntimeAdapterBuildProfileV1;
using Sample = observer::GovernmentRuntimeAdapterCollectorSampleV1;
using SourceStatus = observer::GovernmentRuntimeAdapterSourceStatusV1;
using Selection = observer::GovernmentRuntimeAdapterSelectionStatusV1;
constexpr std::uintptr_t kModuleBase = 0x140000000ULL;
constexpr std::uint64_t kRevision = 701;
constexpr std::int32_t kDateRaw = 1'220'410;
std::string g_available_json;
std::string g_unavailable_json;

// Frozen 1.20.0.2 compiled identifiers, independently retained in the ABI
// receipt. Native reader calls and memory accesses remain the production ones.
constexpr std::array<std::uint32_t, 44> kIdentifiers{{
    0x3587, 0x3588, 0x34A7, 0x3538, 0x3539, 0x3270, 0x366D, 0x34DC,
    0x3773, 0x3608, 0x37CF, 0x37CE, 0x36C4, 0x377A, 0x35E0, 0x394A,
    0x3B0A, 0x3A5B, 0x3A09, 0x3A08, 0x3953, 0x3A00, 0x3A02, 0x3A01,
    0x39DA, 0x3CBB, 0x3A07, 0x3C98, 0x3CA1, 0x3A06, 0x39F7, 0x3D67,
    0x39ED, 0x39EE, 0x39EF, 0x39F0, 0x39DB, 0x39DC, 0x39DD, 0x39DE,
    0x39DF, 0x4101, 0x4102, 0x4169,
}};

template <std::size_t Size, typename Value>
void Put(std::array<std::byte, Size> &blob, std::size_t offset,
         const Value &value) {
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}

struct NativeFeatures {
  alignas(void *) std::array<std::byte, 0x2C0> root{};
  alignas(void *) std::array<std::byte, 0x20> script_dlc_set{};
  void *root_slot = root.data();
  std::array<std::uint32_t, 44> enum_table = kIdentifiers;
  std::array<std::string, 44> names;
  std::unordered_map<const void *, std::string> strings;
  game::LoadedFeatureManifestFrameV1 frame{
      kRevision, kDateRaw, true, true};
};

NativeFeatures *g_native_features = nullptr;

const std::string *__fastcall ResolveName(std::int32_t identifier) noexcept {
  if (g_native_features == nullptr) {
    return nullptr;
  }
  for (std::size_t index = 0; index < kIdentifiers.size(); ++index) {
    if (kIdentifiers[index] == static_cast<std::uint32_t>(identifier)) {
      return &g_native_features->names[index];
    }
  }
  return nullptr;
}

bool CaptureFeatureFrame(void *opaque,
                         game::LoadedFeatureManifestFrameV1 &output) noexcept {
  output = static_cast<NativeFeatures *>(opaque)->frame;
  return true;
}

bool MainThread(void *) noexcept { return true; }

bool ReadMemory(void *, const void *address, void *output,
                std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
  std::memcpy(output, address, size);
  return true;
}

bool ReadString(void *opaque, const void *address,
                std::string &output) noexcept {
  const auto &features = *static_cast<NativeFeatures *>(opaque);
  const auto found = features.strings.find(address);
  if (found == features.strings.end()) {
    return false;
  }
  output = found->second;
  return true;
}

bool ProduceNativeFeatures(game::LoadedFeatureManifestV1 &output) {
  NativeFeatures fixture;
  const auto keys =
      observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1(Profile::ck3_12002);
  if (keys.size() != kIdentifiers.size()) {
    return false;
  }
  for (std::size_t index = 0; index < keys.size(); ++index) {
    fixture.names[index] = keys[index];
    fixture.strings.emplace(&fixture.names[index], fixture.names[index]);
  }
  const std::uint64_t bits = (std::uint64_t{1} << 21) |
                             (std::uint64_t{1} << 22) |
                             (std::uint64_t{1} << 43);
  Put(fixture.root, 0x2B0, bits);
  Put(fixture.root, 0x2B8, std::int32_t{3});
  xar::ck3_12002::LoadedFeatureManifestNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  environment.feature_root_slot = &fixture.root_slot;
  environment.script_dlc_set = fixture.script_dlc_set.data();
  environment.feature_enum_table = fixture.enum_table.data();
  environment.script_identifier_name = &ResolveName;
  xar::ck3_12002::LoadedFeatureManifestAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &CaptureFeatureFrame;
  access.is_main_thread = &MainThread;
  access.read_memory = &ReadMemory;
  access.read_string = &ReadString;
  g_native_features = &fixture;
  const auto result = xar::ck3_12002::ReadLoadedFeatureManifestV1(
      environment, access, {kRevision}, output);
  g_native_features = nullptr;
  return result == game::ReadLoadedFeatureManifestResultV1::available &&
         output.effective_feature_flags.items.size() == 44 &&
         output.effective_feature_flags.items[36].key ==
             "high_medieval_warfare_attire" &&
         output.effective_feature_flags.items[43].key == "by_god_alone" &&
         output.effective_feature_flags.items[43].enabled;
}

struct Collector {
  Sample sample;
  std::size_t captures = 0;
};

bool CaptureSample(void *opaque, Sample &output) noexcept {
  auto &collector = *static_cast<Collector *>(opaque);
  ++collector.captures;
  output = collector.sample;
  return true;
}

bool SetUpCollector(Collector &collector) {
  auto &sample = collector.sample;
  sample.paused = true;
  sample.campaign_lifecycle_identity = 0xCA11;
  sample.feature_lifecycle_identity = 0xFEA7;
  sample.government_object_identity_available = true;
  sample.government_object_identity = 0x6001;
  sample.script_dlc_layout_identity_available = true;
  sample.script_dlc_bucket_base_identity = 0;
  sample.script_dlc_bucket_mask_identity = 0;
  sample.script_dlc_maximum_spill_identity = 0;
  auto &campaign = sample.campaign_root;
  campaign.status = game::CampaignRootContextStatusV1::available;
  campaign.snapshot_revision = kRevision;
  campaign.date_raw = kDateRaw;
  campaign.player_character_id = 29'829;
  campaign.government = game::CampaignRootGovernmentV1{
      "feudal_government",
      {"government_uses_domain_limit", "government_is_feudal"}, 2};
  campaign.readiness.player_identity_ready = true;
  campaign.readiness.government_ready = true;
  campaign.readiness.same_frame_ready = true;
  return ProduceNativeFeatures(sample.loaded_features);
}

observer::GovernmentRuntimeAdapterBridgeBindingEnvironmentV1
BindingEnvironment(Collector &collector, Profile profile) {
  observer::GovernmentRuntimeAdapterBridgeBindingEnvironmentV1 environment{};
  environment.binding_enabled = true;
  environment.exact_build_admitted = true;
  environment.module_base = kModuleBase;
  environment.admitted_game_version = profile == Profile::ck3_12002
      ? xar::ck3_12002::kCampaignRootContextV1GameVersion
      : observer::kGovernmentRuntimeAdapterBridgeBinderV1GameVersion;
  environment.admitted_executable_sha256 = profile == Profile::ck3_12002
      ? xar::ck3_12002::kCampaignRootContextV1ExecutableSha256
      : observer::kGovernmentRuntimeAdapterBridgeBinderV1ExecutableSha256;
  environment.offline_fixture = true;
  environment.fixture_context = &collector;
  environment.fixture_capture = &CaptureSample;
  return environment;
}

bool TestNativeProducerAndSourceProfile() {
  Collector collector;
  if (!SetUpCollector(collector)) {
    return false;
  }
  observer::GovernmentRuntimeAdapterSourceAccessV1 access{};
  access.exact_build_admitted = true;
  access.context = &collector;
  access.is_application_main = &MainThread;
  access.capture = &CaptureSample;
  access.feature_profile = Profile::ck3_12002;
  observer::GovernmentRuntimeAdapterSourceResultV1 result{};
  if (observer::ReadGovernmentRuntimeAdapterSourceV1(access, result) !=
          SourceStatus::available ||
      collector.captures != 2 ||
      result.input.feature_profile != Profile::ck3_12002 ||
      result.semantic_result.adapter.status != Selection::core_supported ||
      !result.semantic_result.adapter.requirements_met ||
      result.semantic_result.effective_feature_flags[43].key != "by_god_alone") {
    return false;
  }
  // The old and new arrays are both 44 long. An old profile must not accept
  // new producer rows solely because their lengths match.
  access.feature_profile = Profile::ck3_11906;
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, result);
  if (result.status != SourceStatus::unavailable ||
      result.semantic_result.unavailable_reason !=
          observer::GovernmentRuntimeAdapterUnavailableReasonV1::
              feature_registry_drift) {
    return false;
  }
  // Source failures preceding a capture still carry the caller's revision in
  // the actual serialized response, so the Python transport can decode them.
  access.exact_build_admitted = false;
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, result);
  g_unavailable_json = observer::SerializeGovernmentRuntimeAdapterSourceV1(
      result, Profile::ck3_12002, kRevision);
  return g_unavailable_json.find("\"snapshot_revision\":701") != std::string::npos &&
         g_unavailable_json.find("\"status\":\"unavailable\"") != std::string::npos &&
         g_unavailable_json.find("unsupported_build") != std::string::npos;
}

bool TestPrivateBinderConsumesNewProducer() {
  Collector collector;
  if (!SetUpCollector(collector)) {
    return false;
  }
  observer::GovernmentRuntimeAdapterBridgeBindingStateV1 binding;
  observer::GovernmentRuntimeAdapterSourceAccessV1 access;
  if (!observer::BindGovernmentRuntimeAdapterBridgeV1(
          BindingEnvironment(collector, Profile::ck3_12002), binding, access) ||
      access.feature_profile != Profile::ck3_12002 ||
      reinterpret_cast<std::uintptr_t>(binding.campaign_environment.game_state_slot) !=
          kModuleBase + xar::ck3_12002::kCampaignRootGameStateSlotRva ||
      reinterpret_cast<std::uintptr_t>(binding.feature_environment.feature_root_slot) !=
          kModuleBase + xar::ck3_12002::kLoadedFeatureRootSlotRva ||
      reinterpret_cast<std::uintptr_t>(binding.feature_environment.feature_enum_table) !=
          kModuleBase + xar::ck3_12002::kLoadedFeatureEnumTableRva) {
    return false;
  }
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox;
  observer::GovernmentRuntimeAdapterPrivateOperationV1 operation;
  if (!observer::PrepareGovernmentRuntimeAdapterPrivateOperationV1(
          binding, mailbox, kRevision, operation)) {
    return false;
  }
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 37;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 0x1000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x2000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x3000;
  stamp.game_state = collector.sample.campaign_lifecycle_identity;
  stamp.date_raw = kDateRaw;
  stamp.paused = true;
  operation.ticket.sequence = 41;
  mailbox.state.store(xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(operation.ticket.sequence);
  mailbox.owner_thread_id.store(stamp.thread_id);
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1;
  mailbox.executor_context = &operation;
  if (!observer::ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
          &operation, stamp) ||
      !operation.completed || operation.executor_invocations != 1 ||
      operation.result.status != SourceStatus::available ||
      operation.result.semantic_result.adapter.status != Selection::core_supported ||
      collector.captures != 2) {
    return false;
  }
  g_available_json = observer::SerializeGovernmentRuntimeAdapterSourceV1(
      operation.result, Profile::ck3_12002);
  return g_available_json.find("ck3-1.20.0.2") != std::string::npos &&
         g_available_json.find("by_god_alone") != std::string::npos &&
         g_available_json.find("barter_troops") == std::string::npos;
}

bool TestLegacyDefaultProfile() {
  const auto legacy = observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1();
  const auto current =
      observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1(Profile::ck3_12002);
  if (legacy.size() != 44 || current.size() != 44 ||
      legacy[36] != "barter_troops" ||
      legacy[43] != "songs_of_the_realm" ||
      current[43] != "by_god_alone") {
    return false;
  }
  Collector collector;
  if (!SetUpCollector(collector)) {
    return false;
  }
  observer::GovernmentRuntimeAdapterBridgeBindingStateV1 binding;
  observer::GovernmentRuntimeAdapterSourceAccessV1 access;
  return observer::BindGovernmentRuntimeAdapterBridgeV1(
             BindingEnvironment(collector, Profile::ck3_11906), binding, access) &&
         access.feature_profile == Profile::ck3_11906 &&
         reinterpret_cast<std::uintptr_t>(binding.feature_environment.feature_enum_table) ==
             kModuleBase + xar::ck3_11906::kLoadedFeatureEnumTableRva;
}

bool TestChangedStockGovernmentIdentities() {
  Collector collector;
  if (!SetUpCollector(collector)) {
    return false;
  }
  observer::GovernmentRuntimeAdapterSourceAccessV1 access{};
  access.exact_build_admitted = true;
  access.context = &collector;
  access.is_application_main = &MainThread;
  access.capture = &CaptureSample;
  access.feature_profile = Profile::ck3_12002;
  collector.sample.campaign_root.government = game::CampaignRootGovernmentV1{
      "tribal_government", {"government_uses_tribal_authority"}, 1};
  observer::GovernmentRuntimeAdapterSourceResultV1 result;
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, result);
  const auto &tribal = result.semantic_result;
  if (result.status != SourceStatus::available ||
      !tribal.government.recognized_stock_key ||
      tribal.adapter.status != Selection::core_supported ||
      tribal.government.applicable_stock_flags !=
          std::vector<std::string>{"government_uses_tribal_authority"}) {
    return false;
  }
  // Identity recognition is needed for routing. Religious implementation
  // remains deferred and must not expose a newly usable flag policy.
  collector.sample.campaign_root.government = game::CampaignRootGovernmentV1{
      "monastic_holy_order_government", {"government_uses_domain_limit"}, 1};
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, result);
  if (result.status != SourceStatus::available ||
      !result.semantic_result.government.recognized_stock_key ||
      !result.semantic_result.government.religious_identity_opaque ||
      !result.semantic_result.government.observed_flags.empty() ||
      !result.semantic_result.government.applicable_stock_flags.empty() ||
      result.semantic_result.adapter.status != Selection::owner_deferred_religious) {
    return false;
  }
  auto legacy_input = result.input;
  legacy_input.feature_profile = Profile::ck3_11906;
  legacy_input.effective_government_stable_key = "theocracy_government";
  const auto old_keys = observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1();
  for (std::size_t index = 0; index < old_keys.size(); ++index) {
    legacy_input.effective_feature_flags[index].key = old_keys[index];
  }
  const auto legacy = legacy_input.Evaluate();
  if (!legacy.government.recognized_stock_key ||
      !legacy.government.religious_identity_opaque ||
      legacy.adapter.status != Selection::owner_deferred_religious) {
    return false;
  }
  // In the new stock definition, Japan's feudal identity has no authored
  // direct feature gate. A disabled DLC capability remains visible in the
  // profile, without inventing an All Under Heaven identity requirement.
  collector.sample.campaign_root.government = game::CampaignRootGovernmentV1{
      "japan_feudal_government", {}, 0};
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, result);
  const auto &japan = result.semantic_result;
  return result.status == SourceStatus::available &&
         japan.government.recognized_stock_key &&
         japan.adapter.status == Selection::adapter_spec_ready_not_implemented &&
         japan.adapter.requirements_met &&
         japan.adapter.required_effective_features.empty() &&
         japan.effective_feature_flags[33].key == "all_under_heaven" &&
         !japan.effective_feature_flags[33].enabled;
}

} // namespace

int main(int argc, char **argv) {
  if (!TestNativeProducerAndSourceProfile()) {
    std::cerr << "government-12002 native producer/source profile: RED\n";
    return 1;
  }
  if (!TestPrivateBinderConsumesNewProducer()) {
    std::cerr << "government-12002 private mailbox binder: RED\n";
    return 1;
  }
  if (!TestLegacyDefaultProfile()) {
    std::cerr << "government-12002 legacy compatibility: RED\n";
    return 1;
  }
  if (!TestChangedStockGovernmentIdentities()) {
    std::cerr << "government-12002 changed stock identities: RED\n";
    return 1;
  }
  if (argc == 3 && std::string_view(argv[1]) == "--wire-json-dir") {
    const std::filesystem::path output(argv[2]);
    std::filesystem::create_directories(output);
    std::ofstream available(output / "available.json", std::ios::binary);
    std::ofstream unavailable(output / "unavailable.json", std::ios::binary);
    available << g_available_json << '\n';
    unavailable << g_unavailable_json << '\n';
    if (!available || !unavailable) {
      std::cerr << "government-12002 wire artifact write: RED\n";
      return 1;
    }
  } else if (argc != 1) {
    std::cerr << "usage: fixture [--wire-json-dir output-directory]\n";
    return 2;
  }
  std::cout << "government-runtime-adapter-12002: GREEN (native feature producer, "
               "source profile, private mailbox, stock identity migration, "
               "legacy compatibility)\n";
  return 0;
}
