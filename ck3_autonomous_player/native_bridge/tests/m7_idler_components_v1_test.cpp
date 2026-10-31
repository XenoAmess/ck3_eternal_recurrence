#include "xar_bridge/m7_idler_components_v1.hpp"
#include <bit>
#include <cstdint>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
namespace xar::ck3_12004::m7_idler::tests {
inline std::uint64_t checks = 0;
inline void check(bool condition,const std::string& message) {
    ++checks;
    if (!condition) throw std::runtime_error(message);
}
struct TestMemory final : Memory {
    std::unordered_map<Address,std::uint8_t> bytes;
    std::vector<Address> reads;
    Address read_pointer(Address a) override {
        reads.push_back(a);
        Address value=0;
        for (std::uint32_t i=0;i<8;++i)
            value|=static_cast<Address>(bytes[a+i])<<(8U*i);
        return value;
    }
    std::int32_t read_i32(Address a) override {
        reads.push_back(a);
        std::uint32_t value=0;
        for (std::uint32_t i=0;i<4;++i)
            value|=static_cast<std::uint32_t>(bytes[a+i])<<(8U*i);
        return std::bit_cast<std::int32_t>(value);
    }
    void write_i32(Address a,std::int32_t v) override {
        const auto bits=std::bit_cast<std::uint32_t>(v);
        for (std::uint32_t i=0;i<4;++i)
            bytes[a+i]=static_cast<std::uint8_t>(bits>>(8U*i));
    }
    void write_i64(Address a,std::uint64_t v) override {
        for (std::uint32_t i=0;i<8;++i)
            bytes[a+i]=static_cast<std::uint8_t>(v>>(8U*i));
    }
};
std::uint32_t dispatch_cases();
std::uint32_t construction_cases();
} // namespace xar::ck3_12004::m7_idler::tests


namespace xar::ck3_12004::m7_idler::tests {
std::uint32_t dispatch_cases() {
    using namespace xar::ck3_12004::m7_idler;
    struct Layout {
        Address holder, event, entryA, entryB, listA, listB;
        Address negativeCell, receiverA, receiverB;
    };
    const Layout l{0x1000, 0x2000, 0x3000, 0x4000, 0x5000,
                   0x6000, 0x7000, 0x8000, 0x9000};
    constexpr Address A_SENT = 0x1111111111111111ULL;
    constexpr Address B_SENT = 0x2222222222222222ULL;
    constexpr std::int32_t CURSOR_MAX =
        std::bit_cast<std::int32_t>(std::uint32_t{0x7FFFFFFFU});
    constexpr std::int32_t NEXT_CURSOR =
        std::bit_cast<std::int32_t>(std::uint32_t{0x80000000U});
    constexpr std::int32_t LIMIT_MIN_PLUS_ONE =
        std::bit_cast<std::int32_t>(std::uint32_t{0x80000001U});
    const std::int64_t negative_offset =
        static_cast<std::int64_t>(NEXT_CURSOR) * std::int64_t{72};
    const Address anchor = l.negativeCell - static_cast<Address>(negative_offset)
                           - Address{0x40};

    struct Calls final : DispatchCalls {
        std::function<void(Address, Address)> v1;
        std::function<std::int32_t(Address, std::int32_t)> find;
        std::function<void(Address)> null_cb;

        void virtual_slot10(Address receiver, Address event_address) override {
            check(static_cast<bool>(v1), "unexpected unconfigured virtual callback");
            v1(receiver, event_address);
        }
        std::int32_t find_event_bucket(Address registry, std::int32_t key) override {
            check(static_cast<bool>(find), "unexpected unconfigured lookup");
            return find(registry, key);
        }
        void on_null_listener(Address target_rva) override {
            check(static_cast<bool>(null_cb), "unexpected unconfigured terminal callback");
            null_cb(target_rva);
        }
    };
    struct TerminalMarker { };

    const auto seed = [&](TestMemory& memory) {
        memory.write_i64(l.holder + 8, 0);
        memory.write_i64(l.holder + 0x10, 0);
        memory.write_i64(l.holder + 0x30, l.entryA);
        memory.write_i32(l.event, std::int32_t{0x6EB});
        memory.write_i64(l.entryA + 0x28, l.listA);
        memory.write_i32(l.entryA + 0x34, 0);
        memory.write_i64(l.entryB + 0x28, l.listB);
        memory.write_i32(l.entryB + 0x34, 0);
        memory.write_i64(l.entryA + 0x40, A_SENT);
        memory.write_i64(l.entryB + 0x40, B_SENT);
        memory.write_i64(l.listA + 0x40, l.receiverA);
        memory.write_i64(l.listA + 0x88, l.receiverB);
        memory.write_i64(l.listB + 0x40, l.receiverA);
        memory.write_i64(l.listB + 0x88, l.receiverA);
    };

    for (std::uint32_t id = 0; id < 6U; ++id) {
        TestMemory memory;
        seed(memory);
        Calls calls;
        TerminalMarker marker;
        std::vector<Address> receivers;
        std::vector<Address> expected_receivers;
        if (id == 0U || id == 1U || id == 4U)
            expected_receivers = {l.receiverA, l.receiverB};
        std::vector<std::int32_t> lookup_keys;
        std::vector<std::int32_t> call_order;
        std::uint32_t lookup_count = 0;
        std::uint32_t terminal_count = 0;

        calls.find = [&](Address registry, std::int32_t key) -> std::int32_t {
            ++lookup_count;
            check(lookup_count == 1U, "dispatch must perform exactly one lookup");
            check(registry == l.holder + 0x30, "lookup registry is H+30");
            check(key == std::int32_t{0x6EB}, "lookup copies the fresh event DWORD");
            lookup_keys.push_back(key);
            call_order.push_back(2);
            if (id == 1U)
                memory.write_i64(l.holder + 0x30, l.entryB);
            return id == 0U ? std::int32_t{-7} : std::int32_t{0};
        };
        calls.v1 = [&](Address receiver, Address event_address) {
            check(event_address == l.event, "virtual callback receives event E");
            check(receivers.size() < 2U, "virtual callback upper bound is two");
            const auto index = receivers.size();
            check(index < expected_receivers.size(), "unexpected virtual callback");
            check(receiver == expected_receivers[index], "ordered virtual receiver");
            receivers.push_back(receiver);
            call_order.push_back(1);
            if (index == 0U && id == 0U) {
                memory.write_i64(l.holder + 0x10, l.receiverB);
                memory.write_i32(l.event, std::int32_t{0x6EB});
            } else if (index == 0U && id == 1U) {
                memory.write_i64(l.holder + 0x30, l.entryA);
                memory.write_i64(l.entryB + 0x28, l.listA);
            } else if (index == 0U && id == 4U) {
                memory.write_i64(l.holder + 0x30, l.entryB);
                memory.write_i32(l.entryA + 0x40, CURSOR_MAX);
                memory.write_i32(l.entryA + 0x44, LIMIT_MIN_PLUS_ONE);
                memory.write_i64(l.entryA + 0x28, anchor);
            }
        };
        calls.null_cb = [&](Address target_rva) {
            ++terminal_count;
            check(id == 5U, "unexpected terminal path");
            check(terminal_count == 1U, "one typed terminal callback");
            check(target_rva == Address{0x42207F8}, "typed terminal target");
            check(memory.read_i32(l.entryA + 0x40) == 0 &&
                  memory.read_i32(l.entryA + 0x44) == 1,
                  "terminal observes the uncleared cursor/limit pair");
            call_order.push_back(3);
            throw &marker;
        };

        if (id == 0U) {
            memory.write_i64(l.holder + 8, l.receiverA);
            memory.write_i64(l.holder + 0x10, l.receiverA);
            memory.write_i32(l.event, std::int32_t{0x601});
        } else if (id == 1U) {
            memory.write_i32(l.entryA + 0x34, 7);
            memory.write_i32(l.entryB + 0x34, 2);
        } else if (id == 3U) {
            memory.write_i32(l.entryA + 0x34, -7);
        } else if (id == 4U) {
            memory.write_i32(l.entryA + 0x34, 2);
            memory.write_i64(l.negativeCell, l.receiverB);
            check(anchor + static_cast<Address>(negative_offset) + Address{0x40}
                      == l.negativeCell,
                  "signed wrapped cursor reaches the exact negative cell");
        } else if (id == 5U) {
            memory.write_i32(l.entryA + 0x34, 1);
            memory.write_i64(l.listA + 0x40, 0);
        }

        if (id == 5U) {
            bool caught = false;
            try {
                xar::ck3_12004::m7_idler::dispatch(l.holder, l.event, memory, calls);
            } catch (TerminalMarker* actual) {
                check(actual == &marker, "catch only this case's marker pointer");
                caught = true;
            }
            check(caught, "typed terminal callback must propagate its marker");
            check(terminal_count == 1U, "one terminal was observed");
        } else {
            xar::ck3_12004::m7_idler::dispatch(l.holder, l.event, memory, calls);
            check(terminal_count == 0U, "normal cases have no terminal callback");
        }

        check(receivers == expected_receivers, "complete ordered receiver trace");
        check(lookup_count == 1U, "one completed lookup per case");
        check(lookup_keys == std::vector<std::int32_t>{0x6EB}, "complete lookup key trace");
        const std::vector<std::int32_t> expected_order =
            id == 0U ? std::vector<std::int32_t>{1, 1, 2} :
            (id == 1U || id == 4U) ? std::vector<std::int32_t>{2, 1, 1} :
            id == 5U ? std::vector<std::int32_t>{2, 3} :
                       std::vector<std::int32_t>{2};
        check(call_order == expected_order, "complete callback projection order");

        if (id == 0U) {
            check(memory.read_i32(l.entryA + 0x34) == 0 &&
                  memory.read_i32(l.entryB + 0x34) == 0, "id0 counts unchanged");
            check(memory.read_pointer(l.entryA + 0x40) == A_SENT &&
                  memory.read_pointer(l.entryB + 0x40) == B_SENT, "id0 sentinels unchanged");
            check(memory.read_pointer(l.holder + 0x10) == l.receiverB &&
                  memory.read_i32(l.event) == std::int32_t{0x6EB}, "id0 fresh forwards/event");
        } else if (id == 1U) {
            check(memory.read_pointer(l.entryA + 0x40) == A_SENT &&
                  memory.read_pointer(l.entryB + 0x40) == 0, "id1 held entry pair");
            check(memory.read_pointer(l.holder + 0x30) == l.entryA &&
                  memory.read_pointer(l.entryB + 0x28) == l.listA, "id1 fresh list pointer");
            check(memory.read_i32(l.entryA + 0x34) == 7 &&
                  memory.read_i32(l.entryB + 0x34) == 2, "id1 counts unchanged");
        } else if (id == 2U || id == 3U) {
            check(memory.read_pointer(l.entryA + 0x40) == 0 &&
                  memory.read_pointer(l.entryB + 0x40) == B_SENT, "nonpositive count pair/sentinel");
            check(memory.read_i32(l.entryA + 0x34) ==
                      (id == 2U ? std::int32_t{0} : std::int32_t{-7}),
                  "nonpositive count is unchanged");
        } else if (id == 4U) {
            check(memory.read_pointer(l.entryA + 0x40) == 0 &&
                  memory.read_pointer(l.entryB + 0x40) == B_SENT, "id4 final pair/sentinel");
            check(memory.read_pointer(l.holder + 0x30) == l.entryB &&
                  memory.read_pointer(l.entryA + 0x28) == anchor, "id4 post-A anchor change");
            check(memory.read_i32(l.entryA + 0x34) == 2 &&
                  memory.read_pointer(l.negativeCell) == l.receiverB, "id4 count/negative cell");
        } else {
            check(memory.read_i32(l.entryA + 0x40) == 0 &&
                  memory.read_i32(l.entryA + 0x44) == 1, "id5 pair remains uncleared");
            check(memory.read_i32(l.entryA + 0x34) == 1 &&
                  memory.read_pointer(l.entryB + 0x40) == B_SENT, "id5 count/sentinel");
        }
    }
    return 6U;
}

std::uint32_t construction_cases() {
    using namespace xar::ck3_12004::m7_idler;
    using namespace xar::ck3_12004::m7_idler::tests;

    const Address BASE = 0x10000000ULL;
    const Address OBJ = BASE + 0x0000ULL;
    const Address P8 = BASE + 0x1000ULL;
    const Address P1 = BASE + 0x2000ULL;
    const Address P2 = BASE + 0x3000ULL;
    const Address S1 = BASE + 0x4000ULL;
    const Address REG = BASE + 0x5000ULL;
    const Address LOOKUP = BASE + 0x6000ULL;
    const Address GLOBAL_RECV = BASE + 0x7000ULL;
    const Address INITIAL_H = BASE + 0x8000ULL;
    const Address CHANGED_O50 = BASE + 0x9000ULL;
    const Address OLD_STR = BASE + 0xA000ULL;
    const Address FRESH_STR = BASE + 0xB000ULL;
    const Address HELPER_H = BASE + 0xC000ULL;
    const Address HEADER_H = BASE + 0xD000ULL;
    const Address INPUT_K = BASE + 0xE000ULL;

    const std::uint64_t CAPACITIES[8] = {
        0ULL, 15ULL, 16ULL, 17ULL, 0x8000000000000000ULL,
        0xFFFFFFFFFFFFFFFFULL, 16ULL, 0ULL
    };
    const std::int32_t LENGTHS[8] = {
        0, 7, -1, std::numeric_limits<std::int32_t>::min(),
        std::numeric_limits<std::int32_t>::max(), -32, 23, -128
    };

    struct LocalSymbols final : Symbols {
        Address base;
        bool tracking = false;
        std::uint32_t phase = 0;

        explicit LocalSymbols(Address b) : base(b) {}

        Address address(Address rva) override {
            if (tracking) {
                if (rva == 0x5434F38ULL || rva == 0x5434F48ULL
                        || rva == 0x5434F50ULL) {
                    check(phase >= 1U, "descriptor symbol resolved before query");
                }
                if (rva == 0x5CBF858ULL) {
                    check(phase >= 2U, "global symbol resolved before findName");
                }
            }
            return base + rva;
        }
    };

    struct LocalCalls final : ConstructionCalls {
        std::function<Address(std::uint64_t)> alloc_fn;
        std::function<Address(Address, Address, std::int32_t)> child_fn;
        std::function<Address(Address)> reg_fn;
        std::function<Address(Address, Descriptor)> name_fn;
        std::function<void(Address, Address, Address)> virt_fn;

        Address allocate(std::uint64_t size) override { return alloc_fn(size); }
        Address construct_child(Address s, Address h, std::int32_t z) override {
            return child_fn(s, h, z);
        }
        Address get_registry(Address r) override { return reg_fn(r); }
        Address find_name(Address r, Descriptor d) override { return name_fn(r, d); }
        void virtual30(Address r, Address l, Address o) override { virt_fn(r, l, o); }
    };

    for (std::uint32_t case_id = 0; case_id < 8U; ++case_id) {
        TestMemory mem;
        LocalSymbols syms(BASE);
        LocalCalls calls;

        const bool mutate_before_helper = (case_id & 1U) != 0U;
        const bool mutate_before_header = (case_id & 2U) != 0U;
        const bool final_global_present = (case_id & 4U) != 0U;
        const bool alias_p8 = (case_id & 3U) == 0U;
        const Address small = alias_p8 ? OBJ + 0x20ULL : P8;
        // Cases 0/4 alias the first allocation to O+20: its vptr replaces INITIAL_H.
        const Address helper_h = mutate_before_helper ? HELPER_H
                : (alias_p8 ? syms.address(0x44BC3F0ULL) : INITIAL_H);
        const Address header_h = mutate_before_header ? HEADER_H : helper_h;
        const Address name_data = CAPACITIES[case_id] >= 16ULL
                ? FRESH_STR : syms.address(0x5434F38ULL);

        struct SeedRegion { Address start; std::uint64_t bytes; };
        const SeedRegion seed_regions[] = {
            {OBJ, 0x98ULL}, {P8, 8ULL}, {P1, 0xB0ULL}, {P2, 0xB0ULL},
            {S1, 16ULL}, {REG, 32ULL}, {LOOKUP, 16ULL}, {GLOBAL_RECV, 8ULL},
            {INITIAL_H, 8ULL}, {CHANGED_O50, 8ULL}, {OLD_STR, 64ULL},
            {FRESH_STR, 64ULL}, {HELPER_H, 8ULL}, {HEADER_H, 8ULL},
            {INPUT_K, 8ULL}
        };
        const std::uint8_t fill = static_cast<std::uint8_t>(0x31U + case_id);
        for (const SeedRegion& region : seed_regions) {
            for (std::uint64_t offset = 0; offset < region.bytes; ++offset) {
                mem.bytes[region.start + offset] = fill;
            }
        }
        // Opposite branch/value seeds make any pre-query cached read observable.
        mem.write_i64(syms.address(0x5434F38ULL), OLD_STR);
        mem.write_i32(syms.address(0x5434F48ULL),
                0x12345678 + static_cast<std::int32_t>(case_id));
        mem.write_i64(syms.address(0x5434F50ULL),
                CAPACITIES[case_id] >= 16ULL ? 0ULL : 16ULL);
        mem.write_i64(syms.address(0x5CBF858ULL),
                final_global_present ? 0ULL : GLOBAL_RECV);

        std::uint32_t alloc_count = 0;
        std::vector<std::string> events;

        calls.alloc_fn = [&](std::uint64_t size) -> Address {
            ++alloc_count;
            events.push_back("allocate");
            if (alloc_count == 1U) {
                check(size == 8ULL, "first alloc size");
                return small;
            }
            if (alloc_count == 2U) {
                check(size == 0xB0ULL, "second alloc size");
                if (mutate_before_helper) mem.write_i64(OBJ + 0x20ULL, HELPER_H);
                return P1;
            }
            if (alloc_count == 3U) {
                check(size == 0xB0ULL, "third alloc size");
                check(mem.read_pointer(OBJ + 0x20ULL) == helper_h,
                        "O20 before header alloc mutation");
                if (mutate_before_header) mem.write_i64(OBJ + 0x20ULL, HEADER_H);
                return P2;
            }
            throw std::runtime_error("unexpected alloc");
        };

        calls.child_fn = [&](Address storage, Address fresh_h, std::int32_t zero) -> Address {
            events.push_back("constructChild");
            check(storage == P1, "helper storage");
            check(fresh_h == helper_h, "helper fresh O20");
            check(zero == 0, "helper R8D zero");
            mem.write_i64(P1, fresh_h);
            mem.write_i64(P1 + 8ULL, 0x1122334455667700ULL + case_id);
            return S1;
        };

        calls.reg_fn = [&](Address architectural_rcx) -> Address {
            syms.phase = 1U;
            events.push_back("getRegistry");
            check(architectural_rcx == syms.address(0x54E0948ULL),
                    "registry query RCX");
            check(mem.read_pointer(OBJ + 0x50ULL) == small, "O50 before query");
            mem.write_i64(OBJ + 0x50ULL, CHANGED_O50);
            mem.write_i64(syms.address(0x5434F38ULL), FRESH_STR);
            mem.write_i32(syms.address(0x5434F48ULL), LENGTHS[case_id]);
            mem.write_i64(syms.address(0x5434F50ULL), CAPACITIES[case_id]);
            return REG;
        };

        calls.name_fn = [&](Address registry, Descriptor d) -> Address {
            syms.phase = 2U;
            events.push_back("findName");
            check(registry == REG, "lookup registry");
            check(d.data == name_data, "descriptor data");
            check(d.length == LENGTHS[case_id], "fresh descriptor length");
            check(d.flag == 0, "descriptor flag");
            mem.write_i64(syms.address(0x5CBF858ULL),
                    final_global_present ? GLOBAL_RECV : 0ULL);
            return LOOKUP;
        };

        calls.virt_fn = [&](Address receiver, Address lookup, Address saved_o50) {
            events.push_back("virtual30");
            check(final_global_present, "unexpected final virtual");
            check(receiver == GLOBAL_RECV, "fresh global receiver");
            check(lookup == LOOKUP, "lookup return");
            check(saved_o50 == small, "saved O50");
            check(mem.read_pointer(OBJ + 0x50ULL) == CHANGED_O50,
                    "query mutated O50");
        };

        mem.reads.clear();
        syms.tracking = true;
        const Address result = construct(OBJ, INITIAL_H, INPUT_K, mem, syms, calls);
        const std::vector<Address> construction_reads = mem.reads;
        syms.tracking = false;

        // Capture precedes all verification reads: inline selection still reads [5434F38].
        bool read_name_pointer = false;
        for (const Address read : construction_reads) {
            if (read == syms.address(0x5434F38ULL)) read_name_pointer = true;
        }
        check(read_name_pointer, "descriptor pointer read even for inline capacity");
        check(result == OBJ, "return O");
        check(alloc_count == 3U, "three allocations");
        const std::size_t expected_events = final_global_present ? 7U : 6U;
        check(events.size() == expected_events, "callback count");
        const char* order[] = {
            "allocate", "allocate", "constructChild", "allocate",
            "getRegistry", "findName", "virtual30"
        };
        for (std::size_t i = 0; i < expected_events; ++i) {
            check(events[i] == order[i], "callback order");
        }

        check(mem.read_pointer(OBJ) == syms.address(0x44BC418ULL), "O primary");
        check(mem.read_pointer(OBJ + 0x18ULL) == syms.address(0x54DF888ULL), "O18");
        check(mem.read_pointer(OBJ + 0x20ULL) == header_h, "final O20");
        check(mem.read_pointer(OBJ + 0x28ULL) == S1, "O28 child result");
        check(S1 != P1, "independent helper return");
        check(mem.read_pointer(OBJ + 0x30ULL) == P2, "O30 P2");
        check(mem.read_pointer(OBJ + 0x48ULL) == syms.address(0x54DF890ULL), "O48");
        check(mem.read_pointer(OBJ + 0x50ULL) == CHANGED_O50, "O50 changed");
        check(mem.read_pointer(OBJ + 0x68ULL) == syms.address(0x54DF760ULL), "O68");
        check(mem.read_pointer(OBJ + 0x80ULL) == syms.address(0x54DF760ULL), "O80");
        check(mem.read_pointer(OBJ + 0x88ULL) == 0ULL, "O88 zero");
        check(mem.read_pointer(OBJ + 0x90ULL) == INPUT_K, "O90 entry K");

        const std::uint64_t zero_offsets[] = {
            8ULL, 0x10ULL, 0x38ULL, 0x40ULL, 0x58ULL, 0x60ULL, 0x70ULL, 0x78ULL
        };
        for (const std::uint64_t off : zero_offsets) {
            check(mem.read_pointer(OBJ + off) == 0ULL, "O zero field");
        }

        check(mem.read_pointer(small) == syms.address(0x44BC3F0ULL), "P8 vptr");
        check(mem.read_pointer(P1) == helper_h, "P1 payload");
        check(mem.read_pointer(P1 + 8ULL) == 0x1122334455667700ULL + case_id,
                "P1 marker");

        const std::uint64_t header_words[22] = {
            header_h, 0ULL, 0ULL,
            syms.address(0x54E0928ULL), 0ULL, 0ULL,
            syms.address(0x54E0928ULL), 0ULL, 0ULL,
            syms.address(0x54E0928ULL), 0ULL, 0ULL,
            syms.address(0x54E0930ULL), 0ULL, 0ULL,
            syms.address(0x54E0938ULL), 0ULL, 0ULL,
            syms.address(0x54E0940ULL), 0ULL, 0ULL,
            syms.address(0x54E0948ULL)
        };
        for (std::uint64_t i = 0; i < 22ULL; ++i) {
            check(mem.read_pointer(P2 + i * 8ULL) == header_words[i], "P2 header word");
        }

        check(mem.read_pointer(syms.address(0x5434F50ULL)) == CAPACITIES[case_id],
                "capacity bits");
        check(mem.read_i32(syms.address(0x5434F48ULL)) == LENGTHS[case_id],
                "length bits");
        check(mem.read_pointer(syms.address(0x5CBF858ULL))
                == (final_global_present ? GLOBAL_RECV : 0ULL), "final global");
        check(mem.bytes[FRESH_STR] == fill, "owned fresh string unchanged");
    }

    return 8U;
}

}
int main() {
    using namespace xar::ck3_12004::m7_idler::tests;
    try {
        const auto dispatched = dispatch_cases();
        check(dispatched == 6U, "six existing dispatcher cases");
        std::cout << "PASS dispatch_cases=" << dispatched << "\n";
        const auto constructed = construction_cases();
        check(constructed == 8U, "eight existing construction cases");
        std::cout << "PASS cases=" << (dispatched + constructed)
                  << " dispatch=" << dispatched << " construction=" << constructed
                  << " checks=" << checks << "\n";
        return 0;
    } catch (const std::exception& failure) {
        std::cerr << "FAIL " << failure.what() << "\n";
        return 1;
    } catch (...) {
        std::cerr << "FAIL unexpected callback exception\n";
        return 2;
    }
}
