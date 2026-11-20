#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <cstdint>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr char kGuiWindowStepV1[]="query-scripted-gui-window-v1";
inline constexpr char kGuiWindowRequestSchemaV1[]="ck3.scripted_gui_window_request.v1";
inline constexpr char kGuiWindowSchemaV1[]="ck3.scripted_gui_window.v1";
inline constexpr char kGuiWindowBackendV1[]="ck3-1.21.0.3-native-headless-main-thread";
inline constexpr std::size_t kGuiWindowMaxNodesV1=4096,kGuiWindowMaxDepthV1=64,kGuiWindowMaxNameBytesV1=192;
struct GuiWindowRequestV1 {
 std::uint64_t connection_generation=0,deadline_unix_ms=0;
 ck3_1210::CoreSnapshotPrefix expected_core{};
 std::string window_name;
};
// Internal identities stay in the owner-side sample only. They are never wire addresses or action tokens.
struct GuiWindowNodeV1 {
 std::uintptr_t widget=0,vtable=0,parent=0,context=0,children=0,name_data=0;
 std::int32_t child_count=0,child_capacity=0,parent_index=-1;
 std::uint64_t name_size=0,name_capacity=0;
 std::uint32_t depth=0,sibling_index=0;
 std::uint8_t flags=0;
 bool visible=false,enabled=false;
 std::string name;
 friend bool operator==(const GuiWindowNodeV1&,const GuiWindowNodeV1&)=default;
};
struct GuiWindowV1 {
 std::uintptr_t logical_owner=0,application=0,first=0,context=0,global_root=0;
 std::uint64_t connection_generation=0,ticket_sequence=0,pump_epoch=0;
 std::uint32_t owner_thread_id=0;
 std::string requested_name;
 GuiWindowNodeV1 root;
 std::vector<GuiWindowNodeV1> top_level,tree;
 // Internal selected-window ancestry, ordered windows_layer through the real
 // parent of tree[0]. Public v1 root-direct reads leave this empty. Physical
 // parent/context/sibling/depth values are preserved; this is not a wire tree.
 std::vector<GuiWindowNodeV1> ancestors;
 bool window_found=false;
 friend bool operator==(const GuiWindowV1&,const GuiWindowV1&)=default;
};
} // namespace
