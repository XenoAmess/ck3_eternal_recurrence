#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace xar::ck3_11906 {

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

} // namespace xar::ck3_11906
