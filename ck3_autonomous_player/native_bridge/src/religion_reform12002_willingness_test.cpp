#include "xar_bridge/religion_reform12002_willingness.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>

using namespace xar::ck3_12002::religion_reform;
namespace {
std::array<std::byte, 0xA0> faith{};
std::array<std::byte, 0x8B8> main_rite{};
std::array<std::byte, 0x8B8> actor_rite{};
bool unresolved = false;
bool change_main = false;
int predicate_calls = 0;
template <typename T, std::size_t N>
void Put(std::array<std::byte, N> &object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
void *Main(void *) { return unresolved ? nullptr : main_rite.data(); }
bool Unreformed(void *) {
  ++predicate_calls;
  if (change_main) Put(faith, kFaithMainRiteIdOffset, 0x82000005U);
  return static_cast<unsigned char>(main_rite[kRiteUnreformedOffset]) != 0;
}
void Check(bool condition, const char *case_name) {
  if (!condition) throw std::runtime_error(case_name);
}
void Reset(std::uint32_t faith_id = 0x81000001U,
           std::uint32_t main_id = 0x82000002U) {
  faith.fill({}); main_rite.fill({}); actor_rite.fill({});
  Put(faith, kObjectFullReferenceOffset, faith_id);
  Put(faith, kFaithMainRiteIdOffset, main_id);
  Put(main_rite, kObjectFullReferenceOffset, main_id);
  Put(actor_rite, kObjectFullReferenceOffset, 0x83000003U);
  unresolved = false; change_main = false; predicate_calls = 0;
}
}
int main() {
  const MainRiteBindings b{true, Main, Unreformed};
  Reset();
  Put(main_rite, kRiteUnreformedOffset, std::uint8_t{1});
  auto v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0x81000001U);
  Check(v.status == MainRiteStatus::observed && v.is_unreformed &&
        v.main_rite_id == 0x82000002U, "unreformed main Rite");
  Reset();
  // The actor's different Rite does not replace the native Faith main Rite.
  Put(actor_rite, kRiteUnreformedOffset, std::uint8_t{1});
  v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0x81000001U);
  Check(v.status == MainRiteStatus::observed && !v.is_unreformed &&
        predicate_calls == 1, "false is observed; actor Rite is different");
  Reset(0, 0);
  v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0);
  Check(v.status == MainRiteStatus::observed && v.faith_id == 0 &&
        v.main_rite_id == 0 && !v.is_unreformed, "zero full reference");
  Reset(); unresolved = true;
  v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0x81000001U);
  Check(v.status == MainRiteStatus::main_rite_unavailable && predicate_calls == 0,
        "unresolved does not become false");
  Reset();
  Put(main_rite, kObjectFullReferenceOffset, 0x84000002U);
  v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0x81000001U);
  Check(v.status == MainRiteStatus::main_rite_unavailable && predicate_calls == 0,
        "same index different generation");
  Reset();
  v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0x85000001U);
  Check(v.status == MainRiteStatus::faith_unavailable && predicate_calls == 0,
        "Faith full identity");
  Reset(); change_main = true;
  v = ReadFaithMainRiteUnreformed12002(b, faith.data(), 0x81000001U);
  Check(v.status == MainRiteStatus::state_changed && predicate_calls == 1,
        "main Rite changed during getter");
  Check(!BindFaithMainRiteUnreformedImage12002(0x140000000ULL, "wrong").enabled &&
        BindFaithMainRiteUnreformedImage12002(
            0x140000000ULL, xar::ck3_12002::kExecutableSha256).enabled,
        "exact image binding");
  std::cout << "PASS 8 cases: actual Faith main Rite bool reader\n";
}
