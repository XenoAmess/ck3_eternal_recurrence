OPTION CASEMAP:NONE
EXTERN ParentFixtureBodySeen:BYTE
EXTERN ParentFixtureInputXmm:BYTE
EXTERN ParentFixtureReturnXmm:BYTE
EXTERN ParentFixtureFxBefore:BYTE
EXTERN ParentFixtureFxAfter:BYTE
EXTERN ParentFixtureReturnedXmm:BYTE
EXTERN ParentFixtureCallEntryRsp:QWORD
EXTERN ParentFixtureCallRbp:QWORD
EXTERN ParentFixtureReturnedRax:QWORD
EXTERN ParentFixtureReturnedRsp:QWORD
EXTERN ParentFixtureBodyCalls:QWORD
EXTERN ParentFixtureCallTarget:QWORD
PUBLIC ParentFixtureInvoke
PUBLIC ParentFixtureBody
PUBLIC ParentFixtureAfterCall
.code
ParentFixtureInvoke PROC FRAME
  push rbx
  .pushreg rbx
  push rbp
  .pushreg rbp
  push rsi
  .pushreg rsi
  push rdi
  .pushreg rdi
  push r12
  .pushreg r12
  push r13
  .pushreg r13
  push r14
  .pushreg r14
  push r15
  .pushreg r15
  sub rsp,0f8h
  .allocstack 0f8h
  lea rbp,[rsp]
  .setframe rbp,0
  movdqu [rsp+40h],xmm6
  .savexmm128 xmm6,40h
  movdqu [rsp+50h],xmm7
  .savexmm128 xmm7,50h
  movdqu [rsp+60h],xmm8
  .savexmm128 xmm8,60h
  movdqu [rsp+70h],xmm9
  .savexmm128 xmm9,70h
  movdqu [rsp+80h],xmm10
  .savexmm128 xmm10,80h
  movdqu [rsp+90h],xmm11
  .savexmm128 xmm11,90h
  movdqu [rsp+0a0h],xmm12
  .savexmm128 xmm12,0a0h
  movdqu [rsp+0b0h],xmm13
  .savexmm128 xmm13,0b0h
  movdqu [rsp+0c0h],xmm14
  .savexmm128 xmm14,0c0h
  movdqu [rsp+0d0h],xmm15
  .savexmm128 xmm15,0d0h
  .endprolog
  mov [rsp+0e0h],rcx
  mov rax,05555h
  mov [rsp+20h],rax
  mov rax,06666h
  mov [rsp+28h],rax
  lea rax,[rsp-8]
  mov ParentFixtureCallEntryRsp,rax
  mov ParentFixtureCallRbp,rbp
  movdqu xmm0,xmmword ptr [ParentFixtureInputXmm+00h]
  movdqu xmm1,xmmword ptr [ParentFixtureInputXmm+10h]
  movdqu xmm2,xmmword ptr [ParentFixtureInputXmm+20h]
  movdqu xmm3,xmmword ptr [ParentFixtureInputXmm+30h]
  movdqu xmm4,xmmword ptr [ParentFixtureInputXmm+40h]
  movdqu xmm5,xmmword ptr [ParentFixtureInputXmm+50h]
  movdqu xmm6,xmmword ptr [ParentFixtureInputXmm+60h]
  movdqu xmm7,xmmword ptr [ParentFixtureInputXmm+70h]
  movdqu xmm8,xmmword ptr [ParentFixtureInputXmm+80h]
  movdqu xmm9,xmmword ptr [ParentFixtureInputXmm+90h]
  movdqu xmm10,xmmword ptr [ParentFixtureInputXmm+0a0h]
  movdqu xmm11,xmmword ptr [ParentFixtureInputXmm+0b0h]
  movdqu xmm12,xmmword ptr [ParentFixtureInputXmm+0c0h]
  movdqu xmm13,xmmword ptr [ParentFixtureInputXmm+0d0h]
  movdqu xmm14,xmmword ptr [ParentFixtureInputXmm+0e0h]
  movdqu xmm15,xmmword ptr [ParentFixtureInputXmm+0f0h]
  mov rax,0aaaah
  mov rcx,01111h
  mov rdx,[rsp+0e0h]
  mov r8,0eeeeeeeefffffff9h
  mov r9,09999h
  mov r10,0a0a0h
  mov r11,0b0b0h
  mov rbx,0bbbbh
  mov rsi,05151h
  mov rdi,0d1d1h
  mov r12,01212h
  mov r13,01313h
  mov r14,01414h
  mov r15,01515h
  push 0ed7h
  popfq
  fxsave [ParentFixtureFxBefore]
  call qword ptr [ParentFixtureCallTarget]
ParentFixtureAfterCall LABEL BYTE
  mov ParentFixtureReturnedRax,rax
  mov ParentFixtureReturnedRsp,rsp
  movdqu xmmword ptr [ParentFixtureReturnedXmm],xmm0
  fxsave [ParentFixtureFxAfter]
  cld
  movdqu xmm6,[rsp+40h]
  movdqu xmm7,[rsp+50h]
  movdqu xmm8,[rsp+60h]
  movdqu xmm9,[rsp+70h]
  movdqu xmm10,[rsp+80h]
  movdqu xmm11,[rsp+90h]
  movdqu xmm12,[rsp+0a0h]
  movdqu xmm13,[rsp+0b0h]
  movdqu xmm14,[rsp+0c0h]
  movdqu xmm15,[rsp+0d0h]
  lea rsp,[rbp+0f8h]
  pop r15
  pop r14
  pop r13
  pop r12
  pop rdi
  pop rsi
  pop rbp
  pop rbx
  ret
ParentFixtureInvoke ENDP

; Entered only after the test's actual copied native prefix. The zero-length
; prologue describes that inherited frame, not a second stack allocation.
ParentFixtureBody PROC FRAME
  .pushreg rbx
  .pushreg rbp
  .allocstack 98h
  .savereg r14,88h
  .endprolog
  mov qword ptr [ParentFixtureBodySeen+00h],rax
  mov qword ptr [ParentFixtureBodySeen+08h],rcx
  mov qword ptr [ParentFixtureBodySeen+10h],rdx
  mov qword ptr [ParentFixtureBodySeen+18h],r8
  mov qword ptr [ParentFixtureBodySeen+20h],r9
  mov qword ptr [ParentFixtureBodySeen+28h],r10
  mov qword ptr [ParentFixtureBodySeen+30h],r11
  mov qword ptr [ParentFixtureBodySeen+38h],rbx
  mov qword ptr [ParentFixtureBodySeen+40h],rbp
  mov qword ptr [ParentFixtureBodySeen+48h],rsi
  mov qword ptr [ParentFixtureBodySeen+50h],rdi
  mov qword ptr [ParentFixtureBodySeen+58h],r12
  mov qword ptr [ParentFixtureBodySeen+60h],r13
  mov qword ptr [ParentFixtureBodySeen+68h],r14
  mov qword ptr [ParentFixtureBodySeen+70h],r15
  mov qword ptr [ParentFixtureBodySeen+78h],rsp
  movdqu xmmword ptr [ParentFixtureBodySeen+080h],xmm0
  movdqu xmmword ptr [ParentFixtureBodySeen+090h],xmm1
  movdqu xmmword ptr [ParentFixtureBodySeen+0a0h],xmm2
  movdqu xmmword ptr [ParentFixtureBodySeen+0b0h],xmm3
  movdqu xmmword ptr [ParentFixtureBodySeen+0c0h],xmm4
  movdqu xmmword ptr [ParentFixtureBodySeen+0d0h],xmm5
  movdqu xmmword ptr [ParentFixtureBodySeen+0e0h],xmm6
  movdqu xmmword ptr [ParentFixtureBodySeen+0f0h],xmm7
  movdqu xmmword ptr [ParentFixtureBodySeen+100h],xmm8
  movdqu xmmword ptr [ParentFixtureBodySeen+110h],xmm9
  movdqu xmmword ptr [ParentFixtureBodySeen+120h],xmm10
  movdqu xmmword ptr [ParentFixtureBodySeen+130h],xmm11
  movdqu xmmword ptr [ParentFixtureBodySeen+140h],xmm12
  movdqu xmmword ptr [ParentFixtureBodySeen+150h],xmm13
  movdqu xmmword ptr [ParentFixtureBodySeen+160h],xmm14
  movdqu xmmword ptr [ParentFixtureBodySeen+170h],xmm15
  mov rax,[rsp+0d0h]
  mov qword ptr [ParentFixtureBodySeen+180h],rax
  mov rax,[rsp+0d8h]
  mov qword ptr [ParentFixtureBodySeen+188h],rax
  lock inc qword ptr [ParentFixtureBodyCalls]
  movdqu xmm0,xmmword ptr [ParentFixtureReturnXmm]
  mov rax,0d00dfeed11223344h
  mov r14,[rsp+88h]
  add rsp,98h
  pop rbp
  pop rbx
  ret
ParentFixtureBody ENDP
END
