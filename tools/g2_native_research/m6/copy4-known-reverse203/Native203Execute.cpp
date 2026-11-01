#define NOMINMAX
#include <windows.h>
#include <intrin.h>
#include <xmmintrin.h>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <utility>
#include "Native203Api.hpp"

namespace copy4knownreverse203 {
namespace {
void need(bool condition,const char* reason) { if(!condition)throw std::runtime_error(reason); }
template<class T> T load(const std::uint8_t* p) { T value{};std::memcpy(&value,p,sizeof(value));return value; }
template<class T> void store(std::uint8_t* p,T value) { std::memcpy(p,&value,sizeof(value)); }
std::uint64_t address(const void* pointer) { return reinterpret_cast<std::uint64_t>(pointer); }
std::string hex(std::uint64_t value) { std::ostringstream out;out<<std::hex<<value;return out.str(); }
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
void protect(std::uint8_t* pointer,DWORD protection) { DWORD previous=0;need(VirtualProtect(pointer,4096,protection,&previous)!=0,"VirtualProtect failed"); }
bool page(const void* pointer,DWORD protection) { MEMORY_BASIC_INFORMATION info{};return VirtualQuery(pointer,&info,sizeof(info))==sizeof(info) && info.State==MEM_COMMIT && info.Protect==protection; }
bool cpuEligible() {
    int info[4];__cpuidex(info,0,0);if(info[0]<7)return false;
    __cpuidex(info,1,0);if(!(info[2]&(1<<27)) || !(info[2]&(1<<28)))return false;
    if((_xgetbv(0)&6u)!=6u)return false;
    __cpuidex(info,7,0);return (info[1]&(1<<5))!=0;
}
enum class Kind { copy,allocate,release };
struct Captured { Kind kind{};std::array<std::uint64_t,4> args{}; };
struct Context {
    std::uint8_t* data{};bool failed{};unsigned used{};std::array<Captured,8> captured{};
    std::uint8_t* header() const { return data+0x100; }
    std::uint8_t* old() const { return data+0x300; }
    std::uint8_t* fresh() const { return data+0x500; }
    std::uint8_t* source() const { return data+0x700; }
    std::uint8_t* allocator() const { return data+0xB00; }
    std::uint8_t* vtable() const { return data+0xB40; }
    void add(Kind kind,std::uint64_t a,std::uint64_t b,std::uint64_t c,std::uint64_t d=0) noexcept {
        if(used>=captured.size()) { failed=true;return; }captured[used++]={kind,{a,b,c,d}};
    }
    bool contains(std::uint64_t pointer,std::uint64_t bytes) const noexcept {
        const auto base=address(data);return pointer>=base && pointer-base<=4096 && bytes<=4096-(pointer-base);
    }
};
thread_local Context* active=nullptr;
class ActiveScope {
public:
    explicit ActiveScope(Context& context) { need(active==nullptr,"callback reentry");active=&context; }
    ~ActiveScope() { active=nullptr; }
    ActiveScope(const ActiveScope&)=delete;ActiveScope& operator=(const ActiveScope&)=delete;
};
void __fastcall copyPort(std::uint64_t destination,std::uint64_t source,std::uint64_t bytes) noexcept {
    if(!active)return;auto& context=*active;context.add(Kind::copy,destination,source,bytes);
    if(bytes>80 || !context.contains(destination,bytes) || !context.contains(source,bytes)) { context.failed=true;return; }
    std::array<std::uint8_t,80> snapshot{};const auto count=static_cast<std::size_t>(bytes);
    std::memcpy(snapshot.data(),reinterpret_cast<const void*>(source),count);
    std::memcpy(reinterpret_cast<void*>(destination),snapshot.data(),count);
}
std::uint64_t __fastcall allocatePort(std::uint64_t rcx,std::uint64_t bytes,std::uint64_t alignment,std::uint64_t end) noexcept {
    if(!active)return 0;auto& context=*active;context.add(Kind::allocate,rcx,bytes,alignment,end);
    if(rcx!=address(context.allocator()) || alignment!=4 || bytes>80 || !context.contains(end,0))context.failed=true;
    return address(context.fresh());
}
void __fastcall releasePort(std::uint64_t rcx,std::uint64_t oldBase,std::uint64_t alignment) noexcept {
    if(!active)return;auto& context=*active;context.add(Kind::release,rcx,oldBase,alignment);
    if(rcx!=address(context.allocator()) || oldBase!=address(context.old()) || alignment!=4)context.failed=true;
}
std::uint64_t logical(const Context& context,std::uint64_t pointer) {
    if(pointer==address(context.header()))return 0x1000;
    if(pointer==address(context.allocator()))return 0x5000;
    if(pointer==address(context.vtable()))return 0x6000;
    const std::array<std::pair<std::uint8_t*,std::uint64_t>,3> regions={{{context.old(),0x2000},{context.source(),0x3000},{context.fresh(),0x4000}}};
    for(const auto& region:regions)if(pointer>=address(region.first) && pointer-address(region.first)<=128)return region.second+pointer-address(region.first);
    throw std::runtime_error("unqualified output pointer");
}
std::string callback(const Context& context,const Captured& captured) {
    const auto& a=captured.args;
    if(captured.kind==Kind::copy)return "copy:"+hex(logical(context,a[0]))+":"+hex(logical(context,a[1]))+":"+hex(a[2]);
    if(captured.kind==Kind::allocate)return "alloc:7000:"+hex(logical(context,a[0]))+":"+hex(a[1])+":"+hex(a[2])+":"+hex(logical(context,a[3]));
    return "free:7010:"+hex(logical(context,a[0]))+":"+hex(logical(context,a[1]))+":"+hex(a[2]);
}
void seedGuard(std::uint8_t* base,std::int32_t words) { store(base-4,std::uint32_t{0x12345678});store(base+static_cast<std::size_t>(words)*4,std::uint32_t{0x76543210}); }
bool guard(const std::uint8_t* base,std::int32_t words) { return load<std::uint32_t>(base-4)==0x12345678u && load<std::uint32_t>(base+static_cast<std::size_t>(words)*4)==0x76543210u; }
std::vector<std::string> words(const std::uint8_t* base,std::int32_t count) {
    std::vector<std::string> values;for(std::int32_t i=0;i<count;++i)values.push_back(hex(load<std::uint32_t>(base+static_cast<std::size_t>(i)*4)));return values;
}
}

Run executeOriginal(std::span<const std::uint8_t,UPPER_BYTES> upper,std::span<const std::uint8_t,CALLER_BYTES> caller,std::span<const std::uint8_t,REVERSE_BYTES> reverse,std::span<const std::uint8_t,4> literal,std::span<const Case> cases) {
    static_assert(sizeof(void*)==8);Mxcsr rounding;
    Allocation image(0x5430000,MEM_RESERVE,PAGE_NOACCESS);
    const std::array<std::size_t,6> pages={0xADD000,0x9D0000,0x4220000,0x4226000,0x49F6000,0x542F000};
    for(auto offset:pages)need(VirtualAlloc(image.bytes()+offset,4096,MEM_COMMIT,PAGE_READWRITE)==image.bytes()+offset,"commit image page failed");
    std::memcpy(image.bytes()+0xADD0D0,upper.data(),upper.size());std::memcpy(image.bytes()+0x9D0950,caller.data(),caller.size());
    std::memcpy(image.bytes()+0x4220AA4,reverse.data(),reverse.size());std::memcpy(image.bytes()+0x49F64F0,literal.data(),literal.size());
    auto* trampoline=image.bytes()+0x4226860;trampoline[0]=0x48;trampoline[1]=0xB8;store(trampoline+2,reinterpret_cast<std::uint64_t>(&copyPort));trampoline[10]=0xFF;trampoline[11]=0xE0;
    for(std::size_t i=0;i<4;++i)protect(image.bytes()+pages[i],PAGE_EXECUTE_READ);protect(image.bytes()+pages[4],PAGE_READONLY);
    need(FlushInstructionCache(GetCurrentProcess(),nullptr,0)!=0,"FlushInstructionCache failed");
    const auto originalUnchanged=[&]() { return std::memcmp(image.bytes()+0xADD0D0,upper.data(),upper.size())==0 && std::memcmp(image.bytes()+0x9D0950,caller.data(),caller.size())==0 && std::memcmp(image.bytes()+0x4220AA4,reverse.data(),reverse.size())==0 && std::memcmp(image.bytes()+0x49F64F0,literal.data(),literal.size())==0; };
    need(originalUnchanged(),"raw initial mismatch");
    using Entry=void(__fastcall*)(std::uint64_t,std::uint64_t,std::uint64_t,std::uint64_t);const auto entry=reinterpret_cast<Entry>(image.bytes()+0xADD0D0);
    Run result{};result.avx2Eligible=cpuEligible();result.rawUnchanged=true;result.protectionsFinal=true;result.mappingReleased=true;result.callbackGuard=true;result.memoryGuard=true;
    for(const auto& item:cases) {
        if(!result.avx2Eligible && item.hasFeature && (item.featureWord&0x20u)!=0) { result.skipped.push_back(item.id);continue; }
        Allocation data(4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);std::memset(data.bytes(),0xA5,4096);Context context{};context.data=data.bytes();
        auto* source=item.aliasOffset>=0?context.old()+static_cast<std::size_t>(item.aliasOffset)*4:context.source();
        if(!item.empty) {
            store(context.header(),address(context.old()));store(context.header()+8,item.capacity);store(context.header()+12,item.oldSize);store(context.header()+16,address(context.allocator()));
            store(context.allocator(),address(context.vtable()));store(context.vtable()+8,reinterpret_cast<std::uint64_t>(&allocatePort));store(context.vtable()+16,reinterpret_cast<std::uint64_t>(&releasePort));
            for(std::int32_t i=0;i<item.capacity;++i)store(context.old()+static_cast<std::size_t>(i)*4,0xcafe0000u+static_cast<std::uint32_t>(i));
            for(std::int32_t i=0;i<item.oldSize;++i)store(context.old()+static_cast<std::size_t>(i)*4,0x10u+static_cast<std::uint32_t>(i));
            seedGuard(context.old(),item.capacity);
            if(item.aliasOffset<0) {
                for(std::int32_t i=0;i<item.sourceCount;++i)store(context.source()+static_cast<std::size_t>(i)*4,0x90u+static_cast<std::uint32_t>(i));
                seedGuard(context.source(),item.sourceCount);
            }
            if(item.newCapacity>0) {
                for(std::int32_t i=0;i<item.newCapacity;++i)store(context.fresh()+static_cast<std::size_t>(i)*4,0xbeef0000u+static_cast<std::uint32_t>(i));
                seedGuard(context.fresh(),item.newCapacity);
            }
        }
        if(item.hasFeature) { protect(image.bytes()+pages[5],PAGE_READWRITE);store(image.bytes()+0x542F09C,item.featureWord);protect(image.bytes()+pages[5],PAGE_READONLY); }
        else protect(image.bytes()+pages[5],PAGE_NOACCESS);
        {
            ActiveScope scope(context);
            entry(item.empty?0:address(context.header()),item.empty?2:static_cast<std::uint64_t>(static_cast<std::int64_t>(item.index)),item.empty?0:address(source),item.empty?0:address(source)+static_cast<std::uint64_t>(item.sourceCount)*4);
        }
        result.callbackGuard=result.callbackGuard && active==nullptr && !context.failed && context.used<=context.captured.size();need(result.callbackGuard,"callback guard failed");
        Row row{};row.id=item.id;row.hasHeader=!item.empty;
        if(!item.empty) {
            row.baseHex=hex(logical(context,load<std::uint64_t>(context.header())));row.capacityHex=hex(load<std::uint32_t>(context.header()+8));row.sizeHex=hex(load<std::uint32_t>(context.header()+12));row.allocatorHex=hex(logical(context,load<std::uint64_t>(context.header()+16)));
            row.oldWordsHex=words(context.old(),item.capacity);row.allocationWordsHex=words(context.fresh(),item.newCapacity);row.sourceWordsHex=words(source,item.sourceCount);
            result.memoryGuard=result.memoryGuard && guard(context.old(),item.capacity) && (item.aliasOffset>=0 || guard(context.source(),item.sourceCount)) && (item.newCapacity==0 || guard(context.fresh(),item.newCapacity));
        }
        for(unsigned i=0;i<context.used;++i)row.callbacks.push_back(callback(context,context.captured[i]));result.rows.push_back(std::move(row));
        for(std::size_t i=0xF0;i<0x100;++i)result.memoryGuard=result.memoryGuard && data.bytes()[i]==0xA5;
        for(std::size_t i=0x118;i<0x128;++i)result.memoryGuard=result.memoryGuard && data.bytes()[i]==0xA5;
        result.rawUnchanged=result.rawUnchanged && originalUnchanged();
        for(std::size_t i=0;i<4;++i)result.protectionsFinal=result.protectionsFinal && page(image.bytes()+pages[i],PAGE_EXECUTE_READ);
        result.protectionsFinal=result.protectionsFinal && page(image.bytes()+pages[4],PAGE_READONLY) && page(image.bytes()+pages[5],item.hasFeature?PAGE_READONLY:PAGE_NOACCESS) && page(data.bytes(),PAGE_READWRITE);
        need(result.memoryGuard && result.rawUnchanged && result.protectionsFinal,"RAM/raw/page invariant failed");result.mappingReleased=data.release() && result.mappingReleased;
    }
    result.mappingReleased=image.release() && result.mappingReleased;return result;
}
}
