#include "xar_bridge/ck3_121003_living_inventory26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_living_inventory26785313_pins_v1.hpp"
#include <windows.h>
#include <bcrypt.h>
#include <cstring>
#include <limits>
#include <vector>
namespace xar::ck3_121003::build26785313 {namespace {
bool LivingPinCopy(std::uintptr_t p,void*out,std::size_t n)noexcept{
 if(!p||!out||!n||n-1>(std::numeric_limits<std::uintptr_t>::max)()-p)return false;
 __try{std::memcpy(out,reinterpret_cast<const void*>(p),n);return true;}
 __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
// CNG hashes only already-bounded code copies; ASLR absolute pointer operands
// are checked separately as module-relative slots/targets, never code hashes.
bool LivingCodeDigest(BCRYPT_ALG_HANDLE algorithm,const std::vector<unsigned char>&bytes,
 std::array<unsigned char,32>&out){
 BCRYPT_HASH_HANDLE hash=nullptr;DWORD size=0,used=0;
 if(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&used,0)<0||!size||size>1024*1024)return false;
 std::vector<unsigned char>object(size);bool good=false;
 if(BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0)<0)return false;
 good=BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)>=0&&
      BCryptFinishHash(hash,out.data(),static_cast<ULONG>(out.size()),0)>=0;
 const bool cleaned=BCryptDestroyHash(hash)>=0;return good&&cleaned;
}
}
bool VerifyLivingInventoryImage267V1(std::uintptr_t image)noexcept{
 if(!image||image>(std::numeric_limits<std::uintptr_t>::max)()-kImageSize||!VerifyReadonlyImage(image))return false;
 BCRYPT_ALG_HANDLE algorithm=nullptr;bool good=false;
 if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
 try{
  good=true;
  for(const auto&pin:living_inventory_pins::kCode){
   if(!pin.size||pin.rva>=kImageSize||pin.size>kImageSize-pin.rva){good=false;break;}
   std::vector<unsigned char>bytes(pin.size);std::array<unsigned char,32>digest{};
   if(!LivingPinCopy(image+pin.rva,bytes.data(),bytes.size())||!LivingCodeDigest(algorithm,bytes,digest)||digest!=pin.sha){good=false;break;}
  }
  if(good)for(const auto&pin:living_inventory_pins::kPointers){
   std::uintptr_t actual=0;
   if(pin.slot>kImageSize-sizeof(actual)||pin.target>=kImageSize||!LivingPinCopy(image+pin.slot,&actual,sizeof(actual))||actual!=image+pin.target){good=false;break;}
  }
 }catch(...){good=false;}
 const bool cleaned=BCryptCloseAlgorithmProvider(algorithm,0)>=0;return good&&cleaned;
}
}
