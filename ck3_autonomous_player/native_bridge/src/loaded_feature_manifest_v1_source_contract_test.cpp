#include "xar_bridge/loaded_feature_manifest_v1.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) {
      std::cerr << "missing source-contract token: " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 12) {
    std::cerr << "expected eleven source-contract paths\n";
    return 1;
  }
  const auto header = ReadAll(argv[1]);
  const auto reader = ReadAll(argv[2]);
  const auto serializer = ReadAll(argv[3]);
  const auto query_mailbox = ReadAll(argv[4]);
  const auto common_mailbox_header = ReadAll(argv[5]);
  const auto common_mailbox_source = ReadAll(argv[6]);
  const auto adapter = ReadAll(argv[7]);
  const auto game_adapter = ReadAll(argv[8]);
  const auto bridge = ReadAll(argv[9]);
  const auto abi = ReadAll(argv[10]);
  const auto fixture = ReadAll(argv[11]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      query_mailbox.empty() || common_mailbox_header.empty() ||
      common_mailbox_source.empty() || adapter.empty() ||
      game_adapter.empty() || bridge.empty() || abi.empty() ||
      fixture.empty()) {
    std::cerr << "source-contract input is unreadable\n";
    return 1;
  }

  using namespace xar::ck3_11906;
  if (kLoadedFeatureManifestV1Capability !=
          "game.command.query-loaded-feature-manifest-v1" ||
      kLoadedFeatureManifestV1Step !=
          "query-loaded-feature-manifest-v1" ||
      kLoadedFeatureManifestV1GameVersion != "1.19.0.6" ||
      kLoadedFeatureManifestV1ExecutableSha256 !=
          "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86" ||
      kLoadedFeatureManifestV1BackendId !=
          "ck3-1.19.0.6-native-loaded-feature-manifest-v1" ||
      kLoadedFeatureRootSlotRva != 0x576CC68 ||
      kLoadedFeatureScriptDlcSetRva != 0x5762590 ||
      kLoadedFeatureEnumTableRva != 0x42F7850 ||
      kLoadedFeatureEnumTableEndRva != 0x42F7900 ||
      kLoadedFeatureScriptIdentifierNameRva != 0x3B58970 ||
      kLoadedFeatureNativeCount != 44) {
    std::cerr << "compiled exact-build binding drifted\n";
    return 1;
  }

  if (!ContainsAll(header,
                   {"game.command.query-loaded-feature-manifest-v1",
                    "ck3-1.19.0.6-native-loaded-feature-manifest-v1",
                    "kLoadedFeatureNativeCount = 44",
                    "LoadedFeatureManifestReadinessV1"}) ||
      !ContainsAll(reader,
                   {"kFeatureBitsetOffset = 0x2B0",
                    "kFeatureEnabledCountOffset = 0x2B8",
                    "kScriptDlcBucketStride = 0x28",
                    "Popcount64(output.feature_bits)",
                    "feature_registry_drift",
                    "script_dlc_keys_native_order",
                    "std::sort(output.script_dlc_keys.begin()",
                    "static_cast<unsigned char>(left_byte)",
                    "second != first"}) ||
      !ContainsAll(serializer,
                   {"\\\"schema\\\":\\\"loaded-feature-manifest-v1\\\"",
                    "\\\"effective_feature_flags\\\"",
                    "\\\"script_dlc_keys\\\"",
                    "\\\"entitlements\\\"",
                    "store_verdict_provenance_unclosed",
                    "\\\"actionable_ready\\\""}) ||
      !ContainsAll(query_mailbox,
                   {"ExecuteLoadedFeatureManifestMailboxQueryV1",
                    "ReadLoadedFeatureManifestV1(",
                    "typed_available",
                    "typed_unavailable"}) ||
      !ContainsAll(common_mailbox_header,
                   {"twenty-six fixed slots", "permitted_executor_denary",
                    "permitted_executor_duodenary",
                    "permitted_executor_sexvigintary"}) ||
      !ContainsAll(common_mailbox_source,
                   {"environment.permitted_executor_denary",
                    "mailbox.permitted_executor_denary"}) ||
      !ContainsAll(adapter,
                   {"game.command.query-loaded-feature-manifest-v1"}) ||
      !ContainsAll(game_adapter,
                   {"ParseLoadedFeatureManifestV1Step",
                    "kLoadedFeatureManifestV1Capability"}) ||
      !ContainsAll(bridge,
                   {"ExecuteLoadedFeatureManifestMailboxQueryV1",
                    "permitted_executor_denary",
                    "LoadedFeatureManifestResultFrame",
                    "\\\"loaded_feature_manifest\\\"",
                    "ParseLoadedFeatureManifestExpectedRevisionV1",
                    "completion_snapshot_stable"}) ||
      !ContainsAll(abi,
                   {"\"root_pointer_slot_rva\": \"0x576CC68\"",
                    "\"object_rva\": \"0x5762590\"",
                    "\"kind\": \"direct_object\"",
                    "unsigned_utf8_bytewise_lexicographical",
                    "false_cache_byte_must_not_be_reported_as_not_entitled"}) ||
      !ContainsAll(fixture,
                   {"\"command_result_key\": \"loaded_feature_manifest\"",
                    "\"mailbox_executor_slot\": \"permitted_executor_denary\"",
                    "\"feature_item_count\": 44",
                    "store_verdict_provenance_unclosed"})) {
    return 1;
  }

  if (Contains(reader, "WriteProcessMemory") ||
      Contains(reader, "SubmitPause") || Contains(reader, "SubmitMove") ||
      Contains(reader, "SubmitDeclare") ||
      Contains(reader, "kLoadedFeatureEntitlementManagerSlotRva")) {
    std::cerr << "reader contains a mutator or unclosed entitlement surface\n";
    return 1;
  }

  std::cout << "loaded-feature-manifest-v1 source contract passed\n";
  return 0;
}
