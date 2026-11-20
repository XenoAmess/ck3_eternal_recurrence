#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <string>
#include <array>
#include <vector>
namespace xar::ck3_121003::build26785313 {
// Bounded data-only primitive. It does not establish row/DoctrineItem provenance,
// evaluate a GUI expression, issue a token, or grant a public capability.
// A future owner caller must first obtain a const SDoctrineType* from an actual
// verified typed argument/Any and bind it to the same Core/Rite/query generation.
inline constexpr std::size_t kDoctrineKeyObservationMaxBytes267V1=256;
struct DoctrineInternalKey267V1 {
 std::uint32_t database_index=0xFFFFFFFFU;
 std::uint32_t stored_identifier_hash=0;
 std::string exact_bytes;
 friend bool operator==(const DoctrineInternalKey267V1&,const DoctrineInternalKey267V1&)=default;
};

inline constexpr std::size_t kRiteDoctrineItemsObservationMax267V1=256;
struct RiteDoctrineItemKey267V1 {
 std::uintptr_t item=0,doctrine=0;
 std::array<std::byte,0x48> exact_item_bytes{};
 DoctrineInternalKey267V1 key;
 friend bool operator==(const RiteDoctrineItemKey267V1&,const RiteDoctrineItemKey267V1&)=default;
};
// Private source custody only; native addresses are never serialized.
struct RiteDoctrineItems267V1 {
 std::uintptr_t controller=0,data=0;
 std::array<std::byte,16> exact_array_header{};
 std::vector<RiteDoctrineItemKey267V1> values;
 friend bool operator==(const RiteDoctrineItems267V1&,const RiteDoctrineItems267V1&)=default;
};
std::span<const ImagePin> RiteDoctrineItemsImagePins267V1() noexcept;
bool VerifyRiteDoctrineItemsImage267V1(std::uintptr_t) noexcept;
bool ReadRiteDoctrineItems267V1(const ReadonlyBindings&,std::uintptr_t,
 RiteDoctrineItems267V1&,std::string&) noexcept;
const RiteDoctrineItemKey267V1 *FindUniqueRiteDoctrineKey267V1(
 const RiteDoctrineItems267V1&,std::string_view) noexcept;

std::span<const ImagePin> DoctrineKeyImagePins267V1() noexcept;
bool VerifyDoctrineKeyImage267V1(std::uintptr_t) noexcept;
bool ReadSDoctrineInternalKey267V1(const ReadonlyBindings&,std::uintptr_t,
    DoctrineInternalKey267V1&,std::string&) noexcept;
}
