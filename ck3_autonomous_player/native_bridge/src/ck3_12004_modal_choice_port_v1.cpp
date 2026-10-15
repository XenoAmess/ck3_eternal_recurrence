#include "ck3_12004_modal_choice_port_v1.hpp"

#include "xar_bridge/ck3_12004_ingame_ui.hpp"
#include "xar_bridge/ck3_12004_event_window_context.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"

#include <Windows.h>
#include <bcrypt.h>

#include <array>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>
#include <unordered_set>

#if defined(_MSC_VER)
#pragma comment(lib, "bcrypt.lib")
#endif

namespace xar::mandatory_choice_v1 {
namespace {
using namespace ck3_11906;
constexpr std::uintptr_t kRectGetterRva = 0x3A75EA0;
constexpr std::size_t kRectGetterLength = 0x114;
constexpr std::string_view kRectGetterSha256 =
    "7a5c5c374af2aded4bc88ee6ae9a6e0ac7223780e047590662886ed16e1a7883";
constexpr std::string_view kExactExeSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
// CEventWindow vtable slot 9 (RVA 0x182A120) obtains the actual GUI widget
// from the admitted GUI factory and stores it at controller+0x60. Its inline
// event data begins at +0xB8; the controller itself is not a GUI widget.
constexpr std::size_t kEventControllerGuiRootOffset = 0x60;
constexpr std::size_t kEventControllerInstanceIdOffset = 0xB8;
constexpr std::size_t kEventManagerFromIdlerOffset = 0x28;
constexpr std::size_t kEventManagerWindowsOffset = 0x18;
constexpr std::size_t kEventManagerWindowCountOffset = 0x24;
using RectGetter = UiRectV1 *(__fastcall *)(void *, UiRectV1 *, const UiRectV1 *);

bool CallPinnedRectGetter(std::uintptr_t module_base, void *widget,
                          UiRectV1 &rect, const UiRectV1 &local) noexcept {
#if defined(_MSC_VER)
  __try {
    auto getter = reinterpret_cast<RectGetter>(module_base + kRectGetterRva);
    return getter(widget, &rect, &local) == &rect;
  } __except(EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  (void)module_base; (void)widget; (void)rect; (void)local;
  return false;
#endif
}

bool Bytes(const void *source, void *destination, std::size_t count) noexcept {
  SIZE_T got = 0;
  return source && destination && count &&
         ReadProcessMemory(GetCurrentProcess(), source, destination, count, &got) &&
         got == count;
}
template<class T> bool Read(const void *source, std::size_t offset, T &value) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(source);
  return address && offset <= (std::numeric_limits<std::uintptr_t>::max)() - address &&
         Bytes(reinterpret_cast<void *>(address + offset), &value, sizeof(value));
}
bool HashRectGetter(std::uintptr_t base) noexcept {
  std::array<std::uint8_t,kRectGetterLength> bytes{};
  if (!base || !Bytes(reinterpret_cast<void *>(base + kRectGetterRva),
                      bytes.data(), bytes.size())) return false;
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  DWORD object_size = 0, actual = 0;
  std::array<unsigned char,32> digest{};
  bool valid = false;
  if (BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0 &&
      BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,
          reinterpret_cast<PUCHAR>(&object_size),sizeof(object_size),&actual,0)>=0 &&
      actual==sizeof(object_size) && object_size>0 && object_size<=65536) {
    std::array<unsigned char,65536> object{};
    if (BCryptCreateHash(algorithm,&hash,object.data(),object_size,nullptr,0,0)>=0 &&
        BCryptHashData(hash,bytes.data(),static_cast<ULONG>(bytes.size()),0)>=0 &&
        BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0)>=0) {
      constexpr char hex[] = "0123456789abcdef";
      std::array<char,64> actual_hash{};
      for (std::size_t i = 0; i < digest.size(); ++i) {
        actual_hash[2*i] = hex[digest[i] >> 4];
        actual_hash[2*i+1] = hex[digest[i] & 15];
      }
      valid = std::string_view(actual_hash.data(),actual_hash.size()) ==
              kRectGetterSha256;
    }
  }
  if (hash) BCryptDestroyHash(hash);
  if (algorithm) BCryptCloseAlgorithmProvider(algorithm,0);
  return valid;
}
std::string PointerId(std::uintptr_t value) {
  std::ostringstream out; out << "0x" << std::hex << value; return out.str();
}
bool Decoration(std::string_view name) noexcept {
  // These are presentation controls, not an unknown business choice.
  for (std::string_view role : {"close_button", "close", "help", "help_button",
                                "back", "back_button", "minimize_button",
                                "pin_button", "drag_handle"})
    if (name == role) return true;
  return false;
}
bool ImageRva(std::uintptr_t base, void *pointer, std::uint64_t &rva) noexcept {
  rva = 0;
  const auto address = reinterpret_cast<std::uintptr_t>(pointer);
  if (!base || address < base ||
      address - base >= GuiExactImageSizeV1(GuiAbiRevisionV1::crozier12004))
    return false;
  rva = address - base;
  return rva != 0;
}
#if defined(_MSC_VER)
int CaptureModalCallbackException(std::uint32_t &code,
                                  EXCEPTION_POINTERS *information) noexcept {
  code = information && information->ExceptionRecord
      ? information->ExceptionRecord->ExceptionCode : 0;
  return EXCEPTION_EXECUTE_HANDLER;
}
#endif
bool CallSingleModalCallback(void *callback, void *function, void *button,
                             std::string_view &stage,
                             std::uint32_t &exception_code) noexcept {
  stage = "preflight_rejected"; exception_code = 0;
  if (!callback || !function || !button) return false;
  using Callback = void(__fastcall *)(void *, void **);
  auto invoke = reinterpret_cast<Callback>(function);
  void *widget = button;
#if defined(_MSC_VER)
  __try {
    stage = "callback_entered";
    invoke(callback, &widget);
    stage = "callback_returned";
    return true;
  } __except(CaptureModalCallbackException(
      exception_code,GetExceptionInformation())) {
    stage = "callback_exception";
    return false;
  }
#else
  stage = "callback_entered";
  invoke(callback, &widget);
  stage = "callback_returned";
  return true;
#endif
}
bool ReadTop(const ZhongguoScoreboardNativeEnvironmentV1 &environment,
             void *&context, void *&owner, void *&receiver,
             bool &has_any) {
  context = owner = receiver = nullptr; has_any = false;
  if (!environment.exact_build_admitted ||
      environment.offline_fixture_function_overrides ||
      environment.gui_abi_revision != GuiAbiRevisionV1::crozier12004 ||
      environment.executable_sha256 != kExactExeSha256 ||
      !ck3_12004::BindIngameUiImage12004V1(environment.module_base,
                                             environment.executable_sha256).enabled)
    return false;
  ZhongguoScoreboardAccessV1 access{};
  if (!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(
          environment,access,context,owner) || !context || !owner) return false;
  void **entries = nullptr, **later_entries = nullptr;
  std::int32_t count = 0, later_count = 0;
  if (!Read(context,kZhongguoGuiModalReceiversOffset,entries) ||
      !Read(context,kZhongguoGuiModalReceiverCountOffset,count) ||
      count < 0 || count > 256 || (count && !entries)) return false;
  has_any = count > 0;
  if (!count) {
    return Read(context,kZhongguoGuiModalReceiversOffset,later_entries) &&
           Read(context,kZhongguoGuiModalReceiverCountOffset,later_count) &&
           later_entries == entries && later_count == 0;
  }
  std::unordered_set<void *> seen;
  for (std::int32_t i = 0; i < count; ++i) {
    void *item = nullptr; std::uint8_t flags = 0;
    if (!Read(entries,std::size_t(i)*sizeof(void *),item) || !item ||
        !seen.insert(item).second ||
        !Read(item,kZhongguoWidgetHiddenFlagsOffset,flags)) return false;
    if (i == count - 1 && !(flags & kZhongguoWidgetEffectiveHiddenMask))
      receiver = item;
  }
  if (!Read(context,kZhongguoGuiModalReceiversOffset,later_entries) ||
      !Read(context,kZhongguoGuiModalReceiverCountOffset,later_count) ||
      later_entries != entries || later_count != count) return false;
  void *later_top = nullptr;
  std::uint8_t later_flags = 0;
  if (!Read(entries,std::size_t(count-1)*sizeof(void *),later_top) ||
      !later_top || !Read(later_top,kZhongguoWidgetHiddenFlagsOffset,later_flags) ||
      ((later_flags & kZhongguoWidgetEffectiveHiddenMask) == 0) !=
          (receiver != nullptr) ||
      (receiver && later_top != receiver))
    return false;
  return true;
}

bool PathToOwnerRoot(void *first, void *owner_root, void *context,
                     std::vector<std::uintptr_t> &path) noexcept {
  path.clear();
  if (!first || !owner_root || !context) return false;
  std::unordered_set<void *> seen;
  void *current = first;
  for (std::size_t depth=0; current && depth<64; ++depth) {
    void *actual_context = nullptr, *parent = nullptr;
    if (!seen.insert(current).second ||
        !Read(current,kZhongguoWidgetGuiContextOffset,actual_context) ||
        actual_context != context) return false;
    path.push_back(reinterpret_cast<std::uintptr_t>(current));
    if (current == owner_root) return true;
    if (!Read(current,kZhongguoWidgetParentOffset,parent)) return false;
    current = parent;
  }
  return false;
}
} // namespace

Crozier12004ModalPort::Crozier12004ModalPort(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept
    : environment_(environment), dispatch_(dispatch) {
  ready_ = environment_.module_base && environment_.exact_build_admitted &&
           !environment_.offline_fixture_function_overrides &&
           environment_.gui_abi_revision == GuiAbiRevisionV1::crozier12004 &&
           environment_.executable_sha256 == kExactExeSha256 &&
           dispatch_.module_base == environment_.module_base &&
           dispatch_.exact_build_admitted &&
           !dispatch_.offline_fixture_function_overrides &&
           dispatch_.gui_abi_revision == environment_.gui_abi_revision &&
           dispatch_.button_base_slot13 &&
           HashRectGetter(environment_.module_base);
}

bool Crozier12004ModalPort::ReadModalRoot(ModalRoot &root) {
  root = {};
  if (!ready_) return false;
  void *context = nullptr, *owner = nullptr, *receiver = nullptr;
  bool has_any = false;
  if (!ReadTop(environment_,context,owner,receiver,has_any) || !receiver) return false;
  ZhongguoScoreboardAccessV1 access{};
  std::string name; void *vtable = nullptr;
  bool visible = false, enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access,receiver,name,vtable,visible,enabled) ||
      !visible) return false;
  root.gui_context = reinterpret_cast<std::uintptr_t>(context);
  root.gui_owner = reinterpret_cast<std::uintptr_t>(owner);
  root.receiver = reinterpret_cast<std::uintptr_t>(receiver);
  root.window_id = name.empty() ? "native_modal_receiver" : name;
  root.window_instance_id = PointerId(root.receiver);
  root.window_type = "exclusive_modal_receiver";
  root.source_identity = "ck3-1.20.0.4-exact-native-gui";
  root.executable_sha256 = environment_.executable_sha256;
  if (!ImageRva(environment_.module_base,vtable,
                root.root_vtable_module_rva)) return false;
  root.exclusive = true; root.blocks_input = true;
  cached_root_ = root;
  return true;
}

bool Crozier12004ModalPort::ReadWidget(std::uintptr_t address, Widget &widget) {
  widget = {};
  if (!ready_ || !address) return false;
  const auto &root = cached_root_;
  if (!root.receiver) return false;
  ZhongguoScoreboardAccessV1 access{};
  void *target = reinterpret_cast<void *>(address), *vtable = nullptr;
  if (!ReadGuiWidgetRuntimeV1(access,target,widget.runtime_name,vtable,
                              widget.visible,widget.enabled) || !vtable) return false;
  void *context = nullptr, *parent = nullptr, **children = nullptr, *slot13 = nullptr;
  std::int32_t count = 0;
  if (!Read(target,kZhongguoWidgetGuiContextOffset,context) ||
      reinterpret_cast<std::uintptr_t>(context) != root.gui_context ||
      !Read(target,kZhongguoWidgetParentOffset,parent) ||
      !Read(target,kZhongguoWidgetChildrenOffset,children) ||
      !Read(target,kZhongguoWidgetChildCountOffset,count) ||
      count < 0 || count > 512 || (count && !children) ||
      !Read(vtable,13*sizeof(void *),slot13)) return false;
  widget.address = address;
  widget.parent = reinterpret_cast<std::uintptr_t>(parent);
  widget.gui_context = reinterpret_cast<std::uintptr_t>(context);
  widget.button_base = slot13 == dispatch_.button_base_slot13;
  if (!ImageRva(environment_.module_base,vtable,
                widget.vtable_module_rva)) return false;
  widget.decorative_role = widget.button_base && Decoration(widget.runtime_name);
  for (std::int32_t i = 0; i < count; ++i) {
    void *child = nullptr;
    if (!Read(children,std::size_t(i)*sizeof(void *),child)) return false;
    if (child) widget.children.push_back(reinterpret_cast<std::uintptr_t>(child));
  }
  return true;
}

bool Crozier12004ModalPort::CallbackAdmitted(std::uintptr_t address) {
  if (!ready_ || !address) return false;
  Widget widget{};
  if (!ReadWidget(address,widget) || !widget.visible || !widget.enabled ||
      !widget.button_base || widget.decorative_role) return false;
  void *vtable = nullptr;
  return Read(reinterpret_cast<void *>(address),0,vtable) && vtable &&
         InspectFixedGuiWidgetDispatchAdmissionV1(
             dispatch_,reinterpret_cast<void *>(address),vtable);
}

bool Crozier12004ModalPort::ReadCallbackIdentity(
    std::uintptr_t address, std::vector<CallbackIdentity> &out) {
  out.clear();
  if (!ready_ || !address) return false;
  auto *target = reinterpret_cast<void *>(address);
  std::int32_t primary_count = 0, count = 0;
  if (!Read(target,kZhongguoPrimaryCallbackGroupOffset +
                       kZhongguoCallbackGroupCountOffset,primary_count) ||
      primary_count < 0 || primary_count > 1) return false;
  if (primary_count == 0) {
    // Slot 13's fallback is the first invoked handler only if all three
    // intermediate groups are empty, as in the fixed B16 Dismiss adapter.
    for (std::size_t offset : {0x2Cu, 0x4Cu, 0x6Cu}) {
      std::int32_t intermediate_count = -1;
      if (!Read(target,kZhongguoPrimaryCallbackGroupOffset+offset,
                intermediate_count) || intermediate_count != 0) return false;
    }
  }
  const auto group = primary_count > 0 ? kZhongguoPrimaryCallbackGroupOffset :
      kZhongguoFallbackCallbackGroupOffset;
  count = primary_count;
  if (primary_count == 0 &&
      (!Read(target,group+kZhongguoCallbackGroupCountOffset,count) ||
       count != 1)) return false;
  if (count != 1) return false;
  void *rows = nullptr;
  if (!Read(target,group+kZhongguoCallbackGroupDataOffset,rows) || !rows)
    return false;
  for (std::int32_t index = 0; index < count; ++index) {
    void *callback = nullptr, *vtable = nullptr, *function = nullptr;
    CallbackIdentity identity{};
    if (!Read(rows,std::size_t(index)*kZhongguoCallbackStride+
                    kZhongguoCallbackObjectOffset,callback) || !callback ||
        !Read(callback,0,vtable) || !vtable ||
        !Read(vtable,kZhongguoCallbackVtableSlot2Offset,function) ||
        !ImageRva(environment_.module_base,vtable,identity.vtable_module_rva) ||
        !ImageRva(environment_.module_base,function,identity.function_module_rva))
      return false;
    out.push_back(identity);
  }
  void *widget_vtable = nullptr;
  return Read(target,0,widget_vtable) && widget_vtable &&
         InspectFixedGuiWidgetDispatchAdmissionV1(
             dispatch_,target,widget_vtable);
}

bool Crozier12004ModalPort::ReadRect(std::uintptr_t address, Bounds &bounds) {
  bounds = {};
  if (!ready_ || !address) return false;
  const auto &root = cached_root_;
  if (!root.receiver) return false;
  void *widget = reinterpret_cast<void *>(address);
  std::unordered_set<void *> seen;
  bool reached = false;
  for (std::size_t depth = 0; widget && depth < 64; ++depth) {
    void *context = nullptr, *parent = nullptr;
    float scale = 0, cumulative = 0;
    if (!seen.insert(widget).second ||
        !Read(widget,kZhongguoWidgetGuiContextOffset,context) ||
        reinterpret_cast<std::uintptr_t>(context) != root.gui_context ||
        !Read(widget,0x110,scale) || !Read(widget,0x114,cumulative) ||
        !std::isfinite(scale) || !std::isfinite(cumulative) ||
        scale <= 0 || scale > 64 || cumulative <= 0 || cumulative > 4096 ||
        !Read(widget,kZhongguoWidgetParentOffset,parent)) return false;
    if (reinterpret_cast<std::uintptr_t>(widget) == root.receiver) reached = true;
    widget = parent;
  }
  if (!reached || widget) return false;
  UiRectV1 local{},rect{};
  if (!Read(reinterpret_cast<void *>(address),0x128,local.width) ||
      !Read(reinterpret_cast<void *>(address),0x12C,local.height) ||
      !std::isfinite(local.width) || !std::isfinite(local.height) ||
      local.width <= 0 || local.height <= 0) return false;
  if (!CallPinnedRectGetter(environment_.module_base,
                            reinterpret_cast<void *>(address), rect, local))
    return false;
  if (!std::isfinite(rect.x) || !std::isfinite(rect.y) ||
      !std::isfinite(rect.width) || !std::isfinite(rect.height) ||
      rect.width <= 0 || rect.height <= 0 ||
      std::abs(rect.x) > 65536 || std::abs(rect.y) > 65536 ||
      rect.width > 65536 || rect.height > 65536) return false;
  float viewport_width = 0, viewport_height = 0;
  if (!Read(reinterpret_cast<void *>(root.gui_context),0x3C0,viewport_width) ||
      !Read(reinterpret_cast<void *>(root.gui_context),0x3C4,viewport_height) ||
      !std::isfinite(viewport_width) || !std::isfinite(viewport_height) ||
      viewport_width <= 0 || viewport_height <= 0 ||
      viewport_width > 65536 || viewport_height > 65536 ||
      rect.x + rect.width <= 0 || rect.y + rect.height <= 0 ||
      rect.x >= viewport_width || rect.y >= viewport_height) return false;
  bounds = {rect.x,rect.y,rect.width,rect.height};
  return true;
}

bool Crozier12004ModalPort::Dispatch(std::uintptr_t address,
                                     bool &native_handled) noexcept {
  native_handled = false;
  last_dispatch_stage_ = "preflight_rejected";
  last_exception_code_ = 0;
  try {
  if (!ready_ || !address || !CallbackAdmitted(address)) return false;
  std::vector<CallbackIdentity> identities;
  if (!ReadCallbackIdentity(address,identities) || identities.size() != 1)
    return false;
  auto *target = reinterpret_cast<void *>(address);
  std::int32_t primary_count = 0;
  void *rows = nullptr, *callback = nullptr, *vtable = nullptr, *function = nullptr;
  if (!Read(target,kZhongguoPrimaryCallbackGroupOffset+
                       kZhongguoCallbackGroupCountOffset,primary_count))
    return false;
  const auto group = primary_count > 0 ? kZhongguoPrimaryCallbackGroupOffset :
      kZhongguoFallbackCallbackGroupOffset;
  std::uint64_t vtable_rva = 0, function_rva = 0;
  if (!Read(target,group+kZhongguoCallbackGroupDataOffset,rows) || !rows ||
      !Read(rows,kZhongguoCallbackObjectOffset,callback) || !callback ||
      !Read(callback,0,vtable) || !vtable ||
      !Read(vtable,kZhongguoCallbackVtableSlot2Offset,function) || !function ||
      !ImageRva(environment_.module_base,vtable,vtable_rva) ||
      !ImageRva(environment_.module_base,function,function_rva) ||
      identities[0] != CallbackIdentity{vtable_rva,function_rva})
    return false;
  // A callback may destroy target. This call never reads target afterwards.
  native_handled = CallSingleModalCallback(callback,function,target,
                                           last_dispatch_stage_,last_exception_code_);
  return native_handled;
  } catch (...) {return false;}
}

bool Crozier12004ModalPort::ReadOldReceiverStillBlocking(
    std::uintptr_t receiver, bool &still_blocking) noexcept {
  still_blocking = false;
  try {
    if (!ready_ || !receiver) return false;
    ZhongguoScoreboardAccessV1 access{};
    void *context = nullptr, *owner = nullptr;
    if (!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(
            environment_,access,context,owner) || !context || !owner)
      return false;
    void **entries = nullptr, **later_entries = nullptr;
    std::int32_t count = 0, later_count = 0;
    if (!Read(context,kZhongguoGuiModalReceiversOffset,entries) ||
        !Read(context,kZhongguoGuiModalReceiverCountOffset,count) ||
        count < 0 || count > 256 || (count && !entries)) return false;
    for (std::int32_t i = 0; i < count; ++i) {
      void *current = nullptr;
      if (!Read(entries,std::size_t(i)*sizeof(void *),current) || !current)
        return false;
      // Do not dereference the old widget after a callback. A registered
      // pointer remains pending even if the control might now be hidden.
      if (reinterpret_cast<std::uintptr_t>(current) == receiver)
        still_blocking = true;
    }
    void *later_context = nullptr, *later_owner = nullptr;
    return ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(
               environment_,access,later_context,later_owner) &&
           later_context == context && later_owner == owner &&
           Read(context,kZhongguoGuiModalReceiversOffset,later_entries) &&
           Read(context,kZhongguoGuiModalReceiverCountOffset,later_count) &&
           later_entries == entries && later_count == count;
  } catch (...) {return false;}
}

TypedWindowRelation Crozier12004ModalPort::ReadActiveEventRootRelation(
    std::uintptr_t jomini_state, std::int32_t active_event_instance_id) noexcept {
  TypedWindowRelation relation{};
  relation.typed_domain = "event";
  relation.typed_window_instance_id = active_event_instance_id;
  relation.top_root = cached_root_.receiver;
  relation.source = "exact_12004_event_controller_gui_root_and_owner_tree";
  try {
    if (!ready_ || !jomini_state || active_event_instance_id <= 0 ||
        !cached_root_.receiver || !cached_root_.gui_context ||
        !cached_root_.gui_owner) return relation;
    void *idler = nullptr, *idler_vtable = nullptr, *manager = nullptr;
    if (!Read(reinterpret_cast<void *>(jomini_state),0x10,idler) || !idler ||
        !Read(idler,0,idler_vtable) ||
        reinterpret_cast<std::uintptr_t>(idler_vtable) !=
            environment_.module_base +
                ck3_12004::kEventWindowIdlerGfxVtableRva12004V1 ||
        !Read(idler,kEventManagerFromIdlerOffset,manager) || !manager)
      return relation;
    void **windows = nullptr, **later_windows = nullptr;
    std::int32_t count = -1, later_count = -1;
    if (!Read(manager,kEventManagerWindowsOffset,windows) ||
        !Read(manager,kEventManagerWindowCountOffset,count) ||
        count <= 0 || count > 32 || !windows) return relation;
    void *matching_window = nullptr, *typed_widget = nullptr;
    for (std::int32_t i=0; i<count; ++i) {
      void *window = nullptr, *vtable = nullptr;
      std::int32_t instance_id = -1;
      if (!Read(windows,std::size_t(i)*sizeof(void *),window) || !window ||
          !Read(window,0,vtable) || !vtable ||
          !Read(window,kEventControllerInstanceIdOffset,instance_id))
        return relation;
      if (instance_id != active_event_instance_id) continue;
      if (reinterpret_cast<std::uintptr_t>(vtable) !=
              environment_.module_base +
                  ck3_12004::kEventWindowPrimaryVtableRva12004V1 ||
          matching_window ||
          !Read(window,kEventControllerGuiRootOffset,typed_widget) ||
          !typed_widget) return relation;
      matching_window = window;
    }
    if (!matching_window || !typed_widget) return relation;
    void *owner_root = nullptr, *actual_context = nullptr, *widget_vtable = nullptr;
    ZhongguoScoreboardAccessV1 access{};
    std::string runtime_name;
    bool visible = false, enabled = false;
    if (!Read(reinterpret_cast<void *>(cached_root_.gui_owner),
              kZhongguoGuiOwnerRootWidgetOffset,owner_root) || !owner_root ||
        !Read(typed_widget,kZhongguoWidgetGuiContextOffset,actual_context) ||
        reinterpret_cast<std::uintptr_t>(actual_context) != cached_root_.gui_context ||
        !ReadGuiWidgetRuntimeV1(access,typed_widget,runtime_name,widget_vtable,
                                visible,enabled) || !visible || !widget_vtable)
      return relation;
    std::vector<std::uintptr_t> top_path, typed_path;
    if (!PathToOwnerRoot(reinterpret_cast<void *>(cached_root_.receiver),
                         owner_root,actual_context,top_path) ||
        !PathToOwnerRoot(typed_widget,owner_root,actual_context,typed_path))
      return relation;
    void *later_widget = nullptr, *later_top = nullptr, *later_context = nullptr,
         *later_owner = nullptr;
    if (!Read(matching_window,kEventControllerGuiRootOffset,later_widget) ||
        later_widget != typed_widget ||
        !Read(matching_window,kEventControllerInstanceIdOffset,active_event_instance_id) ||
        active_event_instance_id != relation.typed_window_instance_id ||
        !Read(manager,kEventManagerWindowsOffset,later_windows) ||
        !Read(manager,kEventManagerWindowCountOffset,later_count) ||
        later_windows != windows || later_count != count) return relation;
    bool has_any = false;
    if (!ReadTop(environment_,later_context,later_owner,later_top,has_any) ||
        reinterpret_cast<std::uintptr_t>(later_context) != cached_root_.gui_context ||
        reinterpret_cast<std::uintptr_t>(later_owner) != cached_root_.gui_owner ||
        reinterpret_cast<std::uintptr_t>(later_top) != cached_root_.receiver)
      return relation;
    relation.status = ClassifyTypedRootPathsV1(top_path,typed_path);
    relation.owner_verified = relation.status != TypedWindowRelationStatus::unknown;
    relation.typed_root = reinterpret_cast<std::uintptr_t>(typed_widget);
    return relation;
  } catch (...) {return relation;}
}

ModalHint ReadTopExclusiveModalHint12004V1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    std::uint64_t native_revision) noexcept {
  ModalHint hint{}; hint.native_revision = native_revision;
  try {
  void *context = nullptr, *owner = nullptr, *receiver = nullptr;
  bool has_any = false;
  if (!ReadTop(environment,context,owner,receiver,has_any)) return hint;
  hint.status = receiver ? ModalHintStatus::present :
                has_any ? ModalHintStatus::unknown : ModalHintStatus::absent;
  hint.receiver = reinterpret_cast<std::uintptr_t>(receiver);
  } catch (...) {hint.status = ModalHintStatus::unknown;}
  return hint;
}
std::string NativeReceiverIdentityV1(std::uintptr_t receiver) {
  return receiver ? PointerId(receiver) : std::string{};
}
} // namespace xar::mandatory_choice_v1
