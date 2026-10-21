; Owned surrogate ABI only. Never a declaration that CK3 is safe to call.
OPTION CASEMAP:NONE
EXTERN PointerColdBodyCalls:QWORD
EXTERN PointerColdLastArgs:BYTE
EXTERN PointerColdLoadedContext:QWORD
EXTERN PointerColdPostFlags:QWORD
EXTERN PointerColdOtherAccessCalls:QWORD
PUBLIC PointerEntryStart
PUBLIC PointerEntryBody
PUBLIC PointerOtherRead
PUBLIC PointerOtherReadPost
PUBLIC PointerOtherWrite
PUBLIC PointerOtherWritePost
.code
PointerEntryStart PROC FRAME
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
 mov rbp,rdx
 mov rdx,qword ptr [rdx+1c0h]
PointerEntryBody LABEL BYTE
 mov r14,rcx
 mov qword ptr [PointerColdLastArgs+00h],rcx
 mov qword ptr [PointerColdLastArgs+08h],rbp
 mov qword ptr [PointerColdLastArgs+10h],r8
 mov qword ptr [PointerColdLastArgs+18h],r9
 mov qword ptr [PointerColdLoadedContext],rdx
 pushfq
 pop rax
 mov qword ptr [PointerColdPostFlags],rax
 lock inc qword ptr [PointerColdBodyCalls]
 mov rax,r8
 xor rax,5a5ah
 mov r14,[rsp+88h]
 add rsp,98h
 pop rbp
 pop rbx
 ret
PointerEntryStart ENDP
PointerOtherRead PROC
 mov rax,qword ptr [rdx+1c0h]
PointerOtherReadPost LABEL BYTE
 lock inc qword ptr [PointerColdOtherAccessCalls]
 ret
PointerOtherRead ENDP
PointerOtherWrite PROC
 mov qword ptr [rdx+1c0h],r8
PointerOtherWritePost LABEL BYTE
 mov rax,r8
 lock inc qword ptr [PointerColdOtherAccessCalls]
 ret
PointerOtherWrite ENDP
END
