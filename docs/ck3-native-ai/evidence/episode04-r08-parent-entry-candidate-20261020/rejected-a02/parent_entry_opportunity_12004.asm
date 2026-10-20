; SOURCE CANDIDATE ONLY: must qualify actual machine code and unwind at every
; instruction boundary before deployment. No guessed C++ original signature.
OPTION CASEMAP:NONE
EXTERN XarParentEntryState12004:BYTE
EXTERN XarParentEntryContinuation12004:QWORD
EXTERN XarParentEntryOriginalPrefixTarget12004:QWORD
PUBLIC XarParentEntryThunk12004
PUBLIC XarParentEntryOriginalPrefix12004
.code
XarParentEntryThunk12004 PROC FRAME
  push rbp
  .pushreg rbp
  pushfq
  .allocstack 8
  lea rsp,[rsp-40h]
  .allocstack 40h
  lea rbp,[rsp]
  .setframe rbp,0
  .endprolog
  ; No instruction above changes RFLAGS. No CALL or XMM/x87/AVX instruction
  ; occurs anywhere in this thunk. Original argument/home slots are untouched.
  mov [rbp+00h],rax
  mov [rbp+08h],rcx
  mov [rbp+10h],rdx
  mov [rbp+18h],r8
  mov [rbp+20h],r9
  mov [rbp+28h],r10
  mov [rbp+30h],r11
  lea r11,XarParentEntryState12004
  lock inc qword ptr [r11+100h]
  cmp qword ptr [r11+00h],0
  je parent_done
  cmp rdx,[r11+08h]
  je parent_matching
  lock inc qword ptr [r11+40h]
  jnz parent_done
  mov qword ptr [r11+108h],1
  jmp parent_done
parent_matching:
  lock inc qword ptr [r11+48h]
  jnz parent_claim
  mov qword ptr [r11+108h],1
parent_claim:
  xor eax,eax
  mov ecx,1
  lock cmpxchg qword ptr [r11+58h],rcx
  je parent_capture
  lock inc qword ptr [r11+50h]
  jnz parent_done
  mov qword ptr [r11+108h],1
  jmp parent_done
parent_capture:
  mov rax,[rbp+00h]
  mov [r11+60h],rax
  mov rax,[rbp+08h]
  mov [r11+68h],rax
  mov rax,[rbp+10h]
  mov [r11+70h],rax
  mov rax,[rbp+18h]
  mov [r11+78h],rax
  mov rax,[rbp+20h]
  mov [r11+80h],rax
  mov rax,[rbp+28h]
  mov [r11+88h],rax
  mov rax,[rbp+30h]
  mov [r11+90h],rax
  mov [r11+98h],rbx
  mov rax,[rbp+48h]
  mov [r11+0a0h],rax
  mov [r11+0a8h],rsi
  mov [r11+0b0h],rdi
  mov [r11+0b8h],r12
  mov [r11+0c0h],r13
  mov [r11+0c8h],r14
  mov [r11+0d0h],r15
  lea rax,[rbp+50h]
  mov [r11+0d8h],rax
  mov rax,[rbp+40h]
  mov [r11+0e0h],rax
  mov rax,[rbp+50h]
  mov [r11+0e8h],rax
  mov rax,gs:[48h]
  mov [r11+0f0h],rax
  rdtsc
  shl rdx,32
  or rax,rdx
  mov [r11+0f8h],rax
  ; x86-64 ordinary stores precede this aligned ready-store. Snapshot must first
  ; turn enabled OFF and observe active_thunks==0 using interlocked operations.
  mov qword ptr [r11+58h],2
parent_done:
  lock dec qword ptr [r11+100h]
  mov rax,[rbp+00h]
  mov rcx,[rbp+08h]
  mov rdx,[rbp+10h]
  mov r8,[rbp+18h]
  mov r9,[rbp+20h]
  mov r10,[rbp+28h]
  mov r11,[rbp+30h]
  ; At POPFQ, ordinary unwind must recover RSP from frame-RBP. At POP RBP and
  ; JMP the standard epilogue is recognizable. This exact boundary behavior is
  ; a required future RtlVirtualUnwind cold, not a claim made by Python tests.
  lea rsp,[rbp+40h]
  popfq
  pop rbp
  jmp qword ptr [XarParentEntryOriginalPrefixTarget12004]
XarParentEntryThunk12004 ENDP

XarParentEntryOriginalPrefix12004 PROC FRAME
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
  ; Exact original first16B must be checked after assembly. No dynamic allocated
  ; trampoline and no return-address substitution. Body executes exactly once.
  jmp qword ptr [XarParentEntryContinuation12004]
XarParentEntryOriginalPrefix12004 ENDP
END
