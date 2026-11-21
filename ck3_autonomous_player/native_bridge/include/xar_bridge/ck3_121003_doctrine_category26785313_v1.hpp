#pragma once
#include "xar_bridge/ck3_121003_doctrine_key26785313_v1.hpp"
#include <array>

namespace xar::ck3_121003::build26785313 {
inline constexpr std::string_view kDynasticMembershipGroupKey267V1="des_dynastic_membership";
struct CategoryLookupString267V1 {
 std::array<char,16> data{};std::uint64_t size=0,capacity=15;
};
static_assert(sizeof(CategoryLookupString267V1)==32);
struct DoctrineCategoryBindings267V1 {
 bool verified=false;std::uintptr_t image=0;
 using Helper=void*(__fastcall*)(void*,const CategoryLookupString267V1*);
 using Array=void*(__fastcall*)(void*,const void*);
 using Show=void(__fastcall*)(void*,std::int32_t);
 Helper get_helper=nullptr;Array get_category_array=nullptr;Show show_window=nullptr;
};
struct DynasticCategoryTarget267V1 {
 std::uintptr_t controller=0,helper=0,array_header=0,data=0,draft_data=0,item=0,doctrine=0,group=0;
 std::array<std::byte,16> exact_pointer_array_header{},exact_draft_array_header{};
 std::vector<std::uintptr_t> category_item_pointers;
 std::array<std::byte,0x48> exact_item{};
 std::int32_t slot=-1;
 DoctrineInternalKey267V1 doctrine_key,group_key;
 friend bool operator==(const DynasticCategoryTarget267V1&,const DynasticCategoryTarget267V1&)=default;
};
std::span<const ImagePin> DoctrineCategoryImagePins267V1() noexcept;
bool VerifyDoctrineCategoryImage267V1(std::uintptr_t) noexcept;
DoctrineCategoryBindings267V1 BindDoctrineCategoryImage267V1(std::uintptr_t,std::string_view sha) noexcept;
// DefaultOFF raw source custody only. Owner/Core/TLS/sourceRite/once admission is
// the future fixed executor's responsibility. This does not call ShowWindow.
bool ReadRawDynasticCategoryTarget267V1(const ReadonlyBindings&,
    std::uintptr_t current_Rite_controller,DynasticCategoryTarget267V1&,std::string&) noexcept;
// Direct current draft value-array reader. No original Game getter/effect is
// called. It does not claim helper/main_group pointer-array provenance; those
// output fields remain zero/empty. The fixed owner supplies Core/source authority.
bool ReadRawDynasticDraftTarget267V1(const ReadonlyBindings&,
    std::uintptr_t current_Rite_controller,DynasticCategoryTarget267V1&,std::string&) noexcept;
} // namespace xar::ck3_121003::build26785313
