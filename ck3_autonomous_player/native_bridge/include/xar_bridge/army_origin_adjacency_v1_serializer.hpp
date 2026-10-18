#pragma once
#include "xar_bridge/army_origin_adjacency_v1.hpp"
#include <string>

namespace xar::game {
template<class Number, class JsonString>
inline void AppendArmyOriginAdjacencyV1(
    std::string &out, const ArmyOriginAdjacencyV1 &row,
    Number number, JsonString append_string) {
  const bool available = row.available && row.identity_before_after_match;
  const auto status = !available ? "unavailable" : row.truncated ? "truncated" : "available";
  out += "{\"schema_version\":1,\"source\":\"native_origin_province_map_node_rows_12004\","
      "\"input_basis\":\"preview_origin_province_native_adjacency_rows\",\"status\":";
  append_string(out, status);
  out += ",\"unavailable_reason\":";
  if (available && !row.truncated) out += "null";
  else append_string(out, available ? "origin_adjacency_row_budget_exhausted" : row.unavailable_reason);
  out += ",\"source_province_id\":" + number(row.source_province_id);
  const auto identity = [&](const char *key, const auto &value) {
    out += ",\"" + std::string(key) + "\":";
    if (value) append_string(out, "native:" + std::to_string(*value));
    else out += "null";
  };
  identity("source_province_identity", row.source_province_identity);
  identity("source_map_node_identity", row.source_map_node_identity);
  identity("adjacency_data_identity", row.adjacency_data_identity);
  out += ",\"native_count\":" + (row.native_count ? number(*row.native_count) : "null");
  out += ",\"published_row_limit\":64,\"observed_count\":";
  out += available && row.rows ? number(row.rows->size()) : "0";
  out += ",\"collection_complete\":" + std::string(available && row.collection_complete ? "true" : "false");
  out += ",\"truncated\":" + std::string(available && row.truncated ? "true" : "false");
  out += ",\"identity_before_after_match\":" + std::string(row.identity_before_after_match ? "true" : "false");
  out += ",\"rows\":";
  if (!available || !row.rows) out += "null";
  else {
    out += "[";
    bool first = true;
    for (const auto &item : *row.rows) {
      if (!first) out += ",";
      first = false;
      out += "{\"occurrence_index\":" + number(item.occurrence_index);
      out += ",\"target_province_id\":" + number(item.target_province_id) + "}";
    }
    out += "]";
  }
  out += ",\"native_condition_evaluated_for_rows\":false,\"route_legality_evaluated_for_rows\":false}";
}
} // namespace xar::game
