#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <string>
namespace xar::ck3_121003::build26785313 {
struct RiteTextValues267V1{std::array<std::byte,32>name_header{},description_header{};std::string name,description;std::uint8_t name_dirty=0,description_dirty=0;friend bool operator==(const RiteTextValues267V1&,const RiteTextValues267V1&)=default;};
// Internal typed data leaf only; fixed owner/actor/SourceRite admission is supplied separately.
bool ReadRiteTextValues267V1(const ReadonlyBindings&,std::uintptr_t,std::uint64_t,std::uint64_t,RiteTextValues267V1&,std::string&)noexcept;
}
