#include "xar_bridge/m7_idler_components_v1.hpp"
#include <bit>
#include <stdexcept>
namespace xar::ck3_12004::m7_idler {
void dispatch(Address holder, Address event_address, Memory& memory, DispatchCalls& calls) {
    // 1. Process H+8 callback
    Address h8 = memory.read_pointer(holder + 8);
    if (h8 != 0) {
        calls.virtual_slot10(h8, event_address);
    }

    // 2. Process H+10 callback
    Address h10 = memory.read_pointer(holder + 0x10);
    if (h10 != 0) {
        calls.virtual_slot10(h10, event_address);
    }

    // 3. Read event type and lookup bucket
    std::int32_t event_type = memory.read_i32(event_address);
    std::int32_t bucket_index = calls.find_event_bucket(holder + 0x30, event_type);

    if (bucket_index < 0) {
        return;
    }

    // 4. Compute entry address
    // Fresh read of H+0x30 after lookup, as per ASM c2029f
    Address base = memory.read_pointer(holder + 0x30);

    // Pointer/entry math unsignedAddress modulo64bits; negativecursor signextend usingint64 before72stride
    // bucket_index is signed int32. We convert to int64 for sign extension before multiplying by 72.
    std::int64_t signed_bucket = static_cast<std::int64_t>(bucket_index);
    std::int64_t stride = 72;
    std::int64_t offset = signed_bucket * stride;

    // Conversion to Address is modular (no invalid C++ pointer cast)
    Address entry = static_cast<Address>(static_cast<std::uint64_t>(base) + static_cast<std::uint64_t>(offset));

    // 5. Initialize entry fields
    // memory.writeInt32(entry + 0x40, 0);
    memory.write_i32(entry + 0x40, 0);

    // int count = memory.readInt32(entry + 0x34);
    std::int32_t count = memory.read_i32(entry + 0x34);

    // memory.writeInt32(entry + 0x44, count);
    memory.write_i32(entry + 0x44, count);

    if (count <= 0) {
        // memory.writeInt64(entry + 0x40, 0L);
        memory.write_i64(entry + 0x40, 0ULL);
        return;
    }

    // 6. Loop over listeners
    // int cursor = 0;
    std::int32_t cursor = 0;

    while (true) {
        // long listeners = memory.readPointer(entry + 0x28);
        Address listeners = memory.read_pointer(entry + 0x28);

        // long listenerAddr = listeners + 72L * cursor + 0x40;
        // cursor is signed int32. Sign extend to int64 before stride.
        std::int64_t signed_cursor = static_cast<std::int64_t>(cursor);
        std::int64_t listener_offset = signed_cursor * 72 + 0x40;
        Address listener_addr = static_cast<Address>(static_cast<std::uint64_t>(listeners) + static_cast<std::uint64_t>(listener_offset));

        // long receiver = memory.readPointer(listenerAddr);
        Address receiver = memory.read_pointer(listener_addr);

        if (receiver == 0) {
            // calls.onNullListener(0x42207F8L);
            calls.on_null_listener(0x42207F8ULL);
            // throw new IllegalStateException("Null listener terminal path");
            throw std::runtime_error("Null listener terminal path");
        }

        // calls.virtualSlot10(receiver, eventAddress);
        calls.virtual_slot10(receiver, event_address);

        // Reload cursor and limit after callback
        // int currentCursor = memory.readInt32(entry + 0x40);
        std::int32_t current_cursor = memory.read_i32(entry + 0x40);

        // int newCursor = currentCursor + 1;
        // Use std::uint32_t addition + std::bit_cast<std::int32_t> for wrap; C++ signed overflow is UB
        std::uint32_t u_cursor = static_cast<std::uint32_t>(current_cursor);
        std::uint32_t u_new_cursor = u_cursor + 1u;
        std::int32_t new_cursor = std::bit_cast<std::int32_t>(u_new_cursor);

        // memory.writeInt32(entry + 0x40, newCursor);
        memory.write_i32(entry + 0x40, new_cursor);

        // int limit = memory.readInt32(entry + 0x44);
        std::int32_t limit = memory.read_i32(entry + 0x44);

        // if (newCursor >= limit) break;
        // Signed compare
        if (new_cursor >= limit) {
            break;
        }

        // cursor = newCursor;
        cursor = new_cursor;
    }

    // 7. Clear cursor and limit
    // memory.writeInt64(entry + 0x40, 0L);
    memory.write_i64(entry + 0x40, 0ULL);
}
Address construct(Address object, Address input_h, Address input_k, Memory& memory, Symbols& symbols, ConstructionCalls& calls) {
    Address O = object;
    Address A = input_h;
    Address K = input_k;

    // Initial stores to O
    Address rax = symbols.address(0x44bc418L);
    memory.write_i64(O + 0L, rax);

    Address rsi = 0L;
    memory.write_i64(O + 8L, rsi);
    memory.write_i64(O + 0x10L, rsi);

    rax = symbols.address(0x54df888L);
    memory.write_i64(O + 0x18L, rax);

    memory.write_i64(O + 0x20L, A);

    memory.write_i64(O + 0x28L, rsi);
    memory.write_i64(O + 0x30L, rsi);
    memory.write_i64(O + 0x38L, rsi);
    memory.write_i64(O + 0x40L, rsi);

    rax = symbols.address(0x54df890L);
    memory.write_i64(O + 0x48L, rax);

    // First allocation (size 8)
    Address rcx = 8L;
    Address p8 = calls.allocate(rcx);

    rcx = symbols.address(0x44bc3f0L);
    memory.write_i64(p8 + 0L, rcx);

    memory.write_i64(O + 0x50L, p8);
    memory.write_i64(O + 0x58L, rsi);
    memory.write_i64(O + 0x60L, rsi);

    rax = symbols.address(0x54df760L);
    memory.write_i64(O + 0x68L, rax);

    memory.write_i64(O + 0x70L, rsi);
    memory.write_i64(O + 0x78L, rsi);
    memory.write_i64(O + 0x80L, rax);
    memory.write_i64(O + 0x88L, rsi);
    memory.write_i64(O + 0x90L, K);

    // Second allocation (size 0xB0) for P1
    rcx = 0xB0L;
    Address p1 = calls.allocate(rcx);

    // Construct child using fresh O+0x20
    int r8 = 0;
    Address rdx = memory.read_pointer(O + 0x20L);
    rcx = p1;
    Address s1 = calls.construct_child(rcx, rdx, r8);

    memory.write_i64(O + 0x28L, s1);

    // Third allocation (size 0xB0) for P2
    rcx = 0xB0L;
    Address p2 = calls.allocate(rcx);

    // Populate P2 fields
    rcx = memory.read_pointer(O + 0x20L);
    memory.write_i64(p2 + 0L, rcx);
    memory.write_i64(p2 + 8L, rsi);
    memory.write_i64(p2 + 0x10L, rsi);

    rcx = symbols.address(0x54e0928L);
    memory.write_i64(p2 + 0x18L, rcx);
    memory.write_i64(p2 + 0x20L, rsi);
    memory.write_i64(p2 + 0x28L, rsi);
    memory.write_i64(p2 + 0x30L, rcx);
    memory.write_i64(p2 + 0x38L, rsi);
    memory.write_i64(p2 + 0x40L, rsi);
    memory.write_i64(p2 + 0x48L, rcx);
    memory.write_i64(p2 + 0x50L, rsi);
    memory.write_i64(p2 + 0x58L, rsi);

    rcx = symbols.address(0x54e0930L);
    memory.write_i64(p2 + 0x60L, rcx);
    memory.write_i64(p2 + 0x68L, rsi);
    memory.write_i64(p2 + 0x70L, rsi);

    rcx = symbols.address(0x54e0938L);
    memory.write_i64(p2 + 0x78L, rcx);
    memory.write_i64(p2 + 0x80L, rsi);
    memory.write_i64(p2 + 0x88L, rsi);

    rcx = symbols.address(0x54e0940L);
    memory.write_i64(p2 + 0x90L, rcx);
    memory.write_i64(p2 + 0x98L, rsi);
    memory.write_i64(p2 + 0xa0L, rsi);

    rcx = symbols.address(0x54e0948L);
    memory.write_i64(p2 + 0xa8L, rcx);

    memory.write_i64(O + 0x30L, p2);

    // Save O50 before get_registry
    Address savedO50 = memory.read_pointer(O + 0x50L);

    // Get registry
    Address registryRcx = symbols.address(0x54e0948L);
    Address r1 = calls.get_registry(registryRcx);

    // Prepare descriptor for find_name
    Address rcx_desc = symbols.address(0x5434f38L);
    Address capacity = memory.read_pointer(symbols.address(0x5434f50L));
    Address loadedVal = memory.read_pointer(symbols.address(0x5434f38L));

    // Unsigned comparison for capacity >= 16
    if (capacity >= 16ULL) {
        rcx_desc = loadedVal;
    }

    Address descData = rcx_desc;
    std::int32_t descLength = memory.read_i32(symbols.address(0x5434f48L));
    std::uint8_t descFlag = 0;

    Descriptor knownDescriptorFields{descData, descLength, descFlag};

    // Find name
    Address r2 = calls.find_name(r1, knownDescriptorFields);

    // Check global pointer
    Address g = memory.read_pointer(symbols.address(0x5cbf858L));
    if (g == 0L) {
        return O;
    }

    // Virtual call
    calls.virtual30(g, r2, savedO50);

    return O;
}
}
