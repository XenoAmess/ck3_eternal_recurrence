#pragma once

#include "native_mandatory_choice_gate_v1.hpp"

#include <optional>

namespace xar::mandatory_choice_v1 {

struct ModalRoot {
  std::uintptr_t gui_context = 0;
  std::uintptr_t gui_owner = 0;
  std::uintptr_t receiver = 0;
  std::string window_id;
  std::string window_instance_id;
  std::string window_type;
  std::string source_identity;
  bool exclusive = false;
  bool blocks_input = false;
  std::string executable_sha256;
  std::uint64_t root_vtable_module_rva = 0;
  friend bool operator==(const ModalRoot &, const ModalRoot &) = default;
};

struct Widget {
  std::uintptr_t address = 0;
  std::uintptr_t parent = 0;
  std::uintptr_t gui_context = 0;
  std::string runtime_name;
  bool visible = false;
  bool enabled = false;
  bool button_base = false;
  bool decorative_role = false;
  std::vector<std::uintptr_t> children;
  std::uint64_t vtable_module_rva = 0;
};

// Production implementation must use the exact admitted .4 GUI owner,
// modal-vector, ButtonBase, dispatch-admission and GetRect ABI. ReadModalRoot
// must return the last effective-visible receiver only if it is the current
// exclusive input receiver. ReadRect must return native absolute GUI bounds.
struct NativeModalPort {
  virtual ~NativeModalPort() = default;
  virtual bool ReadModalRoot(ModalRoot &root) = 0;
  virtual bool ReadWidget(std::uintptr_t address, Widget &widget) = 0;
  virtual bool CallbackAdmitted(std::uintptr_t address) = 0;
  virtual bool ReadCallbackIdentity(std::uintptr_t address,
                                    std::vector<CallbackIdentity> &out) = 0;
  virtual bool ReadRect(std::uintptr_t address, Bounds &bounds) = 0;
};

std::optional<Observation> CollectTopModalChoices(
    const Frame &frame, NativeModalPort &port, std::string &reason);

} // namespace xar::mandatory_choice_v1
