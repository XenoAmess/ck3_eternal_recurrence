#include "xar_bridge/construction_owner_mode3_m4_12004.hpp"

#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct World {
  struct Block {
    std::uintptr_t address;
    std::vector<std::uint8_t> bytes;
  };
  std::vector<Block> blocks;
  static constexpr std::uintptr_t base = 0x100000000ull;
  static constexpr std::uintptr_t receiver = 0x200000000ull;
  static constexpr std::uintptr_t nested = 0x200001000ull;
  static constexpr std::uintptr_t ids = 0x200002000ull;
  static constexpr std::uintptr_t title_storage = 0x200003000ull;
  static constexpr std::uintptr_t title_slots = 0x200004000ull;
  static constexpr std::uintptr_t title = 0x200005000ull;
  static constexpr std::uintptr_t rank = 0x200006000ull;
  static constexpr std::uintptr_t province = 0x200007000ull;
  static constexpr std::uintptr_t character = 0x200008000ull;
  static constexpr std::uintptr_t slot_object = 0x200009000ull;
  static constexpr std::uintptr_t default_object = 0x20000A000ull;
  static constexpr std::uintptr_t character_context = 0x20000B000ull;
  static constexpr std::uintptr_t returned_object = 0x20000C000ull;
  static constexpr std::uint32_t full_id = 0xA1000001u;
  static constexpr std::uint64_t frame = 0xFEDCBA9876543210ull;
  std::int32_t child_count = 9;
  bool child_available = true;
  bool predicate = false;
  bool predicate_available = true;
  std::size_t count_calls = 0, predicate_calls = 0;
  std::uintptr_t received_receiver = 0, received_subobject = 0;
  std::uint64_t received_frame = 0;
  std::uintptr_t denied_address = 0;

  void Add(std::uintptr_t address, std::size_t size) {
    blocks.push_back({address, std::vector<std::uint8_t>(size)});
  }
  template <typename T>
  void Put(std::uintptr_t address, T value) {
    for (auto &block : blocks) {
      if (address >= block.address && address - block.address <= block.bytes.size() &&
          sizeof(T) <= block.bytes.size() - static_cast<std::size_t>(address-block.address)) {
        std::memcpy(block.bytes.data()+static_cast<std::size_t>(address-block.address),
                    &value, sizeof(value));
        return;
      }
    }
    throw std::runtime_error("fixture destination outside owned backing");
  }
  static bool Read(void *context, const void *source, void *destination,
                   std::size_t bytes) {
    auto &world = *static_cast<World *>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    if (address == world.denied_address) return false;
    for (const auto &block : world.blocks) {
      if (address >= block.address && address - block.address <= block.bytes.size() &&
          bytes <= block.bytes.size() - static_cast<std::size_t>(address-block.address)) {
        std::memcpy(destination,
                    block.bytes.data()+static_cast<std::size_t>(address-block.address), bytes);
        return true;
      }
    }
    return false;
  }
  static bool Count(void *context, const RawReceiverAccessV1 &,
                    std::uintptr_t actual_receiver, std::uint64_t actual_frame,
                    std::int32_t &out) noexcept {
    auto &world = *static_cast<World *>(context);
    ++world.count_calls;
    world.received_receiver = actual_receiver;
    world.received_frame = actual_frame;
    if (!world.child_available) return false;
    out = world.child_count;
    return true;
  }
  static bool Predicate(void *context, const RawReceiverAccessV1 &,
                        std::uintptr_t actual_subobject,
                        std::uint64_t actual_frame, bool &out) noexcept {
    auto &world = *static_cast<World *>(context);
    ++world.predicate_calls;
    world.received_subobject = actual_subobject;
    world.received_frame = actual_frame;
    if (!world.predicate_available) return false;
    out = world.predicate;
    return true;
  }
  RawReceiverAccessV1 Access() {
    return {this, Read, base, true};
  }
  Mode3M4ReadBindingsV1 Bindings() {
    return {this, Count, true, this, Predicate, true};
  }
  World() {
    for (const auto [address, size] :
         std::vector<std::pair<std::uintptr_t,std::size_t>>{
             {receiver,0x200}, {nested,0x420}, {ids,0x20},
             {title_storage,0x40}, {title_slots,0x40}, {title,0x360},
             {rank,0x80}, {province,0x880}, {character,0x200},
             {slot_object,0x100}, {default_object,0x50},
             {character_context,0x100}, {returned_object,0x440}})
      Add(address,size);
    for (const auto address : {base+0x5D1DAF8, base+0x5D1DAE0,
                              base+0x5C67568, base+0x5C67570,
                              base+0x5D1E320, base+0x5D1E2A8})
      Add(address,8);
    Add(base+0x5459C88,0x10);
    Put(receiver+0x1C0,nested);
    Put(nested+0x1E0,ids);
    Put(nested+0x1EC,std::int32_t{3});
    Put(nested+0x3D8,std::int32_t{1});
    Put(ids,full_id); Put(ids+4,full_id); Put(ids+8,full_id);
    Put(base+0x5D1DAF8,title_storage);
    Put(base+0x5D1DAE0,title);
    Put(title_storage+0x20,title_slots);
    Put(title_storage+0x2C,std::uint32_t{2});
    Put(title_slots+24,title);
    Put(title+0x10,full_id);
    Put(title+0x48,rank);
    Put(title+0x12C,std::uint32_t{0xFFFFFFFFu});
    Put(title+0x338,province);
    Put(base+0x5C67568,std::uintptr_t{0});
    Put(base+0x5C67570,character);
    Put(base+0x5D1E320,default_object);
    Put(base+0x5D1E2A8,returned_object);
    Put(province+0x85C,std::uint32_t{0x50726F76u});
    Put(province+0x628,std::uint8_t{1});
    Put(province+0x620,slot_object);
    Put(province+0x728,std::uint8_t{2});
    Put(character+0x18,std::uint32_t{0x81000001u});
    Put(character+0x1C,std::uint32_t{0x43686172u});
    Put(character+0x1D0,character_context);
    Put(character_context+0x88,returned_object);
    Put(returned_object+0x418,slot_object);
  }
};

} // namespace

// Sole03d/10 connected compound calls this new export once. No main, native
// getter, initializer, executable invocation or old fixture exists here.
void RunNewMode3M4Cases12004() {
  {
    World world;
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(result.source_ready && result.signed_eax == std::int32_t{5},
            "ordered duplicate count and reduction");
    Require(result.count_7450.occurrences.size()==std::size_t{3} &&
            result.count_7450.signed_eax==std::int32_t{3},
            "three raw duplicate occurrences retained");
    Require(result.count_7450.occurrences[2].raw_full_id==World::full_id &&
            result.count_7450.occurrences[2].raw_predicate_byte==std::uint8_t{2},
            "raw FullID and nonboolean AL byte preserved");
    Require(world.count_calls==std::size_t{1} &&
            world.predicate_calls==std::size_t{3} &&
            world.received_receiver==World::receiver &&
            world.received_subobject==World::province+0x620 &&
            world.received_frame==World::frame &&
            result.snapshot_revision==World::frame,
            "actual receiver/subobject and full64 frame");
  }
  {
    World world; world.Put(World::nested+0x3D8,std::int32_t{-7});
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(result.source_ready && result.minimum_signed==std::int32_t{1} &&
            result.signed_eax==std::int32_t{5},"signed minimum floor");
  }
  {
    World world; world.Put(World::nested+0x3D8,std::int32_t{7});
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(result.source_ready && result.after_minimum_signed==std::int32_t{-1} &&
            result.signed_eax==std::int32_t{0},"signed final zero clamp");
  }
  {
    World world; world.Put(World::nested+0x1EC,std::int32_t{0});
    world.Put(World::nested+0x3D8,std::numeric_limits<std::int32_t>::max());
    world.child_count=-2;
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(result.source_ready && result.signed_eax==
            std::numeric_limits<std::int32_t>::max(),"literal wrapping32 subtraction");
  }
  {
    World world; world.Put(World::receiver+0x1C0,std::uintptr_t{0});
    world.Put(World::base+0x5459C88,std::uintptr_t{0});
    world.Put(World::base+0x5459C94,std::int32_t{0});
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(result.source_ready && result.count_7450.signed_eax==std::int32_t{0} &&
            result.minimum_signed==std::int32_t{1} &&
            result.signed_eax==std::int32_t{8},"static empty descriptor and null minimum");
  }
  {
    World world; world.child_available=false;
    auto bindings=world.Bindings(); std::int32_t sentinel=321;
    Require(!ReadMode3M4SignedEaxChildV1(&bindings,world.Access(),World::receiver,
                                       World::frame,sentinel) && sentinel==321,
            "missing child stays unavailable and preserves out");
  }
  {
    World world; world.Put(World::nested+0x1EC,std::int32_t{-1});
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(!result.source_ready && !result.signed_eax &&
            result.count_7450.declared_count==std::int32_t{-1} &&
            result.count_71e0_signed_eax==std::int32_t{9},
            "negative extent independent partial");
  }
  {
    World world;
    const auto count=ReadMode3M4Count7450V1(world.Access(),World::receiver,
                                          World::frame,world.Bindings(),2);
    Require(!count.source_ready && count.declared_count==std::int32_t{3} &&
            count.occurrences.empty(),"bounded list retains declared count");
  }
  {
    World world; world.predicate_available=false;
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(!result.source_ready && !result.count_7450.signed_eax &&
            result.count_7450.occurrences.size()==std::size_t{3},
            "missing occurrence predicate never numeric zero");
  }
  {
    World world; world.predicate=true;
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(result.source_ready && result.count_7450.signed_eax==std::int32_t{3},
            "reached readonly returned object equality");
    world.Put(World::returned_object+0x418,std::uintptr_t{0});
    const auto mismatch=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                              World::frame,world.Bindings());
    Require(mismatch.source_ready && mismatch.count_7450.signed_eax==std::int32_t{0},
            "known returned object mismatch counts false");
  }
  {
    World world; world.Put(World::title+0x10,std::uint32_t{0});
    const auto count=ReadMode3M4Count7450V1(world.Access(),World::receiver,
                                          World::frame,world.Bindings());
    Require(count.source_ready && !count.occurrences[0].title_registry_matched &&
            count.occurrences[0].selected_title==World::title,
            "full ID mismatch selects actual title fallback");
  }
  {
    World world; world.Put(World::province+0x728,std::uint8_t{0});
    // Default2C39EE0 sees count0 and the actual global default with wrong magic:
    // ALfalse. Actual71E0 counts each reached occurrence through that same
    // false building-magic branch; no native getter or child stub is used.
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame);
    Require(result.source_ready && result.count_7450.signed_eax==std::int32_t{0} &&
            result.count_71e0_signed_eax==std::int32_t{3} &&
            result.signed_eax==std::int32_t{2} && !result.native_function_invoked,
            "production22 and23 providers produce positive M4");
    std::int32_t out=-123;
    Require(ReadMode3M4SignedEaxChildV1(nullptr,world.Access(),World::receiver,
                                      World::frame,out) && out==2,
            "03d default callback actual positive EAX");
  }
  {
    World world; world.denied_address=World::nested+0x3D8;
    const auto result=ReadMode3M4ReductionV1(world.Access(),World::receiver,
                                            World::frame,world.Bindings());
    Require(!result.source_ready && !result.minimum_signed &&
            result.count_7450.source_ready && result.count_71e0_signed_eax,
            "missing minimum preserves independent counts");
  }
  {
    World world; auto access=world.Access(); access.exact_12004_bound=false;
    const auto result=ReadMode3M4ReductionV1(access,World::receiver,
                                            World::frame,world.Bindings());
    Require(!result.source_ready && world.count_calls==std::size_t{0},
            "unadmitted build avoids child projection");
  }
  std::cout << "PASS 14 new Mode3 M4 source-memory cases\n";
}

} // namespace xar::ck3_12004::construction_owner_mode3
