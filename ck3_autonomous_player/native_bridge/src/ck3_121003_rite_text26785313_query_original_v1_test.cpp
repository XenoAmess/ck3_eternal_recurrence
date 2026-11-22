// One additional actual serializer caller; original fifteen files and first EXE stay immutable.
#define main PreservedFirstTextProducerMain
#include "ck3_121003_rite_text26785313_wire_v1_test.cpp"
#undef main
int main(int argc,char**argv){try{if(argc==1){Good(Wire(Available(),"rite-text-original-query-verification"));std::cout<<"PASS one original query beforeSource verifier\n";return 0;}if(argc!=2)throw std::runtime_error("expected NEW emit directory");const std::filesystem::path root=argv[1];if(!CreateDirectoryW(root.c_str(),nullptr))throw std::runtime_error("emit directory must be NEW");auto r=Available();auto bytes=Wire(r,"rite-text-original-result-query-original-source");Good(bytes);WriteNew(root/"query-original-source.json",bytes+"\n");std::cout<<"PASS one original-source actual query serializer frame; no re-emit old15\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
