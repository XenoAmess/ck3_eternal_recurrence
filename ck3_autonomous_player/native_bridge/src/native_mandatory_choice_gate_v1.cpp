#include "native_mandatory_choice_gate_v1.hpp"

#include <cmath>
#include <unordered_set>

namespace xar::mandatory_choice_v1 {
namespace {
bool ValidBounds(const Bounds &b) noexcept {
  return std::isfinite(b.left) && std::isfinite(b.top) &&
         std::isfinite(b.width) && std::isfinite(b.height) &&
         b.width > 0 && b.height > 0;
}
bool ValidNonce(std::string_view value) noexcept {
  if (value.size() < 32 || value.size() > 128) return false;
  for (char c : value)
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
          (c >= '0' && c <= '9') || c == '-' || c == '_')) return false;
  return true;
}
} // namespace

bool Qualified(const Observation &o, std::string &reason) {
  if (!o.frame.game_pid || !o.frame.connection_generation || !o.frame.revision ||
      !o.frame.native_revision || !o.frame.actor_character_id ||
      o.frame.episode_run_id.empty() || o.frame.snapshot_id.empty()) {
    reason = "frame_binding_incomplete"; return false;
  }
  if (!o.blocking_proof.verified || o.blocking_proof.kind == BlockerKind::none ||
      o.blocking_proof.source.empty() ||
      (o.blocking_proof.kind == BlockerKind::exclusive_modal_blocks_input &&
       !o.blocking_proof.receiver)) {
    reason = "blocking_proof_unverified"; return false;
  }
  if (o.window_id.empty() || o.window_instance_id.empty() ||
      o.source_identity.empty() || o.executable_sha256.size() != 64 ||
      !o.root_vtable_module_rva || !o.choices_complete || o.choices.empty() ||
      o.choices.size() > 256) {
    reason = "choice_census_incomplete"; return false;
  }
  std::unordered_set<std::string> ids;
  std::unordered_set<std::uintptr_t> targets;
  std::size_t eligible = 0;
  for (const auto &c : o.choices) {
    if (!c.native_target || c.choice_id.empty() || !ids.insert(c.choice_id).second ||
        !targets.insert(c.native_target).second) {
      reason = "choice_identity_unverified"; return false;
    }
    if (!c.is_choice || c.candidate_basis.empty() ||
        (c.visible && c.enabled &&
         (!c.actionable_callback_verified || !c.widget_vtable_module_rva ||
          c.callback_identities.empty()))) {
      reason = "actionable_modal_candidate_unverified"; return false;
    }
    for (const auto &callback : c.callback_identities)
      if (!callback.vtable_module_rva || !callback.function_module_rva) {
        reason = "callback_source_identity_unverified"; return false;
      }
    if (c.bounds && !ValidBounds(*c.bounds)) {
      reason = "choice_geometry_invalid"; return false;
    }
    if (c.visible && c.enabled) ++eligible;
  }
  if (!eligible) {reason = "no_visible_enabled_choice"; return false;}
  if (eligible > 1) {
    bool all_bounds = true, all_order = true;
    std::unordered_set<std::uint32_t> orders;
    for (const auto &c : o.choices) if (c.visible && c.enabled) {
      all_bounds &= c.bounds.has_value();
      all_order &= c.rendered_index && orders.insert(*c.rendered_index).second;
    }
    if (!all_bounds && (!all_order || o.rendered_order_source.empty())) {
      reason = "choice_presentation_order_unverified"; return false;
    }
  }
  reason.clear(); return true;
}

QueryResult Gate::Query(const Observation &o, const Nonce &nonce) {
  Clear(); QueryResult result{};
  std::string reason;
  try {
    if (!Qualified(o, reason)) {result.unavailable_reason = std::move(reason); return result;}
  } catch (...) {result.unavailable_reason = "qualification_exception"; return result;}
  if (!nonce) {result.unavailable_reason = "nonce_source_missing"; return result;}
  try {
    auto query_id = nonce();
    if (!ValidNonce(query_id)) {result.unavailable_reason = "query_nonce_invalid"; return result;}
    std::vector<std::string> tokens;
    tokens.reserve(o.choices.size());
    std::unordered_set<std::string> seen;
    seen.insert(query_id);
    for (std::size_t i = 0; i < o.choices.size(); ++i) {
      auto token = nonce();
      if (!ValidNonce(token) || !seen.insert(token).second) {
        result.unavailable_reason = "action_nonce_invalid_or_duplicate"; return result;
      }
      tokens.push_back(std::move(token));
    }
    pending_ = o; tokens_ = std::move(tokens); query_id_ = std::move(query_id);
    result.available = true; result.query_id = query_id_; result.frame = o.frame;
    result.blocking_proof = o.blocking_proof;
    result.window_id = o.window_id;
    result.window_instance_id = o.window_instance_id;
    result.window_type = o.window_type;
    result.source_identity = o.source_identity;
    result.executable_sha256 = o.executable_sha256;
    result.root_vtable_module_rva = o.root_vtable_module_rva;
    result.choices_complete = true;
    for (std::size_t i = 0; i < o.choices.size(); ++i) {
      const auto &c = o.choices[i];
      result.choices.push_back({c.choice_id, c.label,
                                c.visible && c.enabled ? tokens_[i] : std::string{},
                                c.visible, c.enabled, c.is_choice, c.bounds,
                                c.rendered_index, c.widget_vtable_module_rva,
                                c.callback_identities});
    }
  } catch (...) {Clear(); result = {}; result.unavailable_reason = "query_exception";}
  return result;
}

SelectResult Gate::Select(const SelectRequest &r, const Observe &observe,
                          const Dispatch &dispatch) {
  SelectResult result{};
  if (query_id_.empty() || r.query_id != query_id_ ||
      r.expected_frame != pending_.frame ||
      r.expected_window_instance_id != pending_.window_instance_id) {
    result.unavailable_reason = "query_or_frame_stale"; return result;
  }
  std::size_t match = tokens_.size();
  for (std::size_t i = 0; i < tokens_.size(); ++i)
    if (tokens_[i] == r.action_token) {match = i; break;}
  if (match == tokens_.size() || !pending_.choices[match].visible ||
      !pending_.choices[match].enabled) {
    result.unavailable_reason = "action_token_unpublished"; return result;
  }
  try {
    if (!observe || !dispatch || observe() != pending_) {
      Clear(); result.unavailable_reason = "native_observation_changed"; return result;
    }
    const auto target = pending_.choices[match].native_target;
    const auto choice_id = pending_.choices[match].choice_id;
    // At most one dispatch even if native invocation faults. A second query
    // needs a new observed frame and fresh choice census.
    Clear(); result.accepted = true; result.selected_choice_id = choice_id;
    result.dispatch_attempted = true;
    result.dispatch_invoked = dispatch(target, result.native_handled);
    result.verification_pending = result.dispatch_invoked;
    if (!result.dispatch_invoked)
      result.unavailable_reason = "native_dispatch_unknown_no_retry";
  } catch (...) {
    Clear(); result.unavailable_reason = "native_dispatch_exception_no_retry";
  }
  return result;
}

void Gate::Clear() noexcept {pending_ = {}; tokens_.clear(); query_id_.clear();}
} // namespace xar::mandatory_choice_v1
