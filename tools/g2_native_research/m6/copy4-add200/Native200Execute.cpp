#define NOMINMAX
#include <windows.h>
#include <xmmintrin.h>
#include "Native200Api.hpp"
#include <cstring>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace copy4add200 {
namespace {
void need(bool ok,const char* reason) { if(!ok)throw std::runtime_error(reason); }
class Allocation {
    void* value_;
public:
    Allocation(SIZE_T bytes,DWORD mode,DWORD protect):value_(VirtualAlloc(nullptr,bytes,mode,protect)) { need(value_!=nullptr,"VirtualAlloc failed"); }
    ~Allocation() { if(value_)VirtualFree(value_,0,MEM_RELEASE); }
    Allocation(const Allocation&)=delete;
    Allocation& operator=(const Allocation&)=delete;
    std::uint8_t* bytes() const { return static_cast<std::uint8_t*>(value_); }
    bool release() { need(VirtualFree(value_,0,MEM_RELEASE)!=0,"VirtualFree failed");value_=nullptr;return true; }
};
class Mxcsr {
    unsigned saved_;
public:
    Mxcsr():saved_(_mm_getcsr()) { _mm_setcsr(saved_&~0x6000u); }
    ~Mxcsr() { _mm_setcsr(saved_); }
};
template<class T> T load(const std::uint8_t* p) { T value{};std::memcpy(&value,p,sizeof(value));return value; }
template<class T> void store(std::uint8_t* p,T value) { std::memcpy(p,&value,sizeof(value)); }
std::uint64_t address(const void* p) { return reinterpret_cast<std::uint64_t>(p); }
bool page(const void* p,DWORD protection) {
    MEMORY_BASIC_INFORMATION info{};
    return VirtualQuery(p,&info,sizeof(info))==sizeof(info) && info.State==MEM_COMMIT && info.Protect==protection;
}
enum class Kind { allocA,freeA,allocB,freeB,copy,range };
struct Captured { Kind kind{};std::array<std::uint64_t,4> args{}; };
struct Context {
    std::uint8_t* data{};int mutation{};unsigned copies{},used{};bool failed{};
    std::array<Captured,8> calls{};
    std::uint8_t* h() const { return data+0x100; }
    std::uint8_t* old() const { return data+0x300; }
    std::uint8_t* fresh() const { return data+0x500; }
    std::uint8_t* source() const { return data+0x700; }
    std::uint8_t* alternate() const { return data+0x900; }
    std::uint8_t* allocatorA() const { return data+0xB00; }
    std::uint8_t* vtableA() const { return data+0xB40; }
    std::uint8_t* allocatorB() const { return data+0xC00; }
    std::uint8_t* vtableB() const { return data+0xC40; }
    void add(Kind kind,std::uint64_t a,std::uint64_t b,std::uint64_t c,std::uint64_t d=0) noexcept {
        if(used>=calls.size()) { failed=true;return; }
        calls[used++]={kind,{a,b,c,d}};
    }
};
thread_local Context* active=nullptr;
std::uint64_t __fastcall allocA(std::uint64_t a,std::uint64_t b,std::uint64_t c,std::uint64_t d) noexcept {
    if(!active)return 0;active->add(Kind::allocA,a,b,c,d);return address(active->fresh());
}
std::uint64_t __fastcall allocB(std::uint64_t a,std::uint64_t b,std::uint64_t c,std::uint64_t d) noexcept {
    if(!active)return 0;active->add(Kind::allocB,a,b,c,d);return address(active->fresh());
}
void __fastcall freeA(std::uint64_t a,std::uint64_t b,std::uint64_t c) noexcept {
    if(active)active->add(Kind::freeA,a,b,c);
}
void __fastcall freeB(std::uint64_t a,std::uint64_t b,std::uint64_t c) noexcept {
    if(active)active->add(Kind::freeB,a,b,c);
}
void __fastcall copy(std::uint64_t a,std::uint64_t b,std::uint64_t c) noexcept {
    if(!active)return;auto& ctx=*active;ctx.add(Kind::copy,a,b,c);++ctx.copies;
    if(ctx.mutation==1 && ctx.copies==1) { store(ctx.h(),address(ctx.alternate()));store(ctx.h()+12,std::int32_t{4}); }
    if(ctx.mutation==2 && ctx.copies==2) {
        store(ctx.h(),address(ctx.alternate()));store(ctx.h()+12,std::int32_t{5});store(ctx.h()+16,address(ctx.allocatorB()));
    }
}
void __fastcall range(std::uint64_t a,std::uint64_t b,std::uint64_t c,std::uint64_t d) noexcept {
    if(active)active->add(Kind::range,a,b,c,d);
}
std::string pointerRole(const Context& ctx,std::uint64_t value) {
    if(value==0)return "NULL";
    if(value==address(ctx.allocatorA()))return "AA";
    if(value==address(ctx.allocatorB()))return "AB";
    const std::array<std::pair<const char*,std::uint64_t>,4> bases={{{"O",address(ctx.old())},{"N",address(ctx.fresh())},{"S",address(ctx.source())},{"ALT",address(ctx.alternate())}}};
    for(const auto& p:bases)if(value>=p.second && value-p.second<128)return std::string(p.first)+"+"+std::to_string(value-p.second);
    throw std::runtime_error("unqualified pointer role");
}
std::string bits(std::uint64_t value) { std::ostringstream out;out<<"0x"<<std::hex<<std::setw(16)<<std::setfill('0')<<value;return out.str(); }
void trampoline(std::uint8_t* where,std::uint64_t target) {
    const std::uint8_t prefix[]={0x48,0xB8};std::memcpy(where,prefix,2);store(where+2,target);where[10]=0xFF;where[11]=0xE0;
}
void protect(std::uint8_t* where,DWORD protection) {
    DWORD old=0;need(VirtualProtect(where,4096,protection,&old)!=0,"VirtualProtect failed");
}
}

Run executeOriginal(std::span<const std::uint8_t,RAW_BYTES> raw,std::span<const std::uint8_t,4> literal,std::span<const Case> cases) {
    static_assert(sizeof(void*)==8);
    Mxcsr rounding;
    Allocation image(0x49F7000,MEM_RESERVE,PAGE_NOACCESS);
    const std::array<std::size_t,4> pages={0xADD000,0x9D0000,0x4226000,0x49F6000};
    for(auto offset:pages)need(VirtualAlloc(image.bytes()+offset,4096,MEM_COMMIT,PAGE_READWRITE)==image.bytes()+offset,"commit image page failed");
    auto* body=image.bytes()+0xADD0D0;
    std::memcpy(body,raw.data(),raw.size());
    std::memcpy(image.bytes()+0x49F64F0,literal.data(),literal.size());
    trampoline(image.bytes()+0x4226860,reinterpret_cast<std::uint64_t>(&copy));
    trampoline(image.bytes()+0x9D0950,reinterpret_cast<std::uint64_t>(&range));
    for(std::size_t i=0;i<3;++i)protect(image.bytes()+pages[i],PAGE_EXECUTE_READ);
    protect(image.bytes()+pages[3],PAGE_READONLY);
    need(FlushInstructionCache(GetCurrentProcess(),nullptr,0)!=0,"FlushInstructionCache failed");
    need(std::memcmp(body,raw.data(),raw.size())==0,"original image mismatch");
    using Entry=void(__fastcall*)(std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t);
    const auto entry=reinterpret_cast<Entry>(body);
    Run result{};
    result.rawUnchanged=true;result.protectionsFinal=true;result.mappingReleased=true;
    result.callbackGuard=true;result.memoryGuard=true;
    for(const auto& item:cases) {
        Allocation data(4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
        std::memset(data.bytes(),0xA5,4096);
        Context ctx{};ctx.data=data.bytes();ctx.mutation=item.mutation;
        store(ctx.h(),item.oldNull?std::uint64_t{0}:address(ctx.old()));
        store(ctx.h()+8,item.capacity);store(ctx.h()+12,item.size);store(ctx.h()+16,address(ctx.allocatorA()));
        store(ctx.allocatorA(),address(ctx.vtableA()));store(ctx.allocatorB(),address(ctx.vtableB()));
        store(ctx.vtableA()+8,reinterpret_cast<std::uint64_t>(&allocA));
        store(ctx.vtableA()+16,reinterpret_cast<std::uint64_t>(&freeA));
        store(ctx.vtableB()+8,reinterpret_cast<std::uint64_t>(&allocB));
        store(ctx.vtableB()+16,reinterpret_cast<std::uint64_t>(&freeB));
        need(active==nullptr,"unexpected callback reentry");
        active=&ctx;
        entry(item.emptyNull?0:address(ctx.h()),static_cast<std::uint64_t>(static_cast<std::int64_t>(item.index)),
              item.emptyNull?0:address(ctx.source()),item.emptyNull?0:address(ctx.source())+static_cast<std::uint64_t>(item.count)*4);
        active=nullptr;
        result.callbackGuard=result.callbackGuard && !ctx.failed && ctx.used<=ctx.calls.size();
        need(result.callbackGuard,"callback capture overflow");
        Row row{};row.id=item.id;row.hasHeader=!item.emptyNull;
        if(row.hasHeader) {
            row.base=pointerRole(ctx,load<std::uint64_t>(ctx.h()));
            row.capacity=load<std::int32_t>(ctx.h()+8);row.size=load<std::int32_t>(ctx.h()+12);
            row.allocator=pointerRole(ctx,load<std::uint64_t>(ctx.h()+16));
        }
        for(unsigned c=0;c<ctx.used;++c) {
            const auto& captured=ctx.calls[c];Call call{};
            bool allocation=false,release=false,directCopy=false;
            switch(captured.kind) {
                case Kind::allocA:call.kind="a";call.target="TA";allocation=true;break;
                case Kind::allocB:call.kind="a";call.target="TB";allocation=true;break;
                case Kind::freeA:call.kind="f";call.target="FA";release=true;break;
                case Kind::freeB:call.kind="f";call.target="FB";release=true;break;
                case Kind::copy:call.kind="c";directCopy=true;break;
                case Kind::range:call.kind="r";break;
            }
            const unsigned count=allocation || captured.kind==Kind::range?4u:3u;
            for(unsigned i=0;i<count;++i) {
                const bool isPointer=allocation?(i==0 || i==3):(release || directCopy?i<2:true);
                call.args.push_back(isPointer?pointerRole(ctx,captured.args[i]):bits(captured.args[i]));
            }
            row.calls.push_back(std::move(call));
        }
        result.rows.push_back(std::move(row));
        for(std::size_t i=0xF0;i<0x100;++i)result.memoryGuard=result.memoryGuard && data.bytes()[i]==0xA5;
        for(std::size_t i=0x118;i<0x128;++i)result.memoryGuard=result.memoryGuard && data.bytes()[i]==0xA5;
        result.rawUnchanged=result.rawUnchanged && std::memcmp(body,raw.data(),raw.size())==0
            && std::memcmp(image.bytes()+0x49F64F0,literal.data(),literal.size())==0;
        for(std::size_t i=0;i<3;++i)result.protectionsFinal=result.protectionsFinal && page(image.bytes()+pages[i],PAGE_EXECUTE_READ);
        result.protectionsFinal=result.protectionsFinal && page(image.bytes()+pages[3],PAGE_READONLY) && page(data.bytes(),PAGE_READWRITE);
        need(result.rawUnchanged && result.protectionsFinal && result.memoryGuard,"raw/page/guard invariant failed");
        result.mappingReleased=data.release() && result.mappingReleased;
    }
    result.mappingReleased=image.release() && result.mappingReleased;
    return result;
}
}
