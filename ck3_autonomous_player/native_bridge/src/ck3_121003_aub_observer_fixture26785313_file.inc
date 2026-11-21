// Exact internal file guard shared with the file-only NoGame test.
struct InputWitness {
 std::wstring path;std::uint32_t volume=0,index_high=0,index_low=0,size_high=0,size_low=0;
 std::uint64_t creation=0,write=0;
 friend bool operator==(const InputWitness&,const InputWitness&)=default;
};
[[maybe_unused]]bool SelfUserdir(std::filesystem::path&out){int argc=0;wchar_t**argv=CommandLineToArgvW(GetCommandLineW(),&argc);if(!argv)return false;std::wstring chosen;bool valid=argc>0&&argc<=512;
 for(int i=1;valid&&i<argc;++i){std::wstring_view a=argv[i];std::wstring_view value;
  if(a==L"-userdir"||a==L"--userdir"){if(++i>=argc){valid=false;break;}value=argv[i];}
  else if(a.starts_with(L"-userdir="))value=a.substr(9);else if(a.starts_with(L"--userdir="))value=a.substr(10);else continue;
  if(!chosen.empty()||value.empty()||value.size()>32700){valid=false;break;}chosen.assign(value);
 }
 LocalFree(argv);if(!valid||chosen.empty())return false;out=std::filesystem::path(chosen);return out.is_absolute();
}
[[maybe_unused]]bool ReadFixedInput(InputWitness&out){
#if defined(XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1) && XAR_CK3_ENABLE_121003_26785313_AUB_PRIVATE_FIXTURE_V1
 static_assert(!kAubObserverFixtureBody267V1.empty()&&kAubObserverFixtureBody267V1.size()<=2048);
 std::filesystem::path userdir;if(!SelfUserdir(userdir))return false;const auto path=userdir/L"run"/L"xar_mcp_inbox.txt";
 HANDLE h=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);if(h==INVALID_HANDLE_VALUE)return false;
 BY_HANDLE_FILE_INFORMATION info{};std::array<char,2049> bytes{};DWORD read=0;const bool good=GetFileInformationByHandle(h,&info)&&!(info.dwFileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))&&info.nFileSizeHigh==0&&info.nFileSizeLow==kAubObserverFixtureBody267V1.size()&&ReadFile(h,bytes.data(),info.nFileSizeLow,&read,nullptr)&&read==info.nFileSizeLow&&std::memcmp(bytes.data(),kAubObserverFixtureBody267V1.data(),read)==0;
 const bool closed=CloseHandle(h)!=0;if(!good||!closed)return false;
 out.path=path.native();out.volume=info.dwVolumeSerialNumber;out.index_high=info.nFileIndexHigh;out.index_low=info.nFileIndexLow;out.size_high=info.nFileSizeHigh;out.size_low=info.nFileSizeLow;
 out.creation=(static_cast<std::uint64_t>(info.ftCreationTime.dwHighDateTime)<<32)|info.ftCreationTime.dwLowDateTime;out.write=(static_cast<std::uint64_t>(info.ftLastWriteTime.dwHighDateTime)<<32)|info.ftLastWriteTime.dwLowDateTime;return true;
#else
 (void)out;return false;
#endif
}
