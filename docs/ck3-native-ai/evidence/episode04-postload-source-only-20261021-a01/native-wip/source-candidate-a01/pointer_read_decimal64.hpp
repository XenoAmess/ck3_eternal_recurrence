#pragma once
#include <cstdint>
#include <ostream>
#include <string>

// This serializer belongs only to the new pointer-read mode. Old execution
// producers keep their exact original serializer and qualification boundary.
struct PointerU64Json {
 std::uint64_t value;
 explicit PointerU64Json(std::uint64_t input):value(input){}
};
inline std::ostream& operator<<(std::ostream& out,PointerU64Json value){
 return out<<'"'<<std::to_string(value.value)<<'"';
}
struct PointerS64Json {
 std::int64_t value;
 explicit PointerS64Json(std::int64_t input):value(input){}
};
inline std::ostream& operator<<(std::ostream& out,PointerS64Json value){
 return out<<'"'<<std::to_string(value.value)<<'"';
}
