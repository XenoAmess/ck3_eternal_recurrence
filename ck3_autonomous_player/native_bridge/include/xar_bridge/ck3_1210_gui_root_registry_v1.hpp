#pragma once
#include "xar_bridge/ck3_1210_gui_control_v1.hpp"
#include <limits>
#include <unordered_set>

namespace xar::ck3_1210 {
inline constexpr std::uintptr_t kGuiScriptedRootManagerRvaV1=0x5D6A9F0;
inline constexpr std::uintptr_t kGuiScriptedRootManagerVtableRvaV1=0x507D570;
inline constexpr std::uintptr_t kGuiScriptedRootEntryVtableRvaV1=0x507D550;
inline constexpr std::size_t kGuiScriptedRootMaximumEntriesV1=4096;
inline constexpr std::size_t kGuiRootMaximumDepthV1=64;
struct GuiControlRootNodeV1 {
  std::uintptr_t p=0,parent=0;std::size_t depth=0;std::string path;
  bool visible=true,enabled=true;
};
// Production supplies only fixed ReadProcessMemory/TreeNode adapters. Fixtures
// share this algorithm with isolated byte storage, never a Game or effect.
struct GuiControlRootReaderV1 {
  void *context=nullptr;
  bool (*bytes)(void *,std::uintptr_t,void *,std::size_t) noexcept=nullptr;
  bool (*widget)(void *,std::uintptr_t,GuiControlIdentityV1 &) noexcept=nullptr;
};
template<class T> inline bool GuiRootLoadV1(const GuiControlRootReaderV1 &r,
    std::uintptr_t object,std::size_t offset,T &value) {
  return r.bytes && object && offset<=(std::numeric_limits<std::uintptr_t>::max)()-object &&
      r.bytes(r.context,object+offset,&value,sizeof(value));
}
enum class GuiControlChildrenResultV1 {
  complete,depth_budget_exhausted,node_budget_exhausted,child_pointer_read_failed,duplicate_or_cycle
};
inline GuiControlChildrenResultV1 AppendGuiControlChildrenV1(const GuiControlRootReaderV1 &reader,
    const GuiControlRootNodeV1 &n,const GuiControlIdentityV1 &w,
    std::vector<GuiControlRootNodeV1> &nodes,std::unordered_set<std::uintptr_t> &seen,std::size_t maximum) {
  if(w.child_count && n.depth>=kGuiRootMaximumDepthV1)return GuiControlChildrenResultV1::depth_budget_exhausted;
  if(w.child_count<0 || nodes.size()>maximum || static_cast<std::size_t>(w.child_count)>maximum-nodes.size())
    return GuiControlChildrenResultV1::node_budget_exhausted;
  for(std::int32_t i=0;i<w.child_count;++i) {
    std::uintptr_t child=0;
    if(!GuiRootLoadV1(reader,w.children,static_cast<std::size_t>(i)*8,child))return GuiControlChildrenResultV1::child_pointer_read_failed;
    if(!child)continue;
    if(!seen.insert(child).second)return GuiControlChildrenResultV1::duplicate_or_cycle;
    std::string path=n.path;if(!path.empty())path+='/';path+=std::to_string(i);
    nodes.push_back({child,n.p,n.depth+1,std::move(path),w.row.effective_visible,w.row.enabled});
  }
  return GuiControlChildrenResultV1::complete;
}
inline bool ResolveGuiScriptedRootV1(const GuiControlRootReaderV1 &reader,
    std::uintptr_t module,std::uintptr_t context,std::uintptr_t global_root,std::string_view name,
    GuiControlRootNodeV1 &selected,GuiControlScriptedRootWitnessV1 &source,std::string &reason) {
  selected={};source={};
  const auto fail=[&](const char *why) {selected={};source={};reason=why;return false;};
  if(!module || !context || !global_root || !reader.bytes || !reader.widget || !GuiControlRootNameV1(name) ||
      module>(std::numeric_limits<std::uintptr_t>::max)()-kGuiScriptedRootManagerRvaV1)
    return fail("gui_scripted_registry_invalid_request");
  source.manager=module+kGuiScriptedRootManagerRvaV1;
  std::uintptr_t manager_vtable=0;
  if(!GuiRootLoadV1(reader,source.manager,0,manager_vtable) || manager_vtable!=module+kGuiScriptedRootManagerVtableRvaV1 ||
      !GuiRootLoadV1(reader,source.manager,0x30,source.data) ||
      !GuiRootLoadV1(reader,source.manager,0x38,source.capacity) || !GuiRootLoadV1(reader,source.manager,0x3C,source.count))
    return fail("gui_scripted_registry_unavailable");
  if(source.count<0 || source.capacity<source.count)return fail("gui_scripted_registry_vector_invalid");
  if(static_cast<std::size_t>(source.count)>kGuiScriptedRootMaximumEntriesV1)return fail("gui_scripted_registry_entry_budget_exhausted");
  if(source.count && !source.data)return fail("gui_scripted_registry_vector_invalid");
  std::vector<std::uintptr_t> entries(static_cast<std::size_t>(source.count));
  if(source.count && !reader.bytes(reader.context,source.data,entries.data(),entries.size()*sizeof(std::uintptr_t)))
    return fail("gui_scripted_registry_entries_read_failed");
  std::unordered_set<std::uintptr_t> seen_entries,seen_roots;std::size_t matches=0;
  for(const auto object:entries) {
    GuiControlScriptedRootEntryV1 entry{};entry.object=object;
    if(!object)return fail("gui_scripted_registry_null_entry");
    if(!seen_entries.insert(object).second)return fail("gui_scripted_registry_duplicate_entry");
    if(!GuiRootLoadV1(reader,object,0,entry.vtable) || entry.vtable!=module+kGuiScriptedRootEntryVtableRvaV1 ||
        !GuiRootLoadV1(reader,object,0x60,entry.widget) || !GuiRootLoadV1(reader,object,0x68,entry.context))
      return fail("gui_scripted_registry_entry_invalid");
    if(entry.context!=context)return fail("gui_scripted_registry_context_mismatch");
    if(!entry.widget) {source.entries.push_back(entry);continue;} // No live root.
    if(!seen_roots.insert(entry.widget).second)return fail("gui_scripted_registry_duplicate_root");
    GuiControlIdentityV1 row{};
    if(!reader.widget(reader.context,entry.widget,row) || row.widget!=entry.widget || row.context!=context)
      return fail("gui_scripted_registry_widget_invalid");
    entry.runtime_name=row.row.runtime_name;source.entries.push_back(entry);
    if(row.row.runtime_name==name) {selected.p=entry.widget;++matches;}
  }
  if(matches!=1)return fail(matches?"gui_root_ambiguous":"gui_root_not_materialized");
  if(selected.p==global_root)return fail("gui_scripted_root_is_global_root");
  std::unordered_set<std::uintptr_t> ancestors;std::uintptr_t cursor=selected.p;
  for(std::size_t depth=0;depth<=kGuiRootMaximumDepthV1;++depth) {
    GuiControlIdentityV1 row{};
    if(!cursor || !ancestors.insert(cursor).second)return fail("gui_root_parent_cycle_or_detached");
    if(!reader.widget(reader.context,cursor,row) || row.widget!=cursor || row.context!=context || row.child_count<0 ||
        row.child_count>4096 || (row.child_count && !row.children))return fail("gui_root_parent_invalid");
    source.ancestry.push_back(row);
    if(cursor==global_root)break;
    if(depth==kGuiRootMaximumDepthV1)return fail("gui_root_parent_depth_budget_exhausted");
    cursor=row.parent;
  }
  if(source.ancestry.empty() || source.ancestry.back().widget!=global_root)return fail("gui_root_parent_not_global");
  for(std::size_t i=1;i<source.ancestry.size();++i) {
    const auto &parent=source.ancestry[i];const auto child=source.ancestry[i-1].widget;
    std::vector<std::uintptr_t> children(static_cast<std::size_t>(parent.child_count));
    if(parent.child_count && !reader.bytes(reader.context,parent.children,children.data(),children.size()*sizeof(std::uintptr_t)))
      return fail("gui_global_parent_children_read_failed");
    std::size_t links=0;for(const auto value:children)if(value==child)++links;
    if(links!=1)return fail("gui_root_parent_child_backref_invalid");
    selected.visible=selected.visible && (parent.flags&0x18)==0;
    selected.enabled=selected.enabled && (parent.flags&0x06)==0;
  }
  selected.parent=source.ancestry.front().parent;
  // Prove this complete root index and ancestry were stable throughout the read.
  std::uintptr_t current_data=0,current_vtable=0;std::int32_t count=0,capacity=0;
  if(!GuiRootLoadV1(reader,source.manager,0,current_vtable) || current_vtable!=manager_vtable ||
      !GuiRootLoadV1(reader,source.manager,0x30,current_data) || current_data!=source.data ||
      !GuiRootLoadV1(reader,source.manager,0x38,capacity) || capacity!=source.capacity ||
      !GuiRootLoadV1(reader,source.manager,0x3C,count) || count!=source.count)
    return fail("gui_scripted_registry_changed");
  std::vector<std::uintptr_t> second(entries.size());
  if(count && (!reader.bytes(reader.context,current_data,second.data(),second.size()*sizeof(std::uintptr_t)) || second!=entries))
    return fail("gui_scripted_registry_changed");
  for(const auto &entry:source.entries) {
    std::uintptr_t vt=0,widget=0,ctx=0;
    if(!GuiRootLoadV1(reader,entry.object,0,vt) || vt!=entry.vtable || !GuiRootLoadV1(reader,entry.object,0x60,widget) ||
        widget!=entry.widget || !GuiRootLoadV1(reader,entry.object,0x68,ctx) || ctx!=entry.context)
      return fail("gui_scripted_registry_changed");
    if(widget) {
      GuiControlIdentityV1 row{};
      if(!reader.widget(reader.context,widget,row) || row.widget!=widget || row.context!=context || row.row.runtime_name!=entry.runtime_name)
        return fail("gui_scripted_registry_changed");
    }
  }
  for(const auto &ancestor:source.ancestry) {
    GuiControlIdentityV1 second_row{};
    if(!reader.widget(reader.context,ancestor.widget,second_row) || second_row!=ancestor)return fail("gui_root_parent_changed");
  }
  reason.clear();return true;
}
} // namespace xar::ck3_1210
