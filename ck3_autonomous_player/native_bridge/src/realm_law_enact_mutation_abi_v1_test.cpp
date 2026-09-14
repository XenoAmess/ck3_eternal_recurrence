#include "xar_bridge/realm_law_enact_mutation_abi_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using xar::ck3_11906::private_law::RealmLawMutationAbiFailureV1;
using xar::ck3_11906::private_law::RealmLawMutationAbiReaderV1;
using xar::ck3_11906::private_law::VerifyRealmLawEnactMutationAbiV1;

void Require(bool condition, const char *message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

struct Section {
  std::uint32_t virtual_address = 0;
  std::uint32_t mapped_size = 0;
  std::uint32_t raw_pointer = 0;
  std::uint32_t raw_size = 0;
};

class DiskPeImage {
public:
  explicit DiskPeImage(const char *path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    Require(input.good(), "could not open exact CK3 executable");
    const std::streamoff length = input.tellg();
    Require(length > 0, "exact CK3 executable is empty");
    bytes_.resize(static_cast<std::size_t>(length));
    input.seekg(0, std::ios::beg);
    input.read(reinterpret_cast<char *>(bytes_.data()), length);
    Require(input.good(), "could not read exact CK3 executable");

    Require(ReadU16(0) == 0x5A4D, "DOS signature mismatch");
    const std::size_t pe = ReadU32(0x3C);
    Require(ReadU32(pe) == 0x00004550, "PE signature mismatch");
    const std::size_t coff = pe + 4;
    Require(ReadU16(coff) == 0x8664, "PE machine mismatch");
    const std::uint16_t section_count = ReadU16(coff + 2);
    const std::uint16_t optional_size = ReadU16(coff + 16);
    const std::size_t optional = coff + 20;
    Require(ReadU16(optional) == 0x20B, "PE32+ header mismatch");
    preferred_base_ = ReadU64(optional + 24);
    image_size_ = ReadU32(optional + 56);
    headers_size_ = ReadU32(optional + 60);
    const std::size_t section_table = optional + optional_size;
    for (std::uint16_t index = 0; index < section_count; ++index) {
      const std::size_t entry = section_table + index * 40U;
      const std::uint32_t virtual_size = ReadU32(entry + 8);
      const std::uint32_t raw_size = ReadU32(entry + 16);
      sections_.push_back(
          {ReadU32(entry + 12),
           virtual_size > raw_size ? virtual_size : raw_size,
           ReadU32(entry + 20), raw_size});
    }
  }

  std::uintptr_t preferred_base() const noexcept { return preferred_base_; }

  bool Read(std::uintptr_t rva, void *destination,
            std::size_t size) const noexcept {
    if (destination == nullptr || rva > image_size_ ||
        size > image_size_ - rva) {
      return false;
    }
    if (rva < headers_size_) {
      return Copy(static_cast<std::size_t>(rva), destination, size);
    }
    for (const auto &section : sections_) {
      if (rva >= section.virtual_address) {
        const std::uintptr_t relative = rva - section.virtual_address;
        if (relative <= section.mapped_size &&
            size <= section.mapped_size - relative &&
            relative <= section.raw_size && size <= section.raw_size - relative) {
          return Copy(static_cast<std::size_t>(section.raw_pointer + relative),
                      destination, size);
        }
      }
    }
    return false;
  }

private:
  std::uint16_t ReadU16(std::size_t offset) const {
    Require(offset <= bytes_.size() && 2 <= bytes_.size() - offset,
            "PE uint16 read out of range");
    std::uint16_t value = 0;
    std::memcpy(&value, bytes_.data() + offset, sizeof(value));
    return value;
  }

  std::uint32_t ReadU32(std::size_t offset) const {
    Require(offset <= bytes_.size() && 4 <= bytes_.size() - offset,
            "PE uint32 read out of range");
    std::uint32_t value = 0;
    std::memcpy(&value, bytes_.data() + offset, sizeof(value));
    return value;
  }

  std::uint64_t ReadU64(std::size_t offset) const {
    Require(offset <= bytes_.size() && 8 <= bytes_.size() - offset,
            "PE uint64 read out of range");
    std::uint64_t value = 0;
    std::memcpy(&value, bytes_.data() + offset, sizeof(value));
    return value;
  }

  bool Copy(std::size_t offset, void *destination,
            std::size_t size) const noexcept {
    if (offset > bytes_.size() || size > bytes_.size() - offset) {
      return false;
    }
    std::memcpy(destination, bytes_.data() + offset, size);
    return true;
  }

  std::vector<unsigned char> bytes_;
  std::vector<Section> sections_;
  std::uintptr_t preferred_base_ = 0;
  std::uintptr_t image_size_ = 0;
  std::uintptr_t headers_size_ = 0;
};

bool ReadDiskImage(void *context, std::uintptr_t rva, void *destination,
                   std::size_t size) noexcept {
  return static_cast<const DiskPeImage *>(context)->Read(rva, destination, size);
}

struct CorruptReadContext {
  const DiskPeImage *image = nullptr;
  std::uintptr_t corrupt_rva = 0;
  bool fail = false;
};

bool ReadCorrupted(void *context, std::uintptr_t rva, void *destination,
                   std::size_t size) noexcept {
  const auto &corruption = *static_cast<const CorruptReadContext *>(context);
  if (corruption.fail ||
      !corruption.image->Read(rva, destination, size)) {
    return false;
  }
  if (rva <= corruption.corrupt_rva && corruption.corrupt_rva - rva < size) {
    auto *bytes = static_cast<unsigned char *>(destination);
    bytes[corruption.corrupt_rva - rva] ^= 0x01U;
  }
  return true;
}

void TestExactImageGreen(const DiskPeImage &image) {
  const RealmLawMutationAbiReaderV1 reader{
      const_cast<DiskPeImage *>(&image), ReadDiskImage};
  const auto proof =
      VerifyRealmLawEnactMutationAbiV1(reader, image.preferred_base());
  Require(proof.verified, "exact image did not verify");
  Require(proof.failure == RealmLawMutationAbiFailureV1::none,
          "GREEN proof retained a failure");
  Require(proof.manifest_sha256.size() == 64,
          "manifest proof digest has the wrong width");
}

void TestInstructionDriftFailsClosed(const DiskPeImage &image) {
  CorruptReadContext context{&image, 0x3DDF770, false};
  const RealmLawMutationAbiReaderV1 reader{&context, ReadCorrupted};
  const auto proof =
      VerifyRealmLawEnactMutationAbiV1(reader, image.preferred_base());
  Require(!proof.verified, "corrupt instruction span verified");
  Require(proof.failure ==
              RealmLawMutationAbiFailureV1::instruction_span_mismatch,
          "corrupt instruction span returned the wrong typed failure");
  Require(std::string(proof.failed_evidence) == "gui_law_can_enact_receiver",
          "corrupt instruction span returned the wrong evidence name");
}

void TestRelocationMismatchFailsClosed(const DiskPeImage &image) {
  const RealmLawMutationAbiReaderV1 reader{
      const_cast<DiskPeImage *>(&image), ReadDiskImage};
  const auto proof = VerifyRealmLawEnactMutationAbiV1(
      reader, image.preferred_base() + 0x1000);
  Require(!proof.verified, "wrong module base verified");
  Require(proof.failure ==
              RealmLawMutationAbiFailureV1::absolute_pointer_mismatch,
          "wrong module base returned the wrong typed failure");
}

void TestRegistryDriftFailsClosed(const DiskPeImage &image) {
  CorruptReadContext context{&image, 0x42C2AE0, false};
  const RealmLawMutationAbiReaderV1 reader{&context, ReadCorrupted};
  const auto proof =
      VerifyRealmLawEnactMutationAbiV1(reader, image.preferred_base());
  Require(!proof.verified, "corrupt command registry key verified");
  Require(proof.failure ==
              RealmLawMutationAbiFailureV1::numeric_evidence_mismatch,
          "corrupt command registry key returned the wrong typed failure");
  Require(std::string(proof.failed_evidence) ==
              "add_law_command_class_key",
          "corrupt command registry key returned the wrong evidence name");
}

void TestReaderFailuresAreTyped(const DiskPeImage &image) {
  const auto invalid = VerifyRealmLawEnactMutationAbiV1({}, 0);
  Require(invalid.failure == RealmLawMutationAbiFailureV1::invalid_reader,
          "invalid reader returned the wrong typed failure");

  CorruptReadContext context{&image, 0, true};
  const RealmLawMutationAbiReaderV1 reader{&context, ReadCorrupted};
  const auto failed =
      VerifyRealmLawEnactMutationAbiV1(reader, image.preferred_base());
  Require(failed.failure == RealmLawMutationAbiFailureV1::read_failed,
          "read failure returned the wrong typed failure");
}

} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: realm_law_enact_mutation_abi_v1_test ck3.exe");
    const DiskPeImage image(argv[1]);
    TestExactImageGreen(image);
    TestInstructionDriftFailsClosed(image);
    TestRelocationMismatchFailsClosed(image);
    TestRegistryDriftFailsClosed(image);
    TestReaderFailuresAreTyped(image);
    std::cout << "realm_law_enact_mutation_abi_v1 tests passed (5)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "realm_law_enact_mutation_abi_v1 RED: " << error.what()
              << '\n';
    return 1;
  }
}
