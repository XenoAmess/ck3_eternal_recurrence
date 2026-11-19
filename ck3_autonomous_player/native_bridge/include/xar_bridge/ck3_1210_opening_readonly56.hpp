#pragma once
#include "xar_bridge/ck3_1210.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>
namespace xar::ck3_1210 {
inline constexpr char kOpeningScopeStep56[]="query-current-lifestyle-scope-26757580-v1";
inline constexpr char kOpeningScopeCapability56[]="game.query.current-lifestyle-scope.26757580.v1";
inline constexpr char kOpeningScopeSchema56[]="xar.ck3.lifestyle-scope.26757580.v1";
inline constexpr char kOpeningCurrentStep56[]="query-current-lifestyle-state-26757580-v1";
inline constexpr char kOpeningCurrentCapability56[]="game.query.current-lifestyle-state.26757580.v1";
inline constexpr char kOpeningCurrentSchema56[]="xar.ck3.lifestyle-current.26757580.v1";
enum class OpeningReadKind56 {government_scope,current_lifestyle};
using OpeningCopy56=bool(*)(void*,const void*,void*,std::size_t) noexcept;
using OpeningAdmission56=bool(*)(void*) noexcept;
using OpeningObjectGetter56=const void*(*)(const void*);
using OpeningNameGetter56=const void*(*)(std::int32_t);
using OpeningXpGetter56=std::int64_t*(*)(const void*,std::int64_t*,const void*,bool);
using OpeningPointsGetter56=std::int32_t(*)(const void*,const void*);
struct OpeningReadAccess56 {void *context=nullptr;OpeningCopy56 copy=nullptr;};
struct OpeningReadBindings56 {
 bool exact_build_admitted=false;
 bool integration_native_calls_permitted=false;
 CoreBindings core{};
 OpeningObjectGetter56 government=nullptr,focus=nullptr,lifestyle=nullptr;
 OpeningNameGetter56 identifier_name=nullptr;
 OpeningXpGetter56 xp=nullptr;
 OpeningPointsGetter56 points=nullptr,used=nullptr;
 void **government_fallback_slot=nullptr,**identifier_manager_slot=nullptr,**focus_fallback_slot=nullptr;
 const void *identifier_missing_string=nullptr;
 std::uintptr_t government_vtable=0,focus_vtable=0,lifestyle_vtable=0;
 OpeningAdmission56 native_call_admission=nullptr;
 void *native_call_admission_context=nullptr;
};
struct OpeningGovernment56 {
 std::string key;std::int32_t native_flag_count=0;std::vector<std::string> flags;
 friend bool operator==(const OpeningGovernment56&,const OpeningGovernment56&)=default;
};
struct OpeningLifestyle56 {
 std::string focus_key,lifestyle_key;
 std::int64_t xp_total_raw=0,xp_within_level_raw=0;
 std::int32_t xp_per_level=0,unspent_perk_points=0,used_perk_points=0;
 friend bool operator==(const OpeningLifestyle56&,const OpeningLifestyle56&)=default;
};
struct OpeningReadObservation56 {
 bool available=false;
 OpeningReadKind56 kind=OpeningReadKind56::government_scope;
 CoreSnapshotPrefix frame{};
 std::optional<OpeningGovernment56> government;
 std::optional<OpeningLifestyle56> lifestyle;
 std::size_t native_call_attempts=0;
 std::string_view unavailable_reason="opening_read_not_performed";
};
OpeningReadBindings56 BindOpeningReadImage56(std::uintptr_t,std::string_view) noexcept;
// No permission comes from the binding or wire. The trusted paused Actor frame
// supplies an admission callback. All native calls have pre/post admission and
// repeated source copies; failure retains call counts and clears all data.
bool ReadOpeningReadonly56(const OpeningReadBindings56&,const CoreSnapshotPrefix&,
 OpeningReadKind56,OpeningReadObservation56&,OpeningReadAccess56={}) noexcept;
}
