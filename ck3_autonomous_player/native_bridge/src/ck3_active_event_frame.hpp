#pragma once
#include "xar_bridge/ck3_1210_adapter.hpp"
#include <algorithm>
#include <string>

namespace xar::bridge {
inline void AppendActiveEventFrame(std::string &result,const game::Snapshot &snapshot,
    const game::AdapterDescriptor *descriptor) {
  result += ",\"active_event\":";
  if (!snapshot.has_active_event) {
    result += "null";
    return;
  }
  if (descriptor && game::IsCk3_121003Full111Descriptor(*descriptor) &&
      std::ranges::find(descriptor->capabilities,ck3_121003::full111::kOrdinaryEventCapabilityV1) !=
          descriptor->capabilities.end()) {
    result += "{\"schema\":\"";
    result += ck3_121003::full111::kOrdinaryEventSchemaV1;
    result += "\",\"instance_id\":" + std::to_string(snapshot.active_event_instance_id);
    result += ",\"authored_option_count\":" + std::to_string(snapshot.active_event_option_count);
    result += '}';
    return;
  }
  result += "{\"instance_id\":" + std::to_string(snapshot.active_event_instance_id);
  result += ",\"option_count\":" + std::to_string(snapshot.active_event_option_count);
  result += ",\"option_indexes\":[";
  for (std::int32_t public_index=1; public_index<=snapshot.active_event_option_count; ++public_index) {
    if (public_index!=1) result += ',';
    result += std::to_string(public_index);
  }
  result += "]}";
}
}
