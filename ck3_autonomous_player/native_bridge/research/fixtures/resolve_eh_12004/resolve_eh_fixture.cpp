// SOURCE ONLY / UNCOMPILED. Standalone fixture process, never load into CK3.
// Changes only its own deliberately reserved NOP marker and own allocated code.
// It derives the handler and FH4 metadata from this EXE's compiled Original().
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <ehdata4_export.h>  // Installed MSVC official compressed FH4 decoder.
#include <intrin.h>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

static_assert(sizeof(void*) == 8);
static_assert(offsetof(DISPATCHER_CONTEXT, ScopeIndex) == 0x48);

namespace {
constexpr DWORD kNested = 0xE042B401;
constexpr DWORD kCollision = 0xE042B402;
constexpr std::uint64_t kToken = 0x42B4E17CF005;
constexpr unsigned kCapacity = 64;
constexpr DWORD kStubRva = 0x1000;
constexpr DWORD kHandlerStubRva = 0x2000;
constexpr DWORD kTableRva = 0x3000;
constexpr DWORD kUnwindRva = 0x4000;
constexpr DWORD kDataRva = 0x5000;
constexpr DWORD kPrefixBytes = 0x20; // JMP entry has no return slot; body RSP is 16-aligned.

enum class Mode { direct, inplace_normal, inplace_nested, inplace_collided, copy_collided,
    empty_direct, inplace_empty, no_language_empty, no_language_active };
bool IsEmpty(Mode m) noexcept {return m==Mode::empty_direct || m==Mode::inplace_empty || m==Mode::no_language_empty;}
bool IsDirect(Mode m) noexcept {return m==Mode::direct || m==Mode::empty_direct;}
bool IsHandlerFree(Mode m) noexcept {return m==Mode::no_language_empty || m==Mode::no_language_active;}
enum class Kind : unsigned { original_frame=1, handler_entry, cleanup_entry,
    nested_filter, nested_continued, outer_filter, outer_continued,
    handler_normal_return, handler_validation_failure };
struct Event {
    unsigned seq{}, kind{};
    DWORD thread{}, code{}, flags{}, scope_actual{}, scope_forwarded{};
    ULONG64 actual_dc{}, forwarded_dc{}, frame{}, expected_frame{}, pc{},
        image{}, function{}, handler_data{}, context{}, target{}, history{}, guard{};
};
struct State {
    Mode mode{};
    DWORD owner{};
    volatile LONG empty_active_branch{0}; // Explicit opt-in layout witness; default unused.
    Event events[kCapacity]{};
    unsigned count{}, dropped{}, cleanup_count{}, handler_count{}, handler_returns{};
    bool failed{}, nested_continued{}, outer_continued{}, collided_flag_seen{},
        collided_disposition_seen{}, cleanup_alias_seen{}, scope_visible{}, copy_loss_seen{};
    DWORD outer_code{};
    ULONG64 expected_original_frame{}, guard_address{};
    PDISPATCHER_CONTEXT active_actual{}, active_forwarded{};
};
thread_local State g{}; // Initialized on the owner thread before any exception.

void Record(Kind kind, PEXCEPTION_RECORD er=nullptr,
            PDISPATCHER_CONTEXT actual=nullptr, PDISPATCHER_CONTEXT forwarded=nullptr,
            ULONG64 frame=0) noexcept {
    if (g.count==kCapacity) { ++g.dropped; g.failed=true; return; }
    Event& e=g.events[g.count++];
    e.seq=g.count; e.kind=static_cast<unsigned>(kind); e.thread=GetCurrentThreadId();
    e.code=er?er->ExceptionCode:0; e.flags=er?er->ExceptionFlags:0;
    if (er && (er->ExceptionFlags&EXCEPTION_COLLIDED_UNWIND)) g.collided_flag_seen=true;
    e.actual_dc=reinterpret_cast<ULONG64>(actual);
    e.forwarded_dc=reinterpret_cast<ULONG64>(forwarded);
    e.scope_actual=actual?actual->ScopeIndex:0;
    e.scope_forwarded=forwarded?forwarded->ScopeIndex:0;
    e.frame=frame; e.expected_frame=g.expected_original_frame; e.guard=g.guard_address;
    if (forwarded) {
        e.pc=forwarded->ControlPc; e.image=forwarded->ImageBase;
        e.function=reinterpret_cast<ULONG64>(forwarded->FunctionEntry);
        e.handler_data=reinterpret_cast<ULONG64>(forwarded->HandlerData);
        e.context=reinterpret_cast<ULONG64>(forwarded->ContextRecord);
        e.target=forwarded->TargetIp; e.history=reinterpret_cast<ULONG64>(forwarded->HistoryTable);
    }
    if (e.thread!=g.owner) g.failed=true;
}

int NestedFilter(PEXCEPTION_POINTERS ep) noexcept {
    Record(Kind::nested_filter,ep->ExceptionRecord);
    return ep->ExceptionRecord->ExceptionCode==kNested ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH;
}
__declspec(noinline) void NestedWithinCleanup() {
    __try { RaiseException(kNested,0,0,nullptr); }
    __except(NestedFilter(GetExceptionInformation())) { g.nested_continued=true; }
    Record(Kind::nested_continued);
}

struct Guard {
    volatile std::uint64_t token{kToken};
    __declspec(noinline) Guard() { g.guard_address=reinterpret_cast<ULONG64>(this); }
    __declspec(noinline) ~Guard() noexcept(false) {
        ++g.cleanup_count;
        Record(Kind::cleanup_entry,nullptr,g.active_actual,g.active_forwarded,g.expected_original_frame);
        if (token!=kToken || reinterpret_cast<ULONG64>(this)!=g.guard_address) g.failed=true;
        if (!IsDirect(g.mode) && !IsEmpty(g.mode)) {
            if (!g.active_actual || !g.active_forwarded) g.failed=true;
            else {
                g.cleanup_alias_seen=g.active_actual==g.active_forwarded;
                if (g.cleanup_alias_seen && g.active_actual->ScopeIndex!=0) g.scope_visible=true;
                if (!g.cleanup_alias_seen && g.active_actual->ScopeIndex==0 &&
                    g.active_forwarded->ScopeIndex!=0) g.copy_loss_seen=true;
            }
        }
        if (g.mode==Mode::inplace_nested) NestedWithinCleanup();
        if (g.mode==Mode::inplace_collided || g.mode==Mode::copy_collided)
            RaiseException(kCollision,0,0,nullptr);  // Escapes original handler; no late writeback.
    }
};
struct PrimaryException { unsigned fixture_marker{0xF005}; };
__declspec(noinline) void ThrowPrimary() { throw PrimaryException{}; }

__declspec(noinline) void Original() {
    Guard guard;
    CONTEXT context{};
    RtlCaptureContext(&context);
    g.expected_original_frame=context.Rsp;
    Record(Kind::original_frame);
    // Exactly one intentionally reserved marker in this fixture function.
    // Future fixture admission requires a unique exact 16x90 byte window.
    __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop();
    __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop();
    ThrowPrimary();
}

__declspec(noinline) void OriginalEmpty() {
    { Guard guard; } // Actual cleanup completes before the only marker.
    // A real, opt-in active-cleanup path keeps actual FH4 metadata in this function.
    // The nine ordinary modes leave this volatile input zero and never enter it.
    if (g.empty_active_branch != 0) {
        Guard auxiliary;
        ThrowPrimary();
    }
    CONTEXT context{};
    RtlCaptureContext(&context);
    g.expected_original_frame=context.Rsp;
    Record(Kind::original_frame);
    __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop();
    __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop(); __nop();
    ThrowPrimary();
}

struct HandlerData {
    std::uint64_t magic{0xB4F0054E41544956};
    ULONG64 original_image{}, original_pc{};
    PRUNTIME_FUNCTION original_function{};
    PEXCEPTION_ROUTINE original_handler{};
    PVOID original_language_data{};
    ULONG64 block_begin{}, block_end{};
    DWORD prefix_bytes{kPrefixBytes};
    DWORD owner{};
};
struct Identity {
    ULONG64 pc{}, image{}, frame{};
    PRUNTIME_FUNCTION function{};
    PEXCEPTION_ROUTINE handler{};
    PVOID data{};
};
Identity SaveIdentity(PDISPATCHER_CONTEXT d) noexcept {
    return {d->ControlPc,d->ImageBase,d->EstablisherFrame,d->FunctionEntry,d->LanguageHandler,d->HandlerData};
}
void RestoreIdentity(PDISPATCHER_CONTEXT d,const Identity& old) noexcept {
    d->ControlPc=old.pc; d->ImageBase=old.image; d->EstablisherFrame=old.frame;
    d->FunctionEntry=old.function; d->LanguageHandler=old.handler; d->HandlerData=old.data;
    // ScopeIndex / ContextRecord / TargetIp / HistoryTable deliberately not restored.
}
extern "C" EXCEPTION_DISPOSITION __cdecl ForwardOriginal(
    PEXCEPTION_RECORD er,PVOID prefix_frame,PCONTEXT context,PDISPATCHER_CONTEXT actual) {
    DWORD data_rva{};
    std::memcpy(&data_rva,actual->HandlerData,sizeof(data_rva));
    if(data_rva!=kDataRva) __fastfail(7);
    auto* data=reinterpret_cast<HandlerData*>(actual->ImageBase+data_rva);
    const auto prefix=reinterpret_cast<ULONG64>(prefix_frame);
    if (!data || data->magic!=0xB4F0054E41544956 || data->owner!=g.owner ||
        GetCurrentThreadId()!=g.owner || actual->ContextRecord!=context ||
        actual->EstablisherFrame!=prefix || actual->ControlPc<data->block_begin ||
        actual->ControlPc>=data->block_end || prefix>~ULONG64{0}-data->prefix_bytes ||
        prefix+data->prefix_bytes!=g.expected_original_frame ||
        (actual->TargetIp>=data->block_begin && actual->TargetIp<data->block_end)) {
        g.failed=true; Record(Kind::handler_validation_failure,er,actual,actual,prefix);
        // Deliberately fail the disposable fixture; do not invent an exception disposition.
        __fastfail(7);
    }
    ++g.handler_count;
    const Identity old=SaveIdentity(actual);
    DISPATCHER_CONTEXT copied=*actual;
    auto* forwarded=g.mode==Mode::copy_collided ? &copied : actual;
    forwarded->ControlPc=data->original_pc; forwarded->ImageBase=data->original_image;
    forwarded->FunctionEntry=data->original_function;
    forwarded->EstablisherFrame=prefix+data->prefix_bytes;
    forwarded->LanguageHandler=data->original_handler;
    forwarded->HandlerData=data->original_language_data;
    g.active_actual=actual; g.active_forwarded=forwarded;
    Record(Kind::handler_entry,er,actual,forwarded,forwarded->EstablisherFrame);
    // Intentionally no __finally and no RAII restoration. If cleanup initiates
    // a collided unwind, the real dispatcher retains the rebased fields and
    // ScopeIndex at that instant. This is the behavior under test, not a claim.
    const auto disposition=data->original_handler(er,
        reinterpret_cast<PVOID>(forwarded->EstablisherFrame),context,forwarded);
    ++g.handler_returns;
    if (disposition==ExceptionCollidedUnwind) g.collided_disposition_seen=true;
    Record(Kind::handler_normal_return,er,actual,forwarded,forwarded->EstablisherFrame);
    if (disposition==ExceptionContinueSearch) {
        if (forwarded!=actual) actual->ScopeIndex=forwarded->ScopeIndex;
        RestoreIdentity(actual,old);
    }
    // Other dispositions remain actual returned values with original view intact.
    // Final qualification rejects unexpected dispositions; none is fabricated.
    g.active_actual=nullptr; g.active_forwarded=nullptr;
    return disposition;
}

struct Installation {
    BYTE* block{};
    PRUNTIME_FUNCTION table{};
    BYTE* marker{};
    BYTE marker_original[16]{};
    DWORD marker_protection{};
    bool table_registered{}, marker_changed{}, pinned_failure{};
    ULONG64 image{};
    PRUNTIME_FUNCTION original{};
    DWORD original_handler_rva{}, func_info_rva{};
    int marker_state{-2}, projected_call_state{-2};
    unsigned original_codes{}, original_flags{};
};

// Finite Windows x64 version1 code slot validator. Original slot order and
// operands are retained verbatim; only operation CodeOffsets become zero.
unsigned SlotCount(unsigned op,unsigned info) noexcept {
    switch(op) {
    case 0:return 1; // PUSH_NONVOL
    case 1:return info==0?2:info==1?3:0; // ALLOC_LARGE
    case 2:return 1; // ALLOC_SMALL
    case 4:case 8:return 2; // SAVE_NONVOL / SAVE_XMM128
    case 5:case 9:return 3; // FAR variants
    default:return 0; // frame registers, MACHFRAME, unknown versions rejected
    }
}
bool Protect(void* p,SIZE_T n,DWORD protect) noexcept {
    DWORD old{};return VirtualProtect(p,n,protect,&old)!=FALSE;
}
void AbsoluteJump(BYTE* out,const void* target) noexcept {
    const BYTE lead[6]={0xff,0x25,0,0,0,0};
    std::memcpy(out,lead,6);std::memcpy(out+6,&target,8);
}
bool Prepare(Installation& x) {
    const auto pc=IsEmpty(g.mode)?reinterpret_cast<ULONG64>(&OriginalEmpty):reinterpret_cast<ULONG64>(&Original);
    x.original=RtlLookupFunctionEntry(pc,&x.image,nullptr);
    if (!x.original || pc<x.image+x.original->BeginAddress ||
        pc>=x.image+x.original->EndAddress ||
        x.original->EndAddress-x.original->BeginAddress>4096) return false;
    BYTE* begin=reinterpret_cast<BYTE*>(x.image+x.original->BeginAddress);
    const unsigned length=x.original->EndAddress-x.original->BeginAddress;
    unsigned marker_count=0;
    for (unsigned i=0;i+16<=length;++i) {
        bool match=true;for(unsigned j=0;j<16;++j) if(begin[i+j]!=0x90)match=false;
        if(match){x.marker=begin+i;++marker_count;}
    }
    if(marker_count!=1)return false;
    auto* ui=reinterpret_cast<const BYTE*>(x.image+x.original->UnwindData);
    x.original_flags=ui[0]>>3; x.original_codes=ui[2];
    if ((ui[0]&7)!=1 || (x.original_flags&4) || !(x.original_flags&2) ||
        ui[3]!=0 || x.original_codes==0 || x.original_codes>32) return false;
    unsigned slot=0;
    while(slot<x.original_codes) {
        const unsigned n=SlotCount(ui[5+slot*2]&15,ui[5+slot*2]>>4);
        if(!n || slot+n>x.original_codes)return false;
        slot+=n;
    }
    const unsigned tail=4+((x.original_codes+1)&~1u)*2;
    std::memcpy(&x.original_handler_rva,ui+tail,4);
    const void* language_data=ui+tail+4;
    std::memcpy(&x.func_info_rva,language_data,4);
    // Official MSVC parser, only this fixture's metadata; never a game image.
    FH4::FuncInfo4 info{};
    FH4::DecompFuncInfo(reinterpret_cast<std::uint8_t*>(x.image+x.func_info_rva),
        info,x.image,static_cast<std::int32_t>(x.original->BeginAddress));
    if(info.header.isCatch || info.header.isSeparated || !info.header.UnwindMap ||
        info.header.TryBlockMap || info.header.NoExcept || !info.header.EHs) return false;
    auto* ip=reinterpret_cast<std::uint8_t*>(x.image+info.dispIPtoStateMap);
    const unsigned count=FH4::ReadUnsigned(&ip);
    if(count==0 || count>32)return false;
    // Decode only the exact same-TU E8 call immediately following the reserved marker.
    const unsigned call_offset=static_cast<unsigned>(x.marker-begin)+16;
    if(call_offset>length || length-call_offset<5)return false;
    const BYTE* call=begin+call_offset;
    if(call[0]!=0xe8)return false;
    std::int32_t relative{};std::memcpy(&relative,call+1,sizeof(relative));
    const auto return_pc=reinterpret_cast<std::intptr_t>(call+5);
    if(return_pc+relative!=reinterpret_cast<std::intptr_t>(&ThrowPrimary))return false;
    const ULONG64 projected_pc=static_cast<ULONG64>(return_pc);
    const ULONG64 marker_pc=reinterpret_cast<ULONG64>(x.marker)+8;
    // Official x64 StateFromIp: unchanged PC; before the first entry is EMPTY (-1).
    std::uint32_t offset=0;int state=-1,marker_state=-1;
    for(unsigned n=0;n<count;++n) {
        offset+=FH4::ReadUnsigned(&ip);
        const int value=static_cast<int>(FH4::ReadUnsigned(&ip))-1;
        const ULONG64 entry_pc=x.image+x.original->BeginAddress+offset;
        if(entry_pc<=projected_pc)state=value;
        if(entry_pc<=marker_pc)marker_state=value;
    }
    x.marker_state=marker_state;x.projected_call_state=state;
    if(state!=(IsEmpty(g.mode)?-1:0) || (IsEmpty(g.mode) && marker_state!=-1))return false;
    x.block=static_cast<BYTE*>(VirtualAlloc(nullptr,0x10000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    if(!x.block)return false;
    BYTE* code=x.block+kStubRva;
    const BYTE sub[4]={0x48,0x83,0xec,0x20};std::memcpy(code,sub,4);
    code[4]=0x48;code[5]=0xb8;
    const void* throwing=reinterpret_cast<const void*>(&ThrowPrimary);std::memcpy(code+6,&throwing,8);
    code[14]=0xff;code[15]=0xd0; // call rax; sole throwing call
    code[16]=0x90;code[17]=0x90; // return PC is not an epilog, handler is consulted
    const BYTE end[5]={0x48,0x83,0xc4,0x20,0xc3};std::memcpy(code+18,end,5);
    AbsoluteJump(x.block+kHandlerStubRva,reinterpret_cast<const void*>(&ForwardOriginal));
    x.table=reinterpret_cast<PRUNTIME_FUNCTION>(x.block+kTableRva);
    *x.table={kStubRva,kStubRva+23,kUnwindRva};
    BYTE* synth=x.block+kUnwindRva;
    synth[0]=IsHandlerFree(g.mode)?(ui[0]&7):ui[0];
    synth[1]=0;synth[2]=static_cast<BYTE>(x.original_codes+1);synth[3]=0;
    synth[4]=0;synth[5]=0x32; // ALLOC_SMALL 0x20 FIRST: original frame = prefix frame + 32
    std::memcpy(synth+6,ui+4,x.original_codes*2);
    slot=0;
    while(slot<x.original_codes) {
        synth[6+slot*2]=0;
        slot+=SlotCount(ui[5+slot*2]&15,ui[5+slot*2]>>4);
    }
    const unsigned synth_tail=4+((x.original_codes+2)&~1u)*2;
    const DWORD handler_rva=kHandlerStubRva;
    std::memcpy(synth+synth_tail,&handler_rva,4);
    const DWORD data_rva=kDataRva;
    std::memcpy(synth+synth_tail+4,&data_rva,4);
    auto* data=reinterpret_cast<HandlerData*>(x.block+kDataRva);
    *data=HandlerData{};
    data->original_image=x.image;data->original_pc=projected_pc;data->original_function=x.original;
    data->original_handler=reinterpret_cast<PEXCEPTION_ROUTINE>(x.image+x.original_handler_rva);
    data->original_language_data=const_cast<void*>(language_data);
    data->block_begin=reinterpret_cast<ULONG64>(code);data->block_end=data->block_begin+23;
    data->owner=g.owner;
    if(!Protect(code,0x1000,PAGE_EXECUTE_READ) ||
        !Protect(x.block+kHandlerStubRva,0x1000,PAGE_EXECUTE_READ) ||
        !Protect(x.table,0x1000,PAGE_READONLY) || !Protect(synth,0x1000,PAGE_READONLY) ||
        !Protect(data,0x1000,PAGE_READONLY) ||
        !FlushInstructionCache(GetCurrentProcess(),code,0x2000))return false;
    if(!RtlAddFunctionTable(x.table,1,reinterpret_cast<ULONG64>(x.block)))return false;
    x.table_registered=true;
    ULONG64 looked_base{};
    if(RtlLookupFunctionEntry(reinterpret_cast<ULONG64>(code+16),&looked_base,nullptr)!=x.table ||
        looked_base!=reinterpret_cast<ULONG64>(x.block))return false;
    std::memcpy(x.marker_original,x.marker,16);
    if(!VirtualProtect(x.marker,16,PAGE_EXECUTE_READWRITE,&x.marker_protection))return false;
    AbsoluteJump(x.marker,code);x.marker_changed=true;
    if(!FlushInstructionCache(GetCurrentProcess(),x.marker,16) ||
        !Protect(x.marker,16,x.marker_protection))return false;
    return true;
}
bool Remove(Installation& x) noexcept {
    if(x.marker_changed) {
        DWORD old{};
        if(!VirtualProtect(x.marker,16,PAGE_EXECUTE_READWRITE,&old)) {x.pinned_failure=true;return false;}
        std::memcpy(x.marker,x.marker_original,16);
        if(!FlushInstructionCache(GetCurrentProcess(),x.marker,16) ||
            !Protect(x.marker,16,x.marker_protection)) {x.pinned_failure=true;return false;}
        x.marker_changed=false;
    }
    if(x.table_registered) {
        if(!RtlDeleteFunctionTable(x.table)) {x.pinned_failure=true;return false;}
        x.table_registered=false;
        ULONG64 base{};
        if(RtlLookupFunctionEntry(reinterpret_cast<ULONG64>(x.block+kStubRva+16),&base,nullptr)) {
            x.pinned_failure=true;return false;
        }
    }
    if(x.block && !VirtualFree(x.block,0,MEM_RELEASE)) {x.pinned_failure=true;return false;}
    x.block=nullptr;return true;
}

int OuterFilter(PEXCEPTION_POINTERS ep) noexcept {
    Record(Kind::outer_filter,ep->ExceptionRecord,g.active_actual,g.active_forwarded);
    const DWORD code=ep->ExceptionRecord->ExceptionCode;
    if(code==0xE06D7363 || code==kCollision) {g.outer_code=code;return EXCEPTION_EXECUTE_HANDLER;}
    return EXCEPTION_CONTINUE_SEARCH;
}
// SEH stays in a function with no C++ objects requiring unwinding (C2712).
__declspec(noinline) void Run() {
    __try { if(IsEmpty(g.mode)) OriginalEmpty(); else Original(); }
    __except(OuterFilter(GetExceptionInformation())) { g.outer_continued=true; }
    Record(Kind::outer_continued);
}
void Dump(const char* mode,const Installation& x,bool qualified,bool removed,const char* reason) noexcept {
    const bool control=g.mode==Mode::copy_collided || g.mode==Mode::no_language_active;
    const char* status=qualified?(control?"NEGATIVE_CONTROL_OBSERVED":"FIXTURE_CASE_PASS"):"NOT_QUALIFIED";
    std::printf("{\"schema\":\"lyd.b4.windows-fh4-fixture.actual.v1\",\"mode\":\"%s\","
        "\"status\":\"%s\",\"reason\":\"%s\",\"live\":false,\"CK3_called\":false,"
        "\"cleanup_count\":%u,\"handler_count\":%u,\"handler_returns\":%u,"
        "\"scope_visible_in_actual_dispatcher\":%s,\"copy_loss_observed\":%s,"
        "\"collided_flag_seen\":%s,\"collided_disposition_seen\":%s,"
        "\"outer_continued\":%s,\"nested_continued\":%s,\"outer_code\":%lu,"
        "\"marker_state\":%d,\"projected_call_state\":%d,\"original_flags\":%u,\"original_codes\":%u,"
        "\"removed\":%s,\"pinned_failure\":%s,\"events\":[",
        mode,status,reason,g.cleanup_count,g.handler_count,g.handler_returns,
        g.scope_visible?"true":"false",g.copy_loss_seen?"true":"false",g.collided_flag_seen?"true":"false",
        g.collided_disposition_seen?"true":"false",g.outer_continued?"true":"false",g.nested_continued?"true":"false",
        g.outer_code,x.marker_state,x.projected_call_state,x.original_flags,x.original_codes,removed?"true":"false",x.pinned_failure?"true":"false");
    for(unsigned i=0;i<g.count;++i) {
        const auto& e=g.events[i];
        std::printf("%s{\"seq\":%u,\"kind\":%u,\"thread\":%lu,\"code\":%lu,\"flags\":%lu,"
            "\"scope_actual\":%lu,\"scope_forwarded\":%lu,\"actual_dc\":\"0x%llx\","
            "\"forwarded_dc\":\"0x%llx\",\"frame\":\"0x%llx\",\"expected_frame\":\"0x%llx\","
            "\"pc\":\"0x%llx\",\"image\":\"0x%llx\",\"function\":\"0x%llx\","
            "\"handler_data\":\"0x%llx\",\"context\":\"0x%llx\",\"target\":\"0x%llx\","
            "\"history\":\"0x%llx\",\"guard\":\"0x%llx\"}",i?",":"",e.seq,e.kind,e.thread,e.code,e.flags,
            e.scope_actual,e.scope_forwarded,e.actual_dc,e.forwarded_dc,e.frame,e.expected_frame,e.pc,e.image,
            e.function,e.handler_data,e.context,e.target,e.history,e.guard);
    }
    std::puts("]}");
}
} // namespace

int main(int argc,char** argv) {
    if(argc!=2 && argc!=3) {std::fputs("mode required; no default execution\n",stderr);return 2;}
    const char* mode=argv[1];
    if(std::strcmp(mode,"direct")==0)g.mode=Mode::direct;
    else if(std::strcmp(mode,"inplace-normal")==0)g.mode=Mode::inplace_normal;
    else if(std::strcmp(mode,"inplace-nested")==0)g.mode=Mode::inplace_nested;
    else if(std::strcmp(mode,"inplace-collided")==0)g.mode=Mode::inplace_collided;
    else if(std::strcmp(mode,"copy-control-collided")==0)g.mode=Mode::copy_collided;
    else if(std::strcmp(mode,"empty-direct")==0)g.mode=Mode::empty_direct;
    else if(std::strcmp(mode,"inplace-empty")==0)g.mode=Mode::inplace_empty;
    else if(std::strcmp(mode,"no-language-empty")==0)g.mode=Mode::no_language_empty;
    else if(std::strcmp(mode,"no-language-active-control")==0)g.mode=Mode::no_language_active;
    else {std::fputs("unknown exact fixture mode\n",stderr);return 2;}
    // Reachability witness only. It never earns an empty-state PASS and is not in the nine-mode argv.
    if(argc==3) {
        if(g.mode!=Mode::empty_direct || std::strcmp(argv[2],"--exercise-empty-active-branch")!=0) {
            std::fputs("auxiliary arm is only explicit empty-direct layout witness\n",stderr);return 2;
        }
        g.empty_active_branch=1;
    }
    g.owner=GetCurrentThreadId();
    Installation x{};
    if(!IsDirect(g.mode) && !Prepare(x)) {
        const bool removed=Remove(x);Dump(mode,x,false,removed,"compiler_metadata_or_install_admission");return 3;
    }
    Run();
    const bool removed=IsDirect(g.mode) || Remove(x);
    bool qualified=!g.failed && !g.dropped && removed && g.outer_continued && !g.empty_active_branch;
    const char* reason="actual_native_case";
    if(g.mode==Mode::no_language_active) {
        qualified=qualified && g.cleanup_count==0 && g.handler_count==0 && g.outer_code==0xE06D7363;
        reason="negative_control_observed_missing_active_cleanup_not_forwarding_credit";
    }
    else if(IsEmpty(g.mode)) {
        qualified=qualified && g.cleanup_count==1 && g.outer_code==0xE06D7363;
        if(g.mode==Mode::no_language_empty)qualified=qualified && g.handler_count==0;
        if(g.mode==Mode::inplace_empty)qualified=qualified && g.handler_count>0;
        reason="empty_state_concrete_continuation_case_only_not_general_handler_elision_proof";
    }
    else if(g.mode==Mode::direct)qualified=qualified && g.cleanup_count==1 && g.outer_code==0xE06D7363;
    else if(g.mode==Mode::copy_collided) {
        qualified=qualified && g.cleanup_count==1 && g.copy_loss_seen && !g.scope_visible && g.outer_code==kCollision;
        reason="negative_control_observed_copy_latewriteback_loss_not_forwarding_credit";
    } else {
        qualified=qualified && g.cleanup_count==1 && g.handler_count>0 && g.cleanup_alias_seen && g.scope_visible;
        if(g.mode==Mode::inplace_normal || g.mode==Mode::inplace_nested)
            qualified=qualified && g.outer_code==0xE06D7363;
        if(g.mode==Mode::inplace_nested)qualified=qualified && g.nested_continued;
        if(g.mode==Mode::inplace_collided) {
            qualified=qualified && g.outer_code==kCollision &&
                (g.collided_flag_seen || g.collided_disposition_seen);
            reason="requires_actual_OS_collided_flag_or_disposition_and_continuation";
        }
    }
    Dump(mode,x,qualified,removed,reason);
    return qualified?0:4;
}
