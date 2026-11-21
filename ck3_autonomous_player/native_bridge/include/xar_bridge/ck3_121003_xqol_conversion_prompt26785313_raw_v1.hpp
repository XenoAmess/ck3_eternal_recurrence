#pragma once
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Internal source only. Existing generic CEventWindow primitive is reused;
// old letter owners, keys, schemas and effects are unchanged.
enum class XqolConversionChoice267V1{confirm,cancel};
inline constexpr char kXqolConversionDefinition267V1[]="xqol.100";
inline constexpr char kXqolConversionConfirm267V1[]="xqol_mass_conversion_event_confirm";
inline constexpr char kXqolConversionCancel267V1[]="xqol_mass_conversion_event_cancel";
struct XqolConversionRoot267V1{std::uintptr_t widget=0;bool visible=false,enabled=false;friend bool operator==(const XqolConversionRoot267V1&,const XqolConversionRoot267V1&)=default;};
struct XqolConversionScene267V1{LetterScene267V1 actual_owner;bool complete_named_root_census=false;std::vector<XqolConversionRoot267V1>roots;friend bool operator==(const XqolConversionScene267V1&,const XqolConversionScene267V1&)=default;};
struct XqolConversionPromptRaw267V1{LetterRaw267V1 census;std::vector<LetterRaw267V1>events;std::optional<std::size_t>known_event;bool confirm_admissible=false,cancel_admissible=false,native_read_entered=false,cleanup_known=true;friend bool operator==(const XqolConversionPromptRaw267V1&,const XqolConversionPromptRaw267V1&)=default;};
bool ReadXqolConversionPromptRaw267V1(const ReadonlyBindings&,const LetterBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,const XqolConversionScene267V1&,std::uint64_t,XqolConversionPromptRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 SelectXqolConversionPromptRaw267V1(const ReadonlyBindings&,const LetterBindings267V1&,const ck3_1210::CoreSnapshotPrefix&,const XqolConversionScene267V1&,std::uint64_t,const XqolConversionPromptRaw267V1&,XqolConversionChoice267V1)noexcept;
}
