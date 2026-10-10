#pragma once

#include "xar_bridge/entry_final_side_capture_12004.hpp"

// Test-only helper owned by the single connected Entry executable. No second
// hook installer, clock, fake Peek/Notify implementation or test main.
inline constexpr std::uintptr_t kEntryFinalSideFixtureImageBase12004 = 0x180000000;

std::optional<xar::ck3_12004::EntryFinalSideCaptureRecord12004>
RunEntryFinalSideFixtureForOriginal12004(
    xar::ck3_12004::EntryFinalSideCaptureOriginal12004 original,
    xar::ck3_12004::PersonInstalledTransferRead12004 read = nullptr,
    void *read_context = nullptr);

bool EntryFinalSideFixtureRead12004(void *, std::uintptr_t, void *,
                                  std::size_t) noexcept;
