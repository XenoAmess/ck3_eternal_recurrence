; Declared synthetic ABI only; never callable CK3 signature inference.
OPTION CASEMAP:NONE
EXTERN ParentColdBodyCalls:QWORD
EXTERN ParentColdLastArgs:BYTE
PUBLIC ParentEntryStart
PUBLIC ParentEntryBody
.code
; uint64 ParentEntryStart(void* RCX, void* RDX, uint64 R8, uint64 R9).
; Exact retained parent first16B, then a fully owned synthetic body.
ParentEntryStart PROC FRAME
  mov rax,rsp
  push rbx
  .pushreg rbx
  push rbp
  .pushreg rbp
  sub rsp,98h
  .allocstack 98h
  mov [rax-20h],r14
  .savereg r14,88h
  .endprolog
ParentEntryBody LABEL BYTE
  mov qword ptr [ParentColdLastArgs+00h],rcx
  mov qword ptr [ParentColdLastArgs+08h],rdx
  mov qword ptr [ParentColdLastArgs+10h],r8
  mov qword ptr [ParentColdLastArgs+18h],r9
  lock inc qword ptr [ParentColdBodyCalls]
  mov rax,r8
  xor rax,5a5ah
  mov r14,[rsp+88h]
  add rsp,98h
  pop rbp
  pop rbx
  ret
ParentEntryStart ENDP
END
