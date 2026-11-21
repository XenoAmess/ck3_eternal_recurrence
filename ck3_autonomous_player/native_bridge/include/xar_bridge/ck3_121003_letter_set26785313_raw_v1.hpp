#pragma once
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_letter_set26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct LetterSetRoot267V1{std::uintptr_t root=0;bool visible=false,enabled=false;friend bool operator==(const LetterSetRoot267V1&,const LetterSetRoot267V1&)=default;};
struct LetterSetScene267V1{LetterScene267V1 common{};std::vector<LetterSetRoot267V1>roots;friend bool operator==(const LetterSetScene267V1&,const LetterSetScene267V1&)=default;};
struct LetterSetRaw267V1{
 LetterSetSource267V1 source;LetterRaw267V1 manager_census;
 std::vector<LetterRaw267V1>letters;
 bool cleanup_known=true,native_read_entered=false;
 friend bool operator==(const LetterSetRaw267V1&,const LetterSetRaw267V1&)=default;
};
bool ReadLetterSetRaw267V1(const ReadonlyBindings&,const LetterBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,const LetterSetScene267V1&,std::uint64_t,LetterSetRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 ReplyKnownLetterSetRaw267V1(const ReadonlyBindings&,const LetterBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,const LetterSetScene267V1&,std::uint64_t,const LetterSetRaw267V1&,std::int32_t)noexcept;
}
