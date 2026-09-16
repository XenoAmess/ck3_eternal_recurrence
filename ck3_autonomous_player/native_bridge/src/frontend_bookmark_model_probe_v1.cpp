#include "xar_bridge/frontend_bookmark_model_probe_v1.hpp"

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <cstring>
#include <limits>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kInterfaceApplicationVtableRva = 0x4093158;
constexpr std::array<std::uintptr_t, 3> kFrontendOwnerVtableRvas{
    0x40C9BD0, 0x40F3A10, 0x40F3CF0};
constexpr std::uintptr_t kFrontendSetupViewVtableRva = 0x410B070;
constexpr std::uintptr_t kFrontendHandlerRttiTypeRva = 0x51FCE10;
constexpr std::uintptr_t kFrontendSetupViewRttiTypeRva = 0x5212C48;
constexpr std::uintptr_t kGuiContextOwnerRegistryOffset = 0x230;
constexpr std::uintptr_t kGuiContextOwnerRegistryEntryStride = 0x50;
constexpr std::uint32_t kMaxBoundedGuiContextOwners = 1024;
constexpr std::uintptr_t kMaxExactImageRva = 0x6000000;
constexpr std::uintptr_t kBookmarkCharacterStride = 0x1A0;
constexpr std::string_view kSupportedBookmarkKey =
    "bm_1066_rags_to_riches";
constexpr std::string_view kSupportedCharacterKey =
    "bookmark_rags_to_riches_petty_king_murchad";
constexpr std::string_view kFeudalGovernmentKey = "feudal_government";
constexpr std::uintptr_t kFinalGovernmentGetterRva = 0x2DAB260;
constexpr std::uint32_t kSupportedDateLowRaw = 0x032AEB08;

bool IsScriptKeyByte(char value) noexcept {
  return (value >= 'a' && value <= 'z') ||
         (value >= '0' && value <= '9') || value == '_';
}

bool ReadBytes(const ZhongguoScoreboardAccessV1 &access,
               const void *address, void *output, std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, address, output, size);
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

template <typename Value>
bool ReadAt(const ZhongguoScoreboardAccessV1 &access,
            const void *base, std::size_t offset, Value &output) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  if (address == 0 ||
      offset > std::numeric_limits<std::uintptr_t>::max() - address) {
    return false;
  }
  return ReadBytes(access, reinterpret_cast<const void *>(address + offset),
                   &output, sizeof(output));
}

bool ReadVtableRva(const ZhongguoScoreboardAccessV1 &access,
                   std::uintptr_t module_base, const void *object,
                   std::uint64_t &output) noexcept {
  output = 0;
  void *vtable = nullptr;
  if (!ReadAt(access, object, 0, vtable)) return false;
  const auto address = reinterpret_cast<std::uintptr_t>(vtable);
  if (address < module_base || address - module_base >= kMaxExactImageRva) {
    return false;
  }
  output = address - module_base;
  return true;
}

bool ReadRttiTypeRva(const ZhongguoScoreboardAccessV1 &access,
                     std::uintptr_t module_base, const void *object,
                     std::uint64_t &output) noexcept {
  output = 0;
  void *vtable = nullptr;
  if (!ReadAt(access, object, 0, vtable)) return false;
  const auto vtable_address = reinterpret_cast<std::uintptr_t>(vtable);
  if (vtable_address < module_base + sizeof(void *) ||
      vtable_address - module_base >= kMaxExactImageRva) {
    return false;
  }
  void *complete_object_locator = nullptr;
  if (!ReadBytes(access,
                 reinterpret_cast<const void *>(vtable_address - sizeof(void *)),
                 &complete_object_locator, sizeof(complete_object_locator))) {
    return false;
  }
  const auto locator_address =
      reinterpret_cast<std::uintptr_t>(complete_object_locator);
  if (locator_address < module_base ||
      locator_address - module_base >= kMaxExactImageRva) {
    return false;
  }
  std::uint32_t signature = 0;
  std::uint32_t offset = 0;
  std::uint32_t type_rva = 0;
  if (!ReadAt(access, complete_object_locator, 0, signature) ||
      !ReadAt(access, complete_object_locator, 4, offset) ||
      !ReadAt(access, complete_object_locator, 0xC, type_rva) ||
      signature != 1 || offset != 0 || type_rva >= kMaxExactImageRva) {
    return false;
  }
  output = type_rva;
  return true;
}

bool ReadScriptKeySso(const ZhongguoScoreboardAccessV1 &access,
                      const void *owner, std::size_t offset,
                      std::string &output) noexcept {
  std::uint64_t length = 0;
  std::uint64_t capacity = 0;
  if (!ReadAt(access, owner, offset + 0x10, length) ||
      !ReadAt(access, owner, offset + 0x18, capacity) ||
      length == 0 || length > 96 || length > capacity) {
    return false;
  }
  const void *characters = nullptr;
  if (capacity < 16) {
    characters = reinterpret_cast<const void *>(
        reinterpret_cast<std::uintptr_t>(owner) + offset);
  } else {
    if (!ReadAt(access, owner, offset, characters) ||
        characters == nullptr) {
      return false;
    }
  }
  std::array<char, 96> bytes{};
  if (!ReadBytes(access, characters, bytes.data(),
                 static_cast<std::size_t>(length))) {
    return false;
  }
  for (std::size_t i = 0; i < length; ++i) {
    if (!IsScriptKeyByte(bytes[i])) return false;
  }
  try {
    output.assign(bytes.data(), static_cast<std::size_t>(length));
  } catch (...) {
    return false;
  }
  return true;
}

bool ResolveRegisteredSetupView(
    const ZhongguoScoreboardAccessV1 &access, std::uintptr_t module_base,
    const void *gui_context, const void *bookmarks_root,
    FrontendBookmarkModelProbeV1 &output, void *&setup_view) noexcept {
  setup_view = nullptr;
  void *entries = nullptr;
  std::uint32_t capacity = 0;
  std::uint32_t count = 0;
  if (!ReadAt(access, gui_context, kGuiContextOwnerRegistryOffset, entries) ||
      !ReadAt(access, gui_context, kGuiContextOwnerRegistryOffset + 8,
              capacity) ||
      !ReadAt(access, gui_context, kGuiContextOwnerRegistryOffset + 0xC,
              count) ||
      count > capacity || count > kMaxBoundedGuiContextOwners ||
      (count != 0 && entries == nullptr)) {
    output.registry_owner_unavailable_reason =
        "frontend_owner_registry_collection_unverified";
    return false;
  }
  output.registry_owner_match_count = 0;
  const auto base = reinterpret_cast<std::uintptr_t>(entries);
  for (std::uint32_t i = 0; i < count; ++i) {
    const auto stride = static_cast<std::uintptr_t>(i) *
                        kGuiContextOwnerRegistryEntryStride;
    if (stride > std::numeric_limits<std::uintptr_t>::max() - base) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_entry_unreadable";
      return false;
    }
    void *handler = nullptr;
    if (!ReadAt(access, reinterpret_cast<const void *>(base + stride), 0,
                handler)) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_entry_unreadable";
      return false;
    }
    if (handler == nullptr) continue;
    std::uint64_t handler_vtable_rva = 0;
    if (!ReadVtableRva(access, module_base, handler, handler_vtable_rva)) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_entry_type_unreadable";
      return false;
    }
    if (handler_vtable_rva != kFrontendOwnerVtableRvas[2]) continue;
    std::uint64_t handler_type_rva = 0;
    if (!ReadRttiTypeRva(access, module_base, handler, handler_type_rva) ||
        handler_type_rva != kFrontendHandlerRttiTypeRva) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_handler_rtti_unverified";
      return false;
    }
    void *view = nullptr;
    if (!ReadAt(access, handler, 0x30, view)) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_view_pointer_unreadable";
      return false;
    }
    if (view == nullptr) continue;
    std::uint64_t view_vtable_rva = 0;
    if (!ReadVtableRva(access, module_base, view, view_vtable_rva)) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_view_type_unreadable";
      return false;
    }
    if (view_vtable_rva != kFrontendSetupViewVtableRva) continue;
    std::uint64_t view_type_rva = 0;
    if (!ReadRttiTypeRva(access, module_base, view, view_type_rva) ||
        view_type_rva != kFrontendSetupViewRttiTypeRva) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_view_rtti_unverified";
      return false;
    }
    void *view_root = nullptr;
    if (!ReadAt(access, view, 0x78, view_root)) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_view_root_unreadable";
      return false;
    }
    if (view_root != bookmarks_root) continue;
    ++output.registry_owner_match_count;
    setup_view = view;
  }
  if (output.registry_owner_match_count != 1) {
    setup_view = nullptr;
    output.registry_owner_unavailable_reason =
        output.registry_owner_match_count == 0
            ? "frontend_owner_registry_no_matching_bookmarks_view"
            : "frontend_owner_registry_ambiguous_bookmarks_view";
    return false;
  }
  return true;
}

} // namespace

bool ProbeFrontendBookmarkModelV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *bookmarks_root,
    FrontendBookmarkModelProbeV1 &output,
    FrontendBookmarkGovernmentGetterV1 fixture_government_getter) noexcept {
  output = {};
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      bookmarks_root == nullptr || environment.gui_global_slot == nullptr ||
      reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) !=
          environment.module_base + kZhongguoGuiGlobalSlotRva) {
    output.unavailable_reason = "exact_bookmarks_gui_root_unavailable";
    return true;
  }

  std::array<void *, 3> chain{};
  if (!ReadAt(access, environment.gui_global_slot, 0, chain[0])) {
    output.unavailable_reason = "gui_owner_chain_unreadable";
    return true;
  }
  if (!ReadVtableRva(access, environment.module_base, chain[0],
                     output.gui_chain_vtable_rvas[0])) {
    output.unavailable_reason = "gui_owner_type_unreadable";
    return true;
  }
  if (output.gui_chain_vtable_rvas[0] != kInterfaceApplicationVtableRva) {
    output.unavailable_reason = "interface_application_unverified";
    return true;
  }
  output.interface_application_chain_level = 0;
  // E317C8 follows app+1B8 and host+58 as untyped GUI-context pointers.
  // Their first qwords may not be vtables; keep the RVAs as diagnostics only.
  if (!ReadAt(access, chain[0], kZhongguoGuiChainFirstOffset, chain[1]) ||
      !ReadAt(access, chain[1], kZhongguoGuiChainSecondOffset, chain[2])) {
    output.unavailable_reason = "gui_owner_chain_unreadable";
    return true;
  }
  std::uintptr_t gui_context_head = 0;
  if (!ReadAt(access, chain[2], 0, gui_context_head)) {
    output.unavailable_reason = "gui_owner_chain_unreadable";
    return true;
  }
  for (std::size_t i = 1; i < chain.size(); ++i) {
    (void)ReadVtableRva(access, environment.module_base, chain[i],
                        output.gui_chain_vtable_rvas[i]);
  }

  const auto *application = chain[0];
  constexpr std::array<std::size_t, 4> owner_offsets{0x78, 0x10, 0x08,
                                                      0x30};
  constexpr std::array<const char *, 4> unreadable_reasons{
      "frontend_idler_pointer_unreadable",
      "frontend_gfx_pointer_unreadable",
      "frontend_handler_pointer_unreadable",
      "frontend_setup_view_pointer_unreadable"};
  constexpr std::array<const char *, 4> null_reasons{
      "frontend_idler_pointer_null", "frontend_gfx_pointer_null",
      "frontend_handler_pointer_null", "frontend_setup_view_pointer_null"};
  constexpr std::array<const char *, 4> type_unreadable_reasons{
      "frontend_idler_type_unreadable", "frontend_gfx_type_unreadable",
      "frontend_handler_type_unreadable",
      "frontend_setup_view_type_unreadable"};
  constexpr std::array<const char *, 4> type_mismatch_reasons{
      "frontend_idler_replaced", "frontend_gfx_replaced",
      "frontend_handler_replaced", "frontend_setup_view_type_mismatch"};
  std::array<void *, 4> owner_chain{};
  const void *previous = application;
  for (std::size_t i = 0; i < owner_chain.size(); ++i) {
    if (!ReadAt(access, previous, owner_offsets[i], owner_chain[i])) {
      output.direct_owner_unavailable_reason = unreadable_reasons[i];
      break;
    }
    if (owner_chain[i] == nullptr) {
      output.direct_owner_unavailable_reason = null_reasons[i];
      break;
    }
    if (!ReadVtableRva(access, environment.module_base, owner_chain[i],
                       output.owner_chain_vtable_rvas[i])) {
      output.direct_owner_unavailable_reason = type_unreadable_reasons[i];
      break;
    }
    (void)ReadRttiTypeRva(access, environment.module_base, owner_chain[i],
                          output.owner_chain_rtti_type_rvas[i]);
    if (i == owner_chain.size() - 1) {
      output.setup_view_vtable_rva = output.owner_chain_vtable_rvas[i];
    }
    const auto expected_vtable =
        i < kFrontendOwnerVtableRvas.size()
            ? kFrontendOwnerVtableRvas[i]
            : kFrontendSetupViewVtableRva;
    if (output.owner_chain_vtable_rvas[i] != expected_vtable) {
      output.direct_owner_unavailable_reason = type_mismatch_reasons[i];
      break;
    }
    previous = owner_chain[i];
  }
  void *setup_view = nullptr;
  if (output.direct_owner_unavailable_reason.empty()) {
    setup_view = owner_chain.back();
    void *view_root = nullptr;
    if (!ReadAt(access, setup_view, 0x78, view_root)) {
      output.direct_owner_unavailable_reason =
          "frontend_setup_view_root_unreadable";
    } else if (view_root != bookmarks_root) {
      output.direct_owner_unavailable_reason =
          "frontend_setup_view_root_mismatch";
    }
  }
  if (output.direct_owner_unavailable_reason.empty()) {
    output.verified_owner_route = "app_idler_chain";
  } else {
    if (!ResolveRegisteredSetupView(access, environment.module_base,
                                    chain[2], bookmarks_root, output,
                                    setup_view)) {
      output.unavailable_reason = output.registry_owner_unavailable_reason;
      return true;
    }
    output.setup_view_vtable_rva = kFrontendSetupViewVtableRva;
    output.verified_owner_route = "gui_context_registry";
  }
  output.setup_view_matches_bookmarks_root = true;

  void *selected_group = nullptr;
  if (!ReadAt(access, setup_view, 0x108, selected_group)) {
    output.unavailable_reason = "selected_bookmark_group_pointer_unreadable";
    return true;
  }
  // frontend_bookmarks.gui:2495-2496 clears the selected group after selecting
  // Bookmark.Self. Original F6FE00 can store a non-key sentinel at view+0x108;
  // the group key is diagnostic, while the selected Bookmark is the identity.
  if (selected_group != nullptr) {
    (void)ReadVtableRva(access, environment.module_base, selected_group,
                        output.selected_bookmark_group_vtable_rva);
    output.selected_bookmark_group_key_available = ReadScriptKeySso(
        access, selected_group, 0x38, output.selected_bookmark_group_key);
  }

  void *selected_bookmark = nullptr;
  if (!ReadAt(access, setup_view, 0x150, selected_bookmark) ||
      !ReadAt(access, setup_view, 0x158,
              output.selected_character_index) ||
      !ReadAt(access, setup_view, 0x15C,
              output.hovered_character_index) ||
      selected_bookmark == nullptr) {
    output.unavailable_reason = "frontend_selected_model_unreadable";
    return true;
  }
  (void)ReadVtableRva(access, environment.module_base, selected_bookmark,
                      output.selected_bookmark_vtable_rva);
  output.model_indices_available = true;
  if (!ReadScriptKeySso(access, selected_bookmark, 0x18,
                        output.selected_bookmark_key)) {
    output.unavailable_reason = "selected_bookmark_script_key_unreadable";
    return true;
  }
  output.selected_bookmark_key_available = true;
  if (!ReadAt(access, selected_bookmark, 0x38,
              output.selected_date_raw)) {
    output.unavailable_reason = "selected_bookmark_date_unreadable";
    return true;
  }
  output.selected_date_raw_available = true;
  output.selected_date_low_raw =
      static_cast<std::uint32_t>(output.selected_date_raw);
  if (!ReadAt(access, selected_bookmark, 0x170,
              output.bookmark_character_base_raw) ||
      !ReadAt(access, selected_bookmark, 0x178,
              output.bookmark_character_capacity_raw) ||
      !ReadAt(access, selected_bookmark, 0x17C,
              output.bookmark_character_count_raw) ||
      !ReadAt(access, selected_bookmark, 0x180,
              output.bookmark_character_allocator_raw)) {
    output.unavailable_reason = "bookmark_character_collection_unreadable";
    return true;
  }
  const auto begin = static_cast<std::uintptr_t>(
      output.bookmark_character_base_raw);
  if (output.bookmark_character_count_raw == 0 ||
      output.bookmark_character_count_raw >
          output.bookmark_character_capacity_raw ||
      output.bookmark_character_count_raw >
          output.bookmark_character_keys.size() ||
      begin == 0 ||
      begin > std::numeric_limits<std::uintptr_t>::max() -
                  output.bookmark_character_count_raw *
                      kBookmarkCharacterStride) {
    output.unavailable_reason =
        "selected_bookmark_character_collection_unverified";
    return true;
  }
  output.bookmark_character_count = static_cast<std::int32_t>(
      output.bookmark_character_count_raw);
  if (output.selected_character_index < -1 ||
      output.selected_character_index >= output.bookmark_character_count) {
    output.unavailable_reason = "selected_character_index_out_of_vector";
    return true;
  }
  for (std::int32_t index = 0; index < output.bookmark_character_count;
       ++index) {
    const auto *element = reinterpret_cast<const void *>(
        begin + static_cast<std::uintptr_t>(index) *
                    kBookmarkCharacterStride);
    void *parent_bookmark = nullptr;
    if (!ReadAt(access, element, 0x130, parent_bookmark) ||
        parent_bookmark != selected_bookmark ||
        !ReadScriptKeySso(access, element, 0x08,
                          output.bookmark_character_keys[
                              static_cast<std::size_t>(index)])) {
      output.unavailable_reason = "bookmark_character_parent_or_key_unverified";
      return true;
    }
  }
  output.bookmark_character_keys_available = true;
  if (output.selected_bookmark_key == kSupportedBookmarkKey) {
    for (std::int32_t index = 0; index < output.bookmark_character_count;
         ++index) {
      if (output.bookmark_character_keys[
              static_cast<std::size_t>(index)] ==
          kSupportedCharacterKey) {
        if (output.supported_1066_candidate_present) {
          output.unavailable_reason = "supported_1066_key_is_ambiguous";
          return true;
        }
        output.supported_1066_candidate_index = index;
        output.supported_1066_candidate_present = true;
      }
    }
  }
  if (!output.supported_1066_candidate_present) {
    output.unavailable_reason =
        "supported_1066_script_key_not_in_selected_bookmark";
    return true;
  }
  const auto index = static_cast<std::uintptr_t>(
      output.supported_1066_candidate_index);
  const auto *target = reinterpret_cast<const void *>(
      begin + index * kBookmarkCharacterStride);
  void *final_government = nullptr;
  if (fixture_government_getter != nullptr) {
    final_government = fixture_government_getter(access.context, target);
  } else if (access.read_memory == nullptr) {
    using NativeGetter = void *(*)(const void *);
    const auto getter = reinterpret_cast<NativeGetter>(
        environment.module_base + kFinalGovernmentGetterRva);
    final_government = getter(target);
  }
  if (final_government == nullptr ||
      !ReadScriptKeySso(access, final_government, 0x18,
                        output.government_type_keys[index])) {
    output.unavailable_reason = "native_final_government_unavailable";
    return true;
  }
  output.government_type_keys_available = true;
  output.supported_1066_candidate_feudal =
      output.government_type_keys[index] == kFeudalGovernmentKey;
  if (!output.supported_1066_candidate_feudal) {
    output.unavailable_reason = "supported_1066_candidate_not_feudal";
    return true;
  }
  output.supported_1066_date_matches =
      output.selected_date_low_raw == kSupportedDateLowRaw;
  if (!output.supported_1066_date_matches) {
    output.unavailable_reason = "selected_bookmark_date_not_1066_09_15";
    return true;
  }
  output.candidate_identity_ready = true;
  output.unavailable_reason.clear();
  return true;
}

bool SelectSupportedFeudalBookmarkCharacterV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *bookmarks_root,
    FrontendBookmarkSelectionV1 &output,
    FrontendBookmarkGovernmentGetterV1 fixture_government_getter,
    FrontendBookmarkSelectionSetterV1 fixture_setter) noexcept {
  output = {};
  if (!ProbeFrontendBookmarkModelV1(environment, access, bookmarks_root,
                                    output.before,
                                    fixture_government_getter)) {
    output.unavailable_reason = "current_bookmarks_model_query_failed";
    return true;
  }
  const auto &model = output.before;
  if (!model.candidate_identity_ready ||
      model.supported_1066_candidate_index < 0 ||
      model.supported_1066_candidate_index >=
          model.bookmark_character_count) {
    output.unavailable_reason = model.unavailable_reason.empty()
                                    ? "current_1066_candidate_not_ready"
                                    : model.unavailable_reason;
    return true;
  }
  if (model.selected_character_index ==
      model.supported_1066_candidate_index) {
    output.already_selected = true;
    output.same_frame_selected_index = model.selected_character_index;
    output.same_frame_index_matches = true;
    return true;
  }
  if (model.selected_character_index != -1) {
    output.unavailable_reason = "another_bookmark_character_is_selected";
    return true;
  }

  // R740's sole owner route was the current GUI-context registry. The
  // direct application/idler path is also accepted when its exact vtables,
  // RTTI and independently named Bookmarks root all still match.
  void *application = nullptr;
  void *host = nullptr;
  void *gui_context = nullptr;
  if (!ReadAt(access, environment.gui_global_slot, 0, application) ||
      !ReadAt(access, application, kZhongguoGuiChainFirstOffset, host) ||
      !ReadAt(access, host, kZhongguoGuiChainSecondOffset, gui_context)) {
    output.unavailable_reason = "current_frontend_owner_unreadable";
    return true;
  }
  std::uint64_t application_vtable_rva = 0;
  if (!ReadVtableRva(access, environment.module_base, application,
                     application_vtable_rva) ||
      application_vtable_rva != kInterfaceApplicationVtableRva) {
    output.unavailable_reason = "current_frontend_application_replaced";
    return true;
  }
  void *setup_view = nullptr;
  if (model.verified_owner_route == "gui_context_registry") {
    FrontendBookmarkModelProbeV1 owner_check{};
    if (!ResolveRegisteredSetupView(access, environment.module_base,
                                    gui_context, bookmarks_root,
                                    owner_check, setup_view) ||
        owner_check.registry_owner_match_count != 1) {
      output.unavailable_reason =
          owner_check.registry_owner_unavailable_reason.empty()
              ? "current_bookmarks_owner_registry_unverified"
              : owner_check.registry_owner_unavailable_reason;
      return true;
    }
  } else if (model.verified_owner_route == "app_idler_chain") {
    const void *previous = application;
    for (std::size_t i = 0; i < kFrontendOwnerVtableRvas.size();
         ++i) {
      void *node = nullptr;
      constexpr std::array<std::size_t, 3> kOwnerOffsets{0x78, 0x10,
                                                          0x08};
      std::uint64_t vtable_rva = 0;
      if (!ReadAt(access, previous, kOwnerOffsets[i], node) ||
          !ReadVtableRva(access, environment.module_base, node,
                         vtable_rva) ||
          vtable_rva != kFrontendOwnerVtableRvas[i]) {
        output.unavailable_reason = "current_app_idler_owner_replaced";
        return true;
      }
      if (i == 2) {
        std::uint64_t handler_type_rva = 0;
        if (!ReadRttiTypeRva(access, environment.module_base, node,
                             handler_type_rva) ||
            handler_type_rva != kFrontendHandlerRttiTypeRva) {
          output.unavailable_reason = "current_app_handler_rtti_unverified";
          return true;
        }
      }
      previous = node;
    }
    std::uint64_t view_vtable_rva = 0;
    std::uint64_t view_type_rva = 0;
    void *view_root = nullptr;
    if (!ReadAt(access, previous, 0x30, setup_view) ||
        !ReadVtableRva(access, environment.module_base, setup_view,
                       view_vtable_rva) ||
        !ReadRttiTypeRva(access, environment.module_base, setup_view,
                         view_type_rva) ||
        view_vtable_rva != kFrontendSetupViewVtableRva ||
        view_type_rva != kFrontendSetupViewRttiTypeRva ||
        !ReadAt(access, setup_view, 0x78, view_root) ||
        view_root != bookmarks_root) {
      output.unavailable_reason = "current_app_bookmarks_view_unverified";
      return true;
    }
  } else {
    output.unavailable_reason = "current_bookmarks_owner_route_unknown";
    return true;
  }
  output.owner_resolved = true;

  void *selected_bookmark = nullptr;
  std::uint64_t current_base = 0;
  std::uint32_t current_count = 0;
  std::uint64_t current_date = 0;
  std::string current_bookmark_key;
  std::int32_t selected_index = -1;
  if (!ReadAt(access, setup_view, 0x150, selected_bookmark) ||
      !ReadAt(access, setup_view, 0x158, selected_index) ||
      selected_bookmark == nullptr ||
      !ReadScriptKeySso(access, selected_bookmark, 0x18,
                        current_bookmark_key) ||
      current_bookmark_key != kSupportedBookmarkKey ||
      !ReadAt(access, selected_bookmark, 0x38, current_date) ||
      current_date != model.selected_date_raw ||
      !ReadAt(access, selected_bookmark, 0x170, current_base) ||
      !ReadAt(access, selected_bookmark, 0x17C, current_count) ||
      current_base != model.bookmark_character_base_raw ||
      current_count != model.bookmark_character_count_raw ||
      selected_index != -1) {
    output.unavailable_reason = "current_bookmarks_collection_changed";
    return true;
  }
  const auto index = static_cast<std::uintptr_t>(
      model.supported_1066_candidate_index);
  const auto *target = reinterpret_cast<const void *>(
      static_cast<std::uintptr_t>(current_base) +
      index * kBookmarkCharacterStride);
  void *parent_bookmark = nullptr;
  std::string current_key;
  if (!ReadAt(access, target, 0x130, parent_bookmark) ||
      parent_bookmark != selected_bookmark ||
      !ReadScriptKeySso(access, target, 0x08, current_key) ||
      current_key != kSupportedCharacterKey) {
    output.unavailable_reason = "current_bookmark_character_key_changed";
    return true;
  }
  output.target_resolved = true;
  if (fixture_setter == nullptr && access.read_memory != nullptr) {
    output.unavailable_reason = "fixture_setter_required";
    return true;
  }

  // Exact stock 0xF71460 invokes 0xF707E0(view, model element). The
  // latter writes view+0x158 from element's offset in Bookmark+0x170.
  // This is one submission. The independent following model frame, not
  // this same-frame read or pipe ACK, proves whether it took effect.
  output.setter_invoked = true;
  if (fixture_setter != nullptr) {
    if (!fixture_setter(access.context, setup_view, target)) {
      output.unavailable_reason = "fixture_setter_rejected";
      return true;
    }
  } else {
    using NativeSetter = void (*)(void *, const void *);
    const auto setter = reinterpret_cast<NativeSetter>(
        environment.module_base + 0xF707E0);
    setter(setup_view, target);
  }
  if (!ReadAt(access, setup_view, 0x158,
              output.same_frame_selected_index)) {
    output.unavailable_reason = "submitted_selection_index_unreadable";
    return true;
  }
  output.same_frame_index_matches =
      output.same_frame_selected_index ==
      model.supported_1066_candidate_index;
  if (!output.same_frame_index_matches) {
    output.unavailable_reason = "submitted_selection_index_unconfirmed";
  }
  return true;
}

} // namespace xar::ck3_11906
