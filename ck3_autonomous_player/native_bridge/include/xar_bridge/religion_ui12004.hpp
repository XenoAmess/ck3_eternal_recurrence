#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004::religion_ui {
enum class Window : std::uint32_t { character=0, faith=1 };
using ReadMemory = bool(*)(void*,const void*,void*,std::size_t) noexcept;
using AnyType = void*(__fastcall*)();
using OpenViewData = void(__fastcall*)(void*,std::uint32_t,const void*);
struct Bindings {
  bool enabled=false;
  std::uintptr_t image_base=0;
  ReadMemory read_memory=nullptr;
  void* read_context=nullptr;
  AnyType character_any=nullptr,faith_any=nullptr;
  OpenViewData open_view_data=nullptr;
};
struct Selection {
  bool available=false,subject_available=false;
  std::uint32_t subject_id=0xFFFFFFFFU,selected_rite_id=0xFFFFFFFFU;
  std::string unavailable_reason;
  // Provider-private identities. Never serialize these addresses.
  const void*handler=nullptr,*window=nullptr,*root=nullptr,*gfx=nullptr;
};
Bindings BindImage12004(std::uintptr_t image_base,std::string_view executable_sha256) noexcept;
bool ReadSelection12004(const Bindings&,const void*admitted_handler,Window,Selection&) noexcept;
bool CanOpen12004(const Bindings&,const void*admitted_handler,Window,std::uint32_t full_id) noexcept;
// Must be called inside the existing owner/TLS/paused/modal UI callback. A true
// return means the original call returned; attempted is not a visible result.
bool InvokeOpen12004(const Bindings&,void*admitted_handler,Window,std::uint32_t full_id,bool&attempted) noexcept;
}
