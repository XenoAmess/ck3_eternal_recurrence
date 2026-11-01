#define NOMINMAX
#include <windows.h>
#include <intrin.h>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <vector>
#include <utility>
#include "Native202Api.hpp"

namespace reverse4220aa4_202 {
namespace {
void need(bool ok, const char* reason) { if (!ok) throw std::runtime_error(reason); }

class Allocation {
    void* value_;
public:
    Allocation(SIZE_T bytes, DWORD mode, DWORD protect) : value_(VirtualAlloc(nullptr, bytes, mode, protect)) { need(value_ != nullptr, "VirtualAlloc failed"); }
    ~Allocation() { if (value_) VirtualFree(value_, 0, MEM_RELEASE); }
    Allocation(const Allocation&) = delete;
    Allocation& operator=(const Allocation&) = delete;
    std::uint8_t* bytes() const { return static_cast<std::uint8_t*>(value_); }
    bool release() { need(VirtualFree(value_, 0, MEM_RELEASE) != 0, "VirtualFree failed"); value_ = nullptr; return true; }
};

bool page(const void* p, DWORD protection) {
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(p, &info, sizeof(info)) == sizeof(info) && info.State == MEM_COMMIT && info.Protect == protection;
}

std::string hex(std::uint64_t v) {
    std::ostringstream out;
    out << std::hex << v;
    return out.str();
}

bool cpuEligible() {
    int info[4];
    __cpuidex(info, 0, 0);
    if (info[0] < 7) return false;
    __cpuidex(info, 1, 0);
    if (!(info[2] & (1 << 27))) return false; // OSXSAVE
    if (!(info[2] & (1 << 28))) return false; // AVX
    unsigned long long xgetbv = _xgetbv(0);
    if ((xgetbv & 0x6) != 0x6) return false; // OS support for AVX
    __cpuidex(info, 7, 0);
    if (!(info[1] & (1 << 5))) return false; // AVX2
    return true;
}

} // end anonymous namespace

Run executeOriginal(std::span<const std::uint8_t, REVERSE_BYTES> reverse, std::span<const std::uint8_t, CALLER_BYTES> caller, std::span<const Case> cases) {
    static_assert(sizeof(void*) == 8);
    
    Allocation image(0x5430000, MEM_RESERVE, PAGE_NOACCESS);
    
    need(VirtualAlloc(image.bytes() + 0x4220000, 4096, MEM_COMMIT, PAGE_READWRITE) == image.bytes() + 0x4220000, "commit 4220000 failed");
    need(VirtualAlloc(image.bytes() + 0x9D0000, 4096, MEM_COMMIT, PAGE_READWRITE) == image.bytes() + 0x9D0000, "commit 9D0000 failed");
    need(VirtualAlloc(image.bytes() + 0x542F000, 4096, MEM_COMMIT, PAGE_READWRITE) == image.bytes() + 0x542F000, "commit 542F000 failed");
    
    std::memcpy(image.bytes() + 0x4220AA4, reverse.data(), REVERSE_BYTES);
    std::memcpy(image.bytes() + 0x9D0950, caller.data(), CALLER_BYTES);
    
    DWORD prev;
    need(VirtualProtect(image.bytes() + 0x4220000, 4096, PAGE_EXECUTE_READ, &prev) != 0, "protect 4220000 failed");
    need(VirtualProtect(image.bytes() + 0x9D0000, 4096, PAGE_EXECUTE_READ, &prev) != 0, "protect 9D0000 failed");
    
    need(FlushInstructionCache(GetCurrentProcess(), nullptr, 0) != 0, "FlushInstructionCache failed");
    
    need(std::memcmp(image.bytes() + 0x4220AA4, reverse.data(), REVERSE_BYTES) == 0, "raw reverse mismatch");
    need(std::memcmp(image.bytes() + 0x9D0950, caller.data(), CALLER_BYTES) == 0, "raw caller mismatch");
    
    bool avx2Eligible = cpuEligible();
    
    Run result{};
    result.avx2Eligible = avx2Eligible;
    result.rawUnchanged = true;
    result.protectionsFinal = true;
    result.mappingReleased = true;
    result.memoryGuard = true;
    
    using Entry194 = std::uint64_t(__fastcall*)(std::uint64_t, std::uint64_t);
    using Entry126 = std::uint64_t(__fastcall*)(std::uint64_t, std::uint64_t, std::uint64_t, std::uint64_t);
    
    const auto entry194 = reinterpret_cast<Entry194>(image.bytes() + 0x4220AA4);
    const auto entry126 = reinterpret_cast<Entry126>(image.bytes() + 0x9D0950);
    
    for (const auto& c : cases) {
        
        bool skip = false;
        if (!avx2Eligible) {
            if (c.hasFeature && (c.featureWord & 0x20u)!=0 && c.words>=16) {
                skip = true;
            }
        }
        
        if (skip) {
            result.skipped.push_back(c.id);
            continue;
        }
        
        Allocation data(4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        
        std::uint64_t dataBegin = reinterpret_cast<std::uint64_t>(data.bytes() + 0x100);
        std::uint64_t dataEnd = dataBegin + c.words * 4;
        
        
        std::uint32_t* dwords = reinterpret_cast<std::uint32_t*>(data.bytes() + 0x100);
        for (unsigned i = 0; i < c.words; ++i) {
            dwords[i] = 0x80000010 + i;
        }
        std::uint32_t* left = reinterpret_cast<std::uint32_t*>(data.bytes() + 0x100 - 4);
        *left = 0x11223344;
        std::uint32_t* right = reinterpret_cast<std::uint32_t*>(data.bytes() + 0x100 + c.words * 4);
        *right = 0x55667788;
        
        
        if (c.hasFeature) {
            DWORD prevFeat;
            need(VirtualProtect(image.bytes() + 0x542F000, 4096, PAGE_READWRITE, &prevFeat) != 0, "protect feature RW failed");
            std::uint32_t* feat = reinterpret_cast<std::uint32_t*>(image.bytes() + 0x542F09C);
            *feat = c.featureWord;
            need(VirtualProtect(image.bytes() + 0x542F000, 4096, PAGE_READONLY, &prevFeat) != 0, "protect feature RO failed");
        } else {
            DWORD prevFeat;
            need(VirtualProtect(image.bytes() + 0x542F000, 4096, PAGE_NOACCESS, &prevFeat) != 0, "protect feature NOACCESS failed");
        }
        
        std::uint64_t rax = 0;
        if (c.whole) {
            std::uint64_t middle = dataBegin + c.splitWords * 4;
            std::uint64_t entryR9 = 0x77770000; // Frozen constant
            rax = entry126(dataBegin, middle, dataEnd, entryR9);
        } else {
            rax = entry194(dataBegin, dataEnd);
        }
        
        Row row{};
        row.id = c.id;
        row.raxHex = hex(rax);
        row.dataBaseHex = hex(dataBegin);
        
        std::uint32_t* finalDwords = reinterpret_cast<std::uint32_t*>(data.bytes() + 0x100);
        for (unsigned i = 0; i < c.words; ++i) {
            row.wordsHex.push_back(hex(finalDwords[i]));
        }
        
        result.rows.push_back(row);
        
        std::uint32_t* leftGuard = reinterpret_cast<std::uint32_t*>(data.bytes() + 0x100 - 4);
        if (*leftGuard != 0x11223344) result.memoryGuard = false;
        
        std::uint32_t* rightGuard = reinterpret_cast<std::uint32_t*>(data.bytes() + 0x100 + c.words * 4);
        if (*rightGuard != 0x55667788) result.memoryGuard = false;
        
        if (std::memcmp(image.bytes() + 0x4220AA4, reverse.data(), REVERSE_BYTES) != 0) result.rawUnchanged = false;
        if (std::memcmp(image.bytes() + 0x9D0950, caller.data(), CALLER_BYTES) != 0) result.rawUnchanged = false;
        
        if (!page(image.bytes() + 0x4220000, PAGE_EXECUTE_READ)) result.protectionsFinal = false;
        if (!page(image.bytes() + 0x9D0000, PAGE_EXECUTE_READ)) result.protectionsFinal = false;
        if (!page(image.bytes() + 0x542F000, c.hasFeature ? PAGE_READONLY : PAGE_NOACCESS)) result.protectionsFinal = false;
        if (!page(data.bytes(), PAGE_READWRITE)) result.protectionsFinal = false;
        
        result.mappingReleased = data.release() && result.mappingReleased;
    }
    
    need(result.rawUnchanged, "raw invariant failed");
    need(result.protectionsFinal, "protection invariant failed");
    need(result.memoryGuard, "memory guard failed");
    
    result.mappingReleased = image.release() && result.mappingReleased;
    
    return result;
}

} // end namespace reverse4220aa4_202
