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

struct FrontendModelAbiV1 {
  std::uintptr_t application_vtable;
  std::array<std::uintptr_t, 3> owner_vtables;
  std::uintptr_t view_vtable;
  std::uintptr_t handler_type;
  std::uintptr_t view_type;
  std::size_t view_root;
  std::size_t selected_group;
  std::size_t group_key;
  std::size_t selected_bookmark;
  std::size_t selected_index;
  std::size_t hovered_index;
  std::size_t bookmark_date;
  std::size_t bookmark_characters;
  std::uintptr_t final_government_getter;
  std::uintptr_t character_setter;
  std::uintptr_t bookmark_setter;
  std::size_t setup_bookmark_collection;
  std::uintptr_t group_setter;
  std::uintptr_t bookmark_database_slot;
  std::uintptr_t bookmark_database_vtable;
};

constexpr FrontendModelAbiV1 kLegacyAbi{
    0x4093158, {0x40C9BD0, 0x40F3A10, 0x40F3CF0}, 0x410B070,
    0x51FCE10, 0x5212C48, 0x78, 0x108, 0x38, 0x150, 0x158, 0x15C,
    0x38, 0x170, 0x2DAB260, 0xF707E0, 0xF706A0, 0xF0, 0, 0, 0};
constexpr FrontendModelAbiV1 kCrozierAbi{
    0x449BDA8, {0x44D5F30, 0x4500660, 0x45008B0}, 0x451B938,
    0x5702BF0, 0x5720228, 0x60, 0xD8, 0x18, 0x120, 0x128, 0x12C,
    0x40, 0x160, 0x321D1A0, 0x1060A90, 0x1060950, 0xC0,
    0x1060090, 0x5C67210, 0x48D0200};

const FrontendModelAbiV1 &ModelAbi(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment) noexcept {
  return environment.gui_abi_revision == GuiAbiRevisionV1::crozier12003
             ? kCrozierAbi : kLegacyAbi;
}

constexpr std::uintptr_t kGuiContextOwnerRegistryOffset = 0x230;
constexpr std::uintptr_t kGuiContextOwnerRegistryEntryStride = 0x50;
constexpr std::uint32_t kMaxBoundedGuiContextOwners = 1024;
constexpr std::uintptr_t kMaxExactImageRva = 0x61C5000;
constexpr std::uintptr_t kBookmarkCharacterStride = 0x1A0;
#if defined(XAR_CK3_FEUDAL_1066_TARGET_ROBERT_V1)
constexpr std::string_view kConfiguredCharacterKey =
    "bookmark_rags_to_riches_duke_robert";
#else
constexpr std::string_view kConfiguredCharacterKey =
    "bookmark_rags_to_riches_petty_king_murchad";
#endif
constexpr FrontendBookmarkTargetProfileV1 kConfiguredTarget{
    "bm_1066_rags_to_riches", kConfiguredCharacterKey,
    "feudal_government", 0x032AEB08, "bm_group_1066"};
constexpr FrontendBookmarkTargetProfileV1 kYahyaTarget{
    "bm_1066_rags_to_riches", "bookmark_rags_to_riches_emir_yahya",
    "clan_government", 0x032AEB08, "bm_group_1066"};
constexpr FrontendBookmarkTargetProfileV1 kRurikTarget{
    "bm_867_adventurers", "bookmark_adventurers_rurik_rurikid",
    "tribal_government", 51394920, "bm_group_867"};

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
    const FrontendModelAbiV1 &abi, const void *gui_context, const void *bookmarks_root,
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
    if (handler_vtable_rva != abi.owner_vtables[2]) continue;
    std::uint64_t handler_type_rva = 0;
    if (!ReadRttiTypeRva(access, module_base, handler, handler_type_rva) ||
        handler_type_rva != abi.handler_type) {
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
    if (view_vtable_rva != abi.view_vtable) continue;
    std::uint64_t view_type_rva = 0;
    if (!ReadRttiTypeRva(access, module_base, view, view_type_rva) ||
        view_type_rva != abi.view_type) {
      output.registry_owner_unavailable_reason =
          "frontend_owner_registry_view_rtti_unverified";
      return false;
    }
    void *view_root = nullptr;
    if (!ReadAt(access, view, abi.view_root, view_root)) {
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

bool ResolveCurrentSetupView(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *bookmarks_root,
    const FrontendBookmarkModelProbeV1 &model, void *&setup_view,
    std::string &reason) noexcept {
  const auto &abi = ModelAbi(environment);
  setup_view = nullptr;
  // R740's sole owner route was the current GUI-context registry. The
  // direct application/idler path is also accepted when its exact vtables,
  // RTTI and independently named Bookmarks root all still match.
  void *application = nullptr;
  void *host = nullptr;
  void *gui_context = nullptr;
  if (!ReadAt(access, environment.gui_global_slot, 0, application) ||
      !ReadAt(access, application, kZhongguoGuiChainFirstOffset, host) ||
      !ReadAt(access, host, kZhongguoGuiChainSecondOffset, gui_context)) {
    reason = "current_frontend_owner_unreadable";
    return false;
  }
  std::uint64_t application_vtable_rva = 0;
  if (!ReadVtableRva(access, environment.module_base, application,
                     application_vtable_rva) ||
      application_vtable_rva != abi.application_vtable) {
    reason = "current_frontend_application_replaced";
    return false;
  }
  if (model.verified_owner_route == "gui_context_registry") {
    FrontendBookmarkModelProbeV1 owner_check{};
    if (!ResolveRegisteredSetupView(access, environment.module_base,
                                    abi, gui_context, bookmarks_root,
                                    owner_check, setup_view) ||
        owner_check.registry_owner_match_count != 1) {
      reason =
          owner_check.registry_owner_unavailable_reason.empty()
              ? "current_bookmarks_owner_registry_unverified"
              : owner_check.registry_owner_unavailable_reason;
      return false;
    }
  } else if (model.verified_owner_route == "app_idler_chain") {
    const void *previous = application;
    for (std::size_t i = 0; i < abi.owner_vtables.size();
         ++i) {
      void *node = nullptr;
      constexpr std::array<std::size_t, 3> kOwnerOffsets{0x78, 0x10,
                                                          0x08};
      std::uint64_t vtable_rva = 0;
      if (!ReadAt(access, previous, kOwnerOffsets[i], node) ||
          !ReadVtableRva(access, environment.module_base, node,
                         vtable_rva) ||
          vtable_rva != abi.owner_vtables[i]) {
        reason = "current_app_idler_owner_replaced";
        return false;
      }
      if (i == 2) {
        std::uint64_t handler_type_rva = 0;
        if (!ReadRttiTypeRva(access, environment.module_base, node,
                             handler_type_rva) ||
            handler_type_rva != abi.handler_type) {
          reason = "current_app_handler_rtti_unverified";
          return false;
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
        view_vtable_rva != abi.view_vtable ||
        view_type_rva != abi.view_type ||
        !ReadAt(access, setup_view, abi.view_root, view_root) ||
        view_root != bookmarks_root) {
      reason = "current_app_bookmarks_view_unverified";
      return false;
    }
  } else {
    reason = "current_bookmarks_owner_route_unknown";
    return false;
  }
  return true;
}

 } // namespace

const FrontendBookmarkTargetProfileV1 &GetFrontendBookmarkTargetProfileV1(
    FrontendBookmarkSeedTargetV1 seed_target) noexcept {
  switch (seed_target) {
  case FrontendBookmarkSeedTargetV1::yahya_1066: return kYahyaTarget;
  case FrontendBookmarkSeedTargetV1::rurik_867: return kRurikTarget;
  default: return kConfiguredTarget;
  }
}

bool ProbeFrontendBookmarkModelV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *bookmarks_root,
    FrontendBookmarkModelProbeV1 &output,
    FrontendBookmarkGovernmentGetterV1 fixture_government_getter,
    FrontendBookmarkSeedTargetV1 seed_target) noexcept {
  output = {};
  const auto &abi = ModelAbi(environment);
  const auto &profile = GetFrontendBookmarkTargetProfileV1(seed_target);
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      bookmarks_root == nullptr || environment.gui_global_slot == nullptr ||
      reinterpret_cast<std::uintptr_t>(environment.gui_global_slot) !=
          environment.module_base + GuiGlobalSlotRvaV1(environment.gui_abi_revision)) {
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
  if (output.gui_chain_vtable_rvas[0] != abi.application_vtable) {
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
        i < abi.owner_vtables.size()
            ? abi.owner_vtables[i]
            : abi.view_vtable;
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
    if (!ReadAt(access, setup_view, abi.view_root, view_root)) {
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
                                    abi, chain[2], bookmarks_root, output,
                                    setup_view)) {
      output.unavailable_reason = output.registry_owner_unavailable_reason;
      return true;
    }
    output.setup_view_vtable_rva = abi.view_vtable;
    output.verified_owner_route = "gui_context_registry";
  }
  output.setup_view_matches_bookmarks_root = true;

  void *selected_group = nullptr;
  if (!ReadAt(access, setup_view, abi.selected_group, selected_group)) {
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
        access, selected_group, abi.group_key, output.selected_bookmark_group_key);
  }

  void *selected_bookmark = nullptr;
  if (!ReadAt(access, setup_view, abi.selected_bookmark, selected_bookmark) ||
      !ReadAt(access, setup_view, abi.selected_index,
              output.selected_character_index) ||
      !ReadAt(access, setup_view, abi.hovered_index,
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
  if (!ReadAt(access, selected_bookmark, abi.bookmark_date,
              output.selected_date_raw)) {
    output.unavailable_reason = "selected_bookmark_date_unreadable";
    return true;
  }
  output.selected_date_raw_available = true;
  output.selected_date_low_raw =
      static_cast<std::uint32_t>(output.selected_date_raw);
  if (!ReadAt(access, selected_bookmark, abi.bookmark_characters,
              output.bookmark_character_base_raw) ||
      !ReadAt(access, selected_bookmark, abi.bookmark_characters + 8,
              output.bookmark_character_capacity_raw) ||
      !ReadAt(access, selected_bookmark, abi.bookmark_characters + 0xC,
              output.bookmark_character_count_raw) ||
      !ReadAt(access, selected_bookmark, abi.bookmark_characters + 0x10,
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
  if (output.selected_bookmark_key == profile.bookmark_key) {
    for (std::int32_t index = 0; index < output.bookmark_character_count;
         ++index) {
      if (output.bookmark_character_keys[
              static_cast<std::size_t>(index)] ==
          profile.character_key) {
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
        environment.module_base + abi.final_government_getter);
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
      output.government_type_keys[index] == "feudal_government";
  if (output.government_type_keys[index] != profile.government_key) {
    output.unavailable_reason = seed_target == FrontendBookmarkSeedTargetV1::configured_1066
            ? "supported_1066_candidate_not_feudal"
            : "supported_bookmark_candidate_government_mismatch";
    return true;
  }
  output.supported_1066_date_matches =
      output.selected_date_low_raw == profile.date_low_raw;
  if (!output.supported_1066_date_matches) {
    output.unavailable_reason = seed_target == FrontendBookmarkSeedTargetV1::configured_1066
            ? "selected_bookmark_date_not_1066_09_15"
            : "selected_bookmark_date_not_target_date";
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
    FrontendBookmarkSelectionSetterV1 fixture_setter,
    FrontendBookmarkSeedTargetV1 seed_target) noexcept {
  output = {};
  const auto &abi = ModelAbi(environment);
  const auto &profile = GetFrontendBookmarkTargetProfileV1(seed_target);
  if (!ProbeFrontendBookmarkModelV1(environment, access, bookmarks_root,
                                    output.before,
                                    fixture_government_getter, seed_target)) {
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
  void *setup_view = nullptr;
  if (!ResolveCurrentSetupView(environment, access, bookmarks_root, model,
                               setup_view, output.unavailable_reason)) {
    return true;
  }
  output.owner_resolved = true;

  void *selected_bookmark = nullptr;
  std::uint64_t current_base = 0;
  std::uint32_t current_count = 0;
  std::uint64_t current_date = 0;
  std::string current_bookmark_key;
  std::int32_t selected_index = -1;
  if (!ReadAt(access, setup_view, abi.selected_bookmark, selected_bookmark) ||
      !ReadAt(access, setup_view, abi.selected_index, selected_index) ||
      selected_bookmark == nullptr ||
      !ReadScriptKeySso(access, selected_bookmark, 0x18,
                        current_bookmark_key) ||
      current_bookmark_key != profile.bookmark_key ||
      !ReadAt(access, selected_bookmark, abi.bookmark_date, current_date) ||
      current_date != model.selected_date_raw ||
      !ReadAt(access, selected_bookmark, abi.bookmark_characters, current_base) ||
      !ReadAt(access, selected_bookmark, abi.bookmark_characters + 0xC, current_count) ||
      current_base != model.bookmark_character_base_raw ||
      current_count != model.bookmark_character_count_raw ||
      // CK3 normally opens Bookmarks with another featured character
      // selected.  Replacing that selection is the native UI's ordinary
      // operation; require only that the selection has not changed since
      // the identity probe.  The independent post-submit probe below the
      // Python facade still proves that the requested key became selected.
      selected_index != model.selected_character_index) {
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
      current_key != profile.character_key) {
    output.unavailable_reason = "current_bookmark_character_key_changed";
    return true;
  }
  output.target_resolved = true;
  if (fixture_setter == nullptr && access.read_memory != nullptr) {
    output.unavailable_reason = "fixture_setter_required";
    return true;
  }

  // Exact stock setters are 0xF707E0 (legacy) and 0x1060A90 (.3).
  // Each derives the index from the current native Bookmark collection.
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
        environment.module_base + abi.character_setter);
    setter(setup_view, target);
  }
  if (!ReadAt(access, setup_view, abi.selected_index,
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

bool SelectSupportedBookmarkV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access, void *bookmarks_root,
    FrontendBookmarkChangeV1 &output, FrontendBookmarkSeedTargetV1 seed_target,
    FrontendBookmarkSetterV1 fixture_setter,
    FrontendBookmarkGroupSetterV1 fixture_group_setter) noexcept {
  output = {};
  const auto &abi = ModelAbi(environment);
  const auto &profile = GetFrontendBookmarkTargetProfileV1(seed_target);
  FrontendBookmarkModelProbeV1 before{};
  if (!ProbeFrontendBookmarkModelV1(environment, access, bookmarks_root,
                                    before, nullptr, seed_target) ||
      !before.setup_view_matches_bookmarks_root ||
      !before.selected_bookmark_key_available) {
    output.unavailable_reason = before.unavailable_reason.empty()
                                    ? "current_bookmark_owner_unavailable"
                                    : before.unavailable_reason;
    return true;
  }
  void *setup_view = nullptr;
  if (!ResolveCurrentSetupView(environment, access, bookmarks_root, before,
                               setup_view, output.unavailable_reason)) {
    return true;
  }
  output.owner_resolved = true;
  const bool crozier =
      environment.gui_abi_revision == GuiAbiRevisionV1::crozier12003;
  if (before.selected_bookmark_key == profile.bookmark_key &&
      (!crozier ||
       (before.selected_date_raw_available &&
        before.selected_date_low_raw == profile.date_low_raw &&
        (!before.selected_bookmark_group_key_available ||
         before.selected_bookmark_group_key == profile.bookmark_group_key)))) {
    output.already_selected = true;
    output.target_resolved = true;
    output.same_frame_bookmark_matches = true;
    return true;
  }
  void *target_group = nullptr;
  void *current_group = nullptr;
  void *collection_owner = setup_view;
  std::size_t collection_offset = abi.setup_bookmark_collection;
  if (crozier) {
    // Exact ResetView 0x105FDE0 copies CBookmarkGroupDatabase+0x50 into
    // view+0xC0. Its entries are Group*, never Bookmark*. Each Bookmark
    // instead comes from CBookmarkDatabase+0x50 and owns Group* at +0x150.
    void *groups = nullptr;
    std::uint32_t group_capacity = 0;
    std::uint32_t group_count = 0;
    if (!ReadAt(access, setup_view, abi.setup_bookmark_collection, groups) ||
        !ReadAt(access, setup_view, abi.setup_bookmark_collection + 8,
                group_capacity) ||
        !ReadAt(access, setup_view, abi.setup_bookmark_collection + 0xC,
                group_count) ||
        group_count == 0 || group_count > group_capacity ||
        group_count > kMaxBoundedGuiContextOwners || groups == nullptr ||
        !ReadAt(access, setup_view, abi.selected_group, current_group)) {
      output.unavailable_reason = "current_bookmark_group_collection_unavailable";
      return true;
    }
    for (std::uint32_t i = 0; i < group_count; ++i) {
      void *candidate = nullptr;
      std::string key;
      if (!ReadAt(access, groups,
                  static_cast<std::size_t>(i) * sizeof(void *), candidate) ||
          candidate == nullptr ||
          !ReadScriptKeySso(access, candidate, abi.group_key, key)) {
        output.unavailable_reason = "current_bookmark_group_key_unavailable";
        return true;
      }
      if (key != profile.bookmark_group_key) continue;
      if (target_group != nullptr) {
        output.unavailable_reason = "target_bookmark_group_key_ambiguous";
        return true;
      }
      target_group = candidate;
    }
    if (target_group == nullptr) {
      output.unavailable_reason = "target_bookmark_group_not_in_current_collection";
      return true;
    }
    void *database = nullptr;
    std::uint64_t database_vtable_rva = 0;
    const auto *database_slot = reinterpret_cast<const void *>(
        environment.module_base + abi.bookmark_database_slot);
    if (!ReadAt(access, database_slot, 0, database) ||
        !ReadVtableRva(access, environment.module_base, database,
                       database_vtable_rva) ||
        database_vtable_rva != abi.bookmark_database_vtable) {
      output.unavailable_reason = "current_bookmark_database_unverified";
      return true;
    }
    collection_owner = database;
    collection_offset = 0x50;
  }
  void *entries = nullptr;
  std::uint32_t capacity = 0;
  std::uint32_t count = 0;
  if (!ReadAt(access, collection_owner, collection_offset, entries) ||
      !ReadAt(access, collection_owner, collection_offset + 8, capacity) ||
      !ReadAt(access, collection_owner, collection_offset + 0xC, count) ||
      count == 0 || count > capacity || count > kMaxBoundedGuiContextOwners ||
      entries == nullptr) {
    output.unavailable_reason = "current_bookmark_collection_unavailable";
    return true;
  }
  void *bookmark = nullptr;
  for (std::uint32_t i = 0; i < count; ++i) {
    void *candidate = nullptr;
    std::string key;
    if (!ReadAt(access, entries, static_cast<std::size_t>(i) * sizeof(void *),
                candidate) || candidate == nullptr ||
        !ReadScriptKeySso(access, candidate, 0x18, key)) {
      output.unavailable_reason = "current_bookmark_key_unavailable";
      return true;
    }
    if (key != profile.bookmark_key) continue;
    if (crozier) {
      void *candidate_group = nullptr;
      if (!ReadAt(access, candidate, 0x150, candidate_group) ||
          candidate_group != target_group) {
        output.unavailable_reason = "target_bookmark_group_mismatch";
        return true;
      }
    }
    if (bookmark != nullptr) {
      output.unavailable_reason = "target_bookmark_key_ambiguous";
      return true;
    }
    bookmark = candidate;
  }
  if (bookmark == nullptr) {
    output.unavailable_reason = "target_bookmark_key_not_in_current_collection";
    return true;
  }
  std::uint64_t date = 0;
  if (!ReadAt(access, bookmark, abi.bookmark_date, date) ||
      static_cast<std::uint32_t>(date) != profile.date_low_raw) {
    output.unavailable_reason = "target_bookmark_date_mismatch";
    return true;
  }
  output.target_resolved = true;
  if (fixture_setter == nullptr && access.read_memory != nullptr) {
    output.unavailable_reason = "fixture_bookmark_setter_required";
    return true;
  }
  if (crozier && current_group != target_group) {
    if (fixture_group_setter == nullptr && access.read_memory != nullptr) {
      output.unavailable_reason = "fixture_bookmark_group_setter_required";
      return true;
    }
    // Stock SelectBookmarkGroup callback unwraps Group.Self into RDX and
    // calls 0x1060090(view, Group*). It writes +0xD8 and picks a native
    // default Bookmark. SetSelectedBookmark 0x1060950 leaves +0xD8 intact.
    output.group_setter_invoked = true;
    if (fixture_group_setter != nullptr) {
      if (!fixture_group_setter(access.context, setup_view, target_group)) {
        output.unavailable_reason = "fixture_bookmark_group_setter_rejected";
        return true;
      }
    } else {
      using NativeSetter = void (*)(void *, const void *);
      reinterpret_cast<NativeSetter>(environment.module_base + abi.group_setter)(
          setup_view, target_group);
    }
    if (!ReadAt(access, setup_view, abi.selected_group, current_group) ||
        current_group != target_group) {
      output.unavailable_reason = "submitted_bookmark_group_not_target";
      return true;
    }
  }
  output.setter_invoked = true;
  if (fixture_setter != nullptr) {
    if (!fixture_setter(access.context, setup_view, bookmark)) {
      output.unavailable_reason = "fixture_bookmark_setter_rejected";
      return true;
    }
  } else {
    using NativeSetter = void (*)(void *, const void *);
    reinterpret_cast<NativeSetter>(environment.module_base + abi.bookmark_setter)(
        setup_view, bookmark);
  }
  void *current = nullptr;
  std::string key;
  std::uint64_t current_date = 0;
  if (!ReadAt(access, setup_view, abi.selected_bookmark, current) ||
      current != bookmark || !ReadScriptKeySso(access, current, 0x18, key) ||
      (crozier &&
       (!ReadAt(access, current, abi.bookmark_date, current_date) ||
        !ReadAt(access, setup_view, abi.selected_group, current_group)))) {
    output.unavailable_reason = "submitted_bookmark_unreadable";
    return true;
  }
  output.same_frame_bookmark_matches = key == profile.bookmark_key &&
      (!crozier ||
       (static_cast<std::uint32_t>(current_date) == profile.date_low_raw &&
        current_group == target_group));
  if (!output.same_frame_bookmark_matches) {
    output.unavailable_reason = "submitted_bookmark_not_target";
  }
  return true;
}

} // namespace xar::ck3_11906
