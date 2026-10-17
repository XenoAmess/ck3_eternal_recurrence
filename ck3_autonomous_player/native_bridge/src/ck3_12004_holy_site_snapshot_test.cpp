// Owned synthetic storage -> production source-bound reader -> production JSON.
// This is not a live-game or native adoption qualification.
#include "xar_bridge/ck3_12004_holy_site_snapshot.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace h = xar::ck3_12004::religion::holy_site;
namespace {
unsigned checks = 0;
void Check(bool ok, const char *why) { ++checks; if (!ok) throw std::runtime_error(why); }
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <class B, class T> void Put(B &b, std::size_t o, T v) { std::memcpy(b.data()+o, &v, sizeof(v)); }
template <class B, class T, std::size_t N> void Ids(B &b, std::size_t o, std::array<T,N> &rows) {
  Put(b,o,rows.data()); Put(b,o+8,static_cast<std::uint32_t>(N));
  Put(b,o+12,static_cast<std::uint32_t>(N));
}
bool Copy(void *, const void *p, void *o, std::size_t n) noexcept { if (!p) return false; std::memcpy(o,p,n); return true; }
struct Fixture {
  static constexpr std::uint32_t site_id=0x81000002U, other_id=0x82000003U;
  static constexpr std::uint32_t faith_id=0x83000001U, faith_other_id=0x84000002U;
  Bytes<0x30> store{},faithstore{}; Bytes<0x80> slots{},faithslots{};
  Bytes<0xB8> site{},other{}; Bytes<0x40> type{},othertype{};
  Bytes<0x8C0> faith{},faithother{};
  Bytes<0x28> owner{}; Bytes<0x90> gfx{}; Bytes<0x5E0> handler{}; Bytes<0xD0> window{};
  void *storeptr=store.data(),*faithptr=faithstore.data();
  std::array<std::uint32_t,2> current{site_id,site_id};
  std::array<std::uint32_t,1> other_sites{site_id}, eminent{site_id};
  std::array<std::uint32_t,2> associations{faith_id,faith_other_id};
  std::array<std::uint32_t,2> artifacts{0x85000004U,0x86000004U};
  Fixture() {
    Put(store,0x20,slots.data());Put(store,0x2C,std::uint32_t{8});
    Put(faithstore,0x20,faithslots.data());Put(faithstore,0x2C,std::uint32_t{8});
    Put(slots,2*16+8,site.data());Put(slots,3*16+8,other.data());
    Put(faithslots,1*16+8,faith.data());Put(faithslots,2*16+8,faithother.data());
    Init(site,type,site_id,"nadjaf");Init(other,othertype,other_id,"ctesiphon");
    Put(faith,8,faith_id);Put(faithother,8,faith_other_id);
    Ids(faith,0x890,current);Ids(faith,0x8A8,eminent);Ids(faithother,0x890,other_sites);
    Ids(site,0x98,associations);Ids(site,0x80,artifacts);
    Put(owner,0x10,gfx.data());Put(gfx,0x88,handler.data());Put(handler,0x5D8,window.data());
    Put(window,0,std::uintptr_t{0x140000000ULL+72950584});
    Put(window,0x98,gfx.data());Put(window,0xA0,handler.data());
    Put(window,0x60,site.data());Put(window,0xC8,site_id);Put(window,0xCC,std::uint32_t{0});
  }
  template<class B> void Init(B &b,Bytes<0x40>&t,std::uint32_t id,const char *key) {
    Put(b,0x10,id);Put(b,0x14,std::uint32_t{0x486F5374});Put(b,0x20,t.data());
    Put(b,0xB0,std::uint32_t{0x87000005});Put(b,0x60,std::uint32_t{0xFFFFFFFF});Put(b,0x64,id);
    std::memcpy(t.data()+0x18,key,std::strlen(key));
    Put(t,0x28,static_cast<std::uint64_t>(std::strlen(key)));Put(t,0x30,std::uint64_t{15});
    Put(t,0x38,std::uint32_t{0x4744624F});
  }
  h::Bindings Bind() { return {true,0x140000000ULL,&storeptr,&faithptr,&Copy,nullptr}; }
  xar::ck3_12002::religion::Context Context() {
    xar::ck3_12002::religion::Context c{};c.available=true;c.capture_epoch=17;
    c.date_raw=53175816;c.played_character_id=0x03000004;c.rite_id=0;c.faith_id=faith_id;return c;
  }
};
void Save(const std::filesystem::path &dir,const char *name,const h::Snapshot &s) {
  std::ofstream f(dir/name);f<<h::SerializeHolySiteCommand12004(s,"g2-read-holy-site-fixture",701,s.date_raw)<<'\n';Check(bool(f),"fixture artifact written");
}
}
int main(int argc,char **argv) {
 try {
  Check(argc==2,"output argument");std::filesystem::path dir(argv[1]);std::filesystem::create_directories(dir);
  Fixture f;auto b=f.Bind();auto c=f.Context();h::Snapshot s;
  Check(h::ReadHolySiteSnapshot12004(b,f.owner.data(),c,std::nullopt,s),"production reader");
  Check(s.current_faith_sites.size()==2&&s.current_faith_sites[0].holy_site_id==Fixture::site_id&&
        s.current_faith_sites[1].holy_site_id==Fixture::site_id,"native order and duplicate full references");
  Check(s.selected_holy_site&&s.selected_holy_site->associated_faiths.size()==2&&
        s.selected_holy_site->associated_faiths[0].eminent&&
        !s.selected_holy_site->associated_faiths[1].eminent,"per-Faith independent eminent true and observed false");
  Check(s.selected_holy_site->inventory.artifact_ids==std::vector<std::uint32_t>(f.artifacts.begin(),f.artifacts.end()),
        "artifact generations survive same low index");
  Check(s.loaded_registry_roster.size()==2&&s.window_model.holy_site_item_raw==0U,"registry and zero item raw");
  Save(dir,"window-selected.json",s);
  Check(h::ReadHolySiteSnapshot12004(b,f.owner.data(),c,Fixture::other_id,s)&&
        s.selected_holy_site&&s.selected_holy_site->holy_site_id==Fixture::other_id,"explicit reference overrides window");
  Save(dir,"explicit-selected.json",s);
  const auto stale=Fixture::site_id+0x1000000U;
  Check(h::ReadHolySiteSnapshot12004(b,f.owner.data(),c,stale,s)&&s.selected_holy_site&&!s.selected_holy_site->available&&
        s.selected_holy_site->unavailable_reason=="holy_site_full_reference_unavailable","stale generation is unavailable not aliased");
  Save(dir,"stale-generation.json",s);
  Put(f.faithstore,0x2C,std::uint32_t{0});
  Check(!h::ReadHolySiteSnapshot12004(b,f.owner.data(),c,std::nullopt,s)&&
        s.unavailable_reason=="current_faith_holy_site_array_unavailable","root unavailable preserves source diagnostic");
  Save(dir,"faith-unavailable.json",s);
  Check(!h::BindHolySiteSnapshotImage12004(0x140000000ULL,"wrong-image").enabled,"foreign executable rejected");
  std::cout<<"PASS checks="<<checks<<" actual_reader=true actual_serializer=true synthetic_storage=true live=false\n";
  return 0;
 } catch(const std::exception &e) {std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}
}
