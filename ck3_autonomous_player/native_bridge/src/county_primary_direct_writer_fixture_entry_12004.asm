; Cold owned-target caller only; production entry thunk is unchanged.
OPTION CASEMAP:NONE
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
  call r9
XarCountyPrimaryFixtureReturn12004 LABEL BYTE
  add rsp, 20h
  pop r13
  ret
XarCountyPrimaryFixtureInvoke12004 ENDP
END
