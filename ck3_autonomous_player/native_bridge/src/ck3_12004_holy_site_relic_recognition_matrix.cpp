#include "xar_bridge/ck3_12004_holy_site_relic_recognition_matrix.hpp"
#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"
#include <algorithm>
#include <iterator>
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion::holy_site_relic {
namespace {
constexpr std::uint32_t absent = 0xFFFFFFFFU;
constexpr std::uint32_t max_source_rows = 4096;
const void *At(const void *p, std::size_t offset) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(p);
  return address && offset <= std::numeric_limits<std::uintptr_t>::max() - address
      ? reinterpret_cast<const void *>(address + offset) : nullptr;
}
template<class T> bool Read(const Bindings &b,const void *p,std::size_t offset,T &value) noexcept {
  const auto *address = At(p,offset);
  return address && b.read_memory && b.read_memory(b.read_context,address,&value,sizeof(value));
}
struct Header {
  const void *data = nullptr;
  std::uint32_t capacity = 0, count = 0;
  std::uintptr_t allocator = 0;
  bool operator==(const Header &) const = default;
};
static_assert(sizeof(Header) == 24);
bool Array(const Bindings &b,const void *p,std::size_t offset,Header &header) noexcept {
  return Read(b,p,offset,header) && header.count <= header.capacity &&
      header.count <= max_source_rows && header.capacity <= max_source_rows*2 &&
      (header.count == 0 || header.data);
}
template<class T> bool Rows(const Bindings &b,const Header &header,std::vector<T> &out) {
  out.resize(header.count);
  return out.empty() || b.read_memory(b.read_context,header.data,out.data(),out.size()*sizeof(T));
}
bool Ids(const Bindings &b,const void *p,std::size_t offset,Header &header,std::vector<std::uint32_t> &out) {
  Header after{};
  return Array(b,p,offset,header) && Rows(b,header,out) &&
      std::none_of(out.begin(),out.end(),[](auto id){return id==absent;}) &&
      Array(b,p,offset,after) && after==header;
}
const void *Resolve(const Bindings &b,void **global,std::uint32_t id,std::size_t identity_offset,
    std::size_t magic_offset=0,std::uint32_t expected_magic=0) noexcept {
  const void *storage=nullptr,*rows=nullptr,*object=nullptr;
  std::uint32_t capacity=0,identity=absent,magic=0;
  if(id==absent || !Read(b,global,0,storage) || !storage || !Read(b,storage,0x20,rows) || !rows ||
      !Read(b,storage,0x2C,capacity) || (id&0xFFFFFFU)>=capacity ||
      !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object) || !object ||
      !Read(b,object,identity_offset,identity) || identity!=id ||
      (expected_magic && (!Read(b,object,magic_offset,magic) || magic!=expected_magic))) return nullptr;
  return object;
}
struct SlotRow {
  std::uintptr_t vtable=0,type=0;
  std::uint32_t artifact=absent,magic=0;
  bool operator==(const SlotRow &)const=default;
};
static_assert(sizeof(SlotRow)==24);
struct Window {
  const void *gfx=nullptr,*handler=nullptr,*window=nullptr,*root=nullptr;
  std::uint32_t selected_site=absent;
  Header candidates{};
  std::vector<std::uint32_t> ids;
  bool operator==(const Window &)const=default;
};
bool ReadWindow(const Bindings &b,const void *owner,std::uint32_t site,Window &w) {
  const void *back=nullptr,*bound_owner=nullptr;
  std::uintptr_t primary=0,secondary=0;
  return owner && Read(b,owner,0x10,w.gfx) && w.gfx && Read(b,w.gfx,0x88,w.handler) && w.handler &&
      Read(b,w.handler,0x5D8,w.window) && w.window &&
      Read(b,w.window,0,primary) && primary==b.image_base+0x4592338 &&
      Read(b,w.window,0x10,secondary) && secondary==b.image_base+0x4592310 &&
      Read(b,w.window,0xA0,back) && back==w.handler &&
      Read(b,w.window,0x98,bound_owner) && bound_owner==owner &&
      Read(b,w.window,0x60,w.root) && w.root &&
      Read(b,w.window,0xC8,w.selected_site) && w.selected_site==site &&
      Ids(b,w.window,0x130,w.candidates,w.ids);
}
struct County {
  const void *barony=nullptr,*county=nullptr,*holder=nullptr,*rite=nullptr,*faith=nullptr;
  std::uint32_t barony_id=absent,county_id=absent,holder_id=absent,rite_id=absent,faith_id=absent;
  bool operator==(const County &)const=default;
};
bool ReadCounty(const Bindings &b,const void *site,County &out) noexcept {
  return Read(b,site,0xB0,out.barony_id) &&
      (out.barony=Resolve(b,b.title_storage,out.barony_id,0x10)) &&
      Read(b,out.barony,0x108,out.county_id) &&
      (out.county=Resolve(b,b.title_storage,out.county_id,0x10)) &&
      Read(b,out.county,0x128,out.holder_id) &&
      (out.holder=Resolve(b,b.character_storage,out.holder_id,0x18)) &&
      Read(b,out.holder,0xB4,out.rite_id) &&
      (out.rite=Resolve(b,b.rite_storage,out.rite_id,8)) &&
      Read(b,out.rite,0x4B8,out.faith_id) && (out.faith=Resolve(b,b.faith_storage,out.faith_id,8));
}
struct ArtifactState {
  const void *object=nullptr,*definition=nullptr;
  std::uint32_t id=absent,character_owner=absent,site_owner=absent;
  std::int32_t rarity=0;
  Header sanctified{};
  std::vector<std::uint32_t> sanctified_ids;
  bool operator==(const ArtifactState &)const=default;
};
struct PlayerState {
  const void *actor=nullptr,*rite=nullptr,*faith=nullptr;
  std::uint32_t rite_id=absent,faith_id=absent;
  bool operator==(const PlayerState &)const=default;
};
bool ReadPlayer(const Bindings &b,const ck3_12002::religion::Context &c,PlayerState &p) noexcept {
  return c.played_character_id>0 && c.rite_id && c.faith_id &&
      (p.actor=Resolve(b,b.character_storage,static_cast<std::uint32_t>(c.played_character_id),0x18,0x1C,0x43686172U)) &&
      Read(b,p.actor,0xB4,p.rite_id) && p.rite_id==*c.rite_id &&
      (p.rite=Resolve(b,b.rite_storage,p.rite_id,8)) && Read(b,p.rite,0x4B8,p.faith_id) && p.faith_id==*c.faith_id &&
      (p.faith=Resolve(b,b.faith_storage,p.faith_id,8));
}
bool ReadArtifact(const Bindings &b,std::uint32_t id,ArtifactState &a) {
  a.id=id;
  a.object=Resolve(b,b.artifact_storage,id,0x10,0x14,0x41727469U);
  return a.object && Read(b,a.object,0x78,a.character_owner) && Read(b,a.object,0x7C,a.site_owner) &&
      Read(b,a.object,0xB0,a.rarity) && Read(b,a.object,0x490,a.definition) &&
      Ids(b,a.object,0x498,a.sanctified,a.sanctified_ids);
}
void Invalidate(RecognitionMatrix &out,const char *reason) {
  out.available=false;out.complete=false;out.source_arrays_stable=false;out.unavailable_reason=reason;
  for(auto &cell:out.cells){cell.available=false;cell.value.reset();cell.unavailable_reason=reason;}
}
}

bool ReadHolySiteRelicRecognitionMatrix12004(const Bindings &b,const void *owner,
    const ck3_12002::religion::Context &context,std::uint32_t site_id,
    std::optional<std::uint32_t> requested,const Snapshot *expected,RecognitionMatrix &out) noexcept {
  out={};out.holy_site_id=site_id;out.capture_epoch=context.capture_epoch;
  out.date_raw=context.date_raw;out.played_character_id=context.played_character_id;
  out.player_faith_id=context.faith_id;out.requested_action_artifact_id=requested;
  try {
    if(!b.enabled || !b.image_base || !b.read_memory || !context.available || !context.faith_id ||
        site_id==absent || (requested && *requested==absent)) {
      Invalidate(out,"recognition_matrix_context_unavailable");return false;
    }
    const void *site=Resolve(b,b.holy_site_storage,site_id,0x10,0x14,0x486F5374U);
    if(!site){Invalidate(out,"recognition_matrix_site_full_reference_unavailable");return false;}
    PlayerState player{};
    if(!ReadPlayer(b,context,player)){Invalidate(out,"recognition_matrix_current_player_rite_faith_unavailable");return false;}
    Header faith_header{},slot_header{};
    std::vector<SlotRow> slots;
    out.associated_available=Ids(b,site,0x98,faith_header,out.associated_faith_ids);
    if(!out.associated_available)out.associated_faith_ids.clear();
    out.slots_available=Array(b,site,0x68,slot_header) && Rows(b,slot_header,slots) &&
        std::all_of(slots.begin(),slots.end(),[](const SlotRow &r){return r.magic==0x496E7653U;});
    if(out.slots_available)for(const auto &slot:slots)out.slot_artifact_ids.push_back(slot.artifact==absent?std::nullopt:std::optional<std::uint32_t>{slot.artifact});
    County county{};
    const bool county_available=ReadCounty(b,site,county);
    if(county_available)out.county_holder_faith_id=county.faith_id;
    Window window{};
    out.window_candidates_available=ReadWindow(b,owner,site_id,window);
    if(out.window_candidates_available)out.window_candidate_artifact_ids=window.ids;
    if(expected){
      bool same=expected->requested_holy_site_id==site_id && expected->capture_epoch==context.capture_epoch &&
          expected->date_raw==context.date_raw && expected->played_character_id==context.played_character_id &&
          expected->player_faith_id==out.player_faith_id;
      if(expected->associated_faith_ids_available)same=same && out.associated_available && expected->associated_faith_ids==out.associated_faith_ids;
      if(expected->county_context.available)same=same && county_available && expected->county_context.county_holder_faith_id==out.county_holder_faith_id;
      if(expected->inventory.available){
        same=same && out.slots_available && expected->inventory.slots.size()==out.slot_artifact_ids.size();
        if(same)for(std::size_t i=0;i<out.slot_artifact_ids.size();++i)same=same && expected->inventory.slots[i].artifact_id==out.slot_artifact_ids[i];
      }
      if(!same){Invalidate(out,"recognition_matrix_crossed_parent_sources");return false;}
    }
    if(out.slot_artifact_ids.size()>RecognitionMatrix::max_slots ||
        out.window_candidate_artifact_ids.size()>RecognitionMatrix::max_candidates){
      Invalidate(out,"recognition_matrix_source_shape_limit_exceeded");return false;
    }
    const auto faith=[&](std::uint32_t id,bool associated,bool player,bool holder){
      auto it=std::find_if(out.faiths.begin(),out.faiths.end(),[id](const auto &row){return row.faith_id==id;});
      if(it==out.faiths.end()){MatrixFaith row{};row.faith_id=id;out.faiths.push_back(std::move(row));it=std::prev(out.faiths.end());}
      it->source_associated=it->source_associated||associated;it->source_player=it->source_player||player;it->source_county_holder=it->source_county_holder||holder;
    };
    for(auto id:out.associated_faith_ids)faith(id,true,false,false);
    if(out.player_faith_id)faith(*out.player_faith_id,false,true,false);
    if(out.county_holder_faith_id)faith(*out.county_holder_faith_id,false,false,true);
    const auto artifact=[&](std::uint32_t id)->MatrixArtifact&{
      auto it=std::find_if(out.artifacts.begin(),out.artifacts.end(),[id](const auto &row){return row.artifact_id==id;});
      if(it==out.artifacts.end()){MatrixArtifact row{};row.artifact_id=id;out.artifacts.push_back(std::move(row));it=std::prev(out.artifacts.end());}
      return *it;
    };
    for(std::size_t i=0;i<out.slot_artifact_ids.size();++i)if(out.slot_artifact_ids[i])artifact(*out.slot_artifact_ids[i]).slot_indices.push_back(static_cast<std::uint32_t>(i));
    for(std::size_t i=0;i<out.window_candidate_artifact_ids.size();++i)artifact(out.window_candidate_artifact_ids[i]).candidate_indices.push_back(static_cast<std::uint32_t>(i));
    if(requested)artifact(*requested).source_action_request=true;
    if(out.faiths.size()>RecognitionMatrix::max_faiths || out.artifacts.size()>RecognitionMatrix::max_artifacts ||
        out.faiths.size()*out.artifacts.size()>RecognitionMatrix::max_native_getter_calls){
      out.faiths.clear();out.artifacts.clear();Invalidate(out,"recognition_matrix_native_call_or_shape_limit_exceeded");return false;
    }
    std::vector<const void*> faith_objects;
    for(auto &row:out.faiths){
      const void *object=Resolve(b,b.faith_storage,row.faith_id,8);faith_objects.push_back(object);
      row.object_resolved=object!=nullptr;if(!object)row.unavailable_reason="recognition_matrix_faith_full_reference_unavailable";
    }
    std::vector<ArtifactState> artifact_states(out.artifacts.size());
    for(std::size_t i=0;i<out.artifacts.size();++i){
      auto &row=out.artifacts[i];row.object_resolved=ReadArtifact(b,row.artifact_id,artifact_states[i]);
      if(!row.object_resolved)row.unavailable_reason="recognition_matrix_artifact_identity_or_fields_unavailable";
    }
    for(std::size_t i=0;i<out.artifacts.size();++i)for(std::size_t j=0;j<out.faiths.size();++j){
      MatrixCell cell{};cell.artifact_id=out.artifacts[i].artifact_id;cell.faith_id=out.faiths[j].faith_id;
      if(!out.artifacts[i].object_resolved)cell.unavailable_reason="recognition_matrix_artifact_unavailable";
      else if(!out.faiths[j].object_resolved)cell.unavailable_reason="recognition_matrix_faith_unavailable";
      else if(!b.recognition)cell.unavailable_reason="native_recognition_getter_unavailable";
      else {
        bool value=false;++out.native_getter_calls;
        if(b.recognition(b,artifact_states[i].object,cell.faith_id,value)){cell.available=true;cell.value=value;cell.unavailable_reason.clear();}
        else cell.unavailable_reason="native_recognition_getter_failed";
      }
      out.cells.push_back(std::move(cell));
    }
    Header after_faiths{},after_slots_header{};std::vector<std::uint32_t> after_faith_ids;std::vector<SlotRow> after_slots;
    County after_county{};Window after_window{};
    bool stable=Resolve(b,b.holy_site_storage,site_id,0x10,0x14,0x486F5374U)==site;
    PlayerState after_player{};
    stable=stable && ReadPlayer(b,context,after_player) && after_player==player;
    stable=stable && Ids(b,site,0x98,after_faiths,after_faith_ids)==out.associated_available;
    if(out.associated_available)stable=stable && after_faiths==faith_header && after_faith_ids==out.associated_faith_ids;
    const bool after_slots_available=Array(b,site,0x68,after_slots_header) && Rows(b,after_slots_header,after_slots) &&
        std::all_of(after_slots.begin(),after_slots.end(),[](const SlotRow &r){return r.magic==0x496E7653U;});
    stable=stable && after_slots_available==out.slots_available;
    if(out.slots_available)stable=stable && after_slots_header==slot_header && after_slots==slots;
    const bool after_county_available=ReadCounty(b,site,after_county);
    stable=stable && after_county_available==county_available && (!county_available || after_county==county);
    const bool after_window_available=ReadWindow(b,owner,site_id,after_window);
    stable=stable && after_window_available==out.window_candidates_available && (!out.window_candidates_available || after_window==window);
    for(std::size_t i=0;i<out.faiths.size();++i)stable=stable && Resolve(b,b.faith_storage,out.faiths[i].faith_id,8)==faith_objects[i];
    for(std::size_t i=0;i<out.artifacts.size();++i){
      ArtifactState after{};const bool resolved=ReadArtifact(b,out.artifacts[i].artifact_id,after);
      stable=stable && resolved==out.artifacts[i].object_resolved && (!resolved || after==artifact_states[i]);
    }
    if(!stable){Invalidate(out,"recognition_matrix_sources_changed_during_native_evaluation");return false;}
    out.source_arrays_stable=true;out.available=true;
    out.complete=out.associated_available && out.slots_available && out.window_candidates_available &&
        out.player_faith_id.has_value() && out.county_holder_faith_id.has_value() &&
        std::all_of(out.faiths.begin(),out.faiths.end(),[](const auto &row){return row.object_resolved;}) &&
        std::all_of(out.artifacts.begin(),out.artifacts.end(),[](const auto &row){return row.object_resolved;}) &&
        std::all_of(out.cells.begin(),out.cells.end(),[](const auto &cell){return cell.available;});
    if(out.complete)out.unavailable_reason.clear();else out.unavailable_reason="recognition_matrix_partial_sources_or_cells";
    return true;
  }catch(...){Invalidate(out,"recognition_matrix_copy_exception");return false;}
}
}
