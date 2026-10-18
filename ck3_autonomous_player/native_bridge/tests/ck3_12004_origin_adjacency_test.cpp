// Owned memory only. No game/SDK/native predicate/provider is invoked.
#include "xar_bridge/ck3_12004_origin_adjacency.hpp"
#include "xar_bridge/army_origin_adjacency_v1_serializer.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>

namespace {
using namespace xar::ck3_12004;
template<std::size_t N> using Blob = std::array<std::byte, N>;
template<class B, class T> void Put(B &blob, std::size_t offset, T value) {
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Fixture {
  Blob<0x860> province{};
  Blob<0x60> node{};
  Blob<65 * 0x30> rows{};
  const void *denied = nullptr;
  unsigned reads = 0;
  Fixture() {
    Put(province, 0x10, std::int32_t{2635});
    Put(province, 0x85C, std::uint32_t{0x50726F76});
    Put(province, 0x08, node.data());
    Put(node, 0x50, rows.data());
    Put(node, 0x5C, std::int32_t{3});
    Put(rows, 0x00, std::int32_t{2}); Put(rows, 0x04, std::int32_t{2645});
    Put(rows, 0x30, std::int32_t{0}); Put(rows, 0x34, std::int32_t{2634});
    Put(rows, 0x60, std::int32_t{2}); Put(rows, 0x64, std::int32_t{2645});
  }
  bool Read(const void *base, std::size_t offset, void *out, std::size_t bytes) {
    ++reads;
    const auto address = reinterpret_cast<std::uintptr_t>(base) + offset;
    if (address == reinterpret_cast<std::uintptr_t>(denied)) return false;
    const std::array<std::pair<const void *, std::size_t>, 3> spans{{
        {province.data(), province.size()}, {node.data(), node.size()}, {rows.data(), rows.size()}}};
    for (const auto &[begin_ptr, size] : spans) {
      const auto begin = reinterpret_cast<std::uintptr_t>(begin_ptr);
      if (address >= begin && bytes <= size && address - begin <= size - bytes) {
        std::memcpy(out, reinterpret_cast<const void *>(address), bytes);
        return true;
      }
    }
    return false;
  }
  xar::game::ArmyOriginAdjacencyV1 Sample() {
    return ReadOriginAdjacency12004(province.data(), 2635,
        [&](const void *base, std::size_t offset, void *out, std::size_t bytes) {
          return Read(base, offset, out, bytes);
        });
  }
  xar::game::ArmyOriginAdjacencyV1 Stable() {
    const auto a = Sample(), b = Sample();
    return FinishOriginAdjacency12004(a, b, true);
  }
};
void Emit(const xar::game::ArmyOriginAdjacencyV1 &value) {
  std::string out;
  xar::game::AppendArmyOriginAdjacencyV1(out, value,
      [](auto number) { return std::to_string(number); },
      [](std::string &target, const std::string &value_string) {
        target += '"'; target += value_string; target += '"';
      });
  std::cout << out << '\n';
}
}
int main() {
  try {
    { Fixture f; const auto a = f.Stable();
      Check(a.available && a.collection_complete && a.rows->size() == 3U, "complete native order");
      Check((*a.rows)[0].target_province_id == 2645 && (*a.rows)[2].target_province_id == 2645,
            "native duplicate occurrences retained"); Emit(a); }
    { Fixture f; Put(f.node, 0x5C, std::int32_t{65});
      for (std::size_t i = 0; i < 65U; ++i) {
        Put(f.rows, i * 0x30, std::int32_t{4});
        Put(f.rows, i * 0x30 + 4, static_cast<std::int32_t>(2700U + i));
      }
      const auto a = f.Stable();
      Check(a.available && a.truncated && !a.collection_complete && a.rows->size() == 64U,
            "bounded prefix cannot claim complete65");
      Check(f.reads == 138U, "exactly two bounded origin samples; no65th row read"); Emit(a); }
    { Fixture f; Put(f.node, 0x5C, std::int32_t{0}); f.denied = f.node.data() + 0x50;
      const auto empty = f.Stable();
      Check(empty.available && empty.rows->empty() && empty.collection_complete,
            "observed zero does not read unused data pointer"); Emit(empty);
      f.denied = f.node.data() + 0x5C;
      const auto failed = f.Stable();
      Check(!failed.available && !failed.native_count && !failed.rows,
            "count read failure is unknown, not zero"); Emit(failed); }
    { Fixture f; const auto a = f.Sample(); Put(f.rows, 4, std::int32_t{2636});
      const auto b = f.Sample(); const auto changed = FinishOriginAdjacency12004(a, b, true);
      Check(!changed.available && !changed.rows && !changed.identity_before_after_match,
            "same native storage with changed row is rejected"); Emit(changed);
      const auto wrong_owner = FinishOriginAdjacency12004(b, b, false);
      Check(!wrong_owner.available && !wrong_owner.rows,
            "owning preview A/B identity failure cannot publish stable origin rows"); Emit(wrong_owner); }
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
