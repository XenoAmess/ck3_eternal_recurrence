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
