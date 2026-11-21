// Actual production file guard only; no owner/native stubs.
#include <fstream>
#include <iostream>
#include <stdexcept>
#include "xar_bridge/ck3_121003_aub_observer_fixture_body26785313_v1.hpp"
#include <array>
#include <filesystem>
#include <string>
#include <cstring>
#include <windows.h>
#include <shellapi.h>
namespace xar::ck3_121003::build26785313 {namespace {
#include "ck3_121003_aub_observer_fixture26785313_file.inc"
}}
using namespace xar::ck3_121003::build26785313;
void Check(bool v){if(!v)throw std::runtime_error("fixed body/path/file witness invariant");}
void Write(const std::filesystem::path&p,std::string_view bytes){std::ofstream f(p,std::ios::binary|std::ios::trunc);f.write(bytes.data(),static_cast<std::streamsize>(bytes.size()));f.close();Check(!f.fail());}
int main(){try{
 std::filesystem::path userdir;Check(SelfUserdir(userdir));const auto file=userdir/L"run"/L"xar_mcp_inbox.txt";
 InputWitness a,b;Check(ReadFixedInput(a)&&ReadFixedInput(b)&&a==b);Check(a.size_low==52);
 Write(file,"random_player = { trigger_event = { id = aubf.2 } }\n");Check(!ReadFixedInput(b));
 Write(file,std::string(kAubObserverFixtureBody267V1)+"\n");Check(!ReadFixedInput(b));
 Write(file,kAubObserverFixtureBody267V1);Check(ReadFixedInput(b));
 const auto moved=file.parent_path()/L"retained-test-input.txt";Check(!std::filesystem::exists(moved));
 std::filesystem::rename(file,moved);Check(!ReadFixedInput(a));std::filesystem::rename(moved,file);Check(ReadFixedInput(a));
 std::cout<<"PASS exact own-userdir/run file, 52-byte body, changed-event/extra-byte/missing refusal; no Native calls\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
