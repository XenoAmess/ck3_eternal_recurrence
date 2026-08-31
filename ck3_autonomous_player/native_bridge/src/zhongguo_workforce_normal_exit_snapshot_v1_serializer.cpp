#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

void AppendEscaped(std::string &output, std::string_view value) {
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output.append("\\\""); break;
    case '\\': output.append("\\\\"); break;
    case '\b': output.append("\\b"); break;
    case '\f': output.append("\\f"); break;
    case '\n': output.append("\\n"); break;
    case '\r': output.append("\\r"); break;
    case '\t': output.append("\\t"); break;
    default:
      if (character < 0x20) {
        constexpr char hex[] = "0123456789ABCDEF";
        output.append("\\u00");
        output.push_back(hex[(character >> 4) & 0x0F]);
        output.push_back(hex[character & 0x0F]);
      } else {
        output.push_back(static_cast<char>(character));
      }
    }
  }
  output.push_back('"');
}

struct ObjectWriter {
  std::string &output;
  bool first = true;

  explicit ObjectWriter(std::string &target) : output(target) {
    output.push_back('{');
  }
  ~ObjectWriter() { output.push_back('}'); }

  void Key(std::string_view key) {
    if (!first) output.push_back(',');
    first = false;
    AppendEscaped(output, key);
    output.push_back(':');
  }
};

void AppendBool(std::string &output, bool value) {
  output.append(value ? "true" : "false");
}

template <typename Value, typename AppendValue>
void AppendTyped(std::string &output,
                 const game::ZhongguoTypedValueV1<Value> &field,
                 AppendValue append_value) {
  ObjectWriter object(output);
  object.Key("status");
  AppendEscaped(output, field.available ? "available" : "unavailable");
  object.Key("value");
  if (field.available && field.value.has_value()) {
    append_value(output, *field.value);
  } else {
    output.append("null");
  }
  object.Key("unavailable_reason");
  if (field.available) {
    output.append("null");
  } else {
    AppendEscaped(output, field.unavailable_reason);
  }
}

void AppendInteger(std::string &output,
                   const game::ZhongguoTypedIntegerV1 &field) {
  AppendTyped(output, field,
              [](std::string &target, std::int64_t value) {
                target.append(std::to_string(value));
              });
}

void AppendBoolean(std::string &output,
                   const game::ZhongguoTypedBooleanV1 &field) {
  AppendTyped(output, field,
              [](std::string &target, bool value) { AppendBool(target, value); });
}

void IntegerField(ObjectWriter &object, std::string_view key,
                  const game::ZhongguoTypedIntegerV1 &field) {
  object.Key(key);
  AppendInteger(object.output, field);
}

void BooleanField(ObjectWriter &object, std::string_view key,
                  const game::ZhongguoTypedBooleanV1 &field) {
  object.Key(key);
  AppendBoolean(object.output, field);
}

void AppendPartition(std::string &output,
                     const game::ZhongguoWorkforceHcPartitionV1 &value) {
  ObjectWriter object(output);
  IntegerField(object, "authorized", value.authorized);
  IntegerField(object, "available", value.available);
  IntegerField(object, "reserved", value.reserved);
  IntegerField(object, "occupied", value.occupied);
  IntegerField(object, "frozen", value.frozen);
  IntegerField(object, "reclaimed", value.reclaimed);
}

std::string_view StatusName(
    game::ZhongguoWorkforceNormalExitSnapshotStatusV1 status) noexcept {
  return status == game::ZhongguoWorkforceNormalExitSnapshotStatusV1::available
             ? "available"
             : "unavailable";
}

std::string_view LifecycleName(
    game::ZhongguoWorkforceNormalExitLifecycleV1 lifecycle) noexcept {
  switch (lifecycle) {
  case game::ZhongguoWorkforceNormalExitLifecycleV1::pre: return "pre";
  case game::ZhongguoWorkforceNormalExitLifecycleV1::migrating:
    return "migrating";
  case game::ZhongguoWorkforceNormalExitLifecycleV1::sealed: return "sealed";
  case game::ZhongguoWorkforceNormalExitLifecycleV1::rehire_captured:
    return "rehire_captured";
  case game::ZhongguoWorkforceNormalExitLifecycleV1::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

void AppendSource(std::string &output,
                  const game::ZhongguoWorkforceNormalExitSourceV1 &value) {
  ObjectWriter object(output);
  IntegerField(object, "owner_character_id", value.owner_character_id);
  IntegerField(object, "subject_character_id", value.subject_character_id);
  IntegerField(object, "cycle_serial", value.cycle_serial);
  IntegerField(object, "case_serial", value.case_serial);
  IntegerField(object, "state", value.state);
  IntegerField(object, "route", value.route);
  IntegerField(object, "offer_gold", value.offer_gold);
  IntegerField(object, "receipt_serial", value.receipt_serial);
  IntegerField(object, "object_owner_character_id",
               value.object_owner_character_id);
  IntegerField(object, "object_subject_character_id",
               value.object_subject_character_id);
  IntegerField(object, "object_cycle_serial", value.object_cycle_serial);
  IntegerField(object, "object_receipt_case_serial",
               value.object_receipt_case_serial);
  IntegerField(object, "object_route", value.object_route);
  BooleanField(object, "object_active", value.object_active);
  BooleanField(object, "object_consumed", value.object_consumed);
  IntegerField(object, "consumer_receipt_case_serial",
               value.consumer_receipt_case_serial);
}

void AppendWorkflow(
    std::string &output,
    const game::ZhongguoWorkforceNormalExitWorkflowV1 &value) {
  ObjectWriter object(output);
  BooleanField(object, "pending", value.pending);
  IntegerField(object, "pending_owner_character_id",
               value.pending_owner_character_id);
  IntegerField(object, "pending_subject_character_id",
               value.pending_subject_character_id);
  IntegerField(object, "pending_cycle_serial", value.pending_cycle_serial);
  IntegerField(object, "pending_case_serial", value.pending_case_serial);
  IntegerField(object, "state", value.state);
  BooleanField(object, "pending_hc_migration_authorized",
               value.pending_hc_migration_authorized);
  object.Key("pending_hc_before");
  AppendPartition(output, value.pending_hc_before);
  IntegerField(object, "pending_slot_case_serial",
               value.pending_slot_case_serial);
}

void AppendCurrentHc(std::string &output,
                     const game::ZhongguoWorkforceCurrentHcV1 &value) {
  ObjectWriter object(output);
  object.Key("partition");
  AppendPartition(output, value.partition);
  BooleanField(object, "formal_active", value.formal_active);
  IntegerField(object, "formal_case_serial", value.formal_case_serial);
}

void AppendReceipt(
    std::string &output,
    const game::ZhongguoWorkforceNormalExitReceiptV1 &value) {
  ObjectWriter object(output);
  BooleanField(object, "active", value.active);
  BooleanField(object, "sealed", value.sealed);
  BooleanField(object, "published", value.published);
  BooleanField(object, "consumed", value.consumed);
  IntegerField(object, "consumed_operation", value.consumed_operation);
  IntegerField(object, "owner_character_id", value.owner_character_id);
  IntegerField(object, "subject_character_id", value.subject_character_id);
  IntegerField(object, "cycle_serial", value.cycle_serial);
  IntegerField(object, "case_serial", value.case_serial);
  IntegerField(object, "state", value.state);
  IntegerField(object, "receipt_id", value.receipt_id);
  IntegerField(object, "receipt_hash", value.receipt_hash);
  BooleanField(object, "hc_ledger_settled", value.hc_ledger_settled);
  BooleanField(object, "hc_destination_frozen", value.hc_destination_frozen);
  BooleanField(object, "hc_conservation_verified",
               value.hc_conservation_verified);
  object.Key("hc_before");
  AppendPartition(output, value.hc_before);
  object.Key("hc_after");
  AppendPartition(output, value.hc_after);
  BooleanField(object, "formal_hc_active_before",
               value.formal_hc_active_before);
  BooleanField(object, "formal_hc_active_after",
               value.formal_hc_active_after);
  IntegerField(object, "formal_hc_case_serial", value.formal_hc_case_serial);
}

void AppendRehire(std::string &output,
                  const game::ZhongguoWorkforceRehireExitV1 &value) {
  ObjectWriter object(output);
  IntegerField(object, "state", value.state);
  IntegerField(object, "subject_character_id", value.subject_character_id);
  IntegerField(object, "exit_owner_character_id",
               value.exit_owner_character_id);
  IntegerField(object, "exit_cycle_serial", value.exit_cycle_serial);
  IntegerField(object, "exit_case_serial", value.exit_case_serial);
  IntegerField(object, "exit_state", value.exit_state);
  IntegerField(object, "exit_receipt_id", value.exit_receipt_id);
  IntegerField(object, "exit_receipt_hash", value.exit_receipt_hash);
  BooleanField(object, "normal_exit_verified", value.normal_exit_verified);
  object.Key("exit_hc_before");
  AppendPartition(output, value.exit_hc_before);
  object.Key("exit_hc_after");
  AppendPartition(output, value.exit_hc_after);
  BooleanField(object, "exit_hc_destination_frozen",
               value.exit_hc_destination_frozen);
  BooleanField(object, "exit_hc_conservation_verified",
               value.exit_hc_conservation_verified);
  BooleanField(object, "exit_formal_hc_active_before",
               value.exit_formal_hc_active_before);
  BooleanField(object, "exit_formal_hc_active_after",
               value.exit_formal_hc_active_after);
  IntegerField(object, "exit_formal_hc_case_serial",
               value.exit_formal_hc_case_serial);
}

void AppendReadiness(
    std::string &output,
    const game::ZhongguoWorkforceNormalExitReadinessV1 &value) {
  ObjectWriter object(output);
  const auto field = [&](std::string_view key, bool ready) {
    object.Key(key);
    AppendBool(output, ready);
  };
  field("player_subject_binding_ready", value.player_subject_binding_ready);
  field("owner_binding_ready", value.owner_binding_ready);
  field("source_object_ready", value.source_object_ready);
  field("pending_snapshot_ready", value.pending_snapshot_ready);
  field("current_hc_partition_ready", value.current_hc_partition_ready);
  field("migration_delta_ready", value.migration_delta_ready);
  field("sealed_receipt_ready", value.sealed_receipt_ready);
  field("rehire_capture_ready", value.rehire_capture_ready);
  field("current_hc_matches_stage_ready",
        value.current_hc_matches_stage_ready);
  field("lifecycle_ready", value.lifecycle_ready);
  field("same_frame_ready", value.same_frame_ready);
  field("ready", value.ready);
}

void AppendProvenance(std::string &output) {
  ObjectWriter object(output);
  const auto string_field = [&](std::string_view key, std::string_view value) {
    object.Key(key);
    AppendEscaped(output, value);
  };
  string_field("game_version", "1.19.0.6");
  string_field(
      "executable_sha256",
      "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86");
  string_field("backend_id", kZhongguoWorkforceNormalExitSnapshotV1BackendId);
  string_field("consumer_id", kZhongguoWorkforceNormalExitSnapshotV1ConsumerId);
  string_field("allowlist_id",
               kZhongguoWorkforceNormalExitSnapshotV1AllowlistId);
  string_field("variable_context_for_scope_rva", "0x3329A40");
  string_field("variable_identifier_table_rva", "0x3B971A0");
  string_field("variable_identifier_lookup_rva", "0x3B97020");
  string_field("variable_identifier_name_rva", "0x3B97090");
  string_field("character_storage_slot_rva", "0x570C130");
  object.Key("subject_allowlist_count");
  output.append("94");
  object.Key("owner_allowlist_count");
  output.append("0");
  string_field("query_scope",
               "paused_received_self_workforce_normal_exit_lifecycle");
}

} // namespace

std::string SerializeZhongguoWorkforceNormalExitSnapshotV1(
    const game::ZhongguoWorkforceNormalExitSnapshotV1 &snapshot) {
  std::string output;
  output.reserve(16'384);
  ObjectWriter object(output);
  object.Key("schema_version");
  output.push_back('1');
  object.Key("status");
  AppendEscaped(output, StatusName(snapshot.status));
  object.Key("case_kind");
  AppendEscaped(output, snapshot.case_kind);
  object.Key("request_nonce");
  AppendEscaped(output, snapshot.request_nonce);
  object.Key("snapshot_revision");
  output.append(std::to_string(snapshot.snapshot_revision));
  object.Key("date_raw");
  output.append(std::to_string(snapshot.date_raw));
  object.Key("paused");
  AppendBool(output, snapshot.paused);
  object.Key("player_character_id");
  output.append(std::to_string(snapshot.player_character_id));
  object.Key("subject_character_id");
  output.append(std::to_string(snapshot.subject_character_id));
  object.Key("requested_owner_character_id");
  output.append(std::to_string(snapshot.requested_owner_character_id));
  object.Key("lifecycle");
  AppendEscaped(output, LifecycleName(snapshot.lifecycle));
  object.Key("source");
  AppendSource(output, snapshot.source);
  object.Key("workflow");
  AppendWorkflow(output, snapshot.workflow);
  object.Key("current_hc");
  AppendCurrentHc(output, snapshot.current_hc);
  object.Key("receipt");
  AppendReceipt(output, snapshot.receipt);
  object.Key("rehire");
  AppendRehire(output, snapshot.rehire);
  object.Key("readiness");
  AppendReadiness(output, snapshot.readiness);
  object.Key("unavailable_reason");
  if (snapshot.unavailable_reason.empty()) {
    output.append("null");
  } else {
    AppendEscaped(output, snapshot.unavailable_reason);
  }
  object.Key("provenance");
  AppendProvenance(output);
  return output;
}

} // namespace xar::ck3_11906
