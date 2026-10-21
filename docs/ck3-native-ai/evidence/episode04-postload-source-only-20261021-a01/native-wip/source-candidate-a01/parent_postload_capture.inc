// Called only for an owned execution fault at the independently anchored post PC.
bool PostloadCapture(std::ofstream& out,HANDLE p,const PostloadOptions& o,const CONTEXT& c,
 DWORD tid,unsigned gen,std::uint64_t birth,DWORD64 exception_pc){
 std::uint32_t id1=0,id2=0,magic1=0,magic2=0;
 DWORD64 death1=0,death2=0,ctx1=0,ctx2=0,ret1=0,ret2=0;
 PostloadClock ca{},cb{};
 const bool stack_ok=c.Rsp<=0x7ffffffff000ULL-0xa8&&c.Rax==c.Rsp+0xa8;
 const DWORD64 entry_sp=stack_ok?c.Rsp+0xa8:0;
 const bool first=Read(p,c.Rbp+0x18,id1)&&Read(p,c.Rbp+0x1c,magic1)&&Read(p,c.Rbp+0x1d0,death1)&&Read(p,c.Rbp+0x1c0,ctx1)&&Read(p,entry_sp,ret1)&&PostloadReadClock(p,o,ca);
 const bool second=Read(p,c.Rbp+0x18,id2)&&Read(p,c.Rbp+0x1c,magic2)&&Read(p,c.Rbp+0x1d0,death2)&&Read(p,c.Rbp+0x1c0,ctx2)&&Read(p,entry_sp,ret2)&&PostloadReadClock(p,o,cb);
 const bool object=first&&second&&c.Rbp==o.x.character&&id1==o.x.full_id&&id2==id1&&magic1==0x43686172&&magic2==magic1&&!death1&&!death2;
 const bool context=first&&second&&ctx1==ctx2&&ctx1==o.x.secondary;
 const bool clock=first&&second&&ca.state==cb.state&&ca.state==o.x.game_state&&ca.date==cb.date&&ca.day==cb.day&&
 ca.date>=o.x.admission_date&&ca.date<=static_cast<std::uint64_t>(o.x.admission_date)+24&&ca.day>=o.x.absolute_day&&ca.day<=o.x.absolute_day+1;
 const bool source=PostloadSource(p,o);
 const bool qualified=object&&clock&&source&&stack_ok&&c.Rip==o.post_pc&&exception_pc==o.post_pc&&Created(p)==o.x.created;
 LARGE_INTEGER q{};QueryPerformanceCounter(&q);
 out<<"{\"kind\":\"parent_postload_execution\",\"thread_id\":"<<tid<<",\"thread_generation\":"<<gen<<",\"thread_created\":"<<PointerU64Json(birth)<<",\"RIP\":"<<PointerU64Json(c.Rip)
 <<",\"exception_address\":"<<PointerU64Json(exception_pc)<<",\"subject_field_address\":"<<PointerU64Json(o.watch)<<",\"RBP\":"<<PointerU64Json(c.Rbp)<<",\"RAX\":"<<PointerU64Json(c.Rax)<<",\"RDX\":"<<PointerU64Json(c.Rdx)<<",\"RCX\":"<<PointerU64Json(c.Rcx)<<",\"R8\":"<<PointerU64Json(c.R8)<<",\"R9\":"<<PointerU64Json(c.R9)<<",\"RSP\":"<<PointerU64Json(c.Rsp)
 <<",\"arguments_basis\":\"preserved_after_load_before_mov_r14_rcx\",\"DR6\":"<<PointerU64Json(c.Dr6)<<",\"eflags\":"<<c.EFlags<<",\"qpc\":"<<PointerS64Json(q.QuadPart)<<",\"entryExact\":false,\"loaded_context\":"<<PointerU64Json(c.Rdx)<<",\"first_read_complete\":"<<(first?"true":"false")
 <<",\"second_read_complete\":"<<(second?"true":"false")<<",\"full_id_before\":"<<id1<<",\"full_id_after\":"<<id2
 <<",\"magic_before\":"<<magic1<<",\"magic_after\":"<<magic2<<",\"death_before\":"<<PointerU64Json(death1)<<",\"death_after\":"<<PointerU64Json(death2)
 <<",\"context_before\":"<<PointerU64Json(ctx1)<<",\"context_after\":"<<PointerU64Json(ctx2)<<",\"admitted_context_unchanged\":"<<(context?"true":"false")
 <<",\"loaded_equals_post_samples\":"<<(first&&second&&c.Rdx==ctx1&&ctx1==ctx2?"true":"false")
 <<",\"return_before\":"<<PointerU64Json(ret1)<<",\"return_after\":"<<PointerU64Json(ret2)<<",\"state_before\":"<<PointerU64Json(ca.state)<<",\"state_after\":"<<PointerU64Json(cb.state)
 <<",\"date_before\":"<<ca.date<<",\"date_after\":"<<cb.date<<",\"day_before\":"<<ca.day<<",\"day_after\":"<<cb.day
 <<",\"source_anchor_matches\":"<<(source?"true":"false")<<",\"postload_owner_clock_qualified\":"<<(qualified?"true":"false")
 <<",\"parent_return_observed\":false,\"paid_maintenance_raw\":null,\"payer\":null,\"cadence\":null}\n";
 out.flush();return qualified;
}
