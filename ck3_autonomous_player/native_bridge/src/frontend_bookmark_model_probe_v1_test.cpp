#include "xar_bridge/frontend_bookmark_model_probe_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string_view>
#include <utility>
#include <vector>

namespace {

constexpr std::uintptr_t kModuleBase = 0x140000000;
constexpr std::uintptr_t kGuiSlot = kModuleBase + 0x576CC68;

struct Region {
  std::uintptr_t base = 0;
  std::array<std::byte, 512> bytes{};
  std::size_t size = 0;
};

struct Fixture {
  std::vector<Region> regions;

  void Add(std::uintptr_t base, std::size_t size) {
    regions.push_back(Region{base, {}, size});
  }

  template <typename T> void Put(std::uintptr_t address, T value) {
    for (auto &region : regions) {
      if (address >= region.base &&
          address - region.base <= region.size - sizeof(value)) {
        std::memcpy(region.bytes.data() + address - region.base, &value,
                    sizeof(value));
        return;
      }
    }
  }

  void PutBytes(std::uintptr_t address, std::string_view value) {
    for (auto &region : regions) {
      if (address >= region.base && value.size() <= region.size &&
          address - region.base <= region.size - value.size()) {
        std::memcpy(region.bytes.data() + address - region.base,
                    value.data(), value.size());
        return;
      }
    }
  }
};

bool ReadFixture(void *opaque, const void *address, void *output,
                 std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto target = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &region : fixture.regions) {
    if (target >= region.base && size <= region.size &&
        target - region.base <= region.size - size) {
      std::memcpy(output, region.bytes.data() + target - region.base, size);
      return true;
    }
  }
  return false;
}

Fixture MakeFixture() {
  Fixture fixture{};
  for (const auto [base, size] :
       std::array<std::pair<std::uintptr_t, std::size_t>, 8>{{
           {kGuiSlot, 8}, {0x1000, 512}, {0x2000, 512},
           {0x3000, 512}, {0x4000, 512}, {0x5000, 512},
           {0x6000, 512}, {0x7000, 512}}}) {
    fixture.Add(base, size);
  }
  fixture.Add(0x8000, 512);
  fixture.Add(0x9000, 512);
  fixture.Add(0xA000, 512);
  fixture.Add(0xB000, 512);
  fixture.Add(0xC000, 512);
  fixture.Add(0xD000, 512);
  fixture.Add(0xE000, 512);
  fixture.Add(0xF000, 512);
  fixture.Put(kGuiSlot, static_cast<std::uintptr_t>(0x1000));
  fixture.Put(0x1000, kModuleBase + 0x4093158);
  fixture.Put(0x1000 + 0x1B8, static_cast<std::uintptr_t>(0x3000));
  fixture.Put(0x3000, kModuleBase + 0x43FB390);
  fixture.Put(0x3000 + 0x58, static_cast<std::uintptr_t>(0x4000));
  fixture.Put(0x4000, kModuleBase + 0x43FB3B0);
  fixture.Put(0x1000 + 0x78, static_cast<std::uintptr_t>(0x5000));
  fixture.Put(0x5000 + 0x10, static_cast<std::uintptr_t>(0x6000));
  fixture.Put(0x6000 + 0x08, static_cast<std::uintptr_t>(0x7000));
  fixture.Put(0x7000 + 0x30, static_cast<std::uintptr_t>(0x8000));
  fixture.Put(0x8000, kModuleBase + 0x410B070);
  fixture.Put(0x8000 + 0x78, static_cast<std::uintptr_t>(0x2000));
  fixture.Put(0x8000 + 0x108, static_cast<std::uintptr_t>(0xD000));
  fixture.Put(0x8000 + 0x150, static_cast<std::uintptr_t>(0x9000));
  fixture.Put(0x8000 + 0x158, std::int32_t{-1});
  fixture.Put(0x8000 + 0x15C, std::int32_t{-1});
  fixture.Put(0x9000, kModuleBase + 0x43FB390);
  fixture.Put(0xD000, kModuleBase + 0x43FB3A0);
  constexpr std::string_view group_key = "bm_group_1066";
  fixture.PutBytes(0xD000 + 0x38, group_key);
  fixture.Put(0xD000 + 0x48, std::uint64_t{group_key.size()});
  fixture.Put(0xD000 + 0x50, std::uint64_t{15});
  constexpr std::string_view bookmark_key = "bm_1066_rags_to_riches";
  fixture.Put(0x9000 + 0x18, std::uintptr_t{0xB000});
  fixture.Put(0x9000 + 0x28, std::uint64_t{bookmark_key.size()});
  fixture.Put(0x9000 + 0x30, std::uint64_t{bookmark_key.size()});
  fixture.PutBytes(0xB000, bookmark_key);
  fixture.Put(0x9000 + 0x38, std::uint64_t{0x12345678});
  fixture.Put(0x9000 + 0x170, std::uint64_t{0xA000});
  fixture.Put(0x9000 + 0x178, std::uint32_t{5});
  fixture.Put(0x9000 + 0x17C, std::uint32_t{1});
  fixture.Put(0x9000 + 0x180, std::int32_t{-1});
  constexpr std::string_view character_key =
      "bookmark_rags_to_riches_petty_king_murchad";
  fixture.Put(0xA000 + 0x08, std::uintptr_t{0xC000});
  fixture.Put(0xA000 + 0x18, std::uint64_t{character_key.size()});
  fixture.Put(0xA000 + 0x20, std::uint64_t{character_key.size()});
  fixture.Put(0xA000 + 0x130, std::uintptr_t{0x9000});
  fixture.PutBytes(0xC000, character_key);
  constexpr std::string_view government_key = "feudal_government";
  fixture.Put(0xE000 + 0x18, std::uintptr_t{0xF000});
  fixture.Put(0xE000 + 0x28, std::uint64_t{government_key.size()});
  fixture.Put(0xE000 + 0x30, std::uint64_t{government_key.size()});
  fixture.PutBytes(0xF000, government_key);
  return fixture;
}

void *FakeFinalGovernment(void *, const void *character) noexcept {
  return character == reinterpret_cast<const void *>(0xA000)
             ? reinterpret_cast<void *>(0xE000)
             : nullptr;
}

bool Probe(Fixture &fixture,
           xar::ck3_11906::FrontendBookmarkModelProbeV1 &output,
           void *root = reinterpret_cast<void *>(0x2000)) {
  xar::ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 environment{};
  environment.module_base = kModuleBase;
  environment.exact_build_admitted = true;
  environment.gui_global_slot = reinterpret_cast<void **>(kGuiSlot);
  xar::ck3_11906::ZhongguoScoreboardAccessV1 access{};
  access.context = &fixture;
  access.read_memory = &ReadFixture;
  return xar::ck3_11906::ProbeFrontendBookmarkModelV1(
      environment, access, root, output, &FakeFinalGovernment);
}

} // namespace

int main() {
  using xar::ck3_11906::FrontendBookmarkModelProbeV1;
  auto fixture = MakeFixture();
  FrontendBookmarkModelProbeV1 result{};
  if (!Probe(fixture, result) || !result.model_indices_available ||
      !result.setup_view_matches_bookmarks_root ||
      result.interface_application_chain_level != 0 ||
      result.selected_character_index != -1 ||
      result.hovered_character_index != -1 ||
      !result.selected_bookmark_group_key_available ||
      result.selected_bookmark_group_key != "bm_group_1066" ||
      !result.selected_bookmark_key_available ||
      result.selected_bookmark_key != "bm_1066_rags_to_riches" ||
      !result.selected_date_raw_available ||
      result.selected_date_raw != 0x12345678 ||
      !result.bookmark_character_keys_available ||
      result.bookmark_character_count != 1 ||
      result.bookmark_character_keys[0] !=
          "bookmark_rags_to_riches_petty_king_murchad" ||
      !result.government_type_keys_available ||
      result.government_type_keys[0] != "feudal_government" ||
      !result.supported_1066_candidate_present ||
      result.supported_1066_candidate_index != 0 ||
      !result.supported_1066_candidate_feudal ||
      result.candidate_identity_ready ||
      result.unavailable_reason !=
          "runtime_bookmark_date_unverified") {
    std::fprintf(stderr,
                 "verified frontend owner/model probe failed: reason=%s group=%s bookmark=%s count=%d candidate=%d feudal=%d government=%s\n",
                 result.unavailable_reason.c_str(),
                 result.selected_bookmark_group_key.c_str(),
                 result.selected_bookmark_key.c_str(),
                 result.bookmark_character_count,
                 result.supported_1066_candidate_index,
                 result.supported_1066_candidate_feudal,
                 result.government_type_keys[0].c_str());
    return 1;
  }
  fixture.Put(0x8000 + 0x108, std::uintptr_t{0});
  if (!Probe(fixture, result) ||
      result.selected_bookmark_group_key_available ||
      !result.selected_bookmark_key_available ||
      !result.bookmark_character_keys_available) {
    std::fprintf(stderr, "cleared selected group is a legal bookmark state\n");
    return 1;
  }
  fixture.Put(0x8000 + 0x108, std::uintptr_t{0xD000});
  // Factory 0x7F7BC0 can leave the shared global in the base-only class;
  // its intermediate/base vtable is never accepted as CInterfaceApplication.
  fixture.Put(0x1000, kModuleBase + 0x44F4650);
  if (!Probe(fixture, result) || result.model_indices_available ||
      result.unavailable_reason !=
          "interface_application_not_in_gui_chain") {
    std::fprintf(stderr, "unverified application must fail closed\n");
    return 1;
  }
  fixture.Put(0x1000, kModuleBase + 0x4093158);
  fixture.Put(0x9000 + 0x17C, std::uint32_t{6});
  if (!Probe(fixture, result) || result.bookmark_character_keys_available ||
      result.unavailable_reason !=
          "selected_bookmark_character_collection_unverified") {
    std::fprintf(stderr, "count above collection capacity must fail closed\n");
    return 1;
  }
  fixture.Put(0x9000 + 0x17C, std::uint32_t{1});
  if (!Probe(fixture, result, reinterpret_cast<void *>(0x2001)) ||
      result.model_indices_available ||
      result.unavailable_reason !=
          "frontend_setup_view_root_mismatch") {
    std::fprintf(stderr, "unmatched bookmark root must fail closed\n");
    return 1;
  }
  return 0;
}
