// Included inside the existing context-source serializer detail namespace.

inline void Following2bca620BalanceJson(std::string &out, const game::ContextSourceFollowing2bca620BalanceV1 &p) {
  out += "{\"component_present\":";
  Boolean(out, p.component_present);
  out += ",\"balance_raw_q64\":";
  Number(out, p.balance_raw_q64);
  out += ",\"numeric_balance_q64\":";
  Number(out, p.numeric_balance_q64);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2bca620ClassifierJson(std::string &out, const game::ContextSourceFollowing2bca620ClassifierV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"index_raw_i32\":";
  Number(out, p.index_raw_i32);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2bca620ProviderJson(std::string &out, const game::ContextSourceFollowing2bca620ProviderV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"provider_loaded\":";
  Boolean(out, p.provider_loaded);
  out += ",\"count_raw\":";
  Number(out, p.count_raw);
  out += ",\"selection\":";
  HelperString(out, p.selection);
  out += ",\"definition_identity\":";
  HelperString(out, p.definition_identity);
  out += ",\"definition_magic_u32\":";
  Number(out, p.definition_magic_u32);
  out += ",\"admitted\":";
  Boolean(out, p.admitted);
  out += ",\"pc\":";
  AfterPcJson(out, p.pc);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}

inline void Following2bca620Json(std::string &out, const game::ContextSourceFollowing2bca620InputsV1 &p) {
  out += "{\"status\":";
  String(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":";
  out += std::to_string(p.character_id);
  out += ",\"balance_source\":";
  Following2bca620BalanceJson(out, p.balance_source);
  out += ",\"classifier\":";
  Following2bca620ClassifierJson(out, p.classifier);
  out += ",\"provider_selection\":";
  Following2bca620ProviderJson(out, p.provider_selection);
  out += ",\"reason\":";
  Reason(out, p.reason);
  out += '}';
}
