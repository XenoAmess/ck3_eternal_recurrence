#pragma once
#include "xar_bridge/ck3_12002_religion_context.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::religion::holy_site_creation {
inline constexpr std::string_view kQueryStep="query-player-holy-site-creation-context-v1";
inline constexpr std::string_view kDomainKey="player_holy_site_creation_context_v1";
using ReadMemory=bool(*)(void*,const void*,void*,std::size_t) noexcept;
using NativeEnabled=bool(__fastcall*)(void*);
using NativeCreate=void(__fastcall*)(void*);
using NativeTooltip=void*(__fastcall*)(void*,void*);
using NativeDestroyString=void(__fastcall*)(void*);
using NativeCanPick=bool(__fastcall*)(void*,const void*,void*);
using NativeRarity=std::int64_t*(__fastcall*)(void*,std::int64_t*);
using NativeSettings=void*(__fastcall*)();
using NativeSelect=void(__fastcall*)(void*,const void*);
using NativeAnyType=void*(__fastcall*)();
using NativeOpenView=void(__fastcall*)(void*,std::uint32_t,const void*);
struct Bindings {
 bool enabled=false;
 std::uintptr_t image_base=0;
 ReadMemory read_memory=nullptr;
 void*read_context=nullptr;
 NativeEnabled native_enabled=nullptr;
 NativeCreate native_create=nullptr;
 NativeTooltip create_tooltip=nullptr;
 NativeDestroyString destroy_string=nullptr;
 NativeCanPick can_pick_type=nullptr;
 NativeRarity rarity_sum=nullptr;
 NativeSettings requirements_settings=nullptr;
 NativeSelect select_type=nullptr,select_barony=nullptr,select_artifact=nullptr;
 NativeAnyType faith_any_type=nullptr;
 NativeOpenView open_view=nullptr;
};
struct TypeCandidate {
 std::string type_key;
 bool is_selected=false,native_can_pick_observed=false,native_can_pick=false;
 bool tooltip_available=false;
 std::string tooltip;
 // Borrowed only inside the admitted callback; never serialized.
 const void*native_type=nullptr;
};
struct Snapshot {
 bool available=false;
 std::string unavailable_reason;
 std::uint64_t capture_epoch=0;
 std::int32_t date_raw=0,played_character_id=-1;
 std::uint32_t player_faith_id=0xFFFFFFFFU;
 bool window_present=false,root_present=false,player_faith_matches=false;
 std::uint32_t window_faith_id=0xFFFFFFFFU;
 bool models_available=false,models_complete=false;
 std::vector<TypeCandidate> available_holy_site_types;
 std::vector<std::uint32_t> potential_barony_title_ids,enshrinable_artifact_ids;
 bool selection_available=false;
 std::optional<std::string> selected_type_key;
 std::optional<std::uint32_t> selected_barony_title_id;
 std::vector<std::uint32_t> selected_artifact_ids;
 bool native_rarity_sum_observed=false;
 std::int64_t native_rarity_sum_raw=0;
 bool native_enabled_observed=false,native_create_button_enabled=false;
 bool bypass_requirements_observed=false;
 std::uint8_t bypass_requirements_raw=0;
 bool create_tooltip_available=false;
 std::string create_tooltip;
 bool cached_resource_quote_available=false;
 std::array<std::int64_t,10> cached_resource_vector_raw{};
 // Bridge-computed SHA256 of observed native preview identity, not an engine hash.
 std::string preview_identity_sha256;
 // These identities cannot cross the public transport or survive this callback.
 const void*handler=nullptr,*window=nullptr,*root=nullptr,*gfx=nullptr;
};
enum class UiAction : std::uint32_t { open=14,select_type=15,select_barony=16,set_artifact=17 };
struct UiRequest {
 UiAction action=UiAction::open;
 std::string type_key;
 std::uint32_t object_id=0xFFFFFFFFU;
 bool selected=false;
};
Bindings BindImage12004(std::uintptr_t,std::string_view) noexcept;
// Existing paused owner mailbox supplies the actual player/frame. This does
// not manufacture a window, context, game command, or candidate collection.
bool ReadContext12004(const Bindings&,const void*handler,
 const ck3_12002::religion::Context&,Snapshot&) noexcept;
// UI-only selection helper; it never invokes the creation callback. It runs
// under the existing native UI owner/TLS/modal/revision guards. A returned
// attempted call remains ACK until a separate selected-state observation.
bool InvokeUi12004(const Bindings&,void*handler,
 const ck3_12002::religion::Context&,const UiRequest&,
 bool&attempted,bool&already_selected,std::string&failure) noexcept;
std::string SerializeContext12004(const Snapshot&);
std::string SerializeCommand12004(const Snapshot&,std::string_view request_id,
 std::uint64_t native_revision,std::int64_t date_raw);
}
