#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004::religion::relic_actions {
inline constexpr std::uint32_t absent=0xFFFFFFFFU;
// These values belong to the shared IngameUiOperationV1 cluster 100..103.
enum class Operation:std::uint32_t {select_artifact=100,set_slot=101,enshrine=102,remove=103};
constexpr std::string_view OperationName(Operation op) noexcept {
 switch(op){case Operation::select_artifact:return "select_relic_artifact";
 case Operation::set_slot:return "set_relic_slot";
 case Operation::enshrine:return "enshrine_relic";
 case Operation::remove:return "remove_relic";}return {};
}
constexpr bool IsOperation(std::uint32_t value) noexcept {return value>=100&&value<=103;}
struct Request {
 Operation operation=Operation::select_artifact;
 std::uint32_t holy_site_id=absent,artifact_id=absent;
 std::optional<std::uint32_t> slot_index;
 std::optional<bool> desired_selected;
 // Gameplay requests freeze the observed effective destination/replacement.
 // For remove, both are null, and frozen_preconditions is still required.
 bool frozen_preconditions=false;
 std::optional<std::uint32_t> expected_effective_slot_index,expected_replacing_artifact_id;
 std::string expected_preview_identity_sha256;
 bool operator==(const Request&)const=default;
};
constexpr bool ValidateRequest(const Request&r) noexcept {
 if(!IsOperation(static_cast<std::uint32_t>(r.operation))||r.holy_site_id==absent||
    (r.artifact_id==absent&&r.operation!=Operation::set_slot))return false;
 if(r.operation==Operation::set_slot)return r.artifact_id==absent&&r.slot_index&&
    *r.slot_index<4096&&r.desired_selected.has_value()&&!r.frozen_preconditions&&
    !r.expected_effective_slot_index&&!r.expected_replacing_artifact_id&&r.expected_preview_identity_sha256.empty();
 if(r.slot_index||r.desired_selected)return false;
 if(r.operation==Operation::select_artifact)return !r.frozen_preconditions&&
    !r.expected_effective_slot_index&&!r.expected_replacing_artifact_id&&r.expected_preview_identity_sha256.empty();
 if(!r.frozen_preconditions||r.expected_replacing_artifact_id==absent||r.expected_preview_identity_sha256.size()!=64)return false;
 for(const char c:r.expected_preview_identity_sha256)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;
 if(r.operation==Operation::enshrine)return r.expected_effective_slot_index&&*r.expected_effective_slot_index<4096;
 return !r.expected_effective_slot_index&&!r.expected_replacing_artifact_id;
}
}
