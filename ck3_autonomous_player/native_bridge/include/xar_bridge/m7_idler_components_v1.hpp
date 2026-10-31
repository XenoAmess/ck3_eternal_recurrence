#pragma once
#include <cstdint>
namespace xar::ck3_12004::m7_idler {
using Address = std::uint64_t;
// Caller supplies exact-width storage. No process attachment or native availability.
struct Memory {
    virtual ~Memory() = default;
    virtual Address read_pointer(Address address) = 0;
    virtual std::int32_t read_i32(Address address) = 0;
    virtual void write_i32(Address address, std::int32_t value) = 0;
    virtual void write_i64(Address address, std::uint64_t value) = 0;
};
struct DispatchCalls {
    virtual ~DispatchCalls() = default;
    virtual void virtual_slot10(Address receiver, Address event_address) = 0;
    virtual std::int32_t find_event_bucket(Address registry_address, std::int32_t copied_event_type) = 0;
    // Opaque original target 0x42207F8. If the supplied callback returns, dispatch throws.
    virtual void on_null_listener(Address native_call_target_rva) = 0;
};
void dispatch(Address holder, Address event_address, Memory& memory, DispatchCalls& calls);
struct Symbols {
    virtual ~Symbols() = default;
    virtual Address address(Address rva) = 0;
};
struct Descriptor { Address data; std::int32_t length; std::uint8_t flag; };
struct ConstructionCalls {
    virtual ~ConstructionCalls() = default;
    virtual Address allocate(std::uint64_t size) = 0;
    virtual Address construct_child(Address storage, Address fresh_h, std::int32_t zero) = 0;
    virtual Address get_registry(Address architectural_rcx) = 0;
    virtual Address find_name(Address registry, Descriptor known_descriptor_fields) = 0;
    virtual void virtual30(Address receiver, Address lookup_result, Address saved_o50) = 0;
};
Address construct(Address object, Address input_h, Address input_k,
                  Memory& memory, Symbols& symbols, ConstructionCalls& calls);
} // namespace xar::ck3_12004::m7_idler
