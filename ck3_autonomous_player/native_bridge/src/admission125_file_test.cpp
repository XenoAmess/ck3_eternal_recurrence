#include "xar_bridge/adapter_admission125.hpp"
#include <iostream>
#include <stdexcept>
int wmain(int argc,wchar_t **argv){try{
 if(argc!=2)throw std::runtime_error("own output path required");
 HANDLE h=CreateFileW(argv[1],GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE)throw std::runtime_error("own file create");DWORD written=0;
 const bool wrote=WriteFile(h,"abc",3,&written,nullptr)!=0;CloseHandle(h);
 if(!wrote||written!=3)throw std::runtime_error("own file write");
 const auto sha=xar::admission125::Sha256File(argv[1]);
 if(sha!="BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD"||xar::admission125::last_hash.bytes_read!=3||std::string_view(xar::admission125::last_hash.stage)!="complete")throw std::runtime_error("actual BCrypt SHA");
 const std::wstring missing=std::wstring(argv[1])+L".nonexistent125";
 if(!xar::admission125::Sha256File(missing.c_str()).empty()||std::string_view(xar::admission125::last_hash.stage)!="file_open"||xar::admission125::last_hash.error!=ERROR_FILE_NOT_FOUND)throw std::runtime_error("first file error");
 std::cout<<"OWNFILE125_PASS BCrypt abc + missing path; no game file/process\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
