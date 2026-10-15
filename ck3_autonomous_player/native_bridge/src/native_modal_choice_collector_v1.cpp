#include "native_modal_choice_collector_v1.hpp"

#include <cmath>
#include <unordered_set>
#include <utility>

namespace xar::mandatory_choice_v1 {
std::optional<Observation> CollectTopModalChoices(
    const Frame &frame, NativeModalPort &port, std::string &reason) {
  try {
    ModalRoot root{};
    if (!port.ReadModalRoot(root) || !root.gui_context || !root.gui_owner ||
        !root.receiver || !root.exclusive || !root.blocks_input ||
        root.window_id.empty() || root.window_instance_id.empty() ||
        root.source_identity.empty() || root.executable_sha256.size() != 64 ||
        !root.root_vtable_module_rva) {
      reason = "exclusive_top_modal_unverified"; return std::nullopt;
    }
    Observation result{};
    result.frame = frame;
    result.blocking_proof = {BlockerKind::exclusive_modal_blocks_input, true,
                             "exact_stock_top_modal_receiver_input_capture",
                             root.receiver};
    result.window_id = root.window_id;
    result.window_instance_id = root.window_instance_id;
    result.window_type = root.window_type;
    result.source_identity = root.source_identity;
    result.executable_sha256 = root.executable_sha256;
    result.root_vtable_module_rva = root.root_vtable_module_rva;
    struct Pending {std::uintptr_t address = 0, parent = 0;};
    std::vector<Pending> queue{{root.receiver, 0}};
    std::unordered_set<std::uintptr_t> seen;
    std::size_t head = 0;
    while (head < queue.size()) {
      if (queue.size() > 2048 || result.choices.size() > 256) {
        reason = "modal_census_budget_exceeded"; return std::nullopt;
      }
      const auto current = queue[head++];
      Widget widget{};
      if (!current.address || !seen.insert(current.address).second ||
          !port.ReadWidget(current.address, widget) ||
          widget.address != current.address ||
          (current.parent && widget.parent != current.parent) ||
          widget.gui_context != root.gui_context ||
          widget.children.size() > 512) {
        reason = "modal_widget_tree_unstable_or_incomplete"; return std::nullopt;
      }
      if (widget.address != root.receiver && widget.button_base &&
          !widget.decorative_role) {
        Choice choice{};
        choice.native_target = widget.address;
        choice.choice_id = std::to_string(head - 1) + ":" + widget.runtime_name;
        choice.label = widget.runtime_name;
        choice.visible = widget.visible;
        choice.enabled = widget.enabled;
        choice.is_choice = true; // candidate role, not known business meaning
        choice.widget_vtable_module_rva = widget.vtable_module_rva;
        choice.candidate_basis =
            "exclusive_modal_descendant_ButtonBase_non_decorative";
        if (choice.visible && choice.enabled) {
          choice.actionable_callback_verified =
              port.CallbackAdmitted(widget.address);
          Bounds bounds{};
          if (!choice.actionable_callback_verified ||
              !choice.widget_vtable_module_rva ||
              !port.ReadCallbackIdentity(widget.address,
                                         choice.callback_identities) ||
              choice.callback_identities.empty()) {
            reason = "modal_button_callback_unverified";
            return std::nullopt;
          }
          // A sole actionable candidate needs no ordering geometry. If there
          // are multiple candidates, Qualified requires complete bounds.
          if (port.ReadRect(widget.address,bounds) &&
              std::isfinite(bounds.left) && std::isfinite(bounds.top) &&
              std::isfinite(bounds.width) && std::isfinite(bounds.height) &&
              bounds.width > 0 && bounds.height > 0)
            choice.bounds = bounds;
        }
        result.choices.push_back(std::move(choice));
      }
      if (queue.size() + widget.children.size() > 2048) {
        reason = "modal_census_budget_exceeded"; return std::nullopt;
      }
      for (auto child : widget.children) {
        if (!child) {reason = "modal_null_child"; return std::nullopt;}
        queue.push_back({child, widget.address});
      }
    }
    ModalRoot later{};
    if (!port.ReadModalRoot(later) || later != root) {
      reason = "modal_receiver_changed_during_census"; return std::nullopt;
    }
    result.choices_complete = true;
    if (!Qualified(result, reason)) return std::nullopt;
    return result;
  } catch (...) {
    reason = "modal_collector_exception"; return std::nullopt;
  }
}
} // namespace xar::mandatory_choice_v1
