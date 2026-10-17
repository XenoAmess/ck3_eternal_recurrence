#include "xar_bridge/holy_site_creation12004_mailbox.hpp"
#include "xar_bridge/ck3_12004_ingame_ui.hpp"
#include <limits>
namespace xar::ck3_12004::religion::holy_site_creation {
namespace {
template<class T>bool Read(const Bindings&b,const void*p,std::size_t off,T&out)noexcept{
 const auto a=reinterpret_cast<std::uintptr_t>(p);
 return a&&off<=std::numeric_limits<std::uintptr_t>::max()-a&&b.read_memory&&
  b.read_memory(b.read_context,reinterpret_cast<const void*>(a+off),&out,sizeof(out));
}
struct Owner {const void*gfx=nullptr,*handler=nullptr;bool operator==(const Owner&)const=default;};
bool ReadOwner(const Bindings&b,const void*jomini,Owner&v)noexcept{
 std::uintptr_t vt=0;
 // Existing exact4 religion detail reader uses jomini+10 -> gfx+88.
 // Bind the same handler vtable as the admitted typed-UI owner resolver.
 return b.enabled&&Read(b,jomini,0x10,v.gfx)&&v.gfx&&Read(b,v.gfx,0x88,v.handler)&&v.handler&&
  Read(b,v.handler,0,vt)&&vt==b.image_base+ck3_12004::kUiHandlerPrimaryVtable12004V1;
}
void Unavailable(const ck3_12002::religion::Context&ctx,Snapshot&out,const char*why){
 out={};out.capture_epoch=ctx.capture_epoch;out.date_raw=ctx.date_raw;out.played_character_id=ctx.played_character_id;
 if(ctx.faith_id)out.player_faith_id=*ctx.faith_id;out.unavailable_reason=why;
}
}
bool ReadFromJomini12004(const Bindings&b,const void*jomini,
 const ck3_12002::religion::Context&ctx,Snapshot&out)noexcept{
 try{
  Owner first{},last{};
  if(!ReadOwner(b,jomini,first)){Unavailable(ctx,out,"holy_site_creation_owner_chain_unverified");return false;}
  const bool observed=ReadContext12004(b,first.handler,ctx,out);
  if(!ReadOwner(b,jomini,last)||first!=last){Unavailable(ctx,out,"holy_site_creation_owner_changed_during_read");return false;}
  return observed;
 }catch(...){Unavailable(ctx,out,"holy_site_creation_owner_read_exception");return false;}
}
}
