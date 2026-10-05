#include "xar_bridge/normal_exit_map_source_v1.hpp"
#include <windows.h>
#include <shellapi.h>
#include <array>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using xar::ck3_12003::NormalExitMapLaunchArgumentsV1;
using xar::ck3_12003::ParseNormalExitMapLaunchArgumentsV1;
static unsigned checked=0;
static void Require(bool okay,const char *name) {
  if(!okay) { std::cerr << "fixture_failed:" << name << '\n'; std::exit(1); }
}
static void Check(std::vector<std::wstring_view> args,bool accept,const char *name) {
  NormalExitMapLaunchArgumentsV1 output{};
  output.userdir=L"C:/sentinel"; output.load_save_key=L"unchanged";
  const bool actual=ParseNormalExitMapLaunchArgumentsV1(args,output);
  Require(actual==accept,name);
  if(!actual) Require(output.userdir==std::filesystem::path(L"C:/sentinel") && output.load_save_key==L"unchanged","rejected_output_unchanged");
  ++checked;
}
int main() {
  const std::array<std::wstring_view,5> actual_r8{{
  L"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\binaries\\ck3.exe",
  L"-debug_mode",
  L"-gdpr-compliant",
  L"-userdir=C:/workspace/ck3_lyd_runtime_20261004/live-attempt-008/userdir",
  L"-loadsave=lyd_r8_resume_0111"
  }};
  NormalExitMapLaunchArgumentsV1 parsed{};
  Require(ParseNormalExitMapLaunchArgumentsV1(actual_r8,parsed),"actual_r8_launch");
  Require(parsed.userdir==std::filesystem::path(L"C:/workspace/ck3_lyd_runtime_20261004/live-attempt-008/userdir") &&
      parsed.load_save_key==L"lyd_r8_resume_0111","actual_r8_values_exact");
  ++checked;
  int argc=0;
  auto **argv=CommandLineToArgvW(L"\"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\binaries\\ck3.exe\" -debug_mode -gdpr-compliant -userdir=C:/workspace/ck3_lyd_runtime_20261004/live-attempt-008/userdir -loadsave=lyd_r8_resume_0111",&argc);
  Require(argv!=nullptr && argc==static_cast<int>(actual_r8.size()),"windows_argv_count");
  std::array<std::wstring_view,5> decoded{};
  for(int i=0;i<argc;++i) {
    decoded[static_cast<std::size_t>(i)]=argv[i];
    Require(decoded[static_cast<std::size_t>(i)]==actual_r8[static_cast<std::size_t>(i)],"windows_argv_exact");
  }
  NormalExitMapLaunchArgumentsV1 decoded_output{};
  Require(ParseNormalExitMapLaunchArgumentsV1(decoded,decoded_output) &&
      decoded_output.userdir==parsed.userdir && decoded_output.load_save_key==parsed.load_save_key,"windows_actual_r8_parse");
  LocalFree(argv); ++checked;
  constexpr auto exe=L"C:/game/binaries/ck3.exe", dir=L"-userdir=C:/owned-fixture/userdir";
  Check({exe,L"-debug_mode",L"-gdpr-compliant",dir},true,"original_r7_no_loadsave");
  Check({exe,dir},true,"required_userdir_only");
  Check({exe,L"-loadsave=generic_save-01",dir,L"-gdpr-compliant",L"-debug_mode"},true,"generic_reordered_save");
  const std::wstring max_key=L"-loadsave="+std::wstring(128,L'a');
  Check({exe,dir,max_key},true,"save_key_max128");
  Check({},false,"missing_executable");
  Check({exe},false,"missing_userdir");
  Check({L"",dir},false,"empty_executable");
  Check({exe,L"-userdir="},false,"empty_userdir");
  Check({exe,L"-userdir=relative/path"},false,"relative_userdir");
  Check({exe,dir,dir},false,"duplicate_userdir");
  Check({exe,dir,L"-debug_mode",L"-debug_mode"},false,"duplicate_debug");
  Check({exe,dir,L"-gdpr-compliant",L"-gdpr-compliant"},false,"duplicate_gdpr");
  Check({exe,dir,L"-loadsave=one",L"-loadsave=two"},false,"duplicate_loadsave");
  Check({exe,dir,L"-loadsave="},false,"empty_loadsave");
  const std::wstring too_long=L"-loadsave="+std::wstring(129,L'a');
  Check({exe,dir,too_long},false,"save_key_max129_rejected");
  Check({exe,dir,L"-loadsave=../escape"},false,"traversal_save");
  Check({exe,dir,L"-loadsave=C:/elsewhere/save"},false,"absolute_save_path");
  Check({exe,dir,L"-loadsave=folder/save"},false,"save_subdirectory");
  Check({exe,dir,L"-loadsave=folder\\save"},false,"save_backslash");
  Check({exe,dir,L"-loadsave=save key"},false,"save_space");
  Check({exe,dir,L"-loadsave=save.ck3"},false,"outside_bare_key_scope");
  Check({exe,dir,L"-loadsave=key;quit"},false,"save_delimiter");
  Check({exe,dir,L"-loadsave=\"key\""},false,"literal_quote_save");
  Check({exe,dir,L"-loadsave=%SAVE%"},false,"save_environment_expression");
  Check({exe,dir,L"-loadsave=\u4e2d\u6587"},false,"save_unicode_outside_scope");
  const std::wstring nul_key(L"-loadsave=one\0two",17);
  Check({exe,dir,nul_key},false,"embedded_nul_key");
  Check({exe,dir,L"-loadsave",L"one"},false,"split_loadsave_flag");
  Check({exe,dir,L"-loadsave=one",L"-loadgame=two"},false,"unknown_flag");
  Check({exe,dir,L"-skip-save"},false,"unknown_save_policy_flag");
  Check({exe,dir,L"-loadsave=one",L"-debug_mode",L"-gdpr-compliant",L"-unknown"},false,"too_many_arguments");
  std::cout << "{\"status\":\"PASS\",\"cases\":" << checked <<
      ",\"actual_r8_argv_and_windows_decoder\":true,\"output_unchanged_on_reject\":true,\"game_calls\":0}\n";
  return 0;
}
