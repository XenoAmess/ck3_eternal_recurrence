#pragma once
// Read-only, fixed named DATA export. No target callback, code scan or address CLI.
#include <windows.h>
#include <tlhelp32.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cwchar>
#include <cstring>
#include <string>
#include <vector>
#include "../../include/xar_bridge/refill_core_carrier_12004.hpp"

namespace xar::research::refill_core_carrier_12004 {
namespace abi = xar::ck3_12004::refill_carrier;
static_assert(abi::kAbi == 1 && abi::kSourceEpoch == 20261018 && abi::kSlots == 16);
static_assert(sizeof(abi::Header) == 64 && sizeof(abi::Words) == 168 &&
              sizeof(abi::Directory) == 2752);
constexpr std::uint64_t kMaxImageBytes = 512ULL * 1024 * 1024;
constexpr std::size_t kMetadataBudget = 128 * 1024;
constexpr DWORD kMaxExports = 4096;
constexpr std::size_t kMaxNameBytes = 256;
struct Binding {
  std::string module_path;
  std::uint64_t module_base = 0, module_size = 0, export_rva = 0;
  std::uint64_t directory_address = 0;
  abi::Header header{};
};
struct Capture {
  bool attempted = false, owners_complete = false, header_complete = false;
  bool first_complete = false, second_complete = false, stable_active = false;
  int slot_index = -1;
  std::uint64_t slot_address = 0;
  std::size_t owner_matches = 0;
  abi::Header header{};
  abi::Words first{}, second{};
  std::string diagnostic = "not_selected_physical_target";
};
inline bool Inside(const Binding &b, std::uint64_t rva, std::uint64_t count) {
  return count <= b.module_size && rva <= b.module_size - count &&
    b.module_base <= UINT64_MAX - b.module_size;
}
struct RemoteRead {
  HANDLE process;
  bool operator()(std::uint64_t address, void *out, std::size_t count) const {
    SIZE_T actual = 0;
    return address != 0 && count != 0 && address <= UINT64_MAX - count &&
      ReadProcessMemory(process, reinterpret_cast<const void *>(address), out,
                        count, &actual) && actual == count;
  }
};
template<class Reader> struct MetadataRead {
  Reader &read;
  const Binding &binding;
  std::size_t remaining = kMetadataBudget;
  bool operator()(std::uint64_t rva, void *out, std::size_t count) {
    if (!count || count > remaining || !Inside(binding, rva, count)) return false;
    remaining -= count;
    return read(binding.module_base + rva, out, count);
  }
  bool Name(std::uint64_t rva, std::string &out) {
    out.clear();
    // Only named-export strings; bounded chunks, total budget shared with tables.
    for (std::size_t used = 0; used < kMaxNameBytes;) {
      if (!Inside(binding, rva, used + 1)) return false;
      const auto count = (std::min)({std::size_t{16}, kMaxNameBytes - used,
        static_cast<std::size_t>(binding.module_size - rva - used)});
      std::array<char, 16> bytes{};
      if (!(*this)(rva + used, bytes.data(), count)) return false;
      for (std::size_t i = 0; i != count; ++i) {
        if (bytes[i] == 0) return true;
        out.push_back(bytes[i]);
      }
      used += count;
    }
    return false;
  }
};
// Reader injection is only for source fixtures; production takes its module
// from Toolhelp and exposes no address/module-name argument.
template<class Reader>
bool ResolveFixedDataExport(Reader &read, Binding &binding, std::string &error) {
  auto fail = [&](const char *why) { error = why; return false; };
  if (!binding.module_base || binding.module_size < sizeof(IMAGE_DOS_HEADER) ||
      binding.module_size > kMaxImageBytes ||
      binding.module_base > UINT64_MAX - binding.module_size)
    return fail("carrier_module_range_invalid");
  MetadataRead<Reader> metadata{read, binding};
  IMAGE_DOS_HEADER dos{};
  IMAGE_NT_HEADERS64 nt{};
  if (!metadata(0, &dos, sizeof dos) || dos.e_magic != IMAGE_DOS_SIGNATURE ||
      dos.e_lfanew < static_cast<LONG>(sizeof dos) ||
      !metadata(static_cast<std::uint32_t>(dos.e_lfanew), &nt, sizeof nt) ||
      nt.Signature != IMAGE_NT_SIGNATURE || nt.FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64 ||
      nt.FileHeader.SizeOfOptionalHeader != sizeof(IMAGE_OPTIONAL_HEADER64) ||
      nt.OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC ||
      nt.OptionalHeader.SizeOfImage != binding.module_size ||
      !nt.OptionalHeader.SizeOfHeaders || nt.OptionalHeader.SizeOfHeaders > binding.module_size ||
      nt.OptionalHeader.NumberOfRvaAndSizes <= IMAGE_DIRECTORY_ENTRY_EXPORT ||
      nt.OptionalHeader.NumberOfRvaAndSizes > IMAGE_NUMBEROF_DIRECTORY_ENTRIES ||
      !nt.FileHeader.NumberOfSections || nt.FileHeader.NumberOfSections > 96)
    return fail("carrier_pe64_header_invalid");
  const auto export_data = nt.OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
  if (export_data.Size < sizeof(IMAGE_EXPORT_DIRECTORY) ||
      !Inside(binding, export_data.VirtualAddress, export_data.Size))
    return fail("carrier_export_directory_invalid");
  IMAGE_EXPORT_DIRECTORY directory{};
  if (!metadata(export_data.VirtualAddress, &directory, sizeof directory) ||
      !directory.NumberOfFunctions || directory.NumberOfFunctions > kMaxExports ||
      !directory.NumberOfNames || directory.NumberOfNames > kMaxExports)
    return fail("carrier_export_counts_invalid");
  std::vector<DWORD> functions(directory.NumberOfFunctions), names(directory.NumberOfNames);
  std::vector<WORD> ordinals(directory.NumberOfNames);
  if (!metadata(directory.AddressOfFunctions, functions.data(), functions.size() * sizeof(DWORD)) ||
      !metadata(directory.AddressOfNames, names.data(), names.size() * sizeof(DWORD)) ||
      !metadata(directory.AddressOfNameOrdinals, ordinals.data(), ordinals.size() * sizeof(WORD)))
    return fail("carrier_export_tables_unreadable_or_over_budget");
  DWORD selected = 0;
  std::size_t matches = 0;
  std::string previous, name;
  for (std::size_t i = 0; i != names.size(); ++i) {
    if (!names[i] || ordinals[i] >= functions.size() || !metadata.Name(names[i], name) ||
        name.empty() || (i && !(previous < name)))
      return fail("carrier_export_names_invalid_or_over_budget");
    if (name == abi::kExportName) { ++matches; selected = functions[ordinals[i]]; }
    previous = name;
  }
  if (matches != 1 || !selected || selected % alignof(abi::Directory) != 0 ||
      !Inside(binding, selected, sizeof(abi::Directory)) ||
      (selected >= export_data.VirtualAddress &&
       selected - export_data.VirtualAddress < export_data.Size))
    return fail("carrier_fixed_export_absent_forwarded_or_outside_image");
  const auto section_rva = static_cast<std::uint64_t>(dos.e_lfanew) +
    sizeof(DWORD) + sizeof(IMAGE_FILE_HEADER) + nt.FileHeader.SizeOfOptionalHeader;
  std::vector<IMAGE_SECTION_HEADER> sections(nt.FileHeader.NumberOfSections);
  const auto section_bytes = sections.size() * sizeof(IMAGE_SECTION_HEADER);
  if (section_rva > nt.OptionalHeader.SizeOfHeaders ||
      section_bytes > nt.OptionalHeader.SizeOfHeaders - section_rva ||
      !metadata(section_rva, sections.data(), section_bytes))
    return fail("carrier_section_headers_unreadable_or_over_budget");
  std::size_t data_sections = 0;
  for (const auto &section : sections) {
    const auto bytes = (std::max)(section.Misc.VirtualSize, section.SizeOfRawData);
    if (!Inside(binding, section.VirtualAddress, bytes))
      return fail("carrier_section_range_invalid");
    if (selected < section.VirtualAddress || sizeof(abi::Directory) > bytes ||
        selected - section.VirtualAddress > bytes - sizeof(abi::Directory)) continue;
    if ((section.Characteristics & IMAGE_SCN_MEM_EXECUTE) ||
        !(section.Characteristics & IMAGE_SCN_MEM_READ) ||
        !(section.Characteristics & (IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_CNT_UNINITIALIZED_DATA)))
      return fail("carrier_export_is_not_readable_nonexecuting_data");
    ++data_sections;
  }
  if (data_sections != 1) return fail("carrier_data_section_not_unique");
  abi::Header header{};
  if (!metadata(selected, header.data(), sizeof header) || header != abi::kHeader)
    return fail("carrier_header_mismatch_or_unreadable");
  binding.export_rva = selected;
  binding.directory_address = binding.module_base + selected;
  binding.header = header;
  error.clear();
  return true;
}
inline bool LocateUniqueModule(DWORD pid, Binding &binding, std::string &error) {
  HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
  if (snapshot == INVALID_HANDLE_VALUE) { error = "carrier_module_snapshot_failed"; return false; }
  MODULEENTRY32W entry{};
  entry.dwSize = sizeof entry;
  bool next = Module32FirstW(snapshot, &entry) != FALSE;
  std::size_t modules = 0, matches = 0;
  bool valid = next;
  while (next && valid) {
    if (++modules > 4096) { valid = false; break; }
    if (_wcsicmp(entry.szModule, L"xar_ck3_bridge.dll") == 0) {
      ++matches;
      const auto length = wcsnlen_s(entry.szExePath, MAX_PATH);
      const std::wstring path(entry.szExePath, length);
      const auto slash = path.find_last_of(L"\\/");
      const auto basename = path.substr(slash == std::wstring::npos ? 0 : slash + 1);
      if (!length || length >= MAX_PATH || _wcsicmp(basename.c_str(), L"xar_ck3_bridge.dll") != 0) {
        valid = false; break;
      }
      const int count = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, path.data(),
        static_cast<int>(path.size()), nullptr, 0, nullptr, nullptr);
      if (count <= 0) { valid = false; break; }
      binding.module_path.assign(static_cast<std::size_t>(count), '\0');
      if (WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, path.data(),
          static_cast<int>(path.size()), binding.module_path.data(), count, nullptr, nullptr) != count) {
        valid = false; break;
      }
      binding.module_base = reinterpret_cast<std::uint64_t>(entry.modBaseAddr);
      binding.module_size = entry.modBaseSize;
    }
    next = Module32NextW(snapshot, &entry) != FALSE;
  }
  if (valid && GetLastError() != ERROR_NO_MORE_FILES) valid = false;
  CloseHandle(snapshot);
  if (!valid || matches != 1) { error = "carrier_module_absent_ambiguous_or_unreadable"; return false; }
  return true;
}
inline bool Resolve(HANDLE process, DWORD pid, Binding &binding, std::string &error) {
  binding = Binding{};
  RemoteRead read{process};
  return LocateUniqueModule(pid, binding, error) && ResolveFixedDataExport(read, binding, error);
}
inline bool HeaderStillValid(HANDLE process, const Binding &binding) {
  RemoteRead read{process};
  abi::Header actual{};
  return binding.directory_address &&
    read(binding.directory_address, actual.data(), sizeof actual) && actual == abi::kHeader;
}
template<class Reader>
Capture ReadSelected(Reader &read, const Binding &binding, std::uint64_t tid) {
  Capture out;
  out.attempted = true;
  out.diagnostic = "carrier_owner_words_unreadable";
  if (!tid || !binding.directory_address || binding.header != abi::kHeader ||
      !Inside(binding, binding.export_rva, sizeof(abi::Directory)) ||
      binding.directory_address != binding.module_base + binding.export_rva) {
    out.diagnostic = "carrier_binding_or_target_tid_invalid"; return out;
  }
  // Exactly 16 owner-word reads, only after physical target selection.
  for (std::size_t i = 0; i != abi::kSlots; ++i) {
    std::uint64_t owner = 0;
    const auto slot = binding.directory_address + sizeof(abi::Header) + i * sizeof(abi::Slot);
    if (!read(slot + abi::owner_tid * 8, &owner, sizeof owner)) return out;
    if (owner == tid) { ++out.owner_matches; out.slot_index = static_cast<int>(i); out.slot_address = slot; }
  }
  out.owners_complete = true;
  if (out.owner_matches != 1) { out.diagnostic = "carrier_owner_slot_absent_or_ambiguous"; return out; }
  out.header_complete = read(binding.directory_address, out.header.data(), sizeof out.header);
  out.first_complete = read(out.slot_address, out.first.data(), sizeof out.first);
  out.second_complete = read(out.slot_address, out.second.data(), sizeof out.second);
  if (!out.header_complete || !out.first_complete || !out.second_complete) {
    out.diagnostic = "carrier_header_or_double_frame_unreadable"; return out;
  }
  if (out.header != abi::kHeader) { out.diagnostic = "carrier_actual_header_mismatch"; return out; }
  out.stable_active = abi::StableActivePair(out.first, out.second, tid);
  out.diagnostic = out.stable_active ? "stable_active" : "carrier_unstable_inactive_or_wrong_provenance";
  return out;
}
inline Capture ReadSelected(HANDLE process, const Binding &binding, std::uint64_t tid) {
  RemoteRead read{process};
  return ReadSelected(read, binding, tid);
}
inline bool SameActivePair(const Capture &a, const Capture &b, std::uint64_t tid) {
  return a.stable_active && b.stable_active && a.slot_index == b.slot_index &&
    a.slot_address == b.slot_address && a.header == b.header &&
    abi::StableActivePair(a.first, a.second, tid) &&
    abi::StableActivePair(b.first, b.second, tid) && a.first == b.first;
}
} // namespace xar::research::refill_core_carrier_12004
