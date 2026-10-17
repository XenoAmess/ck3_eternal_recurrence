#include "xar_bridge/ck3_12004_holy_site_relic_context.hpp"
#ifdef _WIN32
#include <windows.h>
#endif
#include <algorithm>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion::holy_site_relic {
namespace {
constexpr std::uint32_t absent = 0xFFFFFFFFU;
constexpr std::uint32_t maximum_rows = 8192;
const void *At(const void *p, std::size_t offset) noexcept {
  const auto v = reinterpret_cast<std::uintptr_t>(p);
  return v && offset <= std::numeric_limits<std::uintptr_t>::max() - v
      ? reinterpret_cast<const void *>(v + offset) : nullptr;
}
template<class T> bool Read(const Bindings &b, const void *p, std::size_t offset, T &out) noexcept {
  const auto *address = At(p, offset);
  return b.read_memory && address && b.read_memory(b.read_context,address,&out,sizeof(out));
}
bool ProcessRead(void *, const void *p, void *out, std::size_t size) noexcept {
#ifdef _WIN32
  SIZE_T got = 0;
  return p && out && size && ReadProcessMemory(GetCurrentProcess(),p,out,size,&got) && got == size;
#else
  (void)p; (void)out; (void)size;
  return false;
#endif
}
bool NativeRecognition(const Bindings &b, const void *artifact,
    std::uint32_t faith_id, bool &out) noexcept {
  if (!b.enabled || !b.image_base || !artifact || faith_id == absent) return false;
#if defined(_WIN32) && defined(_MSC_VER)
  using Fn = bool (*)(const void *, std::uint32_t, void *);
  __try {
    out = reinterpret_cast<Fn>(b.image_base + 0x2530EF0)(artifact,faith_id,nullptr);
    return true;
  } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  (void)out;
  return false;
#endif
}
bool NativeCurrentRarity(const Bindings &b,const void *site,std::int32_t &out) noexcept {
  if (!b.enabled||!b.image_base||!site) return false;
#if defined(_WIN32) && defined(_MSC_VER)
  using Fn = std::int32_t (*)(const void *);
  __try {
    out=reinterpret_cast<Fn>(b.image_base+0x265A3F0)(site);
    return true;
  } __except(EXCEPTION_EXECUTE_HANDLER) {return false;}
#else
  (void)out;return false;
#endif
}
struct Header {
  const void *data = nullptr;
  std::uint32_t capacity = 0, count = 0;
  const void *allocator = nullptr;
  friend bool operator==(const Header &,const Header &) = default;
};
bool ReadHeader(const Bindings &b,const void *p,std::size_t offset,Header &h) noexcept {
  const auto *a=At(p,offset);
  return Read(b,a,0,h.data) && Read(b,a,8,h.capacity) && Read(b,a,12,h.count) &&
      Read(b,a,16,h.allocator) && h.count <= h.capacity && h.count <= maximum_rows &&
      (h.count == 0 || h.data);
}
bool Ids(const Bindings &b,const void *p,std::size_t offset,std::vector<std::uint32_t> &ids) {
  Header first{},last{};
  if (!ReadHeader(b,p,offset,first)) return false;
  ids.resize(first.count);
  if (first.count && !b.read_memory(b.read_context,first.data,ids.data(),ids.size()*sizeof(ids[0]))) return false;
  return std::none_of(ids.begin(),ids.end(),[](auto id){return id==absent;}) &&
      ReadHeader(b,p,offset,last) && first == last;
}
const void *Resolve(const Bindings &b,void **global,std::uint32_t id,std::size_t identity_offset) noexcept {
  const void *store=nullptr,*rows=nullptr,*object=nullptr;
  std::uint32_t capacity=0,actual=absent;
  if (id==absent || !Read(b,global,0,store) || !store || !Read(b,store,0x20,rows) || !rows ||
      !Read(b,store,0x2C,capacity) || (id&0xFFFFFFU)>=capacity ||
      !Read(b,rows,static_cast<std::size_t>(id&0xFFFFFFU)*16+8,object) || !object ||
      !Read(b,object,identity_offset,actual) || actual!=id) return nullptr;
  return object;
}
bool Magic(const Bindings &b,const void *p,std::size_t offset,std::uint32_t expected) noexcept {
  std::uint32_t value=0;return Read(b,p,offset,value)&&value==expected;
}
bool Ref(const Bindings &b,const void *p,std::size_t offset,std::optional<std::uint32_t> &out) noexcept {
  std::uint32_t value=absent;
  if (!Read(b,p,offset,value)) return false;
  if (value!=absent) out=value;
  return true;
}
void County(const Bindings &b,const void *site,CountyContext &c) {
  c={};
  const auto fail=[&](const char *why){c.unavailable_reason=why;};
  if (!Ref(b,site,0xB0,c.barony_title_id) || !c.barony_title_id) return fail("barony_reference_unavailable");
  const auto *barony=Resolve(b,b.title_storage,*c.barony_title_id,0x10);
  if (!barony || !Ref(b,barony,0x108,c.county_title_id) || !c.county_title_id) return fail("county_reference_unavailable");
  const auto *county=Resolve(b,b.title_storage,*c.county_title_id,0x10);
  if (!county || !Ref(b,county,0x128,c.county_holder_id) || !c.county_holder_id) return fail("county_holder_reference_unavailable");
  const auto *holder=Resolve(b,b.character_storage,*c.county_holder_id,0x18);
  if (!holder || !Ref(b,holder,0xB4,c.county_holder_rite_id) || !c.county_holder_rite_id) return fail("county_holder_rite_unavailable");
  const auto *rite=Resolve(b,b.rite_storage,*c.county_holder_rite_id,8);
  if (!rite || !Ref(b,rite,0x4B8,c.county_holder_faith_id) || !c.county_holder_faith_id ||
      !Resolve(b,b.faith_storage,*c.county_holder_faith_id,8)) return fail("county_holder_faith_unavailable");
  c.available=true;c.unavailable_reason.clear();
}
bool Slots(const Bindings &b,const void *site,std::vector<Slot> &slots) {
  Header first{},last{};
  if (!ReadHeader(b,site,0x68,first)) return false;
  slots.clear();slots.reserve(first.count);
  for (std::uint32_t i=0;i<first.count;++i) {
    std::uint32_t id=absent;
    if (!Read(b,first.data,static_cast<std::size_t>(i)*24+0x10,id)) return false;
    slots.push_back({i,id==absent?std::nullopt:std::optional<std::uint32_t>{id}});
  }
  if (!ReadHeader(b,site,0x68,last)||first!=last) return false;
  // Element contents also need independent readback; header stability alone is
  // insufficient when an existing slot is replaced in place.
  for (const auto &slot:slots) {
    std::uint32_t id=absent;
    if (!Read(b,first.data,static_cast<std::size_t>(slot.slot_index)*24+0x10,id) ||
        id!=slot.artifact_id.value_or(absent)) return false;
  }
  return true;
}
Recognition Recognize(const Bindings &b,const void *artifact,
    std::optional<std::uint32_t> faith,std::uint32_t &calls) {
  Recognition out{};out.faith_id=faith;
  if (!faith || !Resolve(b,b.faith_storage,*faith,8)) {out.unavailable_reason="recognition_faith_full_reference_unavailable";return out;}
  if (!b.recognition) {out.unavailable_reason="native_recognition_getter_unavailable";return out;}
  bool value=false;++calls;
  if (!b.recognition(b,artifact,*faith,value)) {out.unavailable_reason="native_recognition_getter_failed";return out;}
  out.available=true;out.value=value;out.unavailable_reason.clear();return out;
}
void ReadArtifact(const Bindings &b,std::uint32_t id,const Snapshot &context,
    Artifact &out,std::uint32_t &calls) {
  out={};out.artifact_id=id;
  const auto *artifact=Resolve(b,b.artifact_storage,id,0x10);
  if (!artifact || !Magic(b,artifact,0x14,0x41727469U)) {out.unavailable_reason="artifact_full_reference_unavailable";return;}
  std::int32_t rarity=0;std::uint32_t site_owner=absent;
  if (!Read(b,artifact,0xB0,rarity)||!Read(b,artifact,0x7C,site_owner)) {out.unavailable_reason="artifact_fields_unavailable";return;}
  out.rarity_level=rarity;
  if (site_owner!=absent) out.native_holy_site_owner_id=site_owner;
  // Dynamic sanctification is an independent native collection. Reading it
  // explains an OR arm, but never replaces the original combined predicate.
  out.sanctified_faith_ids_available=Ids(b,artifact,0x498,out.sanctified_faith_ids);
  if (!out.sanctified_faith_ids_available) out.sanctified_faith_ids.clear();
  out.recognition_for_player_faith=Recognize(b,artifact,context.player_faith_id,calls);
  out.recognition_for_county_holder_faith=Recognize(b,artifact,context.county_context.county_holder_faith_id,calls);
  std::int32_t after_rarity=0;std::uint32_t after_owner=absent;
  std::vector<std::uint32_t> after_sanctified;
  if (Resolve(b,b.artifact_storage,id,0x10)!=artifact || !Read(b,artifact,0xB0,after_rarity) ||
      after_rarity!=rarity || !Read(b,artifact,0x7C,after_owner)||after_owner!=site_owner ||
      (out.sanctified_faith_ids_available&&(!Ids(b,artifact,0x498,after_sanctified)||after_sanctified!=out.sanctified_faith_ids))) {
    out.recognition_for_player_faith={};out.recognition_for_county_holder_faith={};
    out.rarity_level.reset();out.native_holy_site_owner_id.reset();
    out.sanctified_faith_ids_available=false;out.sanctified_faith_ids.clear();
    out.unavailable_reason="artifact_identity_or_fields_changed";return;
  }
  out.available=true;out.unavailable_reason.clear();
}
void EvaluateCurrent(const Bindings &b,const void *site,Snapshot &out) {
  auto &e=out.current_relic_evaluation;
  const auto fail=[&](const char *why){e.unavailable_reason=why;};
  std::int32_t count=0;
  if (!Read(b,site,0x8C,count)||count<0||static_cast<std::uint32_t>(count)>maximum_rows) return fail("inventory_count_unavailable");
  e.inventory_artifact_count_raw=count;
  if (out.county_context.available&&out.associated_faith_ids_available)
    e.county_holder_faith_associated=std::find(out.associated_faith_ids.begin(),out.associated_faith_ids.end(),
        *out.county_context.county_holder_faith_id)!=out.associated_faith_ids.end();
  if (count!=0&&(!out.inventory.available||!out.associated_faith_ids_available))
    return fail("current_rarity_source_arrays_unavailable");
  if (!b.current_rarity) return fail("native_current_rarity_getter_unavailable");
  std::int32_t sum=0;++out.native_getter_calls;
  // The original producer invokes its own per-slot recognition checks. Do not
  // replace them with an earlier sampled Boolean or reorder/deduplicate them:
  // arbitrary loaded template-trigger RNG state effects remain unverified.
  if (!b.current_rarity(b,site,sum)) return fail("native_current_rarity_getter_failed");
  e.active_artifact_rarity_sum=sum;e.is_active=sum>0;
  if (out.cached_world_state.available)
    e.cache_evaluation_disagreement=*out.cached_world_state.total_active_artifact_rarity!=sum ||
        *out.cached_world_state.is_active!=(sum>0);
  e.available=true;e.unavailable_reason.clear();
}
} // namespace

Bindings BindHolySiteRelicContextImage12004(std::uintptr_t base,std::string_view sha) noexcept {
  Bindings b{};
  if (!base||sha!=ck3_12004::kExecutableSha256) return b;
  const auto at=[base](std::uintptr_t rva){return reinterpret_cast<void **>(base+rva);};
  b.enabled=true;b.image_base=base;b.holy_site_storage=at(0x5D1DE80);b.artifact_storage=at(0x5D1DE68);
  b.title_storage=at(0x5D1DAF8);b.character_storage=at(0x5C67568);b.rite_storage=at(0x5D1E2F8);b.faith_storage=at(0x5D1E300);
  b.read_memory=&ProcessRead;b.recognition=&NativeRecognition;b.current_rarity=&NativeCurrentRarity;
  b.getter_backend="source_bound_native_getter";
  return b;
}
bool ReadHolySiteRelicContext12004(const Bindings &b,const ck3_12002::religion::Context &c,
    std::uint32_t requested,Snapshot &out,const void *jomini_owner) noexcept {
  out={};out.capture_epoch=c.capture_epoch;out.date_raw=c.date_raw;out.played_character_id=c.played_character_id;
  out.player_rite_id=c.rite_id;out.player_faith_id=c.faith_id;out.requested_holy_site_id=requested;out.holy_site_id=requested;
  out.getter_backend=std::string(b.getter_backend);
  const auto fail=[&](const char *why){out.recognition_matrix.reset();out.modifier_aggregate_observation.reset();out.unavailable_reason=why;return false;};
  try {
    if (!b.enabled||!b.image_base||!b.read_memory||!c.available||!c.capture_epoch||c.played_character_id<=0||!c.faith_id)
      return fail("current_player_religion_context_unavailable");
    const auto *site=Resolve(b,b.holy_site_storage,requested,0x10);
    if (!site||!Magic(b,site,0x14,0x486F5374U)) return fail("holy_site_full_reference_unavailable");
    std::uint8_t active=0;std::int32_t rarity=0;
    if (Read(b,site,0x18,active)&&active<=1&&Read(b,site,0x1C,rarity)) {
      out.cached_world_state.available=true;out.cached_world_state.is_active=active!=0;
      out.cached_world_state.total_active_artifact_rarity=rarity;out.cached_world_state.unavailable_reason.clear();
    } else out.cached_world_state.unavailable_reason="holy_site_world_cache_unavailable";
    out.associated_faith_ids_available=Ids(b,site,0x98,out.associated_faith_ids);
    if (!out.associated_faith_ids_available) out.associated_faith_ids.clear();
    County(b,site,out.county_context);
    if (Ids(b,site,0x80,out.inventory.artifact_ids)&&Slots(b,site,out.inventory.slots)) {
      out.inventory.available=true;out.inventory.unavailable_reason.clear();
      std::vector<std::uint32_t> ids=out.inventory.artifact_ids;
      for (const auto &slot:out.inventory.slots) if (slot.artifact_id) ids.push_back(*slot.artifact_id);
      for (const auto id:ids) {
        if (id==absent||std::any_of(out.inventory.artifact_objects.begin(),out.inventory.artifact_objects.end(),
            [id](const auto &a){return a.artifact_id==id;})) continue;
        Artifact artifact{};ReadArtifact(b,id,out,artifact,out.native_getter_calls);
        out.inventory.artifact_objects.push_back(std::move(artifact));
      }
    } else {out.inventory.artifact_ids.clear();out.inventory.slots.clear();out.inventory.unavailable_reason="inventory_reference_or_slot_array_unavailable";}
    EvaluateCurrent(b,site,out);
    if (jomini_owner) {
      RecognitionMatrix matrix{};
      (void)ReadHolySiteRelicRecognitionMatrix12004(b,jomini_owner,c,requested,std::nullopt,&out,matrix);
      out.recognition_matrix=std::move(matrix);
      ModifierAggregateObservation modifiers{};
      (void)ReadHolySiteModifierAggregate12004(b,c,requested,modifiers);
      out.modifier_aggregate_observation=std::move(modifiers);
    }
    // The legacy counter keeps its original scope. Matrix calls are disclosed
    // separately, and all original post-evaluation identity/cache checks follow.
    std::vector<std::uint32_t> after_ids,after_faiths;std::vector<Slot> after_slots;
    CountyContext after_county{};County(b,site,after_county);
    const bool county_same=after_county.available==out.county_context.available &&
        after_county.barony_title_id==out.county_context.barony_title_id &&
        after_county.county_title_id==out.county_context.county_title_id &&
        after_county.county_holder_id==out.county_context.county_holder_id &&
        after_county.county_holder_rite_id==out.county_context.county_holder_rite_id &&
        after_county.county_holder_faith_id==out.county_context.county_holder_faith_id;
    if (Resolve(b,b.holy_site_storage,requested,0x10)!=site||!county_same)
      return fail("holy_site_or_county_identity_changed");
    if (out.associated_faith_ids_available&&(!Ids(b,site,0x98,after_faiths)||after_faiths!=out.associated_faith_ids))
      return fail("associated_faith_ids_changed");
    if (out.inventory.available) {
      if (!Ids(b,site,0x80,after_ids)||after_ids!=out.inventory.artifact_ids||!Slots(b,site,after_slots)||after_slots.size()!=out.inventory.slots.size())
        return fail("inventory_or_slots_changed");
      for (std::size_t i=0;i<after_slots.size();++i)
        if (after_slots[i].artifact_id!=out.inventory.slots[i].artifact_id) return fail("slot_artifact_changed");
    }
    if (out.cached_world_state.available) {
      std::uint8_t after_active=0;std::int32_t after_rarity=0;
      if (!Read(b,site,0x18,after_active)||!Read(b,site,0x1C,after_rarity)||
          (after_active!=0)!=*out.cached_world_state.is_active||after_rarity!=*out.cached_world_state.total_active_artifact_rarity)
        return fail("world_cache_changed_during_recognition");
    }
    out.available=true;out.unavailable_reason.clear();return true;
  } catch (...) {return fail("holy_site_relic_context_copy_exception");}
}
} // namespace xar::ck3_12004::religion::holy_site_relic
