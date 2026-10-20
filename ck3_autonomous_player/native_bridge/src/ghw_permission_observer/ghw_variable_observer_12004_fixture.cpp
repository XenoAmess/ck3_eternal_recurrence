#include "ghw_variable_observer_12004.hpp"
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

namespace g = xar::ck3_12004::religion::ghw_variables_candidate;
namespace {
struct Region { std::uintptr_t address; std::vector<std::byte> bytes; };
struct Owned {
  std::vector<Region> regions;
  g::BoundFrame frame{71, 53144328, 31254, 103, 19,
      0x10000, 0x11000, true, true, true};
  std::array<std::uintptr_t, 3> contexts{0x20000, 0x21000, 0x22000};
  std::array<std::uintptr_t, 3> rows{0x30000, 0x31000, 0x32000};
  int missing_token = -1;
  int no_context = -1;
  std::uintptr_t denied = 0;
  int frame_reads = 0;
  int identifier_reads = 0;
  bool change_frame = false;
  bool change_rows = false;
  bool negative_token = false;

  Owned() {
    Add(frame.faith_object, 0x100);
    Add(frame.religion_object, 0x100);
    Put(frame.faith_object+8, frame.faith_id);
    Put(frame.faith_object+0x0C, std::uint32_t{0x46616974});
    Put(frame.faith_object+0x8C, frame.religion_id);
    Put(frame.religion_object+8, frame.religion_id);
    Put(frame.religion_object+0x0C, std::uint32_t{0x52656c67});
    for (std::size_t i=0; i<contexts.size(); ++i) {
      Add(contexts[i], 0x50);
      Add(rows[i], 0x80);
      Put(contexts[i]+0x10, rows[i]);
      Put(contexts[i]+0x1C, std::int32_t{0});
      Put(contexts[i]+0x28, std::int32_t{20});
    }
  }
  void Add(std::uintptr_t address, std::size_t size) {
    regions.push_back({address, std::vector<std::byte>(size)});
  }
  template<class T> void Put(std::uintptr_t address, T value) {
    for (auto &r: regions)
      if (address >= r.address && address-r.address <= r.bytes.size() &&
          sizeof(T) <= r.bytes.size()-(address-r.address)) {
        std::memcpy(r.bytes.data()+(address-r.address), &value, sizeof(T));
        return;
      }
    throw std::runtime_error("Fixture Put outside owned regions");
  }
  void Row(int domain, int slot, int token, int expiry, std::uint16_t kind=1) {
    const auto address = rows.at(static_cast<std::size_t>(domain)) +
                         static_cast<std::uintptr_t>(slot)*0x20;
    Put(address+8, static_cast<std::int32_t>(token));
    Put(address+0x0C, static_cast<std::int32_t>(expiry));
    Put(address+0x10, kind);
    Put(address+0x18, std::int64_t{100000});
    Put(contexts.at(static_cast<std::size_t>(domain))+0x1C,
        static_cast<std::int32_t>(slot+1));
  }
  static bool Memory(void *p, std::uintptr_t address, void *out,
                     std::size_t size) noexcept {
    auto &o=*static_cast<Owned *>(p);
    if (address == o.denied) return false;
    for (const auto &r: o.regions)
      if (address >= r.address && address-r.address <= r.bytes.size() &&
          size <= r.bytes.size()-(address-r.address)) {
        std::memcpy(out, r.bytes.data()+(address-r.address), size);
        return true;
      }
    return false;
  }
  static bool Frame(void *p, g::BoundFrame &out) noexcept {
    auto &o=*static_cast<Owned *>(p);
    out=o.frame;
    if (++o.frame_reads==2 && o.change_frame) ++out.played_character_id;
    return true;
  }
  static bool Identifier(void *p, std::string_view key,
                         std::int32_t &out) noexcept {
    auto &o=*static_cast<Owned *>(p);
    ++o.identifier_reads;
    if (o.change_rows && o.identifier_reads==5) {
      const std::int32_t changed=41;
      // Explicit owned-memory mutation between the two producer passes.
      for (auto &r:o.regions)
        if (r.address==o.rows[1])
          std::memcpy(r.bytes.data()+0x0C, &changed, sizeof(changed));
    }
    for (std::size_t i=0; i<g::kKeys.size(); ++i)
      if (key==g::kKeys[i]) {
        if (static_cast<int>(i)==o.missing_token) return false;
        out=o.negative_token ? -1 : 100+static_cast<std::int32_t>(i);
        return true;
      }
    return false;
  }
  static bool Context(void *p, g::Scope scope, std::uint32_t id,
                      std::uintptr_t &out) noexcept {
    auto &o=*static_cast<Owned *>(p);
    const int domain=scope==g::Scope::global ? 0 :
        (scope==g::Scope::religion ? 1 : 2);
    if (domain==o.no_context ||
        (scope==g::Scope::faith && id!=o.frame.faith_id) ||
        (scope==g::Scope::religion && id!=o.frame.religion_id) ||
        (scope==g::Scope::global && id!=0)) return false;
    out=o.contexts[static_cast<std::size_t>(domain)];
    return true;
  }
  g::Access Access() {
    return {this, Memory, Frame, Identifier, Context, g::kExactSha};
  }
};
void Check(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
void Unknown(const g::Scalar &s) {
  Check(!s.read_available && !s.present && !s.expiry_raw &&
        !s.current_counter_raw && !s.remaining_raw, "unavailable must stay null");
}
void Run(const char *name, void (*test)()) {
  test(); std::cout << name << "\n";
}
} // namespace

int main() {
  Run("known_registered_absent_is_distinct_from_unknown", [] {
    Owned o; g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          v.all_fields_observed && v.stable_two_pass, "empty known contexts");
    for (const auto &f:v.fields)
      Check(f.present==false && f.timed==false && f.remaining_raw==-1 &&
            !f.expiry_date_raw, "actual absence only after complete known lookup");
  });
  Run("four_fixed_keys_use_correct_scope_and_fullID", [] {
    Owned o; o.Row(1,0,100,-1); o.Row(1,1,101,140);
    o.Row(2,0,102,300); o.Row(0,0,103,3650); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          v.all_fields_observed, "fixed scope coverage");
    Check(v.fields[0].present==true && v.fields[0].timed==false &&
          v.fields[1].remaining_raw==120 && v.fields[2].remaining_raw==280 &&
          v.fields[3].remaining_raw==3630, "actual raw timing differs per scope");
  });
  Run("unregistered_identifier_not_false", [] {
    Owned o; o.missing_token=1; g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          !v.all_fields_observed, "partial useful reads");
    Unknown(v.fields[1]);
    Check(v.fields[1].failure==g::Failure::identifier_unavailable, "missing token");
  });
  Run("negative_identifier_not_absence", [] {
    Owned o; o.negative_token=true; g::Observation v;
    Check(!g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "no usable token");
    for (const auto &f:v.fields) Unknown(f);
  });
  Run("unavailable_religion_context_not_empty", [] {
    Owned o; o.no_context=1; g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "other scopes useful");
    Unknown(v.fields[0]); Unknown(v.fields[1]);
  });
  Run("failed_clock_read_not_zero", [] {
    Owned o; o.denied=o.contexts[1]+0x28; g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "partial reads");
    Unknown(v.fields[0]); Unknown(v.fields[1]);
  });
  Run("negative_count_not_absence", [] {
    Owned o; o.Put(o.contexts[2]+0x1C,std::int32_t{-1}); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "partial reads");
    Unknown(v.fields[2]);
    Check(v.fields[2].failure==g::Failure::count_invalid, "negative count");
  });
  Run("over_bound_count_does_not_scan", [] {
    Owned o; o.Put(o.contexts[2]+0x1C,std::int32_t{65537}); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "partial reads");
    Unknown(v.fields[2]);
  });
  Run("null_rows_with_count_not_empty", [] {
    Owned o; o.Put(o.contexts[2]+0x1C,std::int32_t{1});
    o.Put(o.contexts[2]+0x10,std::uintptr_t{0}); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "partial reads");
    Unknown(v.fields[2]);
  });
  Run("duplicate_key_is_ambiguous", [] {
    Owned o; o.Row(2,0,102,40); o.Row(2,1,102,50); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "partial reads");
    Unknown(v.fields[2]);
    Check(v.fields[2].failure==g::Failure::duplicate_key, "duplicate key");
  });
  Run("timed_computed_minus_one_is_not_permanent", [] {
    Owned o; o.Row(2,0,102,19); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "timed row");
    Check(v.fields[2].present==true && v.fields[2].timed==true &&
          v.fields[2].remaining_raw==-1, "separate presence/timing from -1");
  });
  Run("expired_or_zero_still_retains_present_row", [] {
    Owned o; o.Row(2,0,102,20); g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v), "zero row");
    Check(v.fields[2].present==true && v.fields[2].timed==true &&
          v.fields[2].remaining_raw==0 && !v.fields[2].expiry_date_raw,
          "do not collapse presence or fabricate calendar");
  });
  Run("non_numeric_payload_not_read_or_exported", [] {
    Owned o; o.Row(2,0,102,40,4); o.denied=o.rows[2]+0x18; g::Observation v;
    Check(g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          v.fields[2].read_available && !v.fields[2].numeric_value_raw,
          "non-numeric payload omitted");
  });
  Run("identity_change_rejects_all_stale_components", [] {
    Owned o; o.change_frame=true; g::Observation v;
    Check(!g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          v.failure==g::Failure::identity_changed, "identity must remain exact");
    for (const auto &f:v.fields) Unknown(f);
  });
  Run("changed_two_pass_values_rejected", [] {
    Owned o; o.Row(1,0,100,40); o.change_rows=true; g::Observation v;
    Check(!g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          v.failure==g::Failure::observations_changed, "two-pass change");
  });
  Run("wrong_build_or_object_generation_not_qualified", [] {
    Owned o; auto a=o.Access(); a.executable_sha256="wrong"; g::Observation v;
    Check(!g::ReadCurrentPlayerGhwVariables12004(a,v), "wrong build");
    o.Put(o.frame.faith_object+8,std::uint32_t{104});
    Check(!g::ReadCurrentPlayerGhwVariables12004(o.Access(),v) &&
          v.failure==g::Failure::object_identity_mismatch, "full ID required");
  });
  std::cout << "16 authored owned-memory cases; actual reader; no CK3 IO\n";
}
