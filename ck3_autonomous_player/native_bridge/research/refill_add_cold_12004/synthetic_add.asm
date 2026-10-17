option casemap:none
EXTERN g_AddExecutedCount:DWORD
PUBLIC SyntheticAdd
PUBLIC SyntheticBefore
PUBLIC SyntheticAfter
.code
SyntheticAdd PROC
  push rbx
  push rsi
  sub rsp,68h
  mov rsi,rcx
  lea rbx,[rsi+10h]
  imul r8,r8,24h
  lea rax,[rsi+r8+28h]
  movsxd rcx,dword ptr [rax-4]
  ; Fixture-only q window for the same v3 RPM helper, not a CK3 RSP claim.
  ; MOV preserves all flags/GPRs used by the unchanged original ADD below.
  mov qword ptr [rsp+20h],0
  mov qword ptr [rsp+28h],0
  mov qword ptr [rsp+30h],0
  mov dword ptr [rsp+38h],0
  mov dword ptr [rsp+rcx*4+20h],edx
  mov r9,0123456789ABCDEFh
  mov qword ptr [rsp+58h],r9
SyntheticBefore LABEL BYTE
  add dword ptr [rax-0Ch],edx
SyntheticAfter LABEL BYTE
  mov ecx,dword ptr [rax-0Ch]
  cmp ecx,dword ptr [rax-10h]
  lock inc dword ptr [g_AddExecutedCount]
  add rsp,68h
  pop rsi
  pop rbx
  ret
SyntheticAdd ENDP
END
