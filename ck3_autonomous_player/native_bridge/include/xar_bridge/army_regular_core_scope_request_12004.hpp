#pragma once

#include <algorithm>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004 {
namespace regular_core_scope_request_detail_12004 {

// A scope is a unique, decoded top-level field. Nested or quoted occurrences
// do not enable capture. Python None is represented by omitting the field.
class Reader {
 public:
  constexpr explicit Reader(std::string_view json) : json_(json) {}

  constexpr bool Read(std::string_view step,
            std::optional<std::vector<std::int32_t>> &out) {
    out.reset();
    std::optional<std::vector<std::int32_t>> scope;
    std::string family;
    bool family_seen=false, family_unique=true, family_string=false;
    Space();
    if(!Take('{'))return false;
    Space();
    if(!Take('}')) {
      for(;;) {
        std::string key;
        if(!String(&key))return false;
        Space();if(!Take(':'))return false;Space();
        if(key=="regular_core_full_carmy_ids") {
          if(scope)return false;
          scope.emplace();
          if(!Ids(*scope))return false;
        } else if(key=="observer_family") {
          family_unique=family_unique && !family_seen;family_seen=true;
          family_string=offset_<json_.size() && json_[offset_]=='"';
          if(family_string) { if(!String(&family))return false; }
          else if(!Value(0))return false;
        } else if(!Value(0))return false;
        Space();if(Take('}'))break;
        if(!Take(','))return false;Space();
      }
    }
    Space();if(offset_!=json_.size())return false;
    if(scope && (step!="enable-army-observer-research-sampling-v1" ||
        !family_seen || !family_unique || !family_string || family!="regular_core"))return false;
    out=std::move(scope);return true;
  }

 private:
  constexpr void Space() {
    while(offset_<json_.size() && (json_[offset_]==' ' || json_[offset_]=='\t' ||
          json_[offset_]=='\n' || json_[offset_]=='\r'))++offset_;
  }
  constexpr bool Take(char ch) {
    if(offset_==json_.size() || json_[offset_]!=ch)return false;
    ++offset_;return true;
  }
  static constexpr bool Digit(char ch) { return ch>='0' && ch<='9'; }
  constexpr bool String(std::string *out=nullptr) {
    if(!Take('"'))return false;
    if(out)out->clear();
    while(offset_<json_.size()) {
      auto ch=static_cast<unsigned char>(json_[offset_++]);
      if(ch=='"')return true;
      if(ch<0x20U)return false;
      if(ch=='\\') {
        if(offset_==json_.size())return false;
        ch=static_cast<unsigned char>(json_[offset_++]);
        switch(ch) {
        case '"':case '\\':case '/':break;
        case 'b':ch='\b';break;case 'f':ch='\f';break;
        case 'n':ch='\n';break;case 'r':ch='\r';break;case 't':ch='\t';break;
        case 'u': {
          unsigned unit=0;
          for(unsigned i=0;i<4;++i) {
            if(offset_==json_.size())return false;
            const char hex=json_[offset_++];unsigned digit=0;
            if(hex>='0' && hex<='9')digit=static_cast<unsigned>(hex-'0');
            else if(hex>='a' && hex<='f')digit=static_cast<unsigned>(hex-'a'+10);
            else if(hex>='A' && hex<='F')digit=static_cast<unsigned>(hex-'A'+10);
            else return false;
            unit=unit*16U+digit;
          }
          ch=unit<=0x7fU?static_cast<unsigned char>(unit):'?';break;
        }
        default:return false;
        }
      }
      if(out && out->size()<128U)out->push_back(static_cast<char>(ch));
    }
    return false;
  }
  constexpr bool Ids(std::vector<std::int32_t> &ids) {
    if(!Take('['))return false;
    Space();if(Take(']'))return false;
    for(;;) {
      // Match the native subject bound; do not alter capture object/read caps.
      if(ids.size()==64U)return false;
      const bool negative=Take('-');
      if(offset_==json_.size() || !Digit(json_[offset_]))return false;
      const auto start=offset_;std::uint64_t value=0;
      do {
        value=value*10U+static_cast<unsigned>(json_[offset_++]-'0');
        if(value>(negative?0x80000000ULL:0x7fffffffULL))return false;
      } while(offset_<json_.size() && Digit(json_[offset_]));
      if(offset_-start>1U && json_[start]=='0')return false;
      // int64 arithmetic avoids implementation-defined uint32->int32 casts.
      const auto signed_value=negative?-static_cast<std::int64_t>(value):
          static_cast<std::int64_t>(value);
      const auto id=static_cast<std::int32_t>(signed_value);
      if(id==-1 || std::find(ids.begin(),ids.end(),id)!=ids.end())return false;
      ids.push_back(id);Space();if(Take(']'))return true;
      if(!Take(','))return false;Space();
    }
  }
  constexpr bool Literal(std::string_view text) {
    if(json_.substr(offset_,text.size())!=text)return false;
    offset_+=text.size();return true;
  }
  constexpr bool Number() {
    Take('-');if(offset_==json_.size())return false;
    if(!Take('0')) {
      if(json_[offset_]<'1' || json_[offset_]>'9')return false;
      do { ++offset_; } while(offset_<json_.size() && Digit(json_[offset_]));
    }
    if(Take('.')) {
      if(offset_==json_.size() || !Digit(json_[offset_]))return false;
      do { ++offset_; } while(offset_<json_.size() && Digit(json_[offset_]));
    }
    if(offset_<json_.size() && (json_[offset_]=='e' || json_[offset_]=='E')) {
      ++offset_;
      if(offset_<json_.size() && (json_[offset_]=='+' || json_[offset_]=='-'))++offset_;
      if(offset_==json_.size() || !Digit(json_[offset_]))return false;
      do { ++offset_; } while(offset_<json_.size() && Digit(json_[offset_]));
    }
    return true;
  }
  constexpr bool Value(unsigned depth) {
    if(depth>64U || offset_==json_.size())return false;
    if(json_[offset_]=='"')return String();
    if(Take('{')) {
      Space();if(Take('}'))return true;
      for(;;) {
        if(!String())return false;Space();if(!Take(':'))return false;Space();
        if(!Value(depth+1U))return false;Space();if(Take('}'))return true;
        if(!Take(','))return false;Space();
      }
    }
    if(Take('[')) {
      Space();if(Take(']'))return true;
      for(;;) {
        if(!Value(depth+1U))return false;Space();if(Take(']'))return true;
        if(!Take(','))return false;Space();
      }
    }
    return Literal("true") || Literal("false") || Literal("null") || Number();
  }
  std::string_view json_;
  std::size_t offset_=0;
};
} // namespace regular_core_scope_request_detail_12004

constexpr bool ParseRegularCoreScopeRequest12004(std::string_view json,
    std::string_view step,std::optional<std::vector<std::int32_t>> &out) {
  return regular_core_scope_request_detail_12004::Reader(json).Read(step,out);
}
} // namespace xar::ck3_12004
