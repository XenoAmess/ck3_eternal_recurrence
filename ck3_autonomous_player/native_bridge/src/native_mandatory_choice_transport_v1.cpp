#include "xar_bridge/native_mandatory_choice_transport_v1.hpp"

#include "xar_bridge/ck3_12004_ingame_ui.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/native_mandatory_choice_controller_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/native_modal_choice_hint_policy_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <windows.h>

#include <limits>
#include <optional>
#include <string>
#include <string_view>

namespace xar::mandatory_choice_v1 {
namespace {

void String(std::string &out, std::string_view value) {
  out.push_back('"');
  for (unsigned char c : value) {
    if (c == '"' || c == '\\') {out.push_back('\\'); out.push_back(char(c));}
    else if (c < 0x20) {
      constexpr char hex[] = "0123456789abcdef";
      out += "\\u00"; out.push_back(hex[c >> 4]); out.push_back(hex[c & 15]);
    } else out.push_back(char(c));
  }
  out.push_back('"');
}
void Bool(std::string &out, bool value) {out += value ? "true" : "false";}
void Number(std::string &out, std::uint64_t value) {out += std::to_string(value);}
void Signed(std::string &out, std::int32_t value) {out += std::to_string(value);}

#if !defined(XAR_MANDATORY_CHOICE_WIRE_FIXTURE_ONLY)
bool Once(std::string_view body, std::string_view key) {
  const std::string needle = "\"" + std::string(key) + "\":";
  auto pos = body.find(needle);
  return pos != std::string_view::npos &&
         body.find(needle,pos+needle.size()) == std::string_view::npos;
}

bool Object(std::string_view body, std::string_view key,
            std::string_view &out) {
  out = {};
  if (!Once(body,key)) return false;
  const std::string needle = "\"" + std::string(key) + "\":";
  auto pos = body.find(needle)+needle.size();
  while (pos < body.size() && (body[pos] == ' ' || body[pos] == '\t' ||
                               body[pos] == '\r' || body[pos] == '\n')) ++pos;
  if (pos >= body.size() || body[pos] != '{') return false;
  const auto begin = pos;
  std::size_t depth = 0; bool quoted = false, escaped = false;
  for (; pos < body.size(); ++pos) {
    const char c = body[pos];
    if (quoted) {
      if (escaped) escaped = false;
      else if (c == '\\') escaped = true;
      else if (c == '"') quoted = false;
    } else if (c == '"') quoted = true;
    else if (c == '{') ++depth;
    else if (c == '}' && --depth == 0) {
      out = body.substr(begin,pos-begin+1);
      return out.size() <= 4096;
    }
  }
  return false;
}

bool Unsigned(std::string_view body, std::string_view key,
              std::uint64_t &out) {
  return Once(body,key) && xar::bridge::JsonUnsignedField(body,key,out);
}
bool Text(std::string_view body, std::string_view key, std::string &out,
          std::size_t maximum = 128) {
  return Once(body,key) && xar::bridge::JsonStringField(body,key,out,maximum);
}

bool ParseFrame(std::string_view body, Frame &frame) {
  std::uint64_t pid=0, generation=0, revision=0, native=0, date=0, actor=0;
  if (!Unsigned(body,"game_pid",pid) ||
      !Unsigned(body,"connection_generation",generation) ||
      !Unsigned(body,"revision",revision) ||
      !Unsigned(body,"native_revision",native) ||
      !Unsigned(body,"date_raw",date) ||
      !Unsigned(body,"actor_character_id",actor) ||
      !Text(body,"episode_run_id",frame.episode_run_id,64) ||
      !Text(body,"snapshot_id",frame.snapshot_id,128) ||
      !pid || pid > (std::numeric_limits<std::uint32_t>::max)() ||
      !generation || !revision || !native ||
      date > (std::numeric_limits<std::int32_t>::max)() ||
      !actor || actor > (std::numeric_limits<std::int32_t>::max)())
    return false;
  frame.game_pid = static_cast<std::uint32_t>(pid);
  frame.connection_generation = generation;
  frame.revision = revision;
  frame.native_revision = native;
  frame.date_raw = static_cast<std::int32_t>(date);
  frame.actor_character_id = static_cast<std::int32_t>(actor);
  return frame.episode_run_id.starts_with(
      "native-"+std::to_string(frame.actor_character_id)+"-");
}
#endif

void FrameJson(std::string &out, const Frame &frame) {
  out += "{\"game_pid\":"; Number(out,frame.game_pid);
  out += ",\"connection_generation\":"; Number(out,frame.connection_generation);
  out += ",\"revision\":"; Number(out,frame.revision);
  out += ",\"native_revision\":"; Number(out,frame.native_revision);
  out += ",\"date_raw\":"; Signed(out,frame.date_raw);
  out += ",\"actor_character_id\":"; Signed(out,frame.actor_character_id);
  out += ",\"episode_run_id\":"; String(out,frame.episode_run_id);
  out += ",\"snapshot_id\":"; String(out,frame.snapshot_id);
  out += '}';
}

void CallbackJson(std::string &out, const CallbackIdentity &callback) {
  out += "{\"vtable_module_rva\":";
  Number(out,callback.vtable_module_rva);
  out += ",\"function_module_rva\":";
  Number(out,callback.function_module_rva);
  out += '}';
}

void SourceJson(std::string &out, const QueryResult &query) {
  out += "{\"game_exe_sha256\":"; String(out,query.executable_sha256);
  out += ",\"backend_sha256\":null";
  out += ",\"native_adapter_id\":"; String(out,query.source_identity);
  out += ",\"root_runtime_name\":"; String(out,query.window_id);
  out += ",\"root_type\":"; String(out,query.window_type);
  out += ",\"root_vtable_module_rva\":";
  Number(out,query.root_vtable_module_rva);
  out += ",\"choice_catalogue\":[";
  for (std::size_t i=0;i<query.choices.size();++i) {
    if (i) out.push_back(',');
    const auto &choice = query.choices[i];
    out += "{\"role\":\"modal_button_candidate\",\"runtime_name\":";
    String(out,choice.label);
    out += ",\"widget_vtable_module_rva\":";
    Number(out,choice.widget_vtable_module_rva);
    out += ",\"callback_identities\":[";
    for (std::size_t j=0;j<choice.callback_identities.size();++j) {
      if (j) out.push_back(',');
      CallbackJson(out,choice.callback_identities[j]);
    }
    out += "]}";
  }
  out += "]}";
}

void RelationJson(std::string &out, const TypedWindowRelation &relation) {
  out += "{\"status\":";
  switch (relation.status) {
  case TypedWindowRelationStatus::independent_top_modal:
    String(out,"independent_top_modal"); break;
  case TypedWindowRelationStatus::same_typed_root:
    String(out,"same_typed_root"); break;
  case TypedWindowRelationStatus::not_applicable:
    String(out,"not_applicable"); break;
  default: String(out,"unknown"); break;
  }
  out += ",\"owner_verified\":"; Bool(out,relation.owner_verified);
  out += ",\"source\":"; String(out,relation.source);
  out += ",\"top_opaque_root_id\":";
  if (relation.top_root) String(out,NativeReceiverIdentityV1(relation.top_root));
  else out += "null";
  out += ",\"typed_domain\":";
  if (relation.typed_domain.empty()) out += "null";
  else String(out,relation.typed_domain);
  out += ",\"typed_window_instance_id\":";
  if (relation.typed_window_instance_id > 0)
    Number(out,relation.typed_window_instance_id);
  else out += "null";
  out += ",\"typed_opaque_root_id\":";
  if (relation.typed_root) String(out,NativeReceiverIdentityV1(relation.typed_root));
  else out += "null";
  out += '}';
}

void QueryJson(std::string &out, const QueryResult &query,
               const TypedWindowRelation &relation) {
  out += "{\"schema\":\"xar.native-mandatory-choice-window/v1\",";
  out += "\"query_id\":"; String(out,query.query_id);
  out += ",\"frame_binding\":"; FrameJson(out,query.frame);
  out += ",\"window_id\":"; String(out,query.window_id);
  out += ",\"window_instance_id\":";
  String(out,query.window_instance_id);
  out += ",\"window_type\":"; String(out,query.window_type);
  out += ",\"source_identity\":"; SourceJson(out,query);
  out += ",\"typed_window_relation\":"; RelationJson(out,relation);
  out += ",\"blocking_proof\":{\"kind\":";
  String(out,query.blocking_proof.kind == BlockerKind::exclusive_modal_blocks_input
      ? "exclusive_modal_blocks_input" : "blocks_simulation");
  out += ",\"verified\":"; Bool(out,query.blocking_proof.verified);
  out += ",\"source\":"; String(out,query.blocking_proof.source);
  out += ",\"receiver_identity\":";
  String(out,NativeReceiverIdentityV1(query.blocking_proof.receiver));
  out += "},\"choices_complete\":"; Bool(out,query.choices_complete);
  out += ",\"choices\":[";
  for (std::size_t i=0;i<query.choices.size();++i) {
    if (i) out.push_back(',');
    const auto &choice = query.choices[i];
    out += "{\"choice_id\":"; String(out,choice.choice_id);
    out += ",\"label\":"; String(out,choice.label);
    out += ",\"label_source\":\"native_runtime_name\",";
    out += "\"visible\":"; Bool(out,choice.visible);
    out += ",\"enabled\":"; Bool(out,choice.enabled);
    out += ",\"is_choice\":"; Bool(out,choice.is_choice);
    out += ",\"action_token\":"; String(out,choice.action_token);
    out += ",\"bounds\":";
    if (choice.bounds) {
      out += "{\"left\":"+std::to_string(choice.bounds->left)+
          ",\"top\":"+std::to_string(choice.bounds->top)+
          ",\"width\":"+std::to_string(choice.bounds->width)+
          ",\"height\":"+std::to_string(choice.bounds->height)+'}';
    } else out += "null";
    out += '}';
  }
  out += "]}";
}

#if !defined(XAR_MANDATORY_CHOICE_WIRE_FIXTURE_ONLY)
bool ScopeMatches(const MailboxContext &q, const game::Snapshot &snapshot,
                  const ck3_11906::MainThreadExecutionStampV1 &stamp,
                  const Frame &frame) {
  return q.game && snapshot == q.expected_snapshot &&
      snapshot.map_ready && snapshot.has_played_character &&
      snapshot.played_character_alive && snapshot.date_raw == stamp.date_raw &&
      snapshot.date_raw == frame.date_raw &&
      snapshot.played_character_id == frame.actor_character_id &&
      frame.game_pid == GetCurrentProcessId() &&
      frame.connection_generation == q.connection_generation &&
      frame.native_revision == q.state_revision;
}
#endif
} // namespace

#if !defined(XAR_MANDATORY_CHOICE_WIRE_FIXTURE_ONLY)
std::string_view PrepareMailbox(
    const game::GameAdapter &game, const game::Snapshot *previous_snapshot,
    std::string_view request_id, std::string_view step, std::string_view payload,
    std::uint64_t state_revision, std::uint64_t connection_generation,
    std::uintptr_t module_base,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox, Session &session,
    MailboxContext &q) noexcept {
  try {
    q = {};
    q.query_operation = step == kQueryStep;
    if (!q.query_operation && step != kSelectStep) return "invalid_mandatory_choice_step";
    if (request_id.empty() || request_id.size()>128 || !state_revision ||
        !connection_generation || session.connection_generation != connection_generation ||
        !previous_snapshot) return "mandatory_choice_session_or_snapshot_missing";
    std::uint64_t expected_native = 0;
    if (!Unsigned(payload,"expected_revision",expected_native) ||
        expected_native != state_revision) return "mandatory_choice_revision_stale";
    std::string_view body, frame_body;
    if (q.query_operation) {
      if (!Object(payload,"mandatory_choice_frame_binding",frame_body))
        return "mandatory_choice_query_frame_missing";
    } else {
      if (!Object(payload,"mandatory_choice_selection",body) ||
          !Object(body,"frame_binding",frame_body) ||
          !Text(body,"query_id",q.selection.query_id,128) ||
          !Text(body,"action_token",q.selection.action_token,128) ||
          !Text(body,"window_instance_id",q.selection.expected_window_instance_id,128))
        return "mandatory_choice_selection_invalid";
    }
    if (!ParseFrame(frame_body,q.requested_frame) ||
        q.requested_frame.native_revision != state_revision ||
        q.requested_frame.connection_generation != connection_generation ||
        q.requested_frame.game_pid != GetCurrentProcessId())
      return "mandatory_choice_frame_invalid";
    q.selection.expected_frame = q.requested_frame;
    game::Snapshot current{};
    if (!game::ReadSnapshot(game,current) || current != *previous_snapshot ||
        !current.map_ready ||
        !current.has_played_character || !current.played_character_alive ||
        current.date_raw != q.requested_frame.date_raw ||
        current.played_character_id != q.requested_frame.actor_character_id)
      return "mandatory_choice_current_scope_stale";
    if (!game::IsCk3_12004Descriptor(game.descriptor()) ||
        !ck3_12004::BindIngameUiImage12004V1(
            module_base,game.descriptor().executable_sha256).enabled)
      return "mandatory_choice_exact_build_unavailable";
    q.mailbox = &mailbox; q.game = &game; q.expected_snapshot = current;
    q.session = &session; q.request_id = request_id; q.step = step;
    q.state_revision = state_revision;
    q.connection_generation = connection_generation;
    q.environment = ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(
        module_base,true,ck3_11906::GuiAbiRevisionV1::crozier12004,
        game.descriptor().executable_sha256);
    q.dispatch = ck3_11906::BindZhongguoScoreboardActionDispatchEnvironmentV1(
        module_base,true,ck3_11906::GuiAbiRevisionV1::crozier12004);
    return {};
  } catch (...) {return "mandatory_choice_prepare_exception";}
}

bool ExecuteMailbox(void *opaque,
                    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *q = static_cast<MailboxContext *>(opaque);
  if (!q) return false;
  try {
    q->execution_stamp = stamp;
    q->completed = true;
    if (!q->mailbox || !q->game || !q->session || !q->ticket.sequence ||
        q->mailbox->executor_started_sequence.load(std::memory_order_acquire) !=
            q->ticket.sequence ||
        q->mailbox->published_sequence.load(std::memory_order_acquire) !=
            q->ticket.sequence ||
        !OwnerModalChoiceCommandAllowedV1(
            *q->mailbox,stamp,GetCurrentThreadId()) ||
        q->session->connection_generation != q->connection_generation) {
      q->unavailable_reason = "mandatory_choice_owner_unverified"; return true;
    }
    q->owner_verified = true;
    game::Snapshot before{};
    if (!game::ReadSnapshot(*q->game,before) ||
        !ScopeMatches(*q,before,stamp,q->requested_frame)) {
      q->unavailable_reason = "mandatory_choice_owner_scope_stale"; return true;
    }
    Crozier12004ModalPort port(q->environment,q->dispatch);
    if (!port.Ready()) {
      q->unavailable_reason = "mandatory_choice_native_gui_unavailable";
      return true;
    }
    if (q->query_operation) {
      q->session->gate.Clear();
      q->session->last_query_frame = q->requested_frame;
      q->session->last_receiver = 0;
      q->session->last_window_id.clear();
      q->session->last_window_instance_id.clear();
      q->session->last_typed_relation = {};
      std::string reason;
      auto observed = CollectTopModalChoices(q->requested_frame,port,reason);
      if (!observed) {q->unavailable_reason = reason; return true;}
      q->query_result = q->session->gate.Query(
          *observed,SecureNativeChoiceNonceV1);
      if (!q->query_result.available)
        q->unavailable_reason = q->query_result.unavailable_reason;
      else {
        if (before.has_active_event && !before.has_pending_character_interaction) {
          q->typed_relation = port.ReadActiveEventRootRelation(
              stamp.jomini_state,before.active_event_instance_id);
        } else if (before.has_active_event ||
                   before.has_pending_character_interaction) {
          q->typed_relation.status = TypedWindowRelationStatus::unknown;
          q->typed_relation.typed_domain = before.has_active_event
              ? "event_and_interaction" : "interaction";
          q->typed_relation.typed_window_instance_id = before.has_active_event
              ? before.active_event_instance_id
              : before.pending_character_interaction_id;
          q->typed_relation.top_root = observed->blocking_proof.receiver;
          q->typed_relation.source = "typed_interaction_gui_root_not_qualified";
        } else {
          q->typed_relation.status = TypedWindowRelationStatus::not_applicable;
          q->typed_relation.owner_verified = true;
          q->typed_relation.top_root = observed->blocking_proof.receiver;
          q->typed_relation.source = "fresh_snapshot_has_no_typed_event_or_interaction";
        }
        q->session->last_typed_relation = q->typed_relation;
        q->session->last_receiver = observed->blocking_proof.receiver;
        q->session->last_window_id = observed->window_id;
        q->session->last_window_instance_id = observed->window_instance_id;
      }
    } else {
      q->old_window_id = q->session->last_window_id;
      q->old_window_instance_id = q->session->last_window_instance_id;
      const auto &earlier_relation = q->session->last_typed_relation;
      if ((before.has_active_event || before.has_pending_character_interaction) &&
          earlier_relation.status !=
              TypedWindowRelationStatus::independent_top_modal) {
        q->session->gate.Clear();
        q->session->last_typed_relation = {};
        q->unavailable_reason = "mandatory_choice_known_typed_window_priority";
        return true;
      }
      if (earlier_relation.status ==
              TypedWindowRelationStatus::independent_top_modal) {
        ModalRoot current_top{};
        const bool same_top = port.ReadModalRoot(current_top) &&
            current_top.receiver == earlier_relation.top_root;
        const auto current_relation = before.has_active_event &&
              !before.has_pending_character_interaction && same_top
            ? port.ReadActiveEventRootRelation(
                  stamp.jomini_state,before.active_event_instance_id)
            : TypedWindowRelation{};
        if (current_relation.status != earlier_relation.status ||
            !current_relation.owner_verified ||
            current_relation.typed_window_instance_id !=
                earlier_relation.typed_window_instance_id ||
            current_relation.top_root != earlier_relation.top_root ||
            current_relation.typed_root != earlier_relation.typed_root) {
          q->session->gate.Clear();
          q->session->last_typed_relation = {};
          q->unavailable_reason = "mandatory_choice_typed_root_relation_stale";
          return true;
        }
      }
      auto observe = [&]() -> Observation {
        game::Snapshot fresh{};
        if (!game::ReadSnapshot(*q->game,fresh) ||
            !ScopeMatches(*q,fresh,stamp,q->session->last_query_frame))
          return {};
        std::string reason;
        auto result = CollectTopModalChoices(
            q->session->last_query_frame,port,reason);
        return result.value_or(Observation{});
      };
      q->select_result = q->session->gate.Select(
          q->selection,observe,
          [&](std::uintptr_t target,bool &native_handled) {
            return port.Dispatch(target,native_handled);
          });
      q->dispatch_stage = port.LastDispatchStage();
      q->dispatch_exception_code = port.LastExceptionCode();
      if (q->select_result.dispatch_attempted && q->session->last_receiver) {
        q->old_receiver_read = port.ReadOldReceiverStillBlocking(
            q->session->last_receiver,q->old_receiver_still_registered);
      }
      if (!q->select_result.accepted)
        q->unavailable_reason = q->select_result.unavailable_reason;
      q->session->last_query_frame = {};
      q->session->last_receiver = 0;
      q->session->last_window_id.clear();
      q->session->last_window_instance_id.clear();
      q->session->last_typed_relation = {};
    }
    return true;
  } catch (...) {
    q->unavailable_reason = "mandatory_choice_executor_exception_no_retry";
    if (q->session) q->session->gate.Clear();
    return true;
  }
}
#endif

std::string CommandResultFrame(const MailboxContext &q) {
  std::string out = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  String(out,q.request_id);
  out += ",\"ok\":true,\"result\":{\"step\":"; String(out,q.step);
  out += ",\"accepted\":";
  Bool(out,q.query_operation ? q.query_result.available : q.select_result.accepted);
  out += ",\"status\":";
  String(out,q.query_operation
      ? q.query_result.available ? "available" : "unavailable"
      : q.select_result.verification_pending ? "verification_pending" : "unavailable");
  out += ",\"owner_verified\":"; Bool(out,q.owner_verified);
  out += ",\"queried_snapshot_id\":"; String(out,q.requested_frame.snapshot_id);
  out += ",\"queried_revision\":"; Number(out,q.requested_frame.revision);
  out += ",\"queried_native_revision\":";
  Number(out,q.requested_frame.native_revision);
  out += ",\"unavailable_reason\":"; String(out,q.unavailable_reason);
  if (q.query_operation) {
    out += ",\"mandatory_choice\":";
    if (q.query_result.available) QueryJson(out,q.query_result,q.typed_relation);
    else out += "null";
  } else {
    out += ",\"selected_choice_id\":";
    String(out,q.select_result.selected_choice_id);
    out += ",\"dispatch_attempted\":";
    Bool(out,q.select_result.dispatch_attempted);
    out += ",\"dispatch_invoked\":";
    Bool(out,q.select_result.dispatch_invoked);
    out += ",\"native_handled\":";
    Bool(out,q.select_result.native_handled);
    out += ",\"verification_pending\":";
    Bool(out,q.select_result.verification_pending);
    out += ",\"dispatch_stage\":"; String(out,q.dispatch_stage);
    out += ",\"dispatch_exception_code\":";
    Number(out,q.dispatch_exception_code);
    out += ",\"mandatory_choice_postcondition\":{\"verified\":";
    Bool(out,q.old_receiver_read);
    out += ",\"old_window_id\":"; String(out,q.old_window_id);
    out += ",\"old_instance\":"; String(out,q.old_window_instance_id);
    out += ",\"selected_choice_id\":";
    String(out,q.select_result.selected_choice_id);
    out += ",\"old_window_no_longer_blocking\":";
    Bool(out,q.old_receiver_read && !q.old_receiver_still_registered);
    out += ",\"source\":\"fresh_native_modal_receiver_vector_no_old_widget_dereference\"}";
  }
  out += "}}";
  return out;
}

} // namespace xar::mandatory_choice_v1
