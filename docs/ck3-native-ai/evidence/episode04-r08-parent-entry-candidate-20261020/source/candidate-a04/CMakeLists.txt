cmake_minimum_required(VERSION 3.20)
project(xar_parent_entry_opportunity_source_candidate LANGUAGES CXX)
option(XAR_ENABLE_PARENT_ENTRY_OPPORTUNITY_12004 "Unqualified parent-entry candidate" OFF)
if(XAR_ENABLE_PARENT_ENTRY_OPPORTUNITY_12004)
  if(NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "This candidate requires qualified MSVC x64/MASM")
  endif()
  enable_language(ASM_MASM)
  add_library(xar_parent_entry_opportunity_12004 STATIC
    parent_entry_opportunity_12004.cpp parent_entry_opportunity_12004.asm)
  target_compile_features(xar_parent_entry_opportunity_12004 PRIVATE cxx_std_17)
  target_compile_definitions(xar_parent_entry_opportunity_12004 PRIVATE
    XAR_ENABLE_PARENT_ENTRY_OPPORTUNITY_12004=1)
  target_compile_options(xar_parent_entry_opportunity_12004 PRIVATE
    $<$<COMPILE_LANGUAGE:CXX>:/W4>)
  # No bridge/host startup registration, no automatic installation/arming.
endif()
