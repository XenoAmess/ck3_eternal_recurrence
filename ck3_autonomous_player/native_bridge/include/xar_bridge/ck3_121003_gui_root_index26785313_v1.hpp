#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <cstddef>
#include <cstdint>
#include <vector>

namespace xar::ck3_121003::build26785313 {
inline constexpr std::uintptr_t kGuiRootApplicationVtableRvaV1=0x4AFA650;
inline constexpr std::uintptr_t kGuiRootManagerRvaV1=0x5D6A9F0;
inline constexpr std::uintptr_t kGuiRootManagerVtableRvaV1=0x507D8E0;
inline constexpr std::uintptr_t kGuiRootEntryVtableRvaV1=0x507D8C0;
inline constexpr std::size_t kGuiRootIndexMaximumEntriesV1=4096;
// Internal addresses are equality witnesses, never consumer-supplied handles.
// No widget/TreeNode fields, names, modal data or callable pointers are read.
struct GuiRootIndexEntryV1 {
  std::uintptr_t object=0,widget=0,context=0;
  friend bool operator==(const GuiRootIndexEntryV1&,const GuiRootIndexEntryV1&)=default;
};
struct GuiRootIndexV1 {
  std::uintptr_t logical_owner=0,application=0,first=0,context=0,manager=0,data=0;
  std::int32_t capacity=0,count=0;
  std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
  std::uint32_t owner_thread_id=0;
  std::vector<GuiRootIndexEntryV1> entries;
  friend bool operator==(const GuiRootIndexV1&,const GuiRootIndexV1&)=default;
};
struct GuiRootIndexRequestV1 {
  // Trusted caller supplies its existing Core occurrence; no public route or
  // Full/GUI/action capability is introduced by this internal reader mode.
  std::uint64_t connection_generation=0;
  std::uint64_t deadline_unix_ms=0;
  ck3_1210::CoreSnapshotPrefix expected_core{};
};
} // namespace xar::ck3_121003::build26785313
