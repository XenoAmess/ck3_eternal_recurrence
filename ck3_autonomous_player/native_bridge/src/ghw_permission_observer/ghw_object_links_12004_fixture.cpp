#include "ghw_object_links_12004.hpp"
#include <array>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>

// Owned-memory fixture source only; NOTRUN, no build or execution authorized.
// Calls the actual candidate reader rather than reimplementing its logic.
namespace g = xar::ck3_12004::religion::ghw_links_candidate;
namespace {
struct Block { std::uintptr_t address; std::vector<std::byte> bytes; };
struct Owned {
  std::vector<Block> blocks;
  std::uintptr_t fail_at = 0;
  unsigned faith_reads = 0;
  bool change_second = false;
  static constexpr std::uintptr_t base = 0x10000000;
  static constexpr std::uintptr_t faith = 0x20000000;
  static constexpr std::uintptr_t ghw_db = 0x21000000;
  static constexpr std::uintptr_t ghw_table = 0x22000000;
  static constexpr std::uintptr_t ghw = 0x23000000;
  static constexpr std::uintptr_t war_db = 0x24000000;
  static constexpr std::uintptr_t war_table = 0x25000000;
  static constexpr std::uintptr_t war = 0x26000000;
  static constexpr std::uint32_t ghw_id = 0x02000001;
  static constexpr std::uint32_t war_id = 0x03000002;
  Owned() {
    Add(base+g::kGhwDatabaseSlotRva,8); Add(base+g::kWarDatabaseSlotRva,8);
    Add(faith,0x830); Add(ghw_db,0x30); Add(ghw_table,48);
    Add(ghw,0x30); Add(war_db,0x30); Add(war_table,64); Add(war,0x10);
    Put(base+g::kGhwDatabaseSlotRva,ghw_db);
    Put(base+g::kWarDatabaseSlotRva,war_db);
    Put(faith+g::kFaithGhwReferenceOffset,ghw_id);
    Put(ghw_db+0x20,ghw_table); Put(ghw_db+0x2c,std::uint32_t{3});
    Put(ghw_table+24,ghw); Put(ghw+0x10,ghw_id); Put(ghw+0x14,g::kGhwMagic);
    Put(ghw+0x28,war_id);
    Put(war_db+0x20,war_table); Put(war_db+0x2c,std::uint32_t{4});
    Put(war_table+40,war); Put(war+0x08,war_id); Put(war+0x0c,g::kWarMagic);
  }
  void Add(std::uintptr_t address,std::size_t n) { blocks.push_back({address,std::vector<std::byte>(n)}); }
  template<class T> void Put(std::uintptr_t at,T value) {
    for (auto &b:blocks) if (at>=b.address && at-b.address<=b.bytes.size() &&
        sizeof(T)<=b.bytes.size()-(at-b.address)) {
      std::memcpy(b.bytes.data()+(at-b.address),&value,sizeof(T)); return;
    }
  }
  static bool Read(void *opaque,std::uintptr_t at,void *out,std::size_t n) noexcept {
    auto &f=*static_cast<Owned*>(opaque);
    if (at==faith+g::kFaithGhwReferenceOffset && ++f.faith_reads==2 && f.change_second)
      f.Put(at,g::kNullReference);
    if (at==f.fail_at) return false;
    for (const auto &b:f.blocks) if (at>=b.address && at-b.address<=b.bytes.size() &&
        n<=b.bytes.size()-(at-b.address)) {
      std::memcpy(out,b.bytes.data()+(at-b.address),n); return true;
    }
    return false;
  }
  g::Access access() { return {&Read,this,base,faith,g::kExactSha}; }
};
int failed=0,checks=0;
void Check(bool ok,const char *name) { ++checks; if (!ok) { ++failed; std::printf("FAIL %s\n",name); } }
void Run() {
  {
    Owned f; g::Observation o; Check(g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.stable_two_pass && o.ghw==g::State::present && o.war==g::State::present &&
      o.ghw_reference_full_id==Owned::ghw_id && o.war_reference_full_id==Owned::war_id &&
      o.has_war_started==true,"valid full generations and separate War ID");
  }
  {
    Owned f; f.Put(Owned::faith+g::kFaithGhwReferenceOffset,g::kNullReference);
    f.fail_at=Owned::base+g::kGhwDatabaseSlotRva; g::Observation o;
    Check(g::ReadGhwObjectLinks12004(f.access(),o) && o.ghw==g::State::absent &&
      o.war==g::State::absent && o.faith_has_offensive_ghw==false &&
      !o.has_war_started.has_value(),"Faith null is known absent without database read");
  }
  {
    Owned f; f.Put(Owned::ghw+0x28,g::kNullReference); g::Observation o;
    Check(g::ReadGhwObjectLinks12004(f.access(),o) && o.ghw==g::State::present &&
      o.war==g::State::absent && o.has_war_started==false,"GHW exists before War starts");
  }
  {
    Owned f; f.Put(Owned::ghw+0x10,std::uint32_t{0x01000001}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) && o.stable_two_pass &&
      o.ghw==g::State::unknown && o.failure==g::Failure::generation_mismatch,
      "same low index with old GHW generation is unknown");
  }
  {
    Owned f; f.Put(Owned::war+0x08,std::uint32_t{0x01000002}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) && o.ghw==g::State::present &&
      o.war==g::State::unknown && o.has_war_started==true &&
      o.failure==g::Failure::generation_mismatch,"started reference is not valid War");
  }
  {
    Owned f; f.Put(Owned::base+g::kGhwDatabaseSlotRva,std::uintptr_t{0}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) && o.ghw==g::State::unknown &&
      o.failure==g::Failure::database_unavailable,"non-null reference with missing DB is unknown");
  }
  {
    Owned f; f.Put(Owned::ghw_db+0x2c,std::uint32_t{0x1000001}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::database_count_invalid,"component count bounded");
  }
  {
    Owned f; f.Put(Owned::ghw_db+0x2c,std::uint32_t{1}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::reference_index_out_of_range,"low index range checked");
  }
  {
    Owned f; f.Put(Owned::ghw_db+0x20,std::uintptr_t{0}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::table_unavailable,"missing table is unknown");
  }
  {
    Owned f; f.Put(Owned::ghw_table+24,std::uintptr_t{0}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::object_unavailable,"empty slot is unknown");
  }
  {
    Owned f; f.Put(Owned::war+0x0c,std::uint32_t{0}); g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::magic_mismatch,"War type magic required");
  }
  {
    Owned f; f.fail_at=Owned::ghw+0x28; g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::memory_unreadable,"read failure is unknown");
  }
  {
    Owned f; f.change_second=true; g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(f.access(),o) && !o.stable_two_pass &&
      o.ghw==g::State::unknown && !o.ghw_reference_full_id.has_value() &&
      o.failure==g::Failure::observations_changed,"two-pass change rejects mixed snapshot");
  }
  {
    Owned f; auto a=f.access(); a.executable_sha256="wrong"; g::Observation o;
    Check(!g::ReadGhwObjectLinks12004(a,o) && f.faith_reads==0 &&
      o.failure==g::Failure::input_not_admitted,"wrong build rejected before reading");
  }
  {
    Owned f; auto a=f.access(); a.bound_faith=std::numeric_limits<std::uintptr_t>::max()-1;
    g::Observation o; Check(!g::ReadGhwObjectLinks12004(a,o) &&
      o.failure==g::Failure::arithmetic_overflow,"Faith offset overflow rejected");
  }
  {
    Owned f; f.Put(Owned::ghw_db+0x20,std::numeric_limits<std::uintptr_t>::max()-1);
    g::Observation o; Check(!g::ReadGhwObjectLinks12004(f.access(),o) &&
      o.failure==g::Failure::arithmetic_overflow,"table offset overflow rejected");
  }
}
} // namespace
int main() { Run(); std::printf("%d checks, %d failures\n",checks,failed); return failed?1:0; }
