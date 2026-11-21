#pragma once
#include "xar_bridge/ck3_121003_letter26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct LetterBindings267V1{std::uintptr_t image=0;bool verified=false;};
struct LetterScene267V1{
 std::uint64_t wall_deadline=0;std::uintptr_t jomini=0,gfx=0,context=0,global=0,events=0,letter=0;
 bool visible=false,enabled=false;friend bool operator==(const LetterScene267V1&,const LetterScene267V1&)=default;
};
struct LetterRaw267V1{
 LetterSource267V1 source;std::uintptr_t game=0,jomini=0,manager=0,windows=0,window=0,data=0,runtime_event=0,definition=0,options=0;
 std::array<std::byte,16>windows_header{},options_header{},authored_header{};std::vector<std::uintptr_t>window_pointers,option_pointers,authored_option_pointers;
 std::int32_t authored_option_count=0;
 bool cleanup_known=true,native_read_entered=false;
 friend bool operator==(const LetterRaw267V1&,const LetterRaw267V1&)=default;
};
enum class LetterRawCallStatus267V1{unavailable,returned,indeterminate};
struct LetterRawCall267V1{LetterRawCallStatus267V1 status=LetterRawCallStatus267V1::unavailable;bool effect_entered=false,cleanup_known=true;};
bool VerifyLetterImage267V1(std::uintptr_t)noexcept;
LetterBindings267V1 BindLetterImage267V1(std::uintptr_t,std::string_view)noexcept;
// No owner or lease authority is granted by these raw primitives.
bool ReadLetterRaw267V1(const ReadonlyBindings&,const LetterBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,
 const LetterScene267V1&,std::uint64_t monotonic_deadline,LetterRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 ReplyKnownLetterRaw267V1(const ReadonlyBindings&,const LetterBindings267V1&,
 const ck3_1210::CoreSnapshotPrefix&,const LetterScene267V1&,std::uint64_t monotonic_deadline,const LetterRaw267V1&)noexcept;
} // namespace
