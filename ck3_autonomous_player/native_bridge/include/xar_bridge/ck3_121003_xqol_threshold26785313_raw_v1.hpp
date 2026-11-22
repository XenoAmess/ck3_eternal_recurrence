#pragma once
#include "xar_bridge/ck3_121003_xqol_threshold26785313_v1.hpp"
#include "xar_bridge/ck3_121003_xqol_conversion_prompt26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct XqolThresholdScene267V1{
 XqolConversionScene267V1 prompt_scene;
 XqolConversionPromptRaw267V1 sampled_prompt;
 std::vector<GuiWindowNodeV1>widgets;
 friend bool operator==(const XqolThresholdScene267V1&,const XqolThresholdScene267V1&)=default;
};
struct XqolThresholdRaw267V1{
 XqolThresholdSource267V1 source;
 XqolConversionPromptRaw267V1 prompt;
 std::uintptr_t actor=0,definition=0,slider=0,scrollbar=0,handle=0;
 std::array<std::byte,64>definition_header{};
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const XqolThresholdRaw267V1&,const XqolThresholdRaw267V1&)=default;
};
bool VerifyXqolThresholdImage267V1(std::uintptr_t)noexcept;
bool ReadXqolThresholdRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const XqolThresholdScene267V1&,std::uint64_t,std::uint32_t,XqolThresholdRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 SetXqolThresholdRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const XqolThresholdScene267V1&,std::uint64_t,const XqolThresholdRaw267V1&)noexcept;
}
