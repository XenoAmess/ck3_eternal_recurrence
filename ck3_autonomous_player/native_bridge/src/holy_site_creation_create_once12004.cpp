#include "xar_bridge/holy_site_creation_create_once12004.hpp"
#include <windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <limits>

namespace xar::ck3_12004::religion::holy_site_creation {
namespace {
// Same CNG SHA256 provider used by the existing relic preview, with local
// handle cleanup also covering allocation failures.
std::string Sha256(std::string_view input) {
  struct Handles {
    BCRYPT_ALG_HANDLE alg=nullptr; BCRYPT_HASH_HANDLE hash=nullptr;
    std::vector<unsigned char> object;
    ~Handles() { if(hash)(void)BCryptDestroyHash(hash); if(alg)(void)BCryptCloseAlgorithmProvider(alg,0); }
  } handles;
  DWORD bytes=0, size=0; std::array<unsigned char,32> digest{};
  if(input.size()>std::numeric_limits<ULONG>::max() ||
      BCryptOpenAlgorithmProvider(&handles.alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0 ||
      BCryptGetProperty(handles.alg,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&bytes,0)<0)
    return {};
  handles.object.resize(size);
  if(BCryptCreateHash(handles.alg,&handles.hash,handles.object.data(),size,nullptr,0,0)<0 ||
      BCryptHashData(handles.hash,reinterpret_cast<PUCHAR>(const_cast<char*>(input.data())),static_cast<ULONG>(input.size()),0)<0 ||
      BCryptFinishHash(handles.hash,digest.data(),static_cast<ULONG>(digest.size()),0)<0) return {};
  constexpr char hex[]="0123456789abcdef"; std::string result; result.reserve(64);
  for(const auto byte:digest){result+=hex[byte>>4];result+=hex[byte&15];}
  return result;
}
void U64(std::string& out,std::uint64_t value) {
  for(unsigned shift=0;shift<64;shift+=8)out+=static_cast<char>((value>>shift)&255U);
}
void Text(std::string& out,std::string_view value) { U64(out,value.size());out.append(value); }
}
bool PreviewIdentityValid12004(std::string_view value) noexcept {
  return value.size()==64 && std::all_of(value.begin(),value.end(),[](char c){
    return (c>='0'&&c<='9')||(c>='a'&&c<='f');});
}
std::string PreviewIdentitySha25612004(const Snapshot& s,std::uintptr_t image,
    const void* type,const void* gui) noexcept {
  try {
    if(!image||!s.available||!s.models_complete||!s.selection_available||!s.player_faith_matches||
        !s.handler||!s.window||!s.root||!s.gfx||!type||!gui||!s.selected_type_key||!s.selected_barony_title_id||
        !s.native_enabled_observed||!s.bypass_requirements_observed||!s.create_tooltip_available||
        !s.cached_resource_quote_available)return {};
    std::string input; Text(input,"ck3-1.20.0.4.creation-preview.bridge-sha256.v1");
    U64(input,image);U64(input,reinterpret_cast<std::uintptr_t>(s.handler));
    U64(input,reinterpret_cast<std::uintptr_t>(s.window));U64(input,reinterpret_cast<std::uintptr_t>(s.root));
    U64(input,reinterpret_cast<std::uintptr_t>(s.gfx));U64(input,reinterpret_cast<std::uintptr_t>(gui));
    U64(input,reinterpret_cast<std::uintptr_t>(type));
    U64(input,static_cast<std::uint32_t>(s.played_character_id));U64(input,s.player_faith_id);
    U64(input,s.window_faith_id);U64(input,static_cast<std::uint32_t>(s.date_raw));
    Text(input,*s.selected_type_key);U64(input,*s.selected_barony_title_id);
    U64(input,s.selected_artifact_ids.size());for(auto id:s.selected_artifact_ids)U64(input,id);
    U64(input,s.native_rarity_sum_observed);U64(input,static_cast<std::uint64_t>(s.native_rarity_sum_raw));
    U64(input,s.native_enabled_observed);U64(input,s.native_create_button_enabled);
    U64(input,s.bypass_requirements_observed);U64(input,s.bypass_requirements_raw);
    Text(input,s.create_tooltip);for(auto raw:s.cached_resource_vector_raw)U64(input,static_cast<std::uint64_t>(raw));
    return Sha256(input);
  } catch(...) {return {};}
}
std::string_view CreateOnceGuard12004(const Snapshot& s,std::string_view expected,bool enabled) noexcept {
  if(!enabled)return "holy_site_creation_create_once_optin_disabled";
  if(!PreviewIdentityValid12004(expected)||!PreviewIdentityValid12004(s.preview_identity_sha256))
    return "holy_site_creation_create_preview_identity_unavailable";
  if(expected!=s.preview_identity_sha256)return "holy_site_creation_create_preview_identity_changed";
  if(!s.available||!s.models_complete||!s.selection_available||!s.player_faith_matches||
      !s.selected_type_key||!s.selected_barony_title_id||!s.create_tooltip_available||!s.cached_resource_quote_available)
    return "holy_site_creation_create_preview_unavailable";
  if(!s.bypass_requirements_observed||s.bypass_requirements_raw!=0)
    return "holy_site_creation_create_requires_observed_normal_requirements";
  if(!s.native_enabled_observed||!s.native_create_button_enabled)
    return "holy_site_creation_create_native_refused";
  return {};
}
OnceClaim12004 CreateOnceLedger12004::Claim(std::uintptr_t process,std::uintptr_t owner,
    std::uint64_t revision,std::string_view preview) noexcept {
  if(!process||!owner||!revision||!PreviewIdentityValid12004(preview))return OnceClaim12004::invalid_scope;
  try {
    Entry key{};key.process_scope=process;key.owner_scope=owner;key.revision=revision;
    std::copy(preview.begin(),preview.end(),key.preview.begin());
    const std::lock_guard lock(mutex_);
    for(std::size_t i=0;i<size_;++i)if(entries_[i]==key)return OnceClaim12004::already_attempted;
    if(size_==capacity)return OnceClaim12004::capacity_exhausted;
    entries_[size_++]=key;return OnceClaim12004::claimed;
  } catch(...) {return OnceClaim12004::unavailable;}
}
}
