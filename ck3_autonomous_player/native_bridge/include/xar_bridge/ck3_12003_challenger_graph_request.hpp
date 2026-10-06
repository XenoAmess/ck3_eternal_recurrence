#pragma once

#include "xar_bridge/ck3_12003_readonly_revision.hpp"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12003::challenger_graph {
inline constexpr std::size_t kMaximumRequestedFaiths = 8;
struct Request {
  std::uint64_t expected_snapshot_revision = 0;
  std::array<std::uint32_t, kMaximumRequestedFaiths> faith_full_ids{};
  std::size_t faith_count = 0;
};

namespace request_detail {
// The existing revision helper first validates the complete JSON grammar.
// This second pass extracts exactly one decoded top-level faith_full_ids key.
// Other command-envelope fields cannot select a Faith or a Title.
class FaithListParser final {
public:
  explicit FaithListParser(std::string_view text) noexcept : text_(text) {}
  bool Parse(Request &out) noexcept {
    Space(); if (!Take('{')) return false; Space();
    if (Take('}')) return false;
    for (;;) {
      bool relevant = false;
      if (!String(&relevant)) return false;
      Space(); if (!Take(':')) return false; Space();
      if (relevant) {
        if (seen_ || !FaithArray(out)) return false;
        seen_ = true;
      } else if (!Skip(1)) return false;
      Space(); if (Take('}')) break;
      if (!Take(',')) return false; Space();
    }
    Space(); return seen_ && at_ == text_.size();
  }
private:
  std::string_view text_;
  std::size_t at_ = 0;
  bool seen_ = false;
  void Space() noexcept {
    while (at_ < text_.size() && (text_[at_] == ' ' || text_[at_] == '\t' ||
        text_[at_] == '\r' || text_[at_] == '\n')) ++at_;
  }
  bool Take(char c) noexcept {
    if (at_ == text_.size() || text_[at_] != c) return false;
    ++at_; return true;
  }
  bool String(bool *relevant = nullptr) noexcept {
    static constexpr std::string_view key = "faith_full_ids";
    if (!Take('"')) return false;
    bool matches = true; std::size_t length = 0;
    while (at_ < text_.size()) {
      if (Take('"')) { if (relevant) *relevant = matches && length == key.size(); return true; }
      std::uint32_t c = static_cast<unsigned char>(text_[at_++]);
      if (c == '\\') {
        if (at_ == text_.size()) return false;
        const char escaped = text_[at_++];
        if (escaped == 'u') {
          c = 0;
          for (unsigned i = 0; i < 4; ++i) {
            if (at_ == text_.size()) return false;
            const char digit = text_[at_++];
            const int value = digit >= '0' && digit <= '9' ? digit - '0' :
                digit >= 'a' && digit <= 'f' ? digit - 'a' + 10 :
                digit >= 'A' && digit <= 'F' ? digit - 'A' + 10 : -1;
            if (value < 0) return false;
            c = c * 16U + static_cast<std::uint32_t>(value);
          }
        } else {
          switch (escaped) {
          case 'b': c = 8; break;
          case 'f': c = 12; break;
          case 'n': c = 10; break;
          case 'r': c = 13; break;
          case 't': c = 9; break;
          default: c = static_cast<unsigned char>(escaped); break;
          }
        }
      }
      if (length >= key.size() || c != static_cast<unsigned char>(key[length])) matches = false;
      ++length;
    }
    return false;
  }
  bool FaithArray(Request &out) noexcept {
    if (!Take('[')) return false; Space();
    if (Take(']')) return false;
    for (;;) {
      if (out.faith_count == kMaximumRequestedFaiths || at_ == text_.size() ||
          text_[at_] < '0' || text_[at_] > '9') return false;
      std::uint64_t value = 0;
      while (at_ < text_.size() && text_[at_] >= '0' && text_[at_] <= '9') {
        value = value * 10U + static_cast<unsigned>(text_[at_++] - '0');
        if (value >= UINT32_MAX) return false;
      }
      const auto id = static_cast<std::uint32_t>(value);
      for (std::size_t i = 0; i < out.faith_count; ++i) if (out.faith_full_ids[i] == id) return false;
      out.faith_full_ids[out.faith_count++] = id;
      Space(); if (Take(']')) return true;
      if (!Take(',')) return false; Space();
    }
  }
  bool Skip(unsigned depth) noexcept {
    if (depth > 64 || at_ == text_.size()) return false;
    if (text_[at_] == '"') return String();
    if (Take('{')) {
      Space(); if (Take('}')) return true;
      for (;;) {
        if (!String()) return false; Space(); if (!Take(':')) return false; Space();
        if (!Skip(depth + 1)) return false; Space(); if (Take('}')) return true;
        if (!Take(',')) return false; Space();
      }
    }
    if (Take('[')) {
      Space(); if (Take(']')) return true;
      for (;;) {
        if (!Skip(depth + 1)) return false; Space(); if (Take(']')) return true;
        if (!Take(',')) return false; Space();
      }
    }
    const auto start = at_;
    while (at_ < text_.size() && text_[at_] != ',' && text_[at_] != '}' && text_[at_] != ']' &&
        text_[at_] != ' ' && text_[at_] != '\t' && text_[at_] != '\r' && text_[at_] != '\n') ++at_;
    return at_ != start;
  }
};
} // namespace request_detail

inline bool ParseRequest(std::string_view payload, Request &out) noexcept {
  out = {};
  Request value;
  if (!readonly_query::ParseUniqueTopLevelRevision(payload, value.expected_snapshot_revision) ||
      !request_detail::FaithListParser(payload).Parse(value)) return false;
  out = value; return true;
}
} // namespace xar::ck3_12003::challenger_graph
