#include "xar_bridge/appointment_character_level12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/appointment_window_snapshot_v1.hpp"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>

namespace {
using xar::ck3_11906::AppointmentWindowAccessV1;
using xar::ck3_11906::AppointmentWindowSnapshotV1;
using xar::ck3_11906::SerializeAppointmentWindowSnapshotV1;
using xar::ck3_12004::AppointmentCharacterLevel12004;
using xar::ck3_12004::ReadAppointmentCharacterLevel12004;
constexpr std::string_view kExactSha =
    xar::ck3_12004::kExecutableSha256;

void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}

// Same bounded byte-addressed mock-read boundary as the existing appointment
// reader fixture. No native callback, process memory, game or runtime linkage.
struct Memory {
  std::unordered_map<std::uintptr_t, unsigned char> bytes;
  const std::uintptr_t base = 0x140000000ULL, storage = 0x100000;
  const std::uintptr_t slots = 0x102000, character = 0x104000;
  const std::uintptr_t title = 0x106000, title_template = 0x108000;
  const std::uintptr_t rule = 0x10A000, extension = 0x10C000;
  const std::uintptr_t thresholds = 0x10E000, floors = 0x110000;
  const std::uint32_t character_id = 0x7A000006U, title_id = 0x34000002U;
  int accumulated_reads = 0;
  bool change_second_sample = false;

  template<class T> void Put(std::uintptr_t address, T value) {
    const auto *data = reinterpret_cast<const unsigned char *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[address+i] = data[i];
  }
  static bool Read(void *context, std::uintptr_t address, void *out,
                   std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    if (address == m.extension+0x178 && ++m.accumulated_reads == 2 &&
        m.change_second_sample) {
      m.Put(m.extension+0x178, std::int64_t(200001));
    }
    if (size > 64) return false;
    for (std::size_t i = 0; i < size; ++i) {
      const auto it = m.bytes.find(address+i);
      if (it == m.bytes.end()) return false;
      static_cast<unsigned char *>(out)[i] = it->second;
    }
    return true;
  }
  Memory() {
    Put(base+0x5C67568, storage);
    Put(storage+0x20, slots); Put(storage+0x2C, std::uint32_t(7));
    Put(slots+6*0x10+8, character); Put(character+0x18, character_id);
    Put(title+0x10, title_id); Put(title+0x48, title_template);
    Put(title_template+0x64, std::int32_t(4));
    Put(rule+0x148, std::uint8_t(0)); Put(character+0x1B0, extension);
    Put(extension+0x178, std::int64_t(200000));
    Put(extension+0x180, std::int32_t(-1));
    Put(base+0x5458818, thresholds); Put(base+0x5458824, std::int32_t(3));
    Put(thresholds, std::int64_t(100000));
    Put(thresholds+8, std::int64_t(200000));
    Put(thresholds+16, std::int64_t(300000));
    Put(base+0x5461660, floors); Put(floors+4*4, std::int32_t(2));
  }
  AppointmentWindowAccessV1 Access() {
    AppointmentWindowAccessV1 a{};
    a.context = this; a.read = Read; a.module_base = base;
    a.admitted_executable_sha256 = kExactSha;
    return a;
  }
  bool Get(AppointmentCharacterLevel12004 &out,
           std::string_view sha = kExactSha, std::uint32_t id = 0) {
    Check(bytes.size() <= 16384, "mock memory exceeded its fixed fixture budget");
    return ReadAppointmentCharacterLevel12004(Access(), sha, rule, title,
        title_id, id ? id : character_id, out);
  }
  std::string Wire(const AppointmentCharacterLevel12004 &d) const {
    AppointmentWindowSnapshotV1 parent{};
    parent.available = true;
    parent.current_window_title_id = title_id;
    parent.diagnostic_character_id = character_id;
    parent.character_level_diagnostic = d;
    return SerializeAppointmentWindowSnapshotV1(parent);
  }
};

void Contains(const std::string &wire, std::string_view fragment) {
  Check(wire.find(fragment) != std::string::npos, "missing expected serialized field");
}
template<class F> void Case(const char *name, F body, int &passed) {
  body(); ++passed;
  std::cout << "{\"case\":\"" << name << "\",\"source_mock_pass\":true}\n";
}
}

int main() {
  try {
    int passed = 0;
    Case("threshold_and_native_floor_equality", [] {
      Memory m; AppointmentCharacterLevel12004 d;
      Check(m.Get(d) && d.available, "equal threshold read unavailable");
      Check(d.native_level == 2 && d.required_native_level == 2 &&
          d.meets_native_level_floor, "native >= equality boundary changed");
      Check(d.character_id == m.character_id && d.title_id == m.title_id &&
          m.accumulated_reads == 2, "complete identity or double sample missing");
      const auto wire = m.Wire(d);
      Contains(wire, "\"native_level\":2");
      Contains(wire, "\"meets_native_level_floor\":true");
      Check(wire.find("\"eligible\"") == std::string::npos,
          "one native floor became overall eligibility");
      std::cout << wire << '\n';
    }, passed);
    Case("old_character_generation_rejected", [] {
      Memory m; AppointmentCharacterLevel12004 d;
      Check(!m.Get(d, kExactSha, m.character_id ^ 0x01000000U) &&
          !d.available, "low-24-only stale generation accepted");
      Check(m.accumulated_reads == 0, "stale identity reached resource read");
    }, passed);
    Case("wrong_exact_executable_rejected", [] {
      Memory m; AppointmentCharacterLevel12004 d;
      Check(!m.Get(d, "wrong-executable") && !d.available &&
          d.unavailable_reason == "exact4_current_rule_lease_required",
          "wrong executable admitted");
      Check(m.accumulated_reads == 0, "wrong executable reached memory fields");
    }, passed);
    Case("other_ordinal_explicitly_unavailable", [] {
      Memory m; m.Put(m.rule+0x148, std::uint8_t(1));
      AppointmentCharacterLevel12004 d;
      Check(!m.Get(d) && !d.available &&
          d.native_level_source_ordinal_available && d.native_level_source_ordinal == 1 &&
          d.unavailable_reason == "appointment_level_source_ordinal_not_supported",
          "unsupported ordinal lost its explicit reason");
      const auto wire = m.Wire(d);
      Contains(wire, "\"native_level_source_ordinal\":1");
      Contains(wire, "\"native_level\":null");
      Contains(wire, "\"meets_native_level_floor\":null");
    }, passed);
    Case("null_extension_is_real_zero_with_null_raw_wire", [] {
      Memory m; m.Put(m.character+0x1B0, std::uintptr_t(0));
      AppointmentCharacterLevel12004 d;
      Check(m.Get(d) && d.available && !d.resource_extension_present &&
          d.native_level == 0 && !d.meets_native_level_floor,
          "null extension differs from native zero return");
      Check(m.accumulated_reads == 0, "null extension read fabricated resource fields");
      const auto wire = m.Wire(d);
      Contains(wire, "\"resource_extension_present\":false");
      Contains(wire, "\"accumulated_raw\":null");
      Contains(wire, "\"level_cap_raw\":null");
      Contains(wire, "\"native_level\":0");
      std::cout << wire << '\n';
    }, passed);
    Case("nonnegative_cap_limits_native_level", [] {
      Memory m; m.Put(m.extension+0x180, std::int32_t(1));
      AppointmentCharacterLevel12004 d;
      Check(m.Get(d) && d.native_level == 1 && d.level_cap_raw == 1 &&
          !d.meets_native_level_floor, "native cap ignored");
    }, passed);
    Case("second_sample_resource_change_rejected", [] {
      Memory m; m.change_second_sample = true;
      AppointmentCharacterLevel12004 d;
      Check(!m.Get(d) && !d.available && m.accumulated_reads == 2 &&
          d.unavailable_reason == "native_type0_level_fields_changed",
          "changed second sample accepted");
      const auto wire = m.Wire(d);
      Contains(wire, "\"native_level\":null");
      Contains(wire, "\"accumulated_raw\":null");
    }, passed);
    Case("stale_current_title_generation_rejected", [] {
      Memory m; m.Put(m.title+0x10, m.title_id ^ 0x01000000U);
      AppointmentCharacterLevel12004 d;
      Check(!m.Get(d) && !d.available, "stale current title admitted");
    }, passed);
    Case("missing_resource_byte_is_unavailable_not_zero", [] {
      Memory m; m.bytes.erase(m.extension+0x178);
      AppointmentCharacterLevel12004 d;
      Check(!m.Get(d) && !d.available, "unreadable resource became valid zero");
      Contains(m.Wire(d), "\"native_level\":null");
    }, passed);
    Case("bounded_threshold_count_rejected", [] {
      Memory m; m.Put(m.base+0x5458824, std::int32_t(257));
      AppointmentCharacterLevel12004 d;
      Check(!m.Get(d) && !d.available, "out-of-bound threshold table accepted");
    }, passed);
    std::cerr << "PASS " << passed << " new bounded mock cases; NOT LIVE\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "FAIL " << e.what() << '\n';
    return 1;
  }
}
