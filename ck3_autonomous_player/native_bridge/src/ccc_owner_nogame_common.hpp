#pragma once
#include <windows.h>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include "xar_bridge/ck3_121003_ccc_owner26785313_v1.hpp"
// Self-owned DATA only. No host-memory reads, Game, mailbox submission or ABI calls.
// Tests enter actual family Inner at an explicit guard seam; this is not proof of
// the common CCC transition/case-binding authority. Raw case_bound is test DATA.
namespace ccc_nogame {
namespace c=xar::ck3_121003::build26785313;
namespace old=xar::ck3_1210;
namespace mt=xar::ck3_11906;
inline void Check(bool value,const char*why){if(!value)throw std::runtime_error(why);}
inline std::uint64_t WallNow(){return static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count());}
inline old::CoreSnapshotPrefix Core(std::int32_t actor=36423){old::CoreSnapshotPrefix x;x.clock={53144376,3,true};x.local_player_id=1;x.map_ready=x.has_played_character=x.played_character_alive=true;x.played_character_id=actor;return x;}
template<class Request>void SetId(Request&q,std::string_view id){Check(!id.empty()&&id.size()<=96,"test id length");std::copy(id.begin(),id.end(),q.request_id.begin());q.request_id_size=static_cast<std::uint8_t>(id.size());}
}
namespace xar::ck3_121003::build26785313 {
// The real owner's Frame checks this fixed address. No common owner execution or
// fabricated CCC case permission is performed by this explicitly inert stub.
bool ExecuteCccOnOwner267V1(void*,const ck3_11906::MainThreadExecutionStampV1&)noexcept{return false;}
ReadonlyBindings BindReadonlyImage(std::uintptr_t,std::string_view)noexcept{return {};}
}
