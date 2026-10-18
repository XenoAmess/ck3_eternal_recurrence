; Existing 2634190 detour destination only. No new native patch site.
; Capture incoming county caller nonvolatile R13 BEFORE a C++ prologue.
OPTION CASEMAP:NONE
EXTERN XarActualLossWriterHookCapturedCounty12004V1:PROC
PUBLIC XarActualLossWriterCountyEntryThunk12004V1
.code
XarActualLossWriterCountyEntryThunk12004V1 PROC FRAME
  sub rsp, 28h
  .allocstack 28h
  .endprolog
  lea r8, [rsp+28h]
  mov r9, r13
  call XarActualLossWriterHookCapturedCounty12004V1
  add rsp, 28h
  ret
XarActualLossWriterCountyEntryThunk12004V1 ENDP
END
