#include "xar_bridge/ingame_decision_item_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include <Windows.h>
#include <array>
#include <charconv>
#include <cstring>
#include <limits>
#include <vector>
#include <utility>

namespace xar::ck3_11906 {
namespace {
constexpr std::uintptr_t kImageSize=0x61C5000;
constexpr std::size_t kMaximumGroups=64, kMaximumRows=2048, kMaximumKey=192;
bool Bytes(const void *p,void *out,std::size_t size) noexcept {
  if(!p||!out||!size)return false;SIZE_T got=0;
  return ReadProcessMemory(GetCurrentProcess(),p,out,size,&got)&&got==size;
}
const void *At(const void *p,std::size_t offset) noexcept {
  const auto value=reinterpret_cast<std::uintptr_t>(p);
  return !value||offset>std::numeric_limits<std::uintptr_t>::max()-value?nullptr:reinterpret_cast<const void *>(value+offset);
}
template<class T> bool Read(const void *p,std::size_t offset,T &out) noexcept {return Bytes(At(p,offset),&out,sizeof(out));}
bool CodePins(const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  const std::array<unsigned char,32> find{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x81,0xd0,0x00,0x00,0x00,0x48,0x8b,0xfa,0x48,0x8b};
  const std::array<unsigned char,8> groups{0x48,0x8d,0x81,0x58,0x02,0x00,0x00,0xc3};
  const std::array<unsigned char,4> decision{0x48,0x8b,0x01,0xc3};
  std::array<unsigned char,32> actual_find{};std::array<unsigned char,8> actual_groups{};std::array<unsigned char,4> actual_decision{};
  return Bytes(reinterpret_cast<const void *>(env.module_base+0x3AAB100),actual_find.data(),actual_find.size())&&actual_find==find&&
      Bytes(reinterpret_cast<const void *>(env.module_base+0x14560B0),actual_groups.data(),actual_groups.size())&&actual_groups==groups&&
      Bytes(reinterpret_cast<const void *>(env.module_base+0xA935B0),actual_decision.data(),actual_decision.size())&&actual_decision==decision;
}
bool KeySyntax(std::string_view key) noexcept {
  if(key.empty()||key.size()>kMaximumKey)return false;
  for(char c:key)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'))return false;
  return true;
}
bool Typed(const void *object,std::uintptr_t base,std::uintptr_t vt,std::uint32_t td) noexcept {
  const void *vtable=nullptr,*locator=nullptr;std::array<std::uint32_t,6> col{};
  if(!Read(object,0,vtable)||reinterpret_cast<std::uintptr_t>(vtable)!=base+vt||
      !Bytes(reinterpret_cast<const void *>(base+vt-8),&locator,sizeof(locator)))return false;
  const auto address=reinterpret_cast<std::uintptr_t>(locator);
  return address>=base&&address-base<=kImageSize-sizeof(col)&&Bytes(locator,col.data(),sizeof(col))&&
      col[0]==1&&col[1]==0&&col[3]==td&&col[5]==address-base;
}
bool DefinitionKey(const void *definition,std::uintptr_t base,std::string &key) {
  // Actual installed .3 RTTI: CDecisionType TD5586B90/COL4F7D400/vtable48BD140.
  // The existing .3 mystical-communion provider reads the same native key at18.
  if(!Typed(definition,base,0x48BD140,0x5586B90))return false;
  const void *string=At(definition,0x18),*text=string;std::uint64_t size=0,capacity=0;
  if(!Read(string,0x10,size)||!Read(string,0x18,capacity)||!size||size>kMaximumKey||size>capacity||
     (capacity<16&&capacity!=15))return false;
  if(capacity>=16&&(!Read(string,0,text)||!text))return false;
  std::array<char,kMaximumKey+1> bytes{};
  if(!Bytes(text,bytes.data(),static_cast<std::size_t>(size)+1)||bytes[size]!=0)return false;
  key.assign(bytes.data(),static_cast<std::size_t>(size));return KeySyntax(key);
}
bool Root(const ZhongguoScoreboardNativeEnvironmentV1 &env,std::string_view name,
    void *&root,bool &visible,bool &complete) {
  ZhongguoScoreboardAccessV1 access{};void *widget=nullptr;NamedGuiTreeInspectionV1 tree{};
  root=nullptr;visible=false;complete=false;
  if(!ResolveNamedGuiWidgetV1(env,access,name,name,root,widget))return false;
  if(!root)return !widget;
  if(root!=widget||!InspectNamedGuiSubtreeV1(access,env.module_base,root,name,tree)||tree.truncated||
     tree.widget_count==0||tree.widget_count!=tree.widgets.size())return false;
  std::size_t matches=0;
  for(const auto &row:tree.widgets)if(row.child_path.empty()){
    if(row.runtime_name!=name)return false;visible=row.effective_visible;++matches;
  }
  complete=matches==1;return complete;
}
struct Vector {const void *data=nullptr;std::uint32_t capacity=0,count=0;const void *allocator=nullptr;bool operator==(const Vector &) const=default;};
bool VectorAt(const void *object,std::size_t offset,std::size_t bound,Vector &v) {
  const void *p=At(object,offset);
  return Read(p,0,v.data)&&Read(p,8,v.capacity)&&Read(p,12,v.count)&&Read(p,16,v.allocator)&&
      v.count<=bound&&v.count<=v.capacity&&(v.count==0||v.data);
}
struct Item {const void *address=nullptr,*definition=nullptr,*scope_reference=nullptr,*owner=nullptr;std::uint32_t context_reference_key=0;std::string key;bool operator==(const Item &) const=default;};
struct Pass {
  const void *application=nullptr,*logical=nullptr,*gfx=nullptr,*handler=nullptr,*list=nullptr,*detail=nullptr;
  const void *list_root=nullptr,*detail_root=nullptr,*selected_definition=nullptr;
  Vector groups{};std::vector<Vector> row_vectors;std::vector<const void *> group_definitions;std::vector<Item> rows;
  std::string selected_key;
  std::int32_t detail_actor_reference_key=-1;
  bool operator==(const Pass &) const=default;
};
bool ModelPass(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *list_root,Pass &p) {
  const auto base=env.module_base;const void *back=nullptr;
  if(!Read(env.gui_global_slot,0,p.application)||!Typed(p.application,base,0x449BDA8,0x5667F88)||
     !Read(p.application,0x78,p.logical)||!Typed(p.logical,base,0x44D6048,0x55072C0)||
     !Read(p.logical,0x18,back)||back!=p.application||!Read(p.logical,0x10,p.gfx)||
     !Typed(p.gfx,base,0x44BC408,0x5514460)||!Read(p.gfx,0x90,back)||back!=p.application||
     !Read(p.gfx,0x20,back)||back!=p.logical||!Read(p.gfx,0x88,p.handler)||
     !Typed(p.handler,base,0x44BA890,0x5694B50)||!Read(p.handler,0x1B0,p.list)||
     !Typed(p.list,base,0x455CC80,0x5794DB0)||!Read(p.list,0x98,back)||back!=p.logical||
     !Read(p.list,0xA0,back)||back!=p.handler||!Read(p.list,0x60,p.list_root)||p.list_root!=list_root||
     !Read(p.handler,0x1B8,p.detail)||!Typed(p.detail,base,0x455D4E8,0x5795080)||
     !Read(p.detail,0xA0,back)||back!=p.handler||!Read(p.detail,0x60,p.detail_root)||
      !Read(p.detail,0xD0,p.selected_definition)||!Read(p.detail,0xD8,p.detail_actor_reference_key)||
      !VectorAt(p.list,0x258,kMaximumGroups,p.groups))return false;
  if(p.selected_definition&&!DefinitionKey(p.selected_definition,base,p.selected_key))return false;
  for(std::size_t n=0;n<p.groups.count;++n){
    const void *group=At(p.groups.data,n*0x20),*definition=nullptr;Vector rows{};
    if(!Read(group,0,definition)||!definition||!VectorAt(group,8,kMaximumRows,rows)||
       p.rows.size()+rows.count>kMaximumRows)return false;
    p.group_definitions.push_back(definition);p.row_vectors.push_back(rows);
    for(std::size_t i=0;i<rows.count;++i){
      const void *row=At(rows.data,i*0x20);Item item{};item.address=row;
      if(!Read(row,0,item.definition)||!Read(row,8,item.scope_reference)||
         !Read(row,0x10,item.context_reference_key)||!Read(row,0x18,item.owner)||item.owner!=p.list||
         !DefinitionKey(item.definition,base,item.key))return false;
      p.rows.push_back(std::move(item));
    }
  }
  return true;
}
bool ActionPins(const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  constexpr std::array<unsigned char,189> expected0{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x30,0x48,0x8b,0x41,0x18,0x48,0x8b,0xf9,0x48,0x8b,0x31,0x48,0x8b,0x90,0xa0,0x00,0x00,0x00,0x48,0x8b,0x9a,0xb8,0x01,0x00,0x00,0x48,0x85,0xdb,0x75,0x39,0xb9,0x6d,0x2e,0x00,0x00,0xe8,0xfa,0x75,0xaf,0x02,0x48,0x83,0x78,0x18,0x10,0x72,0x03,0x48,0x8b,0x00,0x48,0x89,0x44,0x24,0x28,0x4c,0x8d,0x0d,0xe8,0x59,0x8c,0x04,0x33,0xd2,0x48,0x8d,0x05,0x63,0x90,0x04,0x03,0x33,0xc9,0x48,0x89,0x44,0x24,0x20,0x44,0x8d,0x42,0x01,0xe8,0x5b,0x28,0xb2,0x02,0x48,0x8b,0xcb,0xe8,0x63,0x80,0xd0,0x00,0x84,0xc0,0x74,0x14,0x48,0x39,0xb3,0xd0,0x00,0x00,0x00,0x75,0x0b,0x48,0x8b,0x03,0x48,0x8b,0xcb,0xff,0x50,0x20,0xeb,0x13,0x48,0x8b,0xd6,0x48,0x8b,0xcb,0xe8,0xf0,0x92,0x01,0x00,0x48,0x8b,0xcb,0xe8,0x78,0x85,0x01,0x00,0x48,0x8b,0x47,0x18,0x48,0x8b,0x5c,0x24,0x40,0x48,0x8b,0x74,0x24,0x48,0xc7,0x80,0xd4,0x02,0x00,0x00,0x00,0x00,0x00,0x00,0xc6,0x80,0xd0,0x02,0x00,0x00,0x01,0x48,0x83,0xc4,0x30,0x5f,0xc3};
  std::array<unsigned char,189> actual0{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x14582D0),actual0.data(),actual0.size())||actual0!=expected0)return false;
  constexpr std::array<unsigned char,28> expected1{0x48,0x83,0xec,0x28,0x48,0x85,0xc9,0x74,0x0c,0xe8,0x92,0xed,0xff,0xff,0xb0,0x01,0x48,0x83,0xc4,0x28,0xc3,0x32,0xc0,0x48,0x83,0xc4,0x28,0xc3};
  std::array<unsigned char,28> actual1{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x1459530),actual1.data(),actual1.size())||actual1!=expected1)return false;
  constexpr std::array<unsigned char,205> expected2{0x48,0x89,0x5c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x30,0x4c,0x8b,0x05,0x02,0x5f,0x7f,0x04,0x48,0x8b,0xf2,0xc7,0x81,0xdc,0x00,0x00,0x00,0xff,0xff,0xff,0xff,0x48,0x8b,0xf9,0x4d,0x85,0xc0,0x74,0x2c,0x8b,0x05,0x7f,0xa5,0x06,0x04,0x8b,0xc8,0x81,0xe1,0xff,0xff,0xff,0x00,0x41,0x3b,0x48,0x2c,0x73,0x18,0x8b,0xd1,0x49,0x8b,0x48,0x20,0x48,0x03,0xd2,0x48,0x8b,0x5c,0xd1,0x08,0x48,0x85,0xdb,0x74,0x05,0x39,0x43,0x18,0x74,0x07,0x48,0x8b,0x1d,0xc2,0x5e,0x7f,0x04,0x48,0x8b,0xd3,0x48,0x8b,0xce,0xe8,0x47,0x1d,0xc9,0x01,0x84,0xc0,0x75,0x42,0xe8,0xfe,0xc0,0x67,0x01,0x48,0x8b,0xd6,0x48,0x8b,0xc8,0xe8,0x73,0xff,0xd9,0x01,0x4c,0x8b,0xc0,0x48,0xc7,0x44,0x24,0x20,0x00,0x00,0x00,0x00,0x41,0xb1,0x01,0x48,0x8d,0x4c,0x24,0x40,0x48,0x8b,0xd3,0xe8,0x37,0x14,0x7d,0x01,0x44,0x8b,0x44,0x24,0x40,0x41,0x83,0xf8,0xff,0x74,0x0b,0x8b,0x43,0x18,0x89,0x87,0xdc,0x00,0x00,0x00,0xeb,0x04,0x44,0x8b,0x43,0x18,0x48,0x8b,0xd6,0x48,0x8b,0xcf,0x48,0x8b,0x5c,0x24,0x48,0x48,0x8b,0x74,0x24,0x50,0x48,0x83,0xc4,0x30,0x5f,0xe9,0x13,0xfb,0xff,0xff};
  std::array<unsigned char,205> actual2{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x1471650),actual2.data(),actual2.size())||actual2!=expected2)return false;
  constexpr std::array<unsigned char,32> expected3{0x48,0x8b,0xc4,0x48,0x89,0x58,0x08,0x48,0x89,0x68,0x10,0x48,0x89,0x70,0x20,0x57,0x41,0x56,0x41,0x57,0x48,0x81,0xec,0x90,0x00,0x00,0x00,0x41,0x8b,0xd8,0x4c,0x8b};
  std::array<unsigned char,32> actual3{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x1471230),actual3.data(),actual3.size())||actual3!=expected3)return false;
  constexpr std::array<unsigned char,32> expected4{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x60,0x49,0x8b,0xf0,0x8b,0xea,0x48,0x8b,0xf9,0x49,0x8b,0x59,0x48};
  std::array<unsigned char,32> actual4{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x3ABC4D0),actual4.data(),actual4.size())||actual4!=expected4)return false;
  constexpr std::array<unsigned char,32> expected5{0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xf1,0x48,0x8b,0xea,0x48,0x8b,0x89,0xf0,0x00,0x00};
  std::array<unsigned char,32> actual5{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x3A78230),actual5.data(),actual5.size())||actual5!=expected5)return false;
  constexpr std::array<unsigned char,32> expected6{0x40,0x53,0x48,0x83,0xec,0x20,0x48,0x8b,0xd9,0x0f,0xb6,0x89,0xd0,0x00,0x00,0x00,0x80,0xe1,0x02,0x74,0x26,0x44,0x8b,0x42,0x10,0x41,0x83,0xe8,0x0d,0x74,0x0c,0x41};
  std::array<unsigned char,32> actual6{};
  if(!Bytes(reinterpret_cast<const void *>(env.module_base+0x3AA0D40),actual6.data(),actual6.size())||actual6!=expected6)return false;
  return true;
}

bool NoVisibleModals(void *context) noexcept {
  const void *data=nullptr;std::int32_t count=-1;
  if(!Read(context,kZhongguoGuiModalVectorOffset,data)||!Read(context,kZhongguoGuiModalCountOffset,count)||
      count<0||count>kZhongguoMaximumModalReceivers||(count&&!data))return false;
  for(std::int32_t n=0;n<count;++n){
    const void *receiver=nullptr;std::uint8_t flags=0;
    if(!Read(data,static_cast<std::size_t>(n)*sizeof(void *),receiver)||!receiver||
       !Read(receiver,kZhongguoWidgetHiddenFlagsOffset,flags)||(flags&kZhongguoWidgetEffectiveHiddenMask)==0)return false;
  }
  return true;
}
bool ActualActor(const ZhongguoScoreboardNativeEnvironmentV1 &env,std::int32_t id) noexcept {
  // SetDecision(1471650) uses this exact .3 current-player reference/storage chain.
  std::int32_t current=-1;const void *storage=nullptr,*data=nullptr,*actor=nullptr,*death=nullptr;std::uint32_t count=0;
  std::int32_t observed=-1;
  const auto base=env.module_base;
  return id>0&&Read(reinterpret_cast<const void *>(base+0x54DBC00),0,current)&&current==id&&
      Read(reinterpret_cast<const void *>(base+0x5C67568),0,storage)&&storage&&Read(storage,0x20,data)&&data&&
      Read(storage,0x2C,count)&&count>0&&count<=0x1000000&&
      (static_cast<std::uint32_t>(id)&0xFFFFFF)<count&&
      Read(data,(static_cast<std::uint32_t>(id)&0xFFFFFF)*0x10ULL+8,actor)&&actor&&
      Read(actor,0x18,observed)&&observed==id&&Read(actor,0x1D0,death)&&!death;
}
bool CallOnSelect(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *row) noexcept {
  // Wrapper1459530 forwards RCX unchanged. Handler14582D0 reads row[0]/row+18 directly.
  using OnSelect=void(__fastcall *)(void *);
#if defined(_MSC_VER)
  __try {reinterpret_cast<OnSelect>(env.module_base+0x14582D0)(row);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
#else
  reinterpret_cast<OnSelect>(env.module_base+0x14582D0)(row);return true;
#endif
}
const NamedGuiWidgetInspectionV1 *TreeRow(const NamedGuiTreeInspectionV1 &tree,std::string_view path) noexcept {
  const NamedGuiWidgetInspectionV1 *found=nullptr;
  for(const auto &row:tree.widgets)if(row.child_path==path){if(found)return nullptr;found=&row;}
  return found;
}
const NamedGuiWidgetInspectionV1 *NamedRow(const NamedGuiTreeInspectionV1 &tree,std::string_view name) noexcept {
  const NamedGuiWidgetInspectionV1 *found=nullptr;
  for(const auto &row:tree.widgets)if(row.runtime_name==name){if(found)return nullptr;found=&row;}
  return found;
}
bool Census(const ZhongguoScoreboardNativeEnvironmentV1 &env,std::string_view name,
    void *&root,NamedGuiTreeInspectionV1 &tree,bool &visible) {
  ZhongguoScoreboardAccessV1 access{};void *widget=nullptr;root=nullptr;tree={};visible=false;
  if(!ResolveNamedGuiWidgetV1(env,access,name,name,root,widget))return false;
  if(!root)return !widget;
  if(widget!=root||!InspectNamedGuiSubtreeV1(access,env.module_base,root,name,tree)||tree.truncated||
     tree.widget_count==0||tree.widget_count!=tree.widgets.size())return false;
  const auto *row=TreeRow(tree,"");if(!row||row->runtime_name!=name)return false;
  visible=row->effective_visible;return true;
}
bool ParseChildPath(std::string_view text,std::vector<std::uint32_t> &path) {
  path.clear();if(text.empty())return true;
  while(!text.empty()){
    if(path.size()>=64)return false;const auto sep=text.find('/');const auto token=text.substr(0,sep);std::uint32_t n=0;
    const auto r=std::from_chars(token.data(),token.data()+token.size(),n);
    if(token.empty()||r.ec!=std::errc{}||r.ptr!=token.data()+token.size()||n>=2048)return false;
    path.push_back(n);if(sep==std::string_view::npos)break;text.remove_prefix(sep+1);if(text.empty())return false;
  }return true;
}
bool QualifiedPath(const ZhongguoScoreboardNativeEnvironmentV1 &env,const NamedGuiTreeInspectionV1 &tree,
    std::string_view root_name,void *expected_root,void *context,std::string_view path,void *&target,void *&vtable) {
  target=nullptr;vtable=nullptr;std::vector<std::uint32_t> indices;if(!ParseChildPath(path,indices)||indices.empty())return false;
  ZhongguoScoreboardAccessV1 access{};void *previous=nullptr;std::string prefix;
  for(std::size_t length=0;length<=indices.size();++length){
    void *root=nullptr,*widget=nullptr,*actual_vtable=nullptr,*actual_context=nullptr;bool visible=false,enabled=false;std::string name;
    const auto *row=TreeRow(tree,prefix);
    if(!row||!row->effective_visible||!row->enabled||!row->vtable_rva||row->vtable_rva>=kImageSize||
        !ResolveFixedGuiChildPathV1(env,access,root_name,indices.data(),length,root,widget)||root!=expected_root||!widget||
        !ReadGuiWidgetRuntimeV1(access,widget,name,actual_vtable,visible,enabled)||!visible||!enabled||name!=row->runtime_name||
        reinterpret_cast<std::uintptr_t>(actual_vtable)!=env.module_base+row->vtable_rva||
        !Read(widget,kZhongguoWidgetGuiContextOffset,actual_context)||actual_context!=context)return false;
    if(previous){const void *parent=nullptr;if(!Read(widget,kZhongguoWidgetParentOffset,parent)||parent!=previous)return false;}
    previous=widget;if(length==indices.size()){target=widget;vtable=actual_vtable;break;}
    if(!prefix.empty())prefix+='/';prefix+=std::to_string(indices[length]);
  }return target!=nullptr;
}
bool ParentPath(std::string_view path,std::string &parent,std::uint32_t &index) {
  std::vector<std::uint32_t> values;if(!ParseChildPath(path,values)||values.empty())return false;
  index=values.back();const auto slash=path.rfind('/');parent=slash==std::string_view::npos?"":std::string(path.substr(0,slash));return true;
}
bool ConfirmReceiver(const ZhongguoScoreboardNativeEnvironmentV1 &env,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch,const Pass &model,void *context,
    void *&target,void *&vtable,std::string &target_path) {
  void *root=nullptr;NamedGuiTreeInspectionV1 tree{};bool visible=false;
  if(!Census(env,"decisiondetail_view",root,tree,visible)||!root||!visible||root!=model.detail_root)return false;
  const auto *cost=NamedRow(tree,"cost"),*back=NamedRow(tree,"back"),*highlight=NamedRow(tree,"cram_study_start_tutorial_highlight");
  if(!cost||!back||!highlight)return false;
  std::string footer,regular_branch,custom_branch;std::uint32_t cost_index=0,back_index=0,highlight_index=0;
  if(!ParentPath(cost->child_path,footer,cost_index)||cost_index!=0||
     !ParentPath(back->child_path,custom_branch,back_index)||back_index!=0||
     !ParentPath(highlight->child_path,regular_branch,highlight_index)||highlight_index!=2)return false;
  const auto *footer_row=TreeRow(tree,footer),*regular=TreeRow(tree,regular_branch),*custom=TreeRow(tree,custom_branch);
  if(!footer_row||footer_row->child_count!=6||!regular||regular->child_count!=3||!custom||custom->child_count!=2)return false;
  std::string parent;std::uint32_t index=0;
  if(!ParentPath(regular_branch,parent,index)||parent!=footer||index!=2||
     !ParentPath(custom_branch,parent,index)||parent!=footer||index!=3)return false;
  // Stock .3 source has exactly these two confirm instances. Their anonymous child indices
  // are derived from named sibling anchors and the complete actual parent layout, not a list row guess.
  target=nullptr;vtable=nullptr;std::size_t matches=0;
  for(const auto &branch:{regular_branch,custom_branch}){
    const auto path=branch+"/1";const auto *button=TreeRow(tree,path);
    if(!button||!button->runtime_name.empty())return false;
    if(!button->effective_visible||!button->enabled)continue;
    void *candidate=nullptr,*candidate_vtable=nullptr;
    if(!QualifiedPath(env,tree,"decisiondetail_view",root,context,path,candidate,candidate_vtable)||
       !InspectFixedGuiWidgetDispatchAdmissionV1(dispatch,candidate,candidate_vtable))return false;
    ++matches;target=candidate;vtable=candidate_vtable;target_path=path;
  }return matches==1;
}
bool InnerPanel(const ZhongguoScoreboardNativeEnvironmentV1 &env,void *context,std::string_view kind,
    bool &visible,bool &complete) {
  visible=false;complete=false;if(kind!="vivhite_courtier")return false;
  constexpr std::string_view root_name="ervc_courtier_creator_window",modal_name="ervc_courtier_creator_modal";
  void *root=nullptr;NamedGuiTreeInspectionV1 tree{};bool root_visible=false;
  if(!Census(env,root_name,root,tree,root_visible)||!root||!root_visible)return false;
  const auto *outer=TreeRow(tree,""),*modal=NamedRow(tree,modal_name);
  if(!outer||outer->child_count!=1||!modal||modal->child_path!="0")return false;
  ZhongguoScoreboardAccessV1 access{};void *actual_root=nullptr,*widget=nullptr;const std::uint32_t path[]{0};
  std::string name;void *vtable=nullptr,*actual_context=nullptr;const void *parent=nullptr;bool actual_visible=false,enabled=false;
  if(!ResolveFixedGuiChildPathV1(env,access,root_name,path,1,actual_root,widget)||actual_root!=root||!widget||
     !ReadGuiWidgetRuntimeV1(access,widget,name,vtable,actual_visible,enabled)||name!=modal_name||
     reinterpret_cast<std::uintptr_t>(vtable)!=env.module_base+modal->vtable_rva||
     !Read(widget,kZhongguoWidgetParentOffset,parent)||parent!=root||
     !Read(widget,kZhongguoWidgetGuiContextOffset,actual_context)||actual_context!=context||actual_visible!=modal->effective_visible)return false;
  visible=actual_visible;complete=true;return true;
}
} // namespace

bool ExecuteIngameDecisionItemQueryV1(IngameDecisionItemContextV1 &query,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env) noexcept {
  auto &out=query.result;out={};out.native_revision=query.native_revision;out.connection_generation=query.connection_generation;out.game_pid=GetCurrentProcessId();
  try {
    const auto reject=[&](const char *reason){out.available=false;out.unavailable_reason=reason;return true;};
    if(!query.game||query.game->descriptor().game_version!="1.20.0.3"||
       query.game->descriptor().executable_sha256!="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"||
       !query.native_revision||!query.connection_generation||!KeySyntax(query.requested_key)||
       !env.exact_build_admitted||env.offline_fixture_function_overrides||env.gui_abi_revision!=GuiAbiRevisionV1::crozier12003)
      return reject("exact_12003_keyed_query_unavailable");
    if(!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId()))return reject("paused_application_owner_unverified");
    out.owner_thread_verified=true;game::Snapshot before{};
    if(!game::ReadSnapshot(*query.game,before)||before!=query.expected_snapshot||!before.paused||!before.map_ready||
       !before.has_played_character||!before.played_character_alive||before.played_character_id<=0||before.date_raw!=stamp.date_raw)
      return reject("fresh_alive_paused_frame_unverified");
    out.played_character_id=before.played_character_id;out.date_raw=before.date_raw;
    // Check the loaded exact .3 root resolver and two actual leaf property entrypoints before traversing.
    if(!CodePins(env))return reject("loaded_12003_keyed_reader_pins_changed");
    out.source_abi_pins_verified=true;
    ZhongguoScoreboardAccessV1 access{};void *context=nullptr,*owner=nullptr;
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner))return reject("gui_owner_unavailable");
    void *root=nullptr;
    if(!Root(env,"decisions_view",root,out.decisions_root_visible,out.decisions_tree_complete)||!root||!out.decisions_root_visible)
      return reject("actual_decisions_root_hidden_or_census_incomplete");
    Pass first{},second{};
    if(!ModelPass(env,root,first)||!ModelPass(env,root,second)||first!=second)
      return reject("actual_keyed_decision_model_or_owner_unstable");
    out.group_count=first.groups.count;out.row_count=first.rows.size();out.row_owner_verified=true;
    for(const auto &row:first.rows)if(row.key==query.requested_key){
      ++out.matching_row_count;out.decision_key=row.key;
      out.row_context_reference_key=row.context_reference_key;out.row_scope_reference_available=row.scope_reference!=nullptr;
      out.detail_definition_matches_target=first.selected_definition==row.definition;
    }
    if(out.matching_row_count!=1)return reject(out.matching_row_count?"requested_decision_key_ambiguous":"requested_decision_key_not_in_actual_rows");
    out.detail_definition_available=first.selected_definition!=nullptr;out.detail_decision_key=first.selected_key;
    out.detail_actor_reference_key=first.detail_actor_reference_key;
    out.detail_actor_binding_verified=first.selected_definition&&first.detail_actor_reference_key==before.played_character_id;
    void *detail_root=nullptr;
    if(!Root(env,"decisiondetail_view",detail_root,out.detail_root_visible,out.detail_tree_complete)||
       (detail_root&&detail_root!=first.detail_root))return reject("actual_detail_root_or_census_unverified");
    void *last_context=nullptr,*last_owner=nullptr;game::Snapshot after{};Pass last{};
    out.gui_owner_binding_verified=ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,last_context,last_owner)&&last_context==context&&last_owner==owner;
    out.frame_verified=game::ReadSnapshot(*query.game,after)&&after==before;
    if(!out.gui_owner_binding_verified||!out.frame_verified||!ModelPass(env,root,last)||last!=first)
      return reject("keyed_query_completion_binding_changed");
    out.available=true;return true;
  }catch(...){out.available=false;out.unavailable_reason="native_keyed_reader_exception";return true;}
}

std::string SerializeIngameDecisionItemV1(const IngameDecisionItemResultV1 &v) {
  std::string s="{\"schema\":\"ck3-ingame-decision-item-v1\",\"step\":\"query-ingame-decision-item-v1\",\"read_only\":true,\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\"";
  const auto number=[&](const char *key,auto n){s+=",\"";s+=key;s+="\":";s+=std::to_string(n);};
  const auto boolean=[&](const char *key,bool b){s+=",\"";s+=key;s+="\":";s+=b?"true":"false";};
  const auto text=[&](const char *key,const std::string &value){s+=",\"";s+=key;s+="\":\"";s+=value;s+='"';};
  number("native_revision",v.native_revision);number("connection_generation",v.connection_generation);number("game_pid",v.game_pid);
  number("played_character_id",v.played_character_id);number("date_raw",v.date_raw);number("group_count",v.group_count);
  number("row_count",v.row_count);number("matching_row_count",v.matching_row_count);number("row_context_reference_key",v.row_context_reference_key);
  number("detail_actor_reference_key",v.detail_actor_reference_key);
  boolean("available",v.available);boolean("owner_thread_verified",v.owner_thread_verified);boolean("frame_verified",v.frame_verified);
  boolean("source_abi_pins_verified",v.source_abi_pins_verified);boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);
  boolean("decisions_tree_complete",v.decisions_tree_complete);boolean("decisions_root_visible",v.decisions_root_visible);
  boolean("row_owner_verified",v.row_owner_verified);boolean("row_scope_reference_available",v.row_scope_reference_available);
  boolean("detail_tree_complete",v.detail_tree_complete);boolean("detail_root_visible",v.detail_root_visible);
  boolean("detail_definition_available",v.detail_definition_available);boolean("detail_definition_matches_target",v.detail_definition_matches_target);
  boolean("detail_actor_binding_verified",v.detail_actor_binding_verified);
  // Scope/context scalar is observed but deliberately not cast to player identity or action qualification.
  boolean("row_widget_datacontext_verified",false);boolean("action_qualified",false);
  text("decision_key",v.decision_key);text("detail_decision_key",v.detail_decision_key);text("unavailable_reason",v.unavailable_reason);return s+'}';
}
bool ExecuteIngameDecisionItemActionV1(IngameDecisionItemActionContextV1 &query,
    MainThreadQueryMailboxV1 &mailbox,const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &env,ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch) noexcept {
  auto &out=query.result;out={};out.action=query.action;
  try {
    const auto reject=[&](const char *why){out.unavailable_reason=why;return true;};
    if(!ExecuteIngameDecisionItemQueryV1(query.observation,mailbox,stamp,env))return reject("keyed_before_execution_unavailable");
    out.before=query.observation.result;
    if(!out.before.available)return reject("actual_keyed_before_unavailable");
    if(!ActionPins(env)||dispatch.gui_abi_revision!=GuiAbiRevisionV1::crozier12003||
        dispatch.offline_fixture_function_overrides||!dispatch.exact_build_admitted)return reject("loaded_12003_decision_action_pins_changed");
    out.action_abi_pins_verified=true;
    if(!ActualActor(env,out.before.played_character_id))return reject("source_current_player_reference_not_bound_to_snapshot");
    ZhongguoScoreboardAccessV1 access{};void *context=nullptr,*owner=nullptr,*list_root=nullptr;bool visible=false,complete=false;
    if(!ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,context,owner)||
       !Root(env,"decisions_view",list_root,visible,complete)||!list_root||!visible||!complete)return reject("actual_action_root_owner_unavailable");
    Pass first{},second{};
    if(!ModelPass(env,list_root,first)||!ModelPass(env,list_root,second)||first!=second)return reject("actual_predispatch_model_changed");
    const Item *target_row=nullptr;
    for(const auto &row:first.rows)if(row.key==query.observation.requested_key){if(target_row)return reject("actual_action_key_ambiguous");target_row=&row;}
    if(!target_row||!target_row->address||target_row->owner!=first.list)return reject("actual_action_row_owner_unqualified");
    void *target=nullptr,*vtable=nullptr;
    if(query.action==IngameDecisionItemActionKindV1::select){
      // A source OnSelect on an already-selected visible definition toggles Hide.
      // Preserve that source behavior by doing no action for any same-definition state;
      // only subsequent independent actual visible detail proof can count as success.
      out.before_already_selected=first.selected_definition==target_row->definition;
      if(!NoVisibleModals(context))return reject("source_select_blocked_by_visible_modal");
      out.no_blocking_modal_verified=true;out.receiver_qualified=true;
    }else{
      if(query.expected_window_kind!="vivhite_courtier")return reject("fixed_expected_modal_scope_unavailable");
      if(first.selected_definition!=target_row->definition||!out.before.detail_root_visible||
          !out.before.detail_tree_complete||first.detail_actor_reference_key!=out.before.played_character_id)
        return reject("actual_selected_detail_definition_actor_or_visibility_unqualified");
      out.detail_actor_binding_verified=true;
      bool modal_before=false,modal_complete=false;
      if(!InnerPanel(env,context,query.expected_window_kind,modal_before,modal_complete)||!modal_complete||modal_before)
        return reject("actual_expected_inner_modal_before_not_closed_or_incomplete");
      if(!ConfirmReceiver(env,dispatch,first,context,target,vtable,out.target_child_path))return reject("fixed_visible_confirm_receiver_unqualified");
      out.receiver_qualified=true;
    }
    game::Snapshot predispatch{};void *last_context=nullptr,*last_owner=nullptr;Pass pre_model{};
    if(!query.observation.game||!game::ReadSnapshot(*query.observation.game,predispatch)||predispatch!=query.observation.expected_snapshot||
       !ActualActor(env,out.before.played_character_id)||!IsIngameUiPausedOwnerStampV1(mailbox,stamp,GetCurrentThreadId())||
       !ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,last_context,last_owner)||last_context!=context||last_owner!=owner||
       !ModelPass(env,list_root,pre_model)||pre_model!=first)return reject("actual_decision_predispatch_frame_or_owner_changed");
    if(query.action==IngameDecisionItemActionKindV1::select){
      if(!NoVisibleModals(context))return reject("source_select_predispatch_modal_changed");
      if(!out.before_already_selected){
        out.dispatch_invoked=true; // Attempt is consumed even if the native handler faults.
        out.native_call_completed=CallOnSelect(env,const_cast<void *>(target_row->address));
        if(!out.native_call_completed)return reject("source_onselect_fault_result_unknown_no_retry");
      }
      IngameDecisionItemContextV1 after=query.observation;after.result={};
      out.native_after_read=ExecuteIngameDecisionItemQueryV1(after,mailbox,stamp,env);out.after=std::move(after.result);
      out.selected_after_verified=out.native_after_read&&out.after.available&&out.after.detail_tree_complete&&
          out.after.detail_root_visible&&out.after.detail_definition_matches_target&&out.after.detail_actor_binding_verified;
    }else{
      // Resolve and qualify the source receiver again immediately before its one dispatcher invocation.
      void *last_target=nullptr,*last_vtable=nullptr;std::string last_path;
      if(!ConfirmReceiver(env,dispatch,pre_model,context,last_target,last_vtable,last_path)||last_target!=target||
         last_vtable!=vtable||last_path!=out.target_child_path)return reject("fixed_confirm_predispatch_receiver_changed");
      out.dispatch_invoked=DispatchFixedGuiWidgetNativeV1(&dispatch,game::ZhongguoScoreboardActionV1::open,target,vtable,out.native_handled);
      if(!out.dispatch_invoked)return reject("native_confirm_dispatch_failed_no_retry");
      // Take first sets open_pending. Only the production GUI bridge can open the actual inner modal.
      out.native_after_read=InnerPanel(env,context,query.expected_window_kind,out.inner_modal_visible,out.inner_modal_tree_complete);
    }
    game::Snapshot after{};void *after_context=nullptr,*after_owner=nullptr;
    out.gui_owner_binding_verified=ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1(env,access,after_context,after_owner)&&
        after_context==context&&after_owner==owner;
    out.frame_verified=game::ReadSnapshot(*query.observation.game,after)&&after==query.observation.expected_snapshot&&ActualActor(env,out.before.played_character_id);
    out.postcondition_verified=out.gui_owner_binding_verified&&out.frame_verified&&
        (query.action==IngameDecisionItemActionKindV1::select?out.selected_after_verified:
            out.native_after_read&&out.inner_modal_tree_complete&&out.inner_modal_visible);
    out.status=out.postcondition_verified?"observed_postcondition":
        (out.dispatch_invoked||out.before_already_selected)?"acknowledged_verification_pending":"unavailable";
    if(!out.gui_owner_binding_verified||!out.frame_verified)out.unavailable_reason="decision_action_completion_binding_changed";
    return true;
  }catch(...){out.postcondition_verified=false;out.unavailable_reason="native_decision_action_exception_no_retry";return true;}
}

std::string SerializeIngameDecisionItemActionV1(const IngameDecisionItemActionResultV1 &v){
  const bool select=v.action==IngameDecisionItemActionKindV1::select;
  std::string s="{\"schema\":\"ck3-ingame-decision-item-action-v1\",\"step\":\"";
  s+=select?kIngameDecisionItemSelectV1Step:kIngameDecisionItemConfirmV1Step;
  s+="\",\"action\":\"";s+=select?"select":"confirm";
  s+="\",\"game_version\":\"1.20.0.3\",\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\"";
  const auto number=[&](const char *key,auto n){s+=",\"";s+=key;s+="\":";s+=std::to_string(n);};
  const auto boolean=[&](const char *key,bool b){s+=",\"";s+=key;s+="\":";s+=b?"true":"false";};
  const auto text=[&](const char *key,const std::string &value){s+=",\"";s+=key;s+="\":\"";s+=value;s+='"';};
  number("native_revision",v.before.native_revision);number("connection_generation",v.before.connection_generation);
  number("game_pid",v.before.game_pid);number("played_character_id",v.before.played_character_id);number("date_raw",v.before.date_raw);
  boolean("owner_thread_verified",v.before.owner_thread_verified);boolean("source_abi_pins_verified",v.before.source_abi_pins_verified);
  boolean("action_abi_pins_verified",v.action_abi_pins_verified);boolean("receiver_qualified",v.receiver_qualified);
  boolean("detail_actor_binding_verified",v.detail_actor_binding_verified);boolean("no_blocking_modal_verified",v.no_blocking_modal_verified);
  boolean("before_already_selected",v.before_already_selected);boolean("dispatch_invoked",v.dispatch_invoked);
  boolean("native_call_completed",v.native_call_completed);boolean("native_handled",v.native_handled);
  boolean("gui_owner_binding_verified",v.gui_owner_binding_verified);boolean("frame_verified",v.frame_verified);
  boolean("native_after_read",v.native_after_read);boolean("selected_after_verified",v.selected_after_verified);
  boolean("inner_modal_visible",v.inner_modal_visible);boolean("inner_modal_tree_complete",v.inner_modal_tree_complete);
  boolean("postcondition_verified",v.postcondition_verified);boolean("verification_pending",!v.postcondition_verified&&(v.dispatch_invoked||v.before_already_selected));
  text("decision_key",v.before.decision_key);text("target_child_path",v.target_child_path);text("status",v.status);text("unavailable_reason",v.unavailable_reason);
  s+=",\"before_actual_model\":";s+=SerializeIngameDecisionItemV1(v.before);
  s+=",\"after_actual_model\":";s+=SerializeIngameDecisionItemV1(v.after);return s+'}';
}
} // namespace xar::ck3_11906
