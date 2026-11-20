// Included in the current reader private namespace; only bounded fixed copies, never native GUI calls.
[[maybe_unused]]bool GuiWindowTypeV1(std::uintptr_t image,std::uintptr_t widget,std::uintptr_t &vtable) noexcept {
 const auto inside=[&](std::uintptr_t p,std::size_t n){return p>=image&&n<=kImageSize&&p-image<=kImageSize-n;};
 std::uintptr_t col=0;std::uint32_t signature=0,offset=0,self=0,chd_rva=0,count=0,bases_rva=0;
 if(!At(widget,0,vtable)||!inside(vtable,8)||vtable<image+8||!At(vtable-8,0,col)||!inside(col,24)||
    !At(col,0,signature)||signature!=1||!At(col,4,offset)||offset!=0||!At(col,8,self)||self!=0||
    !At(col,20,self)||image+self!=col||!At(col,16,chd_rva)||!inside(image+chd_rva,16))return false;
 const auto chd=image+chd_rva;
 if(!At(chd,0,signature)||signature!=0||!At(chd,8,count)||!count||count>64||
    !At(chd,12,bases_rva)||!inside(image+bases_rva,static_cast<std::size_t>(count)*4))return false;
 for(std::uint32_t i=0;i<count;++i) {
  std::uint32_t desc_rva=0,type=0;std::int32_t mdisp=0,pdisp=0;
  if(!At(image+bases_rva,static_cast<std::size_t>(i)*4,desc_rva)||!inside(image+desc_rva,28)||
     !At(image+desc_rva,0,type)||!At(image+desc_rva,8,mdisp)||!At(image+desc_rva,12,pdisp))return false;
  if(type==0x6082F78&&mdisp==0&&pdisp==-1)return true;
 }
 return false;
}
[[maybe_unused]]bool GuiWindowNodeReadV1(std::uintptr_t image,std::uintptr_t widget,std::uintptr_t context,
    std::uintptr_t parent,GuiWindowNodeV1 &out) {
 GuiWindowNodeV1 n;n.widget=widget;std::array<char,kGuiWindowMaxNameBytesV1+1> text{};
 if(!widget||!GuiWindowTypeV1(image,widget,n.vtable)||!At(widget,0xD0,n.flags)||(n.flags&1)!=0||
    !At(widget,0xD8,n.context)||n.context!=context||!At(widget,0xE8,n.parent)||n.parent!=parent||
    !At(widget,0xF0,n.children)||!At(widget,0xF8,n.child_capacity)||!At(widget,0xFC,n.child_count)||
    n.child_count<0||n.child_capacity<n.child_count||static_cast<std::size_t>(n.child_count)>kGuiWindowMaxNodesV1||
    (n.child_count&&!n.children)||!At(widget,0x1C8,n.name_size)||!At(widget,0x1D0,n.name_capacity)||
    n.name_size>kGuiWindowMaxNameBytesV1||n.name_capacity<n.name_size||n.name_capacity>0x1000000)return false;
 if(n.name_capacity<=15) {if(n.name_capacity!=15||n.name_size>15)return false;n.name_data=widget+0x1B8;}
 else if(!At(widget,0x1B8,n.name_data)||!n.name_data)return false;
 if(!Copy(reinterpret_cast<const void*>(n.name_data),text.data(),static_cast<std::size_t>(n.name_size)+1)||
    text[n.name_size]!=0||std::memchr(text.data(),0,static_cast<std::size_t>(n.name_size)))return false;
 if(n.name_size&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(n.name_size),nullptr,0)==0)return false;
 n.name.assign(text.data(),static_cast<std::size_t>(n.name_size));n.visible=(n.flags&0x18)==0;n.enabled=(n.flags&0x06)==0;
 out=std::move(n);return true;
}
bool ReadGuiWindowV1([[maybe_unused]]ReadonlyContext &q,
 [[maybe_unused]]const ck3_11906::MainThreadExecutionStampV1 &stamp,
 [[maybe_unused]]const ck3_1210::CoreSnapshotPrefix &core,[[maybe_unused]]GuiWindowV1 &out,
 [[maybe_unused]]const OwnerInvocationV1 &invocation={}) noexcept {
#if !defined(XAR_CK3_ENABLE_121003_26785313_GUI_WINDOW_V1)
 return false;
#else
 try {
  const auto valid=[&](){const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();return q.gui_window_request&&wall>=0&&static_cast<std::uint64_t>(wall)<q.gui_window_request->deadline_unix_ms&&Owner(q,stamp,invocation);};
  if(!q.gui_window_request||!q.gui_window_request->connection_generation||!valid()||
     !Same(q.gui_window_request->expected_core,core)||q.gui_window_request->window_name.empty()||
     q.gui_window_request->window_name.size()>kGuiWindowMaxNameBytesV1||!VerifyGuiWindowImageV1(q.bindings.module_base))return false;
  const auto base=q.bindings.module_base;GuiWindowV1 v;std::uintptr_t vt=0;
  v.requested_name=q.gui_window_request->window_name;v.connection_generation=q.gui_window_request->connection_generation;
  v.ticket_sequence=q.ticket.sequence;v.pump_epoch=stamp.pump_epoch;v.owner_thread_id=stamp.thread_id;
  if(!At(reinterpret_cast<std::uintptr_t>(q.bindings.core.jomini_state_slot),0,v.logical_owner)||
     !At(v.logical_owner,0x18,v.application)||!At(v.application,0,vt)||vt!=base+kGuiRootApplicationVtableRvaV1||
     !At(v.application,0x1B8,v.first)||!At(v.first,0x58,v.context)||!v.context||
     !At(v.context,0xD0,v.global_root)||!GuiWindowNodeReadV1(base,v.global_root,v.context,0,v.root))return false;
  std::unordered_set<std::uintptr_t> unique{v.global_root};std::uintptr_t selected=0;std::size_t name_bytes=v.root.name.size();
  for(std::int32_t i=0;i<v.root.child_count;++i) {
   std::uintptr_t p=0;GuiWindowNodeV1 n;
   if(!valid()||!At(v.root.children,static_cast<std::size_t>(i)*8,p)||!unique.insert(p).second||
      !GuiWindowNodeReadV1(base,p,v.context,v.global_root,n))return false;
   n.sibling_index=static_cast<std::uint32_t>(i);n.visible=n.visible&&v.root.visible;n.enabled=n.enabled&&v.root.enabled;name_bytes+=n.name.size();
   if(n.name==v.requested_name){if(selected)return false;selected=p;}
   v.top_level.push_back(std::move(n));
  }
  if(name_bytes>131072)return false;
  if(selected) {
   const auto found=std::find_if(v.top_level.begin(),v.top_level.end(),[&](const auto&n){return n.widget==selected;});
   v.tree.push_back(*found);v.window_found=true;
   struct Pending{std::size_t index;};std::vector<Pending> todo{{0}};
   while(!todo.empty()) {
    const auto index=todo.back().index;todo.pop_back();const auto parent_node=v.tree[index];
    if(!valid()||(parent_node.depth>=kGuiWindowMaxDepthV1&&parent_node.child_count))return false;
    for(std::int32_t i=0;i<parent_node.child_count;++i) {
     std::uintptr_t p=0;GuiWindowNodeV1 n;
     if(v.tree.size()>=kGuiWindowMaxNodesV1||!At(parent_node.children,static_cast<std::size_t>(i)*8,p)||!unique.insert(p).second||
        !GuiWindowNodeReadV1(base,p,v.context,parent_node.widget,n))return false;
     n.parent_index=static_cast<std::int32_t>(index);n.depth=parent_node.depth+1;n.sibling_index=static_cast<std::uint32_t>(i);
     n.visible=n.visible&&parent_node.visible;n.enabled=n.enabled&&parent_node.enabled;
     name_bytes+=n.name.size();if(name_bytes>131072)return false;
     todo.push_back({v.tree.size()});v.tree.push_back(std::move(n));
    }
   }
  }
  if(!valid())return false;out=std::move(v);return true;
 }catch(...){return false;}
#endif
}
