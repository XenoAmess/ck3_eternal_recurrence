#define NOMINMAX
#include <windows.h>
#include <xmmintrin.h>
#include <cstring>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>
#include "Native204Api.hpp"

namespace upper172knownadd204 {
namespace {
void need(bool condition,const char* reason) { if(!condition)throw std::runtime_error(reason); }
template<class T> T load(const std::uint8_t* p) { T value{};std::memcpy(&value,p,sizeof(value));return value; }
template<class T> void store(std::uint8_t* p,T value) { std::memcpy(p,&value,sizeof(value)); }
std::uint64_t address(const void* p) noexcept { return reinterpret_cast<std::uint64_t>(p); }
std::string hex(std::uint64_t value) { std::ostringstream out;out<<std::hex<<value;return out.str(); }
std::string bits(std::uint64_t value) { std::ostringstream out;out<<"0x"<<std::hex<<std::setw(16)<<std::setfill('0')<<value;return out.str(); }
class Allocation {
    void* value_;
public:
    Allocation(SIZE_T bytes,DWORD mode,DWORD protection):value_(VirtualAlloc(nullptr,bytes,mode,protection)) { need(value_!=nullptr,"VirtualAlloc failed"); }
    ~Allocation() { if(value_)VirtualFree(value_,0,MEM_RELEASE); }
    Allocation(const Allocation&)=delete;Allocation& operator=(const Allocation&)=delete;
    std::uint8_t* bytes() const { return static_cast<std::uint8_t*>(value_); }
    bool release() { need(VirtualFree(value_,0,MEM_RELEASE)!=0,"VirtualFree failed");value_=nullptr;return true; }
};
class Mxcsr {
    unsigned saved_;
public:
    Mxcsr():saved_(_mm_getcsr()) { _mm_setcsr(saved_&~0x6000u); }
    ~Mxcsr() { _mm_setcsr(saved_); }
};
void protect(std::uint8_t* p,DWORD protection) { DWORD previous=0;need(VirtualProtect(p,4096,protection,&previous)!=0,"VirtualProtect failed"); }
bool page(const void* p,DWORD protection) { MEMORY_BASIC_INFORMATION info{};return VirtualQuery(p,&info,sizeof(info))==sizeof(info) && info.State==MEM_COMMIT && info.Protect==protection; }
bool reserved(const void* p) { MEMORY_BASIC_INFORMATION info{};return VirtualQuery(p,&info,sizeof(info))==sizeof(info) && info.State==MEM_RESERVE; }
enum class Kind { allocate,copy,release };
struct RawHeader { std::uint64_t base{};std::int32_t capacity{},size{};std::uint64_t allocator{}; };
RawHeader rawHeader(const std::uint8_t* p) noexcept { return {load<std::uint64_t>(p),load<std::int32_t>(p+8),load<std::int32_t>(p+12),load<std::uint64_t>(p+16)}; }
struct Captured { Kind kind{};std::array<std::uint64_t,4> args{}; };
struct Context {
    std::uint8_t* data{};std::uint64_t imageBase{};bool failed{},releaseTaken{};unsigned used{};
    RawHeader beforeRelease{};std::array<Captured,8> captured{};
    std::uint8_t* destination() const noexcept { return data+0x100; }
    std::uint8_t* fresh() const noexcept { return data+0x400; }
    std::uint8_t* source4() const noexcept { return data+0x500; }
    std::uint8_t* vtable() const noexcept { return data+0xB00; }
    std::uint64_t allocator4() const noexcept { return imageBase+0x54de268; }
    void add(Kind kind,std::uint64_t a,std::uint64_t b,std::uint64_t c,std::uint64_t d=0) noexcept {
        if(used>=captured.size()) { failed=true;return; }captured[used++]={kind,{a,b,c,d}};
    }
};
thread_local Context* active=nullptr;
thread_local bool orphan=false;
class Activation {
public:
    explicit Activation(Context& context) { need(active==nullptr,"callback reentry");orphan=false;active=&context; }
    ~Activation() { active=nullptr; }
    Activation(const Activation&)=delete;Activation& operator=(const Activation&)=delete;
};
std::uint64_t __fastcall allocatePort(std::uint64_t rcx,std::uint64_t bytes,std::uint64_t alignment,std::uint64_t end) noexcept {
    if(!active) { orphan=true;return 0; }auto& context=*active;context.add(Kind::allocate,rcx,bytes,alignment,end);
    if(rcx!=context.allocator4() || bytes!=8 || alignment!=4 || end!=address(context.source4())+8)context.failed=true;
    return address(context.fresh());
}
void __fastcall copyPort(std::uint64_t destination,std::uint64_t source,std::uint64_t bytes) noexcept {
    if(!active) { orphan=true;return; }active->add(Kind::copy,destination,source,bytes);
    // The old Java200 SCRIPT port records arguments only, including zero-byte/null calls.
}
void __fastcall releasePort(std::uint64_t rcx,std::uint64_t oldBase,std::uint64_t alignment) noexcept {
    if(!active) { orphan=true;return; }auto& context=*active;context.add(Kind::release,rcx,oldBase,alignment);
    if(rcx!=context.allocator4() || oldBase!=0 || alignment!=4 || context.releaseTaken)context.failed=true;
    context.beforeRelease=rawHeader(context.destination()+0x28);context.releaseTaken=true;
}
std::string role(const Context& context,std::uint64_t pointer) {
    if(pointer==0)return "NULL";if(pointer==context.allocator4())return "ALLOC4";
    const std::array<std::pair<const char*,std::uint64_t>,2> bases={{{"N",address(context.fresh())},{"S",address(context.source4())}}};
    for(const auto& base:bases)if(pointer>=base.second && pointer-base.second<128)return std::string(base.first)+"+"+std::to_string(pointer-base.second);
    throw std::runtime_error("unqualified pointer role");
}
Header header(const Context& context,const RawHeader& raw) { return {role(context,raw.base),raw.capacity,raw.size,hex(raw.allocator-context.imageBase)}; }
Call call(const Context& context,const Captured& captured) {
    Call result{};const auto& args=captured.args;
    if(captured.kind==Kind::allocate) { result.kind="a";result.target="TA";result.args={role(context,args[0]),bits(args[1]),bits(args[2]),role(context,args[3])}; }
    else if(captured.kind==Kind::copy) { result.kind="c";result.args={role(context,args[0]),role(context,args[1]),bits(args[2])}; }
    else { result.kind="f";result.target="FA";result.args={role(context,args[0]),role(context,args[1]),bits(args[2])}; }
    return result;
}
}

Run executeOriginal(std::span<const std::uint8_t,UPPER_BYTES> upper,std::span<const std::uint8_t,RANGE_BYTES> range,std::span<const std::uint8_t,ADD_BYTES> add,std::span<const std::uint8_t,4> literal,std::span<const Case> cases) {
    static_assert(sizeof(void*)==8);need(cases.size()<=2,"only two frozen cases");Mxcsr rounding;
    Allocation image(0x54df000,MEM_RESERVE,PAGE_NOACCESS);
    const std::array<std::size_t,6> pages={0x3729000,0x8c7000,0xadd000,0x4226000,0x49f6000,0x54de000};
    for(auto offset:pages)need(VirtualAlloc(image.bytes()+offset,4096,MEM_COMMIT,PAGE_READWRITE)==image.bytes()+offset,"commit image page failed");
    std::memcpy(image.bytes()+0x37297f0,upper.data(),upper.size());std::memcpy(image.bytes()+0x8c70b0,range.data(),range.size());
    std::memcpy(image.bytes()+0xadd0d0,add.data(),add.size());std::memcpy(image.bytes()+0x49f64f0,literal.data(),literal.size());
    auto* trampoline=image.bytes()+0x4226860;trampoline[0]=0x48;trampoline[1]=0xB8;store(trampoline+2,reinterpret_cast<std::uint64_t>(&copyPort));trampoline[10]=0xFF;trampoline[11]=0xE0;
    for(std::size_t i=0;i<4;++i)protect(image.bytes()+pages[i],PAGE_EXECUTE_READ);protect(image.bytes()+pages[4],PAGE_READONLY);
    need(FlushInstructionCache(GetCurrentProcess(),nullptr,0)!=0,"FlushInstructionCache failed");
    const auto originalUnchanged=[&]() { return std::memcmp(image.bytes()+0x37297f0,upper.data(),upper.size())==0 && std::memcmp(image.bytes()+0x8c70b0,range.data(),range.size())==0 && std::memcmp(image.bytes()+0xadd0d0,add.data(),add.size())==0 && std::memcmp(image.bytes()+0x49f64f0,literal.data(),literal.size())==0; };
    need(originalUnchanged(),"initial raw mismatch");
    using Entry=std::uint64_t(__fastcall*)(std::uint64_t,std::uint64_t);const auto entry=reinterpret_cast<Entry>(image.bytes()+0x37297f0);
    Run result{};result.rawUnchanged=true;result.protectionsFinal=true;result.mappingReleased=true;result.callbackGuard=true;result.memoryGuard=true;result.forbiddenTargetsUnmapped=true;
    for(const auto& item:cases) {
        Allocation data(4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);std::memset(data.bytes(),0xA5,4096);
        Context context{};context.data=data.bytes();context.imageBase=address(image.bytes());auto* destination=context.destination();auto* source=item.sameObject?destination:data.bytes()+0x200;
        store(source+8,std::uint32_t{0x81234567});store(source+0x10,std::uint64_t{0xb000});store(source+0x1c,std::int32_t{0});
        store(source+0x28,address(context.source4()));store(source+0x34,std::int32_t{2});store(source+0x40,std::uint32_t{0x76543210});store(source+0x44,std::uint8_t{0xa5});
        for(unsigned i=0;i<4;++i)destination[0x45+i]=static_cast<std::uint8_t>(0xC5u+i);
        store(context.vtable()+8,reinterpret_cast<std::uint64_t>(&allocatePort));store(context.vtable()+16,reinterpret_cast<std::uint64_t>(&releasePort));
        protect(image.bytes()+pages[5],PAGE_READWRITE);store(image.bytes()+0x54de260,std::uint64_t{0});store(image.bytes()+0x54de268,address(context.vtable()));protect(image.bytes()+pages[5],PAGE_READONLY);
        std::uint64_t returned=0;
        { Activation activation(context);returned=entry(address(destination),address(source)); }
        result.callbackGuard=result.callbackGuard && active==nullptr && !orphan && !context.failed && context.used<=context.captured.size();need(result.callbackGuard,"callback guard failed");
        Row row{};row.id=item.id;row.returnedDestination=returned==address(destination);row.vptrRvaHex=hex(load<std::uint64_t>(destination)-context.imageBase);
        row.kindHex=hex(load<std::uint32_t>(destination+8));row.tailHex=hex(load<std::uint32_t>(destination+0x40));row.flagHex=hex(load<std::uint8_t>(destination+0x44));
        row.header16=header(context,rawHeader(destination+0x10));row.header4=header(context,rawHeader(destination+0x28));row.releaseSnapshotTaken=context.releaseTaken;
        if(context.releaseTaken)row.beforeRelease=header(context,context.beforeRelease);
        for(unsigned i=0;i<context.used;++i)row.calls.push_back(call(context,context.captured[i]));result.rows.push_back(std::move(row));
        for(std::size_t i=0xF0;i<0x100;++i)result.memoryGuard=result.memoryGuard && data.bytes()[i]==0xA5;
        for(std::size_t i=0x149;i<0x159;++i)result.memoryGuard=result.memoryGuard && data.bytes()[i]==0xA5;
        for(unsigned i=0;i<4;++i)result.memoryGuard=result.memoryGuard && destination[0x45+i]==static_cast<std::uint8_t>(0xC5u+i);
        result.memoryGuard=result.memoryGuard && load<std::uint64_t>(image.bytes()+0x54de260)==0 && load<std::uint64_t>(image.bytes()+0x54de268)==address(context.vtable());
        result.rawUnchanged=result.rawUnchanged && originalUnchanged();
        for(std::size_t i=0;i<4;++i)result.protectionsFinal=result.protectionsFinal && page(image.bytes()+pages[i],PAGE_EXECUTE_READ);
        result.protectionsFinal=result.protectionsFinal && page(image.bytes()+pages[4],PAGE_READONLY) && page(image.bytes()+pages[5],PAGE_READONLY) && page(data.bytes(),PAGE_READWRITE);
        result.forbiddenTargetsUnmapped=result.forbiddenTargetsUnmapped && reserved(image.bytes()+0x8f8550) && reserved(image.bytes()+0x9d0950);
        need(result.rawUnchanged && result.protectionsFinal && result.memoryGuard && result.forbiddenTargetsUnmapped,"raw/page/RAM/forbidden invariant failed");result.mappingReleased=data.release() && result.mappingReleased;
    }
    result.mappingReleased=image.release() && result.mappingReleased;return result;
}
}
