#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
namespace xar::ck3_12003 {
struct OrdinaryInteractionRequestV1;
namespace ordinary_interaction { struct Bindings; }
}
namespace xar::ck3_12004::clerical_preview {
inline constexpr std::array<std::string_view,6> kOptionKeys{
    "hook","skill_support","piety_support","dread_support","friendly_support","lunacy_support"};
inline constexpr bool AllowedKey(std::string_view key) noexcept {
  return key=="make_clerical_puppet_interaction"||key=="make_external_clerical_puppet_interaction";
}
struct Context {
  bool available=false,needs_confirmation=false;
  std::string key;
  std::uint32_t definition_hash=0,actor=0,recipient=0,effective_actor=0,kind=255;
  std::uint32_t declared_count=0,selected_count=0;
  std::array<std::uint32_t,6> roles{},option_flags{};
  std::array<std::uint8_t,6> option_bank{};
  bool operator==(const Context&)const=default;
};
inline bool DefaultOnly(const Context&c,std::string_view key,std::uint32_t actor,std::uint32_t recipient) noexcept {
  if(!c.available||!AllowedKey(key)||c.key!=key||!c.needs_confirmation||c.kind!=0||
      !actor||actor==UINT32_MAX||!recipient||recipient==UINT32_MAX||
      c.actor!=actor||c.recipient!=recipient||c.effective_actor!=actor||
      c.roles[0]!=actor||c.roles[1]!=recipient||c.roles[5]!=actor||
      c.declared_count!=6||c.selected_count!=0)return false;
  for(std::size_t i=0;i<6;++i){
    if(c.option_flags[i]==UINT32_MAX||c.option_bank[i]!=0)return false;
    for(std::size_t j=0;j<i;++j)if(c.option_flags[j]==c.option_flags[i])return false;
  }
  return true;
}
struct WindowBindings {
  void*confirmation=nullptr,*handler=nullptr;
  void(*copy_context)(void*,const void*)=nullptr;
  void(*open_window)(void*,std::int32_t,std::int32_t)=nullptr;
  void(*refresh_window)(void*)=nullptr;
};
struct Attempt {
  Context actual_default{};
  bool invoked=false,completed=false;
  const char*reason="not_attempted";
};
// Trusted owner-only calls. No public pointers/callbacks, command or option intent.
bool ReadDefault(const ck3_12003::ordinary_interaction::Bindings&,
    const ck3_12003::OrdinaryInteractionRequestV1&,Context&) noexcept;
bool ReadInstalled(const ck3_12003::ordinary_interaction::Bindings&,
    const ck3_12003::OrdinaryInteractionRequestV1&,const void*owned_context,Context&) noexcept;
void OpenDefault(const ck3_12003::ordinary_interaction::Bindings&,
    const ck3_12003::OrdinaryInteractionRequestV1&,const Context&expected,
    const WindowBindings&,Attempt&) noexcept;
}
