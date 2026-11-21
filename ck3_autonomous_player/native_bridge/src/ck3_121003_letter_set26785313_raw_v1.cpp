#include "xar_bridge/ck3_121003_letter_set26785313_raw_v1.hpp"
#include <cstring>
#include <limits>
#include <unordered_set>
#include <windows.h>
namespace xar::ck3_121003::build26785313 {namespace {
[[maybe_unused]]bool SetCopy(std::uintptr_t p,void*out,std::size_t n)noexcept{if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;__try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}__except(EXCEPTION_EXECUTE_HANDLER){return false;}}
template<class T>bool SetAt(std::uintptr_t p,std::size_t off,T&v)noexcept{return p&&off<=(std::numeric_limits<std::uintptr_t>::max)()-p&&SetCopy(p+off,&v,sizeof(v));}
[[maybe_unused]]bool SetRootName(std::uintptr_t root,std::string&name){std::uint64_t n=0,cap=0;std::uintptr_t data=root+0x1B8;if(!SetAt(root,0x1C8,n)||!SetAt(root,0x1D0,cap)||n>256||n>cap||cap<15||cap>0x1000000)return false;if(cap==15){if(n>15)return false;}else if(!SetAt(root,0x1B8,data)||!data)return false;std::array<char,257>bytes{};if(!SetCopy(data,bytes.data(),static_cast<std::size_t>(n)+1)||bytes[n]||std::memchr(bytes.data(),0,static_cast<std::size_t>(n))||(n&&MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(n),nullptr,0)==0))return false;name.assign(bytes.data(),static_cast<std::size_t>(n));return true;}
[[maybe_unused]]bool SetSample(const ReadonlyBindings&b,const LetterBindings267V1&bindings,const ck3_1210::CoreSnapshotPrefix&core,const LetterSetScene267V1&scene,std::uint64_t mono,LetterSetRaw267V1&out,std::string&reason){
 const auto fail=[&](const char*why){reason=why;return false;};
 if(scene.roots.size()>32||scene.common.letter||scene.common.visible||scene.common.enabled)return fail("letter_set_invalid_complete_scene");
 if(!ReadLetterRaw267V1(b,bindings,core,scene.common,mono,out.manager_census,reason)){out.cleanup_known=out.manager_census.cleanup_known;out.native_read_entered=out.manager_census.native_read_entered;return false;}
 out.source.resident_count=out.manager_census.source.resident_count;out.source.named_root_count=static_cast<std::int32_t>(scene.roots.size());
 std::vector<std::uintptr_t>joined(scene.roots.size());std::unordered_set<std::uintptr_t>roots;for(const auto&root:scene.roots)if(!root.root||!roots.insert(root.root).second)return fail("letter_set_duplicate_root_identity");
 for(const auto window:out.manager_census.window_pointers){std::uintptr_t vt=0,root=0,context=0;if(!SetAt(window,0,vt))return fail("letter_set_resident_type_unreadable");if(vt!=bindings.image+0x4C5D448)continue;if(!SetAt(window,0x70,root)||!SetAt(window,0x78,context))return fail("letter_set_resident_root_context_unreadable");if(!root)continue;
  bool matched=false;for(std::size_t i=0;i<scene.roots.size();++i)if(scene.roots[i].root==root){if(context!=scene.common.context||joined[i])return fail("letter_set_root_controller_context_or_identity_ambiguous");joined[i]=window;matched=true;}
  if(!matched){std::string name;if(!SetRootName(root,name))return fail("letter_set_unmatched_resident_root_name_unreadable");if(name=="letter_event")return fail("letter_set_resident_letter_absent_from_complete_root_census");}
 }
 std::unordered_set<std::int32_t>instances;
 for(std::size_t i=0;i<scene.roots.size();++i){const auto&root=scene.roots[i];if(!joined[i])return fail("letter_set_named_root_missing_exact_controller");
  // All roots are inventoried. Unsupported inactive material is a whole-census
  // refusal; it is never silently skipped or promoted to source authority.
  if(!root.visible)return fail("letter_set_inactive_root_material_unsupported_no_skip");
  auto single=scene.common;single.letter=root.root;single.visible=root.visible;single.enabled=root.enabled;LetterRaw267V1 row;
  if(!ReadLetterRaw267V1(b,bindings,core,single,mono,row,reason)){out.native_read_entered=out.native_read_entered||row.native_read_entered;out.cleanup_known=row.cleanup_known;return false;}
  out.native_read_entered=out.native_read_entered||row.native_read_entered;
  if(row.window!=joined[i]||row.game!=out.manager_census.game||row.jomini!=out.manager_census.jomini||row.manager!=out.manager_census.manager||row.windows!=out.manager_census.windows||row.windows_header!=out.manager_census.windows_header||row.window_pointers!=out.manager_census.window_pointers||!row.source.letter_found||!row.source.named_root_bound||!row.source.instance_id||!instances.insert(*row.source.instance_id).second)return fail("letter_set_complete_manager_or_unique_instance_changed");
  out.source.letters.push_back(row.source);out.letters.push_back(std::move(row));
 }
 out.source.census_complete=true;return true;
}
}
bool ReadLetterSetRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LetterBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const LetterSetScene267V1&scene,[[maybe_unused]]std::uint64_t mono,LetterSetRaw267V1&out,std::string&reason)noexcept{
 out={};reason="current_letter_set_default_off";
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1
 LetterSetRaw267V1 a,z;try{if(!SetSample(b,bindings,core,scene,mono,a,reason)){out=std::move(a);return false;}if(!SetSample(b,bindings,core,scene,mono,z,reason)){z.native_read_entered=z.native_read_entered||a.native_read_entered;out=std::move(z);return false;}if(a!=z){out=std::move(z);reason="letter_set_full_census_changed_between_samples";return false;}out=std::move(z);reason.clear();return true;}catch(...){out.native_read_entered=a.native_read_entered||z.native_read_entered;out.cleanup_known=!out.native_read_entered;reason="letter_set_native_observation_completion_unknown";return false;}
#else
 return false;
#endif
}
LetterRawCall267V1 ReplyKnownLetterSetRaw267V1([[maybe_unused]]const ReadonlyBindings&b,[[maybe_unused]]const LetterBindings267V1&bindings,[[maybe_unused]]const ck3_1210::CoreSnapshotPrefix&core,[[maybe_unused]]const LetterSetScene267V1&scene,[[maybe_unused]]std::uint64_t mono,[[maybe_unused]]const LetterSetRaw267V1&expected,[[maybe_unused]]std::int32_t instance)noexcept{LetterRawCall267V1 result;
#if defined(XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1) && XAR_CK3_ENABLE_121003_26785313_LETTER_SET_V1
 LetterSetRaw267V1 actual;std::string reason;if(!ReadLetterSetRaw267V1(b,bindings,core,scene,mono,actual,reason)){result.cleanup_known=actual.cleanup_known;if(!actual.cleanup_known)result.status=LetterRawCallStatus267V1::indeterminate;return result;}if(actual!=expected||instance<=0)return result;
 const LetterRaw267V1*chosen=nullptr;std::size_t chosen_index=0;for(std::size_t i=0;i<actual.letters.size();++i)if(actual.letters[i].source.instance_id==instance){if(chosen)return result;chosen=&actual.letters[i];chosen_index=i;}
 if(!chosen||!chosen->source.known_reply_admissible)return result;auto single=scene.common;single.letter=scene.roots[chosen_index].root;single.visible=scene.roots[chosen_index].visible;single.enabled=scene.roots[chosen_index].enabled;
 return ReplyKnownLetterRaw267V1(b,bindings,core,single,mono,*chosen);
#else
 return result;
#endif
}
}
