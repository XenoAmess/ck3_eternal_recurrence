# Independent optional finance extension; never enabled by basic36 alone.
option(XAR_CK3_ENABLE_1210_HOTFIX_26757580_PERSONAL_CASH_V2 "Enable qualified BB3 actor personal Cash V2 candidate" OFF)
if(XAR_CK3_ENABLE_1210_HOTFIX_26757580_PERSONAL_CASH_V2)
  if(NOT XAR_CK3_ENABLE_1210_HOTFIX_26757580_BASIC_V1 OR NOT XAR_CK3_ENABLE_1210_PERSONAL_CASH_V2)
    message(FATAL_ERROR "BB3 Cash V2 requires exact basic profile and existing Cash V2 implementation")
  endif()
  set_property(SOURCE src/ck3_1210_adapter.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_1210_HOTFIX_26757580_PERSONAL_CASH_V2=1>")
endif()
