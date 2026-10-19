# Explicit input overlay; the 704bdd Native source files remain unchanged.
function(xar_native30_restore_historical_main_source_defines)
    if(NOT MSVC OR NOT TARGET xar_ck3_12002_runtime)
        message(FATAL_ERROR "Native30 source macro restoration requires the real MSVC runtime target")
    endif()
    set_property(SOURCE "${CMAKE_SOURCE_DIR}/src/ck3_12002.cpp" APPEND PROPERTY COMPILE_DEFINITIONS
        "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1>"
        "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1>")
endfunction()
cmake_language(DEFER DIRECTORY "${CMAKE_SOURCE_DIR}" CALL xar_native30_restore_historical_main_source_defines)
