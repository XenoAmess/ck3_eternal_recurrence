#include "xar_bridge/appointment_window_snapshot_v1.hpp"
#include <unordered_map>
#include <cstring>
#include <iostream>
#include <stdexcept>
using namespace xar::ck3_11906;
struct Fixture {
 std::unordered_map<std::uintptr_t,unsigned char> memory;
 std::uintptr_t base=0x140000000,w=0x100000,h=0x102000,root=0x104000,ts=0x106000,cs=0x108000,tv=0x10A000,cv=0x10C000;
 std::uintptr_t d=0x110000,k=0x112000,holder=0x114000,a=0x116000,b=0x118000,g=0x11A000,first=0x11B000,law=0x11C000;
 std::uintptr_t items=0x120000,pool=0x122000,cache=0x124000,item0=0x128000,item1=0x12A000;
 std::uint32_t did=0x12000001,kid=0x34000002,hid=0x56000003,aid=0x78000004,bid=0x79000005;
 bool change_header=false,bad_total=false;int title_reads=0,calls=0;
 template<class T> void put(std::uintptr_t p,T x){auto *bytes=reinterpret_cast<unsigned char *>(&x);for(std::size_t n=0;n<sizeof(x);++n)memory[p+n]=bytes[n];}
 void zero(std::uintptr_t p,std::size_t n){for(std::size_t x=0;x<n;++x)memory[p+x]=0;}
 void str(std::uintptr_t p,std::string s){zero(p,32);put(p+0x10,std::uint64_t(s.size()));put(p+0x18,std::uint64_t(s.size()>15?63:15));auto at=p;if(s.size()>15){at=p+0x4000;put(p,at);}for(std::size_t n=0;n<=s.size();++n)memory[at+n]=n<s.size()?s[n]:0;}
 static bool read(void *ctx,std::uintptr_t p,void *out,std::size_t n) noexcept {
  auto &f=*static_cast<Fixture *>(ctx);
  if(p==f.w+0xC8&&++f.title_reads==2&&f.change_header)f.put(f.w+0xC8,f.did);
  for(std::size_t k=0;k<n;++k){auto it=f.memory.find(p+k);if(it==f.memory.end())return false;static_cast<unsigned char *>(out)[k]=it->second;}return true;
 }
 static bool key(void *ctx,std::uintptr_t p,std::string &out) noexcept {auto &f=*static_cast<Fixture *>(ctx);if(p==f.d)out="d_fixture";else if(p==f.k)out="k_fixture";else return false;return true;}
 static bool human(void *ctx,std::uint32_t id,bool &out) noexcept {auto &f=*static_cast<Fixture *>(ctx);if(id!=f.aid&&id!=f.bid)return false;out=id==f.bid;return true;}
 static bool breakdown(void *ctx,std::uintptr_t w,std::uintptr_t c,std::uintptr_t &out) noexcept {auto &f=*static_cast<Fixture *>(ctx);++f.calls;if(w!=f.w||c!=f.a)return false;f.put(w+0xAE0+0x78,std::int64_t(f.bad_total?1:100000000000ll));out=w+0xAE0+0x90;return true;}
 Fixture(){
  for(auto p:{w,h,root,ts,cs,tv,cv,d,k,holder,a,b,g,first,law,items,pool,cache,item0,item1})zero(p,0x1000);
  put(base+0x5D1DAF8,ts);put(base+0x5C67568,cs);put(ts+0x20,tv);put(cs+0x20,cv);put(ts+0x2C,std::uint32_t(6));put(cs+0x2C,std::uint32_t(6));
  put(tv+16+8,d);put(tv+32+8,k);put(cv+48+8,holder);put(cv+64+8,a);put(cv+80+8,b);
  put(d+0x10,did);put(k+0x10,kid);put(holder+0x18,hid);put(a+0x18,aid);put(b+0x18,bid);
  put(d+0x128,hid);put(k+0x128,hid);put(holder+0x1C0,g);put(g+0x1EC,std::int32_t(1));put(g+0x1E0,first);put(first,kid);
  put(w,base+0x4587AA8);put(w+0xA0,h);put(w+0x60,root);put(h+0x518,w);put(w+0xC8,kid);put(w+0xBC0,law);put(w+0xBE8,std::uintptr_t(0x133000));str(law+0x18,"fixture_appointment_law");
  auto l=w+0xD0;put(l+0x18,items);put(l+0x24,std::int32_t(2));put(l+0x1C8,pool);put(l+0x1D4,std::int32_t(2));put(l+0x9F8,cache);put(l+0xA04,std::int32_t(2));
  put(items,item0);put(items+8,item1);put(pool,a);put(pool+8,b);put(item0,l);put(item1,l);put(item0+8,aid);put(item0+0xC,std::uint32_t(0));put(item1+8,bid);put(item1+0xC,std::uint32_t(1));
  put(cache+0x40,aid);put(cache+0x28,std::int32_t(1));put(cache+0x38,std::int64_t(100000000000ll));put(cache+0x2F8+0x40,bid);put(cache+0x2F8+0x28,std::int32_t(2));put(cache+0x2F8+0x38,std::int64_t(200000));
  auto tree=w+0xAE0;str(tree+0x18,"fixture score");str(tree+0x38,"");str(tree+0x58,"");put(tree+0x80,std::int64_t(100000));put(tree+0x88,std::int32_t(1));
 }
 AppointmentWindowAccessV1 access(){return {this,read,key,breakdown,human,base,h,w,root};}
 AppointmentWindowRequestV1 request(){return {did,0,1,aid};}
};
void check(bool v,const char *s){if(!v)throw std::runtime_error(s);}
int main(){try{
 int passed=0;
 {Fixture f;AppointmentWindowSnapshotV1 v;check(ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"basic reader");check(v.requested_title_id==f.did&&v.resolved_title_id==f.kid&&v.current_window_title_id==f.kid&&v.requested_resolves_to_current,"normalized title scope");check(v.candidates.size()==1&&v.full_candidate_count==2&&v.next_offset==1,"pagination");check(v.candidates[0].character_id==f.aid&&v.candidates[0].is_ai&&v.breakdown_available&&f.calls==1,"actual full ID score and AI");std::cout<<SerializeAppointmentWindowSnapshotV1(v)<<'\n';++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;auto r=f.request();r.candidate_offset=1;r.breakdown_character_id=0;check(ReadAppointmentWindowSnapshotV1(f.access(),r,v)&&v.candidates[0].is_human_player&&!v.candidates[0].is_ai,"other human player is not AI");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.put(f.item0+8,std::uint32_t(f.aid^0x01000000));check(!ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"stale generation rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.put(f.w+0xD0+0xA04,std::int32_t(1));check(!ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"partial cache rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.put(f.cache+0x40,f.bid);check(!ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"cache ID mismatch rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.change_header=true;check(!ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"changed window rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.bad_total=true;check(ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v)&&!v.breakdown_available&&!v.breakdown_unavailable_reason.empty(),"wrong score total rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;auto p=f.w+0xAE0;f.put(p,p);f.put(p+0xC,std::int32_t(1));check(ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v)&&!v.breakdown_available,"cyclic score tree rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.str(f.law+0x18,"");check(!ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"missing effective law rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;f.put(f.w,std::uintptr_t(0));check(!ReadAppointmentWindowSnapshotV1(f.access(),f.request(),v),"wrong window type rejected");++passed;}
 {Fixture f;AppointmentWindowSnapshotV1 v;auto r=f.request();r.breakdown_character_id=f.hid;check(ReadAppointmentWindowSnapshotV1(f.access(),r,v)&&!v.breakdown_available&&f.calls==0,"non-pool getter target refused");++passed;}
 std::cerr<<"PASS "<<passed<<" synthetic native reader cases; NOT LIVE\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
