#define NOMINMAX
#include <windows.h>
#include "Native201Api.hpp"
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <vector>
#include <utility>

namespace range9d201 {
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

struct Context {
    unsigned used = 0;
    bool failed = false;
    std::array<std::array<std::uint64_t, 4>, 3> calls{};
    std::uint64_t rax = 0;
};

thread_local Context* active = nullptr;
class ActiveContext {
    Context* previous_;
public:
    explicit ActiveContext(Context& context):previous_(active) {
        need(previous_==nullptr,"unexpected callback reentry");
        active=&context;
    }
    ~ActiveContext() { active=previous_; }
    ActiveContext(const ActiveContext&)=delete;
    ActiveContext& operator=(const ActiveContext&)=delete;
};

std::uint64_t __fastcall callback(std::uint64_t a, std::uint64_t b, std::uint64_t c, std::uint64_t d) noexcept {
    if (!active) return 0;
    if (active->used >= 3) { active->failed = true; return 0; }
    active->calls[active->used++] = {a, b, c, d};
    return 0;
}

void trampoline(std::uint8_t* where, std::uint64_t target) {
    const std::uint8_t prefix[] = {0x48, 0xB8};
    std::memcpy(where, prefix, 2);
    std::memcpy(where + 2, &target, 8);
    where[10] = 0xFF;
    where[11] = 0xE0;
}

bool page(const void* p, DWORD protection) {
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(p, &info, sizeof(info)) == sizeof(info) && info.State == MEM_COMMIT && info.Protect == protection;
}

std::string hex(std::uint64_t v) {
    std::ostringstream out;
    out << std::hex << v;
    return out.str();
}

std::string formatEvents(const Context& ctx) {
    std::string out;
    for (unsigned i = 0; i < ctx.used; ++i) {
        if (i == 0) {
            out += "first4(" + hex(ctx.calls[i][0]) + "," + hex(ctx.calls[i][1]) + "," + hex(ctx.calls[i][2]) + "," + hex(ctx.calls[i][3]) + ")";
        } else {
            out += "later2(" + hex(ctx.calls[i][0]) + "," + hex(ctx.calls[i][1]) + ")";
        }
    }
    return out;
}
}

Run executeOriginal(std::span<const std::uint8_t, RAW_BYTES> raw, std::span<const Case> cases) {
    static_assert(sizeof(void*) == 8);
    
    Allocation image(0x4221000, MEM_RESERVE, PAGE_NOACCESS);
    
    // Commit pages 0x9D0000 and 0x4220000
    need(VirtualAlloc(image.bytes() + 0x9D0000, 4096, MEM_COMMIT, PAGE_READWRITE) == image.bytes() + 0x9D0000, "commit 9D0000 failed");
    need(VirtualAlloc(image.bytes() + 0x4220000, 4096, MEM_COMMIT, PAGE_READWRITE) == image.bytes() + 0x4220000, "commit 4220000 failed");
    
    // Copy raw body to 0x9D0950
    std::memcpy(image.bytes() + 0x9D0950, raw.data(), RAW_BYTES);
    
    // Place trampoline at 0x4220AA4
    trampoline(image.bytes() + 0x4220AA4, reinterpret_cast<std::uint64_t>(&callback));
    
    // Protect pages
    DWORD previousProtection=0;
    need(VirtualProtect(image.bytes() + 0x9D0000, 4096, PAGE_EXECUTE_READ, &previousProtection) != 0, "protect 9D0000 failed");
    need(VirtualProtect(image.bytes() + 0x4220000, 4096, PAGE_EXECUTE_READ, &previousProtection) != 0, "protect 4220000 failed");
    
    need(FlushInstructionCache(GetCurrentProcess(), nullptr, 0) != 0, "FlushInstructionCache failed");
    need(std::memcmp(image.bytes() + 0x9D0950, raw.data(), RAW_BYTES) == 0, "raw mismatch");

    using Entry = std::uint64_t(__fastcall*)(std::uint64_t, std::uint64_t, std::uint64_t, std::uint64_t);
    const auto entry = reinterpret_cast<Entry>(image.bytes() + 0x9D0950);

    Run result{};
    result.rawUnchanged = true;
    result.protectionsFinal = true;
    result.mappingReleased = true;
    result.callbackGuard = true;

    for (const auto& item : cases) {
        Context ctx{};
        {
            ActiveContext context(ctx);
            ctx.rax = entry(item.begin, item.middle, item.end, item.entryR9);
        }
        
        result.callbackGuard = result.callbackGuard && !ctx.failed && ctx.used <= 3;
        need(result.callbackGuard, "callback guard failed");

        Row row{};
        row.id = item.id;
        row.rax = hex(ctx.rax);
        row.events = formatEvents(ctx);
        result.rows.push_back(std::move(row));

        result.rawUnchanged = result.rawUnchanged && std::memcmp(image.bytes() + 0x9D0950, raw.data(), RAW_BYTES) == 0;
        result.protectionsFinal = result.protectionsFinal && page(image.bytes() + 0x9D0000, PAGE_EXECUTE_READ) && page(image.bytes() + 0x4220000, PAGE_EXECUTE_READ);
    }

    need(result.rawUnchanged && result.protectionsFinal && result.callbackGuard,"raw/page/callback invariant failed");
    result.mappingReleased = image.release() && result.mappingReleased;
    return result;
}
}
