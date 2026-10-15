#pragma once

#include "native_modal_choice_collector_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <algorithm>
#include <vector>

namespace xar::mandatory_choice_v1 {

enum class TypedWindowRelationStatus {
  unknown, not_applicable, same_typed_root, independent_top_modal,
};
struct TypedWindowRelation {
  TypedWindowRelationStatus status = TypedWindowRelationStatus::unknown;
  bool owner_verified = false;
  std::string source;
  std::uintptr_t top_root = 0;
  std::string typed_domain;
  std::int32_t typed_window_instance_id = -1;
  std::uintptr_t typed_root = 0;
};

// Both complete paths must terminate at the same actual GUI-owner root.
// Distinct sibling branches are independent; either ancestor relation is not.
inline TypedWindowRelationStatus ClassifyTypedRootPathsV1(
    const std::vector<std::uintptr_t> &top_to_owner,
    const std::vector<std::uintptr_t> &typed_to_owner) noexcept {
  if (top_to_owner.empty() || typed_to_owner.empty() ||
      top_to_owner.size() > 64 || typed_to_owner.size() > 64 ||
      top_to_owner.back() == 0 ||
      top_to_owner.back() != typed_to_owner.back())
    return TypedWindowRelationStatus::unknown;
  for (const auto *path : {&top_to_owner,&typed_to_owner})
    for (std::size_t i=0; i<path->size(); ++i)
      for (std::size_t j=i+1; j<path->size(); ++j)
        if ((*path)[i] == 0 || (*path)[i] == (*path)[j])
          return TypedWindowRelationStatus::unknown;
  if (std::find(top_to_owner.begin(), top_to_owner.end(),
                typed_to_owner.front()) != top_to_owner.end() ||
      std::find(typed_to_owner.begin(), typed_to_owner.end(),
                top_to_owner.front()) != typed_to_owner.end())
    return TypedWindowRelationStatus::same_typed_root;
  return TypedWindowRelationStatus::independent_top_modal;
}

// Construct and call only on the admitted CK3 application owner thread.
// The MCP payload never supplies a widget name, path, pointer or callback.
class Crozier12004ModalPort final : public NativeModalPort {
 public:
  Crozier12004ModalPort(
      const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
      ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept;
  bool Ready() const noexcept {return ready_;}
  bool ReadModalRoot(ModalRoot &root) override;
  bool ReadWidget(std::uintptr_t address, Widget &widget) override;
  bool CallbackAdmitted(std::uintptr_t address) override;
  bool ReadCallbackIdentity(std::uintptr_t address,
                            std::vector<CallbackIdentity> &out) override;
  bool ReadRect(std::uintptr_t address, Bounds &bounds) override;
  bool Dispatch(std::uintptr_t address, bool &native_handled) noexcept;
  bool ReadOldReceiverStillBlocking(std::uintptr_t receiver,
                                     bool &still_blocking) noexcept;
  TypedWindowRelation ReadActiveEventRootRelation(
      std::uintptr_t jomini_state, std::int32_t active_event_instance_id) noexcept;
  std::string_view LastDispatchStage() const noexcept {return last_dispatch_stage_;}
  std::uint32_t LastExceptionCode() const noexcept {return last_exception_code_;}

 private:
  const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment_;
  ck3_11906::ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch_;
  bool ready_ = false;
  ModalRoot cached_root_{};
  std::string_view last_dispatch_stage_ = "not_attempted";
  std::uint32_t last_exception_code_ = 0;
};

// Cheap read-only state for the ordinary semantic snapshot. `unknown` must
// remain unknown; it is not a false absence proof.
enum class ModalHintStatus {unknown, absent, present};
struct ModalHint {
  ModalHintStatus status = ModalHintStatus::unknown;
  std::uintptr_t receiver = 0;
  std::string source = "exact_stock_modal_receiver_vector";
  std::uint64_t native_revision = 0;
};
ModalHint ReadTopExclusiveModalHint12004V1(
    const ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::uint64_t native_revision) noexcept;
std::string NativeReceiverIdentityV1(std::uintptr_t receiver);
} // namespace xar::mandatory_choice_v1
