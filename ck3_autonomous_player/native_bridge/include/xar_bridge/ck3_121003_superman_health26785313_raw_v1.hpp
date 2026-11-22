#pragma once
#include "xar_bridge/ck3_121003_superman_health26785313_v1.hpp"
#include "xar_bridge/ck3_121003_letter_set26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
using SupermanHealthScene267V1=LetterSetScene267V1;
struct SupermanHealthNumeric267V1{
 std::array<std::array<std::byte,16>,40>references{};std::array<std::uintptr_t,40>characters{};std::array<std::array<std::int64_t,14>,40>values{};
 std::array<std::uintptr_t,14>definitions{};std::array<std::optional<std::int64_t>,2>phase_vars{};bool entered=false,cleanup_known=true;
 friend bool operator==(const SupermanHealthNumeric267V1&,const SupermanHealthNumeric267V1&)=default;
};
struct SupermanHealthRaw267V1{
 SupermanHealthSource267V1 source;SupermanHealthNumeric267V1 numeric;LetterRaw267V1 manager_census;std::vector<LetterRaw267V1>events;
 std::optional<std::size_t>chosen;bool cleanup_known=true,native_read_entered=false;
 friend bool operator==(const SupermanHealthRaw267V1&,const SupermanHealthRaw267V1&)=default;
};
bool VerifySupermanHealthImage267V1(std::uintptr_t)noexcept;
bool ReadSupermanHealthRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const SupermanHealthScene267V1&,std::uint64_t,SupermanHealthPhase267V1,SupermanHealthRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 ChooseKnownSupermanHealthRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const SupermanHealthScene267V1&,std::uint64_t,const SupermanHealthRaw267V1&)noexcept;
}
