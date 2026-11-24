// Included in actual Readonly TU after the independent inventory reader.
// No native callbacks or generic GUI activation. Only actual private Owner/Read.
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1
namespace {
bool LivingGuiSceneSample267V1(ReadonlyContext&q,const ck3_11906::MainThreadExecutionStampV1&s,
 const OwnerInvocationV1&i,const LivingInventoryQueryRequest267V1&r,std::uint64_t mono,
 LivingWeaponFrame267V1&out,std::string_view fixed_name,std::string&why){
 const auto valid=[&]{const auto wall=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
  return wall>0&&static_cast<std::uint64_t>(wall)<r.deadline_unix_ms&&mono&&GetTickCount64()<mono&&Owner(q,s,i);};
 const auto fail=[&](const char*reason){why=reason;return false;};
 if(!valid()||!Read(q,s,i)||!q.observation.available||q.observation.offline_fixture||!q.observation.main_owner_observed||
  !Same(out.inventory.core,q.observation.core))return fail("living_weapon_exact_owner_Core_unavailable");
 auto&g=out.gui;const auto image=q.bindings.module_base;std::uintptr_t vt=0,back=0;
 if(!At(out.inventory.jomini,0x10,out.gfx)||!At(out.gfx,0,vt)||vt!=image+0x4B24748||
  !At(out.gfx,0x20,back)||back!=out.inventory.jomini||!At(out.gfx,0x88,out.manager)||
  !At(out.manager,0,vt)||vt!=image+0x4B22578||!At(out.manager,0x40,back)||back!=out.inventory.jomini||
  !At(out.inventory.jomini,0x18,g.application)||!At(g.application,0,vt)||vt!=image+kGuiRootApplicationVtableRvaV1||
  !At(g.application,0x1B8,g.first)||!At(g.first,0x58,g.context)||!g.context||
  !At(g.context,0xD0,g.global_root))return fail("living_weapon_current_scene_backrefs_unavailable");
 g.logical_owner=out.inventory.jomini;g.connection_generation=out.inventory.connection_generation;
 g.ticket_sequence=q.ticket.sequence;g.pump_epoch=s.pump_epoch;g.owner_thread_id=s.thread_id;
 g.requested_name=fixed_name;GuiWindowNodeV1 global;
 if(!GuiWindowNodeReadV1(image,g.global_root,g.context,0,global))return false;
 g.tree.push_back(global);std::unordered_set<std::uintptr_t>seen{global.widget};
 const auto children=[&](const GuiWindowNodeV1&parent){
  for(std::int32_t n=0;n<parent.child_count;++n){std::uintptr_t p=0;GuiWindowNodeV1 row;
   if(!valid()||g.tree.size()>=4096||!At(parent.children,static_cast<std::size_t>(n)*8,p)||
    !seen.insert(p).second||!GuiWindowNodeReadV1(image,p,g.context,parent.widget,row))return false;
   row.depth=parent.depth+1;row.sibling_index=static_cast<std::uint32_t>(n);
   row.visible&=parent.visible;row.enabled&=parent.enabled;g.tree.push_back(std::move(row));
  }return true;
 };
 if(!children(global))return fail("living_weapon_global_complete_child_census_unavailable");
 g.top_level.assign(g.tree.begin()+1,g.tree.end());
 for(const auto&layer:g.top_level)if(layer.name=="middle"||layer.name=="windows_layer"||layer.name=="top")
  if(!children(layer))return fail("living_weapon_layer_complete_child_census_unavailable");
 for(const auto&node:g.tree)if(node.name==fixed_name){
  if(g.window_found)return fail("living_weapon_duplicate_inventory_root");g.root=node;g.window_found=true;
 }
 out.owner_observed=valid();return out.owner_observed;
}
}
bool ReadLivingWeaponFrameOnOwner267V1(const ReadonlyBindings&b,
 ck3_11906::MainThreadQueryMailboxV1*m,const ck3_11906::MainThreadQueryTicketV1&t,
 const ck3_11906::MainThreadExecutionStampV1&s,void*context,const LivingInventoryQueryRequest267V1&r,
 std::uint64_t mono,LivingWeaponFrame267V1&out,std::string&why)noexcept{
 out={};why="living_weapon_frame_not_attached";
 try{
  if(!m||m->offline_fixture||!context||m->permitted_executor_artifact_personal_read12004!=&ExecuteLivingOnOwner267V1)return false;
  LivingWeaponFrame267V1 a,z;
  if(!ReadLivingInventoryQueryFrameOnOwner267V1(b,m,t,s,context,r,mono,a.inventory,why))return false;
    // Connection is supplied by the actual enclosing owner context, not request
  // data. It is not derived from an ID or a public serialized Source.
  a.inventory.connection_generation=LivingOwnerConnection267V1(static_cast<const LivingOwnerInvocation267V1*>(context));if(!a.inventory.connection_generation)return false;z.inventory=a.inventory;
  ReadonlyContext q;q.bindings=b;q.mailbox=m;q.ticket=t;q.mode=ReadonlyModeV1::core_only;
  const OwnerInvocationV1 invocation{&ExecuteLivingOnOwner267V1,context};
  if(!LivingGuiSceneSample267V1(q,s,invocation,r,mono,a,"inventory_view",why)||
   !LivingGuiSceneSample267V1(q,s,invocation,r,mono,z,"inventory_view",why)||
   a.gui!=z.gui||a.gfx!=z.gfx||a.manager!=z.manager||!Owner(q,s,invocation)){
   why="living_weapon_complete_UI_census_changed";return false;}
  out=std::move(z);why.clear();return true;
 }catch(...){why="living_weapon_frame_copy_unavailable";return false;}
}
#endif
