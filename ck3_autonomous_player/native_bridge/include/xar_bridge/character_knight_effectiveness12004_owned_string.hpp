#pragma once
#include "xar_bridge/character_skill_effect12004.hpp"
#include <cstring>
namespace xar::bridge::character_skill_effect12004::knight_string_detail {
// Pure owned-copy/cleanup seam shared by the production native callback and
// owned-memory tests. Production supplies only its fixed real Copy/DestroyCall;
// this template supplies no request, ABI override or game-object constructor.
template<class NativeString,class CopyBytes,class ValidateUtf8,class Destroy>
bool CopyThenDestroy(bool invoked,NativeString &text,std::string &out,
    CopyBytes copy,ValidateUtf8 utf8,Destroy destroy) noexcept {
  out.clear();bool copied=false;
  try{
    if(invoked&&text.size<=kMaxBreakdownBytes&&text.size<=text.capacity){
      std::uintptr_t data=reinterpret_cast<std::uintptr_t>(text.storage.data());
      if(text.capacity>=16)std::memcpy(&data,text.storage.data(),sizeof(data));
      if(text.size==0)copied=true;
      else if(data){out.resize(static_cast<std::size_t>(text.size));copied=copy(data,out.data(),out.size())&&utf8(out);}
    }
  }catch(...){copied=false;}
  const bool destroyed=destroy(text); // Exactly one attempt, even partial call.
  if(!invoked||!copied||!destroyed){out.clear();return false;}return true;
}
} // namespace xar::bridge::character_skill_effect12004::knight_string_detail
