// No process/module discovery: exercise the actual closed OFF implementation.
#include "ck3_121003_full111.cpp"
#include <iostream>
int main() {
 namespace current=xar::ck3_121003::full111;
 const auto b=current::BindFull(0x180000000ULL,current::kExecutableSha256);
 if(b.core.enabled||b.exact_build_admitted)return 1;
 xar::ck3_1210::FullSnapshotBindingsV1 forged{};
 forged.core.enabled=true;forged.exact_build_admitted=true;
 xar::game::Snapshot output{};output.date_raw=1;
 xar::ck3_1210::FullSnapshotDiagnosticsV1 diagnostics{};
 if(current::ReadFull(forged,output,diagnostics)||output!=xar::game::Snapshot{}||diagnostics.complete)return 2;
 std::cout<<"PASS current Full111 default OFF: binder and direct reader closed\n";
 return 0;
}
