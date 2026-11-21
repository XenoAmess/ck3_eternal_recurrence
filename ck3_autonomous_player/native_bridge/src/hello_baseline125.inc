std::string BaselineHelloFrame125(const xar::game::GameAdapter &game,
                       std::uint64_t connection_generation) {
  const auto &descriptor = game.descriptor();
  std::string result =
      "{\"type\":\"hello\",\"protocol_version\":1,\"bridge_version\":\"";
  result += XAR_BRIDGE_VERSION;
  result += "\",\"pid\":";
  result += Number(GetCurrentProcessId());
  result +=
      ",\"session_generation\":0,\"connection_generation\":";
  result += Number(connection_generation);
  result += ",\"architecture\":\"x86_64-windows-msvc\","
      "\"expected_ck3_version\":";
  AppendJsonString(result, descriptor.game_version);
  result += ",\"expected_ck3_sha256\":";
  AppendJsonString(result, descriptor.executable_sha256);
  result += ",\"game_adapter_id\":";
  AppendJsonString(result, descriptor.adapter_id);
  result += ",\"game_adapter_status\":";
  AppendJsonString(result, game.enabled() ? "ready" : "unsupported_build");
  result += ",\"ck3_build_match\":";
  result += game.enabled() ? "true" : "false";
  result += ",\"capabilities\":[\"bridge.identity\",\"bridge.heartbeat\","
            "\"bridge.ping\"";
  if (game.enabled()) {
    for (const auto capability : descriptor.capabilities) {
      result += ',';
      AppendJsonString(result, capability);
    }
  }
  if (game.enabled() && xar::game::IsCk3_12004Descriptor(descriptor)) {
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kScriptedWidgetQueryCapability12004);
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kScriptedWidgetActionCapability12004);
  }
#if defined(XAR_ENABLE_RITE_CREATION_ACTIONS12004) && XAR_ENABLE_RITE_CREATION_ACTIONS12004
  if (game.enabled() && xar::game::IsCk3_12004Descriptor(descriptor)) {
    result += ',';
    AppendJsonString(result, xar::ck3_12004::religion::rite_creation_actions::domain_key);
  }
#endif
#if defined(XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1)
  // This capability describes only the closed typed partial source query.
  // It never advertises switch readiness or creates a stock-action admission.
  if(game.enabled() && descriptor.game_version==xar::ck3_12003::kGameVersion &&
      descriptor.executable_sha256==xar::ck3_12003::kExecutableSha256) {
    result += ',';
    AppendJsonString(result,xar::ck3_12003::kPlayerControlV1Capability);
  }
#endif
#if defined(XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1)
  if (game.enabled() && xar::game::IsCk3_12004Descriptor(descriptor)) {
    result += ',';
    AppendJsonString(result,
        xar::ck3_11906::kStewardshipFullFrontierCapabilityV2);
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kAllLifestyleFrontierCapabilityV3);
  }
#endif
#if defined(XAR_ENABLE_PREWAR_FORCE_COALITION_V2)
  // Read support is independent of complete force coverage or DECLARE admission.
  if (game.enabled() && descriptor.game_version == xar::ck3_12004::kGameVersion &&
      descriptor.executable_sha256 == xar::ck3_12004::kExecutableSha256) {
    result += ',';
    AppendJsonString(result, "game.command.query-prewar-force-coalition-coverage-v2-N");
  }
#endif
#if defined(XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1) && XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1
  if (game.enabled() && xar::game::IsCk3_12004Descriptor(descriptor)) {
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kWarDeclaredOverviewQueryV1Capability);
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kWarDeclaredOverviewCloseV1Capability);
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kWarResultsQueryV1Capability);
    result += ',';
    AppendJsonString(result, xar::ck3_11906::kWarResultsCloseV1Capability);
  }
#endif
#if defined(XAR_ENABLE_NATIVE_MANDATORY_CHOICE_V1)
  if (game.enabled() && xar::game::IsCk3_12004Descriptor(descriptor)) {
    result += ',';
    AppendJsonString(result,xar::mandatory_choice_v1::kCapability);
  }
#endif
  result += "]}";
  return result;
}