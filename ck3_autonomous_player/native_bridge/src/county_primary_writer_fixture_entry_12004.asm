; Cold fixture only: owned synthetic caller and R13, never a CK3 pointer.
OPTION CASEMAP:NONE
EXTERN XarActualLossWriterCountyEntryThunk12004V1:PROC
PUBLIC XarCountyPrimaryFixtureInvoke12004
PUBLIC XarCountyPrimaryFixtureReturn12004
.code
XarCountyPrimaryFixtureInvoke12004 PROC FRAME
  push r13
  .pushreg r13
  sub rsp, 20h
  .allocstack 20h
  .endprolog
  mov r13, r8
  call XarActualLossWriterCountyEntryThunk12004V1
XarCountyPrimaryFixtureReturn12004 LABEL BYTE
  add rsp, 20h
  pop r13
  ret
XarCountyPrimaryFixtureInvoke12004 ENDP
END
