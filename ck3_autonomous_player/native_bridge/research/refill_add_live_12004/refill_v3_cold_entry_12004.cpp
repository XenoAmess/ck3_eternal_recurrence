// Explicit cold adapter; the actual production Probe is compiled in this TU.
#ifndef XAR_ENABLE_REFILL_V3_COLD_PROBE_12004
#define XAR_ENABLE_REFILL_V3_COLD_PROBE_12004 0
#endif
#if !XAR_ENABLE_REFILL_V3_COLD_PROBE_12004
#include <iostream>
int wmain(int,wchar_t**){std::cerr<<"default OFF: cold Probe not entered\n";return 3;}
#else
#define XAR_REFILL_V3_COLD_BUILD 1
#define wmain XarDisabledProductionEntryForCold12004
#include "../refill_add_hwprobe_12004.cpp"
#undef wmain

int wmain(int argc,wchar_t **argv){
  if(argc!=15||std::wstring(argv[1])!=L"--fixture-meta"||std::wstring(argv[3])!=L"--timeout-ms"||
      std::wstring(argv[5])!=L"--raw"||std::wstring(argv[7])!=L"--ready"||
      std::wstring(argv[9])!=L"--max-hits"||std::wstring(argv[11])!=L"--select-missing"||
      std::wstring(argv[13])!=L"--machine-id")return 2;
  try{
    const std::filesystem::path metadata(argv[2]);
    if(std::filesystem::file_size(metadata)>8192)return 2;
    std::ifstream input(metadata);if(!input)return 2;
    std::map<std::string,std::string> meta;std::string line;
    while(std::getline(input,line)){
      if(!line.empty()&&line.back()=='\r')line.pop_back();
      const auto at=line.find('=');
      if(at==std::string::npos||line.size()>1024||!meta.emplace(line.substr(0,at),line.substr(at+1)).second)return 2;
    }
    const std::array<const char*,15> keys{"pid","tid","created","module_base","site0","site1",
      "regiment","slot","arrg_registry_slot","army_registry_slot","q","before","go_event","audit_event","finish_event"};
    if(meta.size()!=keys.size())return 2;for(auto key:keys)if(!meta.contains(key))return 2;
    auto number=[](const std::string&s){std::size_t n=0;auto v=std::stoull(s,&n,0);
      if(n!=s.size()||s.empty()||s[0]=='-')throw std::out_of_range("unsigned cold metadata");return v;};
    auto u32=[&](const char*key){auto n=number(meta.at(key));if(n>0xFFFFFFFFULL)throw std::out_of_range("u32");return DWORD(n);};
    const DWORD pid=u32("pid");g_expected_tid=u32("tid");g_expected_created=number(meta.at("created"));
    g_expected_regiment=u32("regiment");g_expected_slot=u32("slot");
    const std::wstring missing(argv[12]);if(missing!=L"0"&&missing!=L"1")return 2;
    if(missing==L"1"){if(g_expected_regiment>=0xFFFFFFFEU)return 2;++g_expected_regiment;}
    g_fixture_base=number(meta.at("module_base"));g_fixture_sites={number(meta.at("site0")),number(meta.at("site1"))};
    g_fixture_arrg_slot=number(meta.at("arrg_registry_slot"));g_fixture_army_slot=number(meta.at("army_registry_slot"));
    auto ascii=[](const std::wstring&s){std::string out;for(auto c:s){if(c>127)throw std::out_of_range("ASCII");out+=char(c);}return out;};
    g_fixture_hit_limit=number(ascii(argv[10]));
    auto timeout=number(ascii(argv[4]));if(timeout<1000||timeout>300000||!g_fixture_hit_limit||g_fixture_hit_limit>100000)return 2;
    const std::wstring machine(argv[14]);if(machine.empty()||machine.size()>128)return 2;
    for(auto c:machine){if(!((c>=L'a'&&c<=L'z')||(c>=L'0'&&c<=L'9')||c==L'-'))return 2;g_machine+=char(c);}
    if(!pid||!g_expected_tid||!g_expected_created||g_expected_slot>=7||g_expected_regiment==0xFFFFFFFFU)return 2;
    // Identity must be the exact named sibling project image, never ck3.exe.
    HANDLE p=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,pid);if(!p)return 2;
    const bool own=ProcessCreationTime(p)==g_expected_created&&ColdSiblingImage12004(p,pid);
    CloseHandle(p);if(!own)return 2;
    return Probe(pid,DWORD(timeout),argv[6],argv[8],g_fixture_sites);
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}
#endif
