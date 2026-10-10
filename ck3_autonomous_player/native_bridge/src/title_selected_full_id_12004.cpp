#include "xar_bridge/title_selected_full_id_12004.hpp"

namespace xar::ck3_12004 {
namespace {

template<class T>
bool Read(const TitleSelectedFullIdAccess12004 &access,
          std::uintptr_t address, T &value) noexcept {
  return address && access.read_memory(access.context, address, &value, sizeof(value));
}

bool Resolve(const TitleSelectedFullIdAccess12004 &access,
             std::uintptr_t title, std::size_t requested_offset,
             std::uintptr_t registry_rva, std::uintptr_t fallback_rva,
             std::size_t selected_full_id_offset,
             TitleSelectedFullIdSource12004 &source,
             std::uintptr_t &selected) noexcept {
  std::uintptr_t store = 0;
  if (!Read(access, access.module_base + registry_rva, store)) return false;
  if (store) {
    std::uint32_t requested = 0, bound = 0;
    if (!Read(access, title + requested_offset, requested)) return false;
    source.requested_full_id = requested;
    if (!Read(access, store + 0x2C, bound)) return false;
    const auto index = requested & 0xFFFFFFU;
    if (index < bound) {
      std::uintptr_t table = 0, object = 0;
      if (!Read(access, store + 0x20, table) || !table ||
          !Read(access, table + std::uintptr_t(index) * 16 + 8, object)) return false;
      if (object) {
        std::uint32_t full = 0;
        if (!Read(access, object + selected_full_id_offset, full)) return false;
        source.checked_selected_full_id = full;
        if (full == requested) {
          selected = object;
          source.selected_object_identity = selected;
          source.used_fallback = false;
          return true;
        }
      }
    }
  }
  if (!Read(access, access.module_base + fallback_rva, selected)) return false;
  source.selected_object_identity = selected;
  source.used_fallback = true;
  return selected != 0;
}

} // namespace

bool ReadTitleSelectedFullId12004(
    const TitleSelectedFullIdAccess12004 &access, std::uintptr_t title,
    std::uint32_t &out_full_id, TitleSelectedFullIdSource12004 *source) noexcept {
  TitleSelectedFullIdSource12004 captured;
  captured.original_title_identity = title;
  const auto publish = [&](bool complete) noexcept {
    captured.source_complete = complete;
    if (source) *source = captured;
    return complete;
  };
  if (!access.exact_12004_bound || !access.module_base || !access.read_memory || !title)
    return publish(false);
  std::uint8_t flag = 0;
  if (!Read(access, title + 0x130, flag)) return publish(false);
  captured.title_flag_130 = flag;
  std::uintptr_t selected = 0;
  std::uint32_t output = 0;
  if (flag) {
    captured.branch = TitleSelectedFullIdBranch12004::flag_nonzero_character_link;
    if (!Resolve(access, title, 0x128, 0x5C67568, 0x5C67570, 0x18, captured, selected))
      return publish(false);
    std::uintptr_t link = 0;
    if (!Read(access, selected + 0x1C0, link)) return publish(false);
    captured.selected_link_identity = link;
    if (!link) output = UINT32_MAX;
    else if (!Read(access, link + 0x1B8, output)) return publish(false);
  } else {
    captured.branch = TitleSelectedFullIdBranch12004::flag_zero_title_reference;
    if (!Resolve(access, title, 0x12C, 0x5D1DAF8, 0x5D1DAE0, 0x10, captured, selected) ||
        !Read(access, selected + 0x128, output)) return publish(false);
  }
  captured.output_full_id = output;
  out_full_id = output;
  return publish(true);
}

bool ReadTitleSelectedFullIdAdapter12004(
    void *context, std::uintptr_t title, std::uint32_t &out_full_id) noexcept {
  if (!context) return false;
  return ReadTitleSelectedFullId12004(
      *static_cast<const TitleSelectedFullIdAccess12004 *>(context), title, out_full_id);
}

} // namespace xar::ck3_12004
