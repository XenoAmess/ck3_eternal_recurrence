#include "xar_bridge/frontend_bookmark_model_probe_v1.hpp"

#define NOMINMAX
#include <windows.h>

#include <cstring>
#include <limits>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

constexpr std::uintptr_t kInterfaceApplicationVtableRva = 0x4093158;
constexpr std::uintptr_t kFrontendSetupViewVtableRva = 0x410B070;
constexpr std::uintptr_t kMaxExactImageRva = 0x6000000;
constexpr std::uintptr_t kBookmarkCharacterStride = 0x1A0;
constexpr std::string_view kSupportedBookmarkKey =
    "bm_1066_rags_to_riches";
constexpr std::string_view kSupportedCharacterKey =
    "bookmark_rags_to_riches_petty_king_murchad";
constexpr std::string_view kFeudalGovernmentKey = "feudal_government";
constexpr std::uintptr_t kFinalGovernmentGetterRva = 0x2DAB260;

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
  if (!ReadAt(access, environment.gui_global_slot, 0, chain[0]) ||
      !ReadAt(access, chain[0], kZhongguoGuiChainFirstOffset, chain[1]) ||
      !ReadAt(access, chain[1], kZhongguoGuiChainSecondOffset,
              chain[2])) {
    output.unavailable_reason = "gui_owner_chain_unreadable";
    return true;
  }
  for (std::size_t i = 0; i < chain.size(); ++i) {
    if (!ReadVtableRva(access, environment.module_base, chain[i],
                       output.gui_chain_vtable_rvas[i])) {
      output.unavailable_reason = "gui_owner_type_unreadable";
      return true;
    }
    if (output.gui_chain_vtable_rvas[i] ==
        kInterfaceApplicationVtableRva) {
      output.interface_application_chain_level =
          static_cast<std::int32_t>(i);
    }
  }
  if (output.interface_application_chain_level < 0) {
    output.unavailable_reason = "interface_application_not_in_gui_chain";
    return true;
  }

  const auto *application = chain[static_cast<std::size_t>(
      output.interface_application_chain_level)];
  void *frontend_orchestrator = nullptr;
  void *wrapper = nullptr;
  void *owner = nullptr;
  void *setup_view = nullptr;
  if (!ReadAt(access, application, 0x78, frontend_orchestrator) ||
      !ReadAt(access, frontend_orchestrator, 0x10, wrapper) ||
      !ReadAt(access, wrapper, 0x08, owner) ||
      !ReadAt(access, owner, 0x30, setup_view) ||
      !ReadVtableRva(access, environment.module_base, setup_view,
                     output.setup_view_vtable_rva) ||
      output.setup_view_vtable_rva != kFrontendSetupViewVtableRva) {
    output.unavailable_reason = "frontend_setup_view_unverified";
    return true;
  }
  void *view_root = nullptr;
  if (!ReadAt(access, setup_view, 0x78, view_root) ||
      view_root != bookmarks_root) {
    output.unavailable_reason = "frontend_setup_view_root_mismatch";
    return true;
  }
  output.setup_view_matches_bookmarks_root = true;

  void *selected_group = nullptr;
  if (!ReadAt(access, setup_view, 0x108, selected_group)) {
    output.unavailable_reason = "selected_bookmark_group_pointer_unreadable";
    return true;
  }
  // frontend_bookmarks.gui:2495-2496 legitimately clears the selected group
  // after selecting Bookmark.Self. A null group is not a missing bookmark.
  if (selected_group != nullptr) {
    if (!ReadScriptKeySso(access, selected_group, 0x38,
                          output.selected_bookmark_group_key)) {
      output.unavailable_reason =
          "selected_bookmark_group_script_key_unreadable";
      return true;
    }
    (void)ReadVtableRva(access, environment.module_base, selected_group,
                        output.selected_bookmark_group_vtable_rva);
    output.selected_bookmark_group_key_available = true;
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
  output.unavailable_reason = "runtime_bookmark_date_unverified";
  return true;
}

} // namespace xar::ck3_11906
