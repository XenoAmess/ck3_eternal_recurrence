#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <windows.h>
#include <bcrypt.h>
#include <vector>

namespace xar::game { class GameAdapter; }
namespace xar::admission125 {
struct HashReport {
  const char *stage="not_observed";
  std::uint32_t error=0;
  std::int32_t status=0;
  std::uint64_t bytes_read=0;
  std::array<char,65> actual_sha{};
};
struct ImageReport {
  const char *stage="not_attempted";
  std::uintptr_t actual_base=0;
  std::uint64_t header_value=0,expected_value=0;
  std::int32_t pin_index=-1;
  std::uint32_t pin_rva=0,byte_count=0;
  bool copy_ok=false;
  std::array<unsigned char,64> observed{},expected{};
};
struct Report {HashReport hash{};ImageReport image{};};
inline thread_local HashReport last_hash{};
inline thread_local ImageReport last_image{};
inline HashReport HashInput(std::string_view sha) noexcept {
  if(sha==last_hash.actual_sha.data()&&last_hash.stage!=std::string_view("not_observed")&&
      last_hash.stage!=std::string_view("factory_supplied_sha"))return last_hash;
  HashReport r{};r.stage="factory_supplied_sha";
  if(sha.size()==64)for(std::size_t i=0;i<64;++i)r.actual_sha[i]=sha[i];
  return r;
}
// The production file-open policy and BCrypt algorithm are unchanged. The own-
// file test uses this exact implementation; it never opens a game process.
inline std::string Sha256File(const wchar_t *path) noexcept {
  last_hash={};last_hash.stage="file_open";
  HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(file==INVALID_HANDLE_VALUE){last_hash.error=GetLastError();return {};}
  BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
  std::vector<std::uint8_t> object;std::array<std::uint8_t,32> digest{};bool ok=false;
  do {
    last_hash.stage="algorithm_open";
    last_hash.status=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0);
    if(last_hash.status<0)break;
    DWORD object_size=0,copied=0;last_hash.stage="object_length";
    last_hash.status=BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&object_size),sizeof(object_size),&copied,0);
    if(last_hash.status<0||object_size==0)break;
    object.resize(object_size);last_hash.stage="hash_create";
    last_hash.status=BCryptCreateHash(algorithm,&hash,object.data(),object_size,nullptr,0,0);
    if(last_hash.status<0)break;
    std::array<std::uint8_t,64U*1024U> buffer{};
    while(true){DWORD read=0;last_hash.stage="file_read";
      if(!ReadFile(file,buffer.data(),static_cast<DWORD>(buffer.size()),&read,nullptr)){last_hash.error=GetLastError();break;}
      last_hash.bytes_read+=read;
      if(!read){last_hash.stage="hash_finish";last_hash.status=BCryptFinishHash(hash,digest.data(),static_cast<ULONG>(digest.size()),0);ok=last_hash.status>=0;break;}
      last_hash.stage="hash_data";last_hash.status=BCryptHashData(hash,buffer.data(),read,0);if(last_hash.status<0)break;
    }
  }while(false);
  if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);CloseHandle(file);
  if(!ok)return {};
  constexpr char digits[]="0123456789ABCDEF";
  for(std::size_t i=0;i<digest.size();++i){last_hash.actual_sha[i*2]=digits[digest[i]>>4U];last_hash.actual_sha[i*2+1]=digits[digest[i]&15U];}
  last_hash.stage="complete";return last_hash.actual_sha.data();
}
Report ReadAdapterReport(const game::GameAdapter&) noexcept;
template<class AppendString,class Number> void AppendFailure(std::string &out,const game::GameAdapter &game,AppendString text,Number number) {
  const auto r=ReadAdapterReport(game);
  out+=",\"admission_diagnostic125\":{\"schema\":\"xar.native.admission-failure125/v1\",\"hash_stage\":";text(out,r.hash.stage);
  out+=",\"actual_sha256\":";text(out,r.hash.actual_sha.data());
  out+=",\"hash_error\":";out+=number(r.hash.error);out+=",\"hash_status_bits\":";out+=number(static_cast<std::uint32_t>(r.hash.status));
  out+=",\"hash_bytes\":";out+=number(r.hash.bytes_read);out+=",\"bind_stage\":";text(out,r.image.stage);
  out+=",\"actual_module_base\":";out+=number(r.image.actual_base);
  out+=",\"header_actual\":";out+=number(r.image.header_value);out+=",\"header_expected\":";out+=number(r.image.expected_value);
  out+=",\"pin_index_plus_one\":";out+=number(static_cast<std::uint32_t>(r.image.pin_index+1));out+=",\"pin_rva\":";out+=number(r.image.pin_rva);
  out+=",\"pin_copy_ok\":";out+=r.image.copy_ok?"true":"false";
  const auto hex=[](const auto &bytes,std::uint32_t count){std::string s;constexpr char d[]="0123456789ABCDEF";for(std::uint32_t i=0;i<count&&i<bytes.size();++i){s+=d[bytes[i]>>4U];s+=d[bytes[i]&15U];}return s;};
  out+=",\"pin_observed\":";text(out,hex(r.image.observed,r.image.byte_count));out+=",\"pin_expected\":";text(out,hex(r.image.expected,r.image.byte_count));out+='}';
}
}
