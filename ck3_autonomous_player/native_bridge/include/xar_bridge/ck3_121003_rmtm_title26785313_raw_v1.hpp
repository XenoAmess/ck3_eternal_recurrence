#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
// Internal candidate only. No wire, mailbox slot, capability or public selector.
// A future fixed owner reader must produce Frame from Owner/Read(core_only),
// exact ticket/context/TLS and the same connection. A caller boolean is no proof.
struct RmtmTitleRequest267V1 {
 ck3_1210::CoreSnapshotPrefix expected{};
 std::uint32_t expected_full_title_id=0xFFFFFFFFU; // guard DATA, not authority
 std::uint64_t deadline_unix_ms=0;
};
struct RmtmTitleFrame267V1 {
 ck3_1210::CoreSnapshotPrefix core{};
 std::uintptr_t game=0,jomini=0,storage=0,data=0,players=0,player=0,actor=0;
 // Private upstream Owner/Read frame, deliberately not a public request field.
 bool facts_verified=false;
};
struct RmtmTitleCharacter267V1 {
 std::uint32_t full_id=0xFFFFFFFFU;
 bool alive=false;
 friend bool operator==(const RmtmTitleCharacter267V1&,const RmtmTitleCharacter267V1&)=default;
};
struct RmtmTitleLaw267V1 {
 std::uint32_t native_definition_id=0xFFFFFFFFU;
 std::string key;
 friend bool operator==(const RmtmTitleLaw267V1&,const RmtmTitleLaw267V1&)=default;
};
struct RmtmTitleSource267V1 {
 std::uint32_t full_title_id=0xFFFFFFFFU;
 std::optional<RmtmTitleCharacter267V1> holder,engine_current_heir;
 std::vector<RmtmTitleLaw267V1> physical_own_laws;
 std::int32_t native_law_count=0,engine_successor_count=0;
 bool sampled_twice=false;
 // No effective-law, realm-law, script-witness or business PASS inference.
 friend bool operator==(const RmtmTitleSource267V1&,const RmtmTitleSource267V1&)=default;
};
struct RmtmTitleRaw267V1 {
 RmtmTitleSource267V1 source{};
 bool entered=false,cleanup_known=true;
};
bool VerifyRmtmTitleImage267V1(std::uintptr_t) noexcept;
bool ReadRmtmTitleRaw267V1(const ReadonlyBindings&,const RmtmTitleFrame267V1&,
 const RmtmTitleRequest267V1&,std::uint64_t original_monotonic_deadline_ms,
 RmtmTitleRaw267V1&,std::string&) noexcept;
}
