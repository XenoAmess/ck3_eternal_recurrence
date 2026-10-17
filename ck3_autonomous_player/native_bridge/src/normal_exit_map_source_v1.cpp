#include "xar_bridge/normal_exit_map_source_v1.hpp"
#include "xar_bridge/normal_exit_map_inventory_context_v1.hpp"
#include "xar_bridge/normal_exit_gui_source_contract_v1.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ingame_private_gui_profile_v1.hpp"
#include <windows.h>
#include <shellapi.h>
#include <bcrypt.h>
#pragma comment(lib, "bcrypt.lib")
#pragma comment(lib, "shell32.lib")

#include <array>
#include <charconv>
#include <climits>
#include <filesystem>
#include <fstream>
#include <map>
#include <set>
#include <vector>

namespace xar::ck3_12003 {
namespace {
namespace fs = std::filesystem;
struct Node {
  enum Kind { object, array, string, number, boolean, null_value } kind = null_value;
  std::map<std::string, Node> fields;
  std::vector<Node> items;
  std::string text;
  std::uint64_t integer = 0;
};
class InventoryParser {
 public:
  explicit InventoryParser(std::string_view source) : source_(source) {}
  bool Parse(Node &node) {
    if (source_.empty() || source_.size() > 16U * 1024U * 1024U) return false;
    return Value(node, 0) && (Space(), at_ == source_.size());
  }
 private:
  std::string_view source_; std::size_t at_ = 0, nodes_ = 0;
  void Space() { while (at_ < source_.size() && (source_[at_]==' ' || source_[at_]=='\t' || source_[at_]=='\r' || source_[at_]=='\n')) ++at_; }
  bool Quote(std::string &value) {
    Space(); if (at_ >= source_.size() || source_[at_++]!='"') return false;
    value.clear();
    while (at_<source_.size()) {
      const auto c=static_cast<unsigned char>(source_[at_++]);
      if(c=='"') return true;
      if(c<0x20 || value.size()>=32768) return false;
      if(c=='\\') {
        if(at_>=source_.size()) return false;
        const char escaped=source_[at_++];
        if(escaped!='"' && escaped!='\\' && escaped!='/') return false;
        value+=escaped;
      } else value+=static_cast<char>(c);
    }
    return false;
  }
  bool Value(Node &node, std::size_t depth) {
    Space(); if(depth>12 || ++nodes_>250000 || at_>=source_.size()) return false;
    const char first=source_[at_];
    if(first=='"') { node.kind=Node::string; return Quote(node.text); }
    if(first=='{' || first=='[') {
      const char end=first=='{'?'}':']'; node.kind=first=='{'?Node::object:Node::array; ++at_; Space();
      if(at_<source_.size() && source_[at_]==end) { ++at_; return true; }
      while(at_<source_.size()) {
        std::string key;
        if(first=='{') {
          if(!Quote(key) || key.empty() || node.fields.contains(key)) return false;
          Space(); if(at_>=source_.size() || source_[at_++]!=':') return false;
        }
        Node item; if(!Value(item,depth+1)) return false;
        if(first=='{') node.fields.emplace(std::move(key),std::move(item)); else node.items.push_back(std::move(item));
        Space(); if(at_>=source_.size()) return false;
        if(source_[at_]==end) { ++at_; return true; }
        if(source_[at_++]!=',') return false;
      }
      return false;
    }
    if(source_.substr(at_,4)=="true" || source_.substr(at_,5)=="false") {
      node.kind=Node::boolean; at_+=source_[at_]=='t'?4:5; return true;
    }
    if(source_.substr(at_,4)=="null") { node.kind=Node::null_value; at_+=4; return true; }
    const auto start=at_;
    while(at_<source_.size() && source_[at_]>='0' && source_[at_]<='9') ++at_;
    if(at_==start || (at_-start>1 && source_[start]=='0')) return false;
    node.kind=Node::number;
    const auto result=std::from_chars(source_.data()+start,source_.data()+at_,node.integer);
    return result.ec==std::errc{} && result.ptr==source_.data()+at_;
  }
};
const Node *Field(const Node &node, const char *name, Node::Kind kind) {
  if(node.kind!=Node::object) return nullptr;
  const auto found=node.fields.find(name);
  return found!=node.fields.end() && found->second.kind==kind?&found->second:nullptr;
}
bool Hex(std::string_view value) noexcept {
  if(value.size()!=64) return false;
  for(char c:value) if(!((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return false;
  return true;
}
std::wstring Wide(std::string_view text) {
  if(text.empty() || text.find('\0')!=std::string_view::npos || text.size()>32767) return {};
  const int size=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),nullptr,0);
  if(size<=0) return {};
  std::wstring output(static_cast<std::size_t>(size),L'\0');
  return MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),output.data(),size)==size?output:std::wstring{};
}
fs::path Path(const Node &node) { return fs::path(Wide(node.text)); }
bool SamePath(const fs::path &first, const fs::path &second) {
  if(first.empty() || second.empty() || !first.is_absolute() || !second.is_absolute()) return false;
  const auto a=fs::weakly_canonical(first).native(), b=fs::weakly_canonical(second).native();
  return CompareStringOrdinal(a.c_str(),static_cast<int>(a.size()),b.c_str(),static_cast<int>(b.size()),TRUE)==CSTR_EQUAL;
}
bool Plain(const fs::path &path) {
  const DWORD attributes=GetFileAttributesW(path.c_str());
  return attributes!=INVALID_FILE_ATTRIBUTES && (attributes&FILE_ATTRIBUTE_REPARSE_POINT)==0;
}
bool ReadFile(const fs::path &path, std::string &bytes, std::size_t bound) {
  bytes.clear(); if(!Plain(path) || !fs::is_regular_file(path)) return false;
  const auto size=fs::file_size(path); if(size>bound) return false;
  std::ifstream input(path,std::ios::binary); if(!input) return false;
  bytes.resize(static_cast<std::size_t>(size));
  input.read(bytes.data(),static_cast<std::streamsize>(bytes.size()));
  return static_cast<bool>(input);
}
bool FileRecord(const Node &node, const fs::path &expected, std::string *content=nullptr) {
  const auto *path=Field(node,"path",Node::string), *size=Field(node,"bytes",Node::number), *hash=Field(node,"sha256",Node::string);
  if(!path || !size || !hash || !Hex(hash->text) || !SamePath(Path(*path),expected)) return false;
  std::string bytes, actual;
  if(!ReadFile(expected,bytes,128U*1024U*1024U) || bytes.size()!=size->integer ||
      !NormalExitMapSha256V1(bytes,actual) || actual!=hash->text) return false;
  if(content) *content=std::move(bytes);
  return true;
}
bool AllocatedRunningSettingsRecord(const Node &settings, const fs::path &userdir,
    std::string_view profile_sha) {
  // Preserve the legacy/prelaunch exact-byte path. A changed output is admitted
  // only through this allocation's authenticated original immutable snapshot.
  if(FileRecord(settings,userdir/L"pdx_settings.txt")) return true;
  const auto *settings_path=Field(settings,"path",Node::string);
  const auto *settings_size=Field(settings,"bytes",Node::number);
  const auto *settings_hash=Field(settings,"sha256",Node::string);
  if(!settings_path || !settings_size || !settings_hash || !Hex(settings_hash->text) ||
      !SamePath(Path(*settings_path),userdir/L"pdx_settings.txt")) return false;
  std::string projection_bytes,actual;
  if(!ReadFile(userdir/L"normal-exit-profile-binding-projection-v1.json",projection_bytes,1048576) ||
      !NormalExitMapSha256V1(projection_bytes,actual) || actual!=profile_sha) return false;
  Node projection;
  if(!InventoryParser(projection_bytes).Parse(projection)) return false;
  const auto *declared_userdir=Field(projection,"userdir",Node::string);
  const auto *state=Field(projection,"state_directory",Node::string);
  const auto *evidence=Field(projection,"evidence_directory",Node::string);
  if(!declared_userdir || !state || !evidence || !SamePath(Path(*declared_userdir),userdir) ||
      !SamePath(Path(*state)/L"profile",userdir)) return false;
  const auto live=Path(*evidence);
  if(live.empty() || !live.is_absolute() || !Plain(live)) return false;
  std::string ready_bytes,frozen_bytes;
  if(!ReadFile(live/L"ready-context.json",ready_bytes,1048576)) return false;
  Node ready,frozen;
  if(!InventoryParser(ready_bytes).Parse(ready)) return false;
  const auto *frozen_ref=Field(ready,"frozen_argv",Node::object);
  const auto *ready_run=Field(ready,"run_id",Node::string);
  const auto *ready_directory=Field(ready,"run_dir",Node::string);
  if(!frozen_ref || !ready_run || !ready_directory || !SamePath(Path(*ready_directory),live) ||
      !FileRecord(*frozen_ref,live/L"frozen-argv.json",&frozen_bytes) ||
      !InventoryParser(frozen_bytes).Parse(frozen)) return false;
  const auto *run=Field(frozen,"run_id",Node::string);
  const auto *frozen_state=Field(frozen,"state_dir",Node::string);
  const auto *files=Field(frozen,"files",Node::object);
  if(!run || !frozen_state || !files || run->text!=ready_run->text ||
      Wide(run->text)!=live.filename().native() || !SamePath(Path(*frozen_state),Path(*state))) return false;
  const auto snapshot=live/L"input-snapshots"/L"profile"/L"pdx_settings.txt";
  const Node *original=nullptr,*saved=nullptr;
  for(const auto &[name,row]:files->fields) {
    Node key; key.kind=Node::string; key.text=name;
    if(SamePath(Path(key),userdir/L"pdx_settings.txt")) {
      if(original) return false; original=&row;
    }
    if(SamePath(Path(key),snapshot)) {
      if(saved) return false; saved=&row;
    }
  }
  if(!original || !saved) return false;
  for(const auto *row:{original,saved}) {
    const auto *size=Field(*row,"bytes",Node::number),*hash=Field(*row,"sha256",Node::string);
    if(!size || !hash || size->integer!=settings_size->integer || hash->text!=settings_hash->text) return false;
  }
  std::string original_bytes,current_output;
  return ReadFile(snapshot,original_bytes,128U*1024U*1024U) &&
      original_bytes.size()==settings_size->integer && NormalExitMapSha256V1(original_bytes,actual) &&
      actual==settings_hash->text && ReadFile(userdir/L"pdx_settings.txt",current_output,128U*1024U*1024U);
}

bool Relative(std::string_view text, fs::path &path) {
  path=fs::path(Wide(text));
  if(path.empty() || path.is_absolute() || path.has_root_name() || path.has_root_directory()) return false;
  for(const auto &part:path) if(part==L".." || part==L".") return false;
  return path==path.lexically_normal();
}
std::wstring Lower(std::wstring value) {
  for(auto &c:value) if(c>=L'A' && c<=L'Z') c=static_cast<wchar_t>(c-L'A'+L'a');
  return value;
}
bool Descriptor(std::string_view bytes, const fs::path &root, bool outer) {
  // Limited first-pilot policy: no archive mount or GUI-affecting replace_path.
  // This lexical pass skips quoted values and comments before recognizing keys.
  std::size_t at=0, paths=0;
  while(at<bytes.size()) {
    if(bytes[at]=='#') { const auto end=bytes.find('\n',at); at=end==std::string_view::npos?bytes.size():end; continue; }
    if(bytes[at]=='"') { ++at; while(at<bytes.size() && bytes[at]!='"') ++at; if(at==bytes.size()) return false; ++at; continue; }
    if(!((bytes[at]>='a'&&bytes[at]<='z') || bytes[at]=='_')) { ++at; continue; }
    const auto start=at; while(at<bytes.size() && ((bytes[at]>='a'&&bytes[at]<='z') || bytes[at]=='_')) ++at;
    const auto key=bytes.substr(start,at-start);
    if(key!="path" && key!="replace_path" && key!="archive") continue;
    if(key=="archive") return false;
    while(at<bytes.size() && (bytes[at]==' '||bytes[at]=='\t'||bytes[at]=='\r'||bytes[at]=='\n')) ++at;
    if(at==bytes.size() || bytes[at++]!='=') return false;
    while(at<bytes.size() && (bytes[at]==' '||bytes[at]=='\t')) ++at;
    if(at==bytes.size() || bytes[at++]!='"') return false;
    const auto value_start=at; while(at<bytes.size() && bytes[at]!='"' && bytes[at]!='\r' && bytes[at]!='\n') ++at;
    if(at==bytes.size() || bytes[at]!='"') return false;
    const auto value=bytes.substr(value_start,at-value_start); ++at;
    if(key=="path") {
      if(++paths>1 || !SamePath(fs::path(Wide(value)),root)) return false;
    } else {
      auto normalized=Lower(fs::path(Wide(value)).generic_wstring());
      while(!normalized.empty() && normalized.back()==L'/') normalized.pop_back();
      if(normalized.empty() || normalized==L"." || normalized==L"gui" || normalized.starts_with(L"gui/") ||
          normalized.starts_with(L"../") || normalized.find(L"/gui")!=std::wstring::npos) return false;
    }
  }
  return !outer || paths==1;
}
struct StockFile { const char *path; std::size_t bytes; const char *sha; };
constexpr std::array<StockFile,6> kStock{{
  {"hud.gui",227658,"77d0beedefe23eee22b24c1c0b160ae5ee8ec938868d3f4b7ae76296347a6ac6"},
  {"frontend_ingame_menu.gui",10812,"8498536c7d565bff610f592d45c79cbb2b0fa47ff184dafe3b324b355e0b0dfb"},
  {"window_resign_confirmation.gui",3051,"9b8ca6d2cc17ecb575c21f5a683719d4ce6472958e3bf311e2419db09c34d1c9"},
  {"shared/buttons_icons.gui",19034,"f5d8e398a396b75f588a3abd9cb07b51639d7201c71fe7a68ec869b40ce215e6"},
  {"shared/buttons.gui",41901,"88403785a1acdacc628730aaa101a04b2ae6293e74aa706a93e0e1695f3b1a0c"},
  {"shared/sounds.gui",10725,"88352f5f6ec36d9fbd703fc05f510d7ce26f6250531e152eb5f9d9131404b0fc"},
}};

bool GuiSpace(char c) noexcept {
  return c==' ' || c=='\t' || c=='\r' || c=='\n' || c=='\v' || c=='\f';
}
bool IdentifierCharacter(char c, bool first=false) noexcept {
  return (c>='a'&&c<='z') || (c>='A'&&c<='Z') || c=='_' ||
      (!first && c>='0'&&c<='9');
}
std::string_view GuiValue(std::string_view token) noexcept {
  return token.size()>=2 && token.front()=='"' && token.back()=='"'
      ? token.substr(1,token.size()-2) : token;
}
std::string LowerIdentifier(std::string_view token,bool quoted_value=true) {
  if(quoted_value) token=GuiValue(token);
  if(token.empty() || !IdentifierCharacter(token.front(),true)) return {};
  std::string result;
  for(char c:token) {
    if(!IdentifierCharacter(c)) return {};
    result+=c>='A'&&c<='Z'?static_cast<char>(c-'A'+'a'):c;
  }
  return result;
}
template<std::size_t N>
bool Contains(const std::array<std::string_view,N> &values,std::string_view value) {
  for(const auto item:values) if(item==value) return true;
  return false;
}
bool ExitReference(std::string_view value) noexcept {
  constexpr std::array<std::string_view,3> names{{"PauseMenu","ResignConfirmationWindow","OnPauseMenu"}};
  for(const auto name:names) {
    for(std::size_t start=value.find(name); start!=std::string_view::npos; start=value.find(name,start+1)) {
      if(start && IdentifierCharacter(value[start-1])) continue;
      auto end=start+name.size();
      if(name=="OnPauseMenu") {
        if(end==value.size() || !IdentifierCharacter(value[end])) return true;
      } else {
        while(end<value.size() && GuiSpace(value[end])) ++end;
        if(end<value.size() && value[end]=='.') return true;
      }
    }
  }
  return false;
}
bool UnrelatedGui(const fs::path &path,std::string_view bytes,std::string &reason) {
  const auto reject=[&](const char *why) { reason=why; return false; };
  const auto relative=Lower(path.generic_wstring());
  for(const auto protected_path:kNormalExitProtectedGuiPathsV1)
    if(relative==Wide(protected_path)) return reject("enabled_mod_gui_exit_dependency_path_collision");
  // Match the Python source reader: comments, quoted values, braces and bare
  // tokens. UTF-8 is validated before the ASCII declaration names are read.
  if(bytes.starts_with("\xef\xbb\xbf")) bytes.remove_prefix(3);
  if(!bytes.empty() && (bytes.size()>static_cast<std::size_t>(INT_MAX) || bytes.find('\0')!=std::string_view::npos ||
      MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,bytes.data(),static_cast<int>(bytes.size()),nullptr,0)<=0))
    return reject("enabled_mod_gui_utf8_invalid");
  std::vector<std::string_view> tokens;
  for(std::size_t at=0;at<bytes.size();) {
    if(GuiSpace(bytes[at])) { ++at; continue; }
    if(bytes[at]=='#') { const auto end=bytes.find_first_of("\r\n",at); at=end==std::string_view::npos?bytes.size():end; continue; }
    const auto begin=at;
    if(bytes[at]=='"') {
      ++at; bool closed=false;
      while(at<bytes.size()) {
        if(bytes[at]=='\\') { if(at+1>=bytes.size()) return reject("enabled_mod_gui_structure_invalid"); at+=2; }
        else if(bytes[at++]=='"') { closed=true; break; }
      }
      if(!closed) return reject("enabled_mod_gui_structure_invalid");
    } else if(bytes[at]=='{' || bytes[at]=='}' || bytes[at]=='=') ++at;
    else while(at<bytes.size() && !GuiSpace(bytes[at]) && bytes[at]!='{' && bytes[at]!='}' && bytes[at]!='=' && bytes[at]!='#') ++at;
    tokens.push_back(bytes.substr(begin,at-begin));
  }
  std::vector<std::size_t> stack;
  for(std::size_t i=0;i<tokens.size();++i) {
    if(tokens[i]=="{") stack.push_back(i);
    else if(tokens[i]=="}") {
      if(stack.empty()) return reject("enabled_mod_gui_structure_invalid");
      stack.pop_back();
    } else if(!stack.empty() && LowerIdentifier(tokens[i],false)=="name" && i+2<tokens.size() && tokens[i+1]=="=") {
      if(Contains(kNormalExitFixedGuiRootsV1,LowerIdentifier(tokens[i+2])))
        return reject("enabled_mod_gui_exit_root_collision");
    }
    if(ExitReference(GuiValue(tokens[i]))) return reject("enabled_mod_gui_exit_callback_reference");
    const auto declaration=LowerIdentifier(tokens[i],false);
    if((declaration=="type" || declaration=="template") && i+2<tokens.size()) {
      const auto name=LowerIdentifier(tokens[i+1]);
      if(name.empty()) continue;
      auto start=i+2;
      while(start<tokens.size() && tokens[start]!="{" && tokens[start]!="}") ++start;
      if(start==tokens.size() || tokens[start]!="{") return reject("enabled_mod_gui_structure_invalid");
      if(Contains(kNormalExitProtectedGuiSymbolsV1,name))
        return reject("enabled_mod_gui_exit_symbol_collision");
    }
  }
  if(!stack.empty()) return reject("enabled_mod_gui_structure_invalid");
  return true;
}
} // namespace

bool ParseNormalExitMapLaunchArgumentsV1(std::span<const std::wstring_view> arguments,
    NormalExitMapLaunchArgumentsV1 &output) noexcept {
  try {
    if(arguments.size()<2 || arguments.size()>5 || arguments.front().empty()) return false;
    NormalExitMapLaunchArgumentsV1 parsed{};
    bool userdir=false, debug=false, gdpr=false, loadsave=false, continue_last=false;
    for(std::size_t i=1;i<arguments.size();++i) {
      const auto arg=arguments[i];
      if(arg.starts_with(L"-userdir=")) {
        if(userdir) return false;
        userdir=true;
        const auto value=arg.substr(9);
        if(value.empty() || value.find(L'\0')!=std::wstring_view::npos) return false;
        parsed.userdir=fs::path(value);
      } else if(arg==L"-debug_mode") {
        if(debug) return false;
        debug=true;
      } else if(arg==L"-gdpr-compliant") {
        if(gdpr) return false;
        gdpr=true;
      } else if(arg==L"-continuelastsave") {
        if(continue_last || loadsave) return false;
        continue_last=true;
      } else if(arg.starts_with(L"-loadsave=")) {
        if(loadsave || continue_last) return false;
        loadsave=true;
        const auto value=arg.substr(10);
        if(value.empty() || value.size()>128) return false;
        for(const auto c:value)
          if(!((c>=L'a'&&c<=L'z') || (c>=L'A'&&c<=L'Z') ||
               (c>=L'0'&&c<=L'9') || c==L'_' || c==L'-')) return false;
        parsed.load_save_key=value;
      } else return false;
    }
    if(!userdir || parsed.userdir.empty() || !parsed.userdir.is_absolute()) return false;
    output=std::move(parsed);
    return true;
  } catch(...) { return false; }
}

bool NormalExitMapSha256V1(std::string_view bytes,std::string &digest) noexcept {
  BCRYPT_ALG_HANDLE algorithm=nullptr; BCRYPT_HASH_HANDLE hash=nullptr;
  bool okay=false; digest.clear();
  try {
    DWORD object_size=0,received=0;
    if(bytes.size()<=ULONG_MAX && BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0 &&
        BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&object_size),sizeof(object_size),&received,0)>=0 &&
        received==sizeof(object_size) && object_size>0 && object_size<=65536) {
      std::vector<unsigned char> object(object_size); std::array<unsigned char,32> value{};
      if(BCryptCreateHash(algorithm,&hash,object.data(),object_size,nullptr,0,0)>=0 &&
          BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char *>(bytes.data())),static_cast<ULONG>(bytes.size()),0)>=0 &&
          BCryptFinishHash(hash,value.data(),static_cast<ULONG>(value.size()),0)>=0) {
        constexpr char hex[]="0123456789abcdef";
        for(auto c:value) { digest+=hex[c>>4]; digest+=hex[c&15]; } okay=true;
      }
    }
  } catch(...) { digest.clear(); }
  if(hash) BCryptDestroyHash(hash);
  if(algorithm) BCryptCloseAlgorithmProvider(algorithm,0);
  return okay;
}

bool NormalExitMapSourceExecutableAdmittedV1(
    const game::AdapterDescriptor &descriptor,
    std::string_view inventory_executable_sha256) noexcept {
  const auto revision = descriptor.adapter_id == ck3_12003::kAdapterId
      ? ck3_11906::GuiAbiRevisionV1::crozier12003
      : descriptor.adapter_id == ck3_12004::kAdapterId
          ? ck3_11906::GuiAbiRevisionV1::crozier12004
          : ck3_11906::GuiAbiRevisionV1::legacy11906;
  if (!ck3_11906::IngamePrivateGuiIdentityAdmittedV1(descriptor.game_version,
          descriptor.executable_sha256, revision) || !Hex(inventory_executable_sha256))
    return false;
  for (std::size_t i = 0; i < inventory_executable_sha256.size(); ++i) {
    const auto expected = descriptor.executable_sha256[i];
    const auto lowercase = expected >= 'A' && expected <= 'F'
        ? static_cast<char>(expected + ('a' - 'A')) : expected;
    if (inventory_executable_sha256[i] != lowercase) return false;
  }
  return true;
}

bool VerifyNormalExitMapInventoryForContextV1(std::string_view expected_sha,
    const game::AdapterDescriptor &descriptor,
    const fs::path &userdir,const fs::path &image_path,
    bool &stock_verified,std::string &reason) noexcept {
  stock_verified=false;
  try {
    const auto reject=[&](const char *why) { reason=why; return false; };
    if(!Hex(expected_sha)) return reject("source_inventory_reference_missing");
    if(userdir.empty() || !userdir.is_absolute() || !Plain(userdir)) return reject("actual_launch_userdir_contract_unsupported");
    const auto manifest_path=userdir/L"normal-exit-source-inventory-v1.json";
    std::string bytes,actual_sha;
    if(!ReadFile(manifest_path,bytes,16U*1024U*1024U) || !NormalExitMapSha256V1(bytes,actual_sha) || actual_sha!=expected_sha)
      return reject("fixed_source_inventory_missing_or_sha_changed");
    Node inventory;
    if(!InventoryParser(bytes).Parse(inventory)) return reject("source_inventory_structure_invalid");
    const auto *schema=Field(inventory,"schema",Node::string), *declared_userdir=Field(inventory,"userdir",Node::string);
    const auto *profile=Field(inventory,"profile_binding_sha256",Node::string);
    const auto *settings=Field(inventory,"settings_file",Node::object), *dlc=Field(inventory,"dlc_load",Node::object);
    const auto *mods=Field(inventory,"enabled_mods",Node::array), *stock=Field(inventory,"stock_gui",Node::array);
    const auto *stock_game_root=Field(inventory,"stock_game_root",Node::string);
    const auto *executable=Field(inventory,"source_executable",Node::object);
    if(!schema || schema->text!="ck3-normal-exit-source-inventory-v1" || !declared_userdir || !SamePath(Path(*declared_userdir),userdir) ||
        !profile || !Hex(profile->text) || !settings || !dlc || !mods || mods->items.size()>64 || !stock || stock->items.size()!=kStock.size() || !stock_game_root || !executable)
      return reject("source_inventory_binding_invalid");
    if(image_path.empty() || !image_path.is_absolute()) return reject("actual_executable_path_unreadable");
    const auto *declared_image=Field(*executable,"path",Node::string), *image_hash=Field(*executable,"sha256",Node::string);
    if(!declared_image || !image_hash || !SamePath(Path(*declared_image),image_path) ||
        !NormalExitMapSourceExecutableAdmittedV1(descriptor,image_hash->text))
      return reject("source_inventory_executable_binding_changed");
    std::string dlc_bytes;
    if(!AllocatedRunningSettingsRecord(*settings,userdir,profile->text) || !FileRecord(*dlc,userdir/L"dlc_load.json",&dlc_bytes))
      return reject("actual_launch_settings_or_dlc_load_changed");
    Node actual_dlc;
    if(!InventoryParser(dlc_bytes).Parse(actual_dlc)) return reject("actual_dlc_load_invalid");
    const auto *enabled=Field(actual_dlc,"enabled_mods",Node::array);
    if(!enabled || enabled->items.size()!=mods->items.size()) return reject("enabled_mods_inventory_order_changed");
    std::set<fs::path> roots; bool gui_mod_present=false;
    for(std::size_t i=0;i<mods->items.size();++i) {
      const auto &mod=mods->items[i]; const auto *root=Field(mod,"root",Node::string), *outer=Field(mod,"outer_descriptor",Node::object);
      const auto *inner=Field(mod,"inner_descriptor",Node::object), *files=Field(mod,"files",Node::array);
      fs::path registered;
      if(!root || !outer || !inner || !files || files->items.size()>100000 || enabled->items[i].kind!=Node::string ||
          !Relative(enabled->items[i].text,registered) || registered.begin()==registered.end() || *registered.begin()!=L"mod")
        return reject("enabled_mod_source_structure_invalid");
      const auto mod_root=Path(*root);
      if(!mod_root.is_absolute() || !Plain(mod_root) || !fs::is_directory(mod_root) || !roots.insert(fs::weakly_canonical(mod_root)).second)
        return reject("enabled_mod_root_unverified");
      std::string outer_bytes,inner_bytes;
      if(!FileRecord(*outer,userdir/registered,&outer_bytes) || !FileRecord(*inner,mod_root/L"descriptor.mod",&inner_bytes) ||
          !Descriptor(outer_bytes,mod_root,true) || !Descriptor(inner_bytes,mod_root,false))
        return reject("enabled_mod_descriptor_or_gui_replace_path_changed");
      std::set<fs::path> expected_files,actual_files;
      for(const auto &file:files->items) {
        const auto *relative=Field(file,"relative_path",Node::string), *size=Field(file,"bytes",Node::number), *hash=Field(file,"sha256",Node::string);
        fs::path path;
        if(!relative || !size || !hash || !Hex(hash->text) || !Relative(relative->text,path) || !expected_files.insert(path).second)
          return reject("enabled_mod_file_inventory_unsupported");
        std::string file_bytes,file_sha;
        if(!ReadFile(mod_root/path,file_bytes,128U*1024U*1024U) || file_bytes.size()!=size->integer ||
            !NormalExitMapSha256V1(file_bytes,file_sha) || file_sha!=hash->text) return reject("enabled_mod_file_bytes_changed");
        if(Lower(path.extension().native())==L".gui") {
          gui_mod_present=true;
          if(!UnrelatedGui(path,file_bytes,reason)) return false;
        }
      }
      for(const auto &entry:fs::recursive_directory_iterator(mod_root)) {
        if(!Plain(entry.path())) return reject("enabled_mod_reparse_source_unsupported");
        if(entry.is_regular_file()) actual_files.insert(fs::relative(entry.path(),mod_root));
      }
      if(actual_files!=expected_files) return reject("enabled_mod_full_file_census_changed");
    }
    const auto game_root=image_path.parent_path().parent_path()/L"game";
    if(!SamePath(Path(*stock_game_root),game_root)) return reject("stock_gui_game_root_changed");
    const auto gui=game_root/L"gui";
    for(std::size_t i=0;i<kStock.size();++i) {
      const auto &file=stock->items[i]; const auto &pin=kStock[i];
      const auto *path=Field(file,"path",Node::string), *size=Field(file,"bytes",Node::number), *hash=Field(file,"sha256",Node::string);
      if(!path || !size || !hash || size->integer!=pin.bytes || hash->text!=pin.sha ||
          !SamePath(Path(*path),gui/fs::path(Wide(pin.path)))) return reject("stock_gui_exact_pin_mismatch");
      if(!FileRecord(file,gui/fs::path(Wide(pin.path)))) return reject("stock_gui_actual_bytes_changed");
    }
    if(gui_mod_present) {
      const auto *dependencies=Field(inventory,"stock_gui_dependencies",Node::array);
      if(!dependencies || dependencies->items.size()!=kNormalExitGuiStockDependenciesV1.size())
        return reject("stock_gui_dependency_inventory_incomplete");
      for(std::size_t i=0;i<kNormalExitGuiStockDependenciesV1.size();++i) {
        const auto &pin=kNormalExitGuiStockDependenciesV1[i]; const auto &file=dependencies->items[i];
        const auto *path=Field(file,"path",Node::string), *size=Field(file,"bytes",Node::number), *hash=Field(file,"sha256",Node::string);
        const auto expected=game_root/fs::path(Wide(pin.relative_path));
        if(!path || !size || !hash || size->integer!=pin.bytes || hash->text!=pin.sha256 || !SamePath(Path(*path),expected))
          return reject("stock_gui_dependency_exact_pin_mismatch");
        if(!FileRecord(file,expected)) return reject("stock_gui_dependency_actual_bytes_changed");
      }
    }
    // Re-read the manifest and launch configuration after the full census.
    std::string final_bytes;
    if(!ReadFile(manifest_path,final_bytes,16U*1024U*1024U) || final_bytes!=bytes ||
        !AllocatedRunningSettingsRecord(*settings,userdir,profile->text) || !FileRecord(*dlc,userdir/L"dlc_load.json"))
      return reject("source_inventory_changed_during_validation");
    stock_verified=true; reason.clear(); return true;
  } catch(...) { try { reason="source_inventory_validation_exception"; } catch(...) {} return false; }
}

bool VerifyNormalExitMapSourcesV1(std::string_view expected_sha,
    const game::AdapterDescriptor &descriptor,
    bool &stock_verified,std::string &reason) noexcept {
  stock_verified=false;
  try {
    const auto reject=[&](const char *why) { reason=why; return false; };
    if(!Hex(expected_sha)) return reject("source_inventory_reference_missing");
    int argc=0; auto **argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(!argv) return reject("actual_launch_arguments_unreadable");
    NormalExitMapLaunchArgumentsV1 launch{}; bool args_okay=false;
    if(argc>=2 && argc<=5) {
      std::array<std::wstring_view,5> arguments{};
      for(int i=0;i<argc;++i) arguments[static_cast<std::size_t>(i)]=argv[i];
      args_okay=ParseNormalExitMapLaunchArgumentsV1(
          std::span<const std::wstring_view>(arguments.data(),static_cast<std::size_t>(argc)),launch);
    }
    LocalFree(argv);
    if(!args_okay) return reject("actual_launch_userdir_contract_unsupported");
    std::array<wchar_t,32768> image{};
    const auto length=GetModuleFileNameW(nullptr,image.data(),static_cast<DWORD>(image.size()));
    if(length==0 || length>=image.size()) return reject("actual_executable_path_unreadable");
    return VerifyNormalExitMapInventoryForContextV1(expected_sha,descriptor,launch.userdir,
        fs::path(image.data()),stock_verified,reason);
  } catch(...) { try { reason="source_inventory_validation_exception"; } catch(...) {} return false; }
}
} // namespace xar::ck3_12003
