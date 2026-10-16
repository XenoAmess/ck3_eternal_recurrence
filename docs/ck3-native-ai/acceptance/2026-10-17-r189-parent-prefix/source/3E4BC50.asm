; machine_id=desktop-3fevhd2-1c74096080; observed_at=2026-10-16T19:38:11.161688+00:00; EXE_sha256=98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518; exact complete extent reviewed separately
3E4BC50 4c89442418 mov qword ptr [rsp + 0x18], r8
3E4BC55 4889542410 mov qword ptr [rsp + 0x10], rdx
3E4BC5A 48894c2408 mov qword ptr [rsp + 8], rcx
3E4BC5F 53 push rbx
3E4BC60 56 push rsi
3E4BC61 57 push rdi
3E4BC62 4156 push r14
3E4BC64 4157 push r15
3E4BC66 4881ec80000000 sub rsp, 0x80
3E4BC6D 4863b18c000000 movsxd rsi, dword ptr [rcx + 0x8c]
3E4BC74 488bda mov rbx, rdx
3E4BC77 4c8bf9 mov r15, rcx
3E4BC7A 4885f6 test rsi, rsi
3E4BC7D 7e61 jle 0x3e4bce0
3E4BC7F 4533f6 xor r14d, r14d
3E4BC82 0f1f4000 nop dword ptr [rax]
3E4BC86 66660f1f840000000000 nop word ptr [rax + rax]
3E4BC90 498b9780000000 mov rdx, qword ptr [r15 + 0x80]
3E4BC97 4903d6 add rdx, r14
3E4BC9A 8b4228 mov eax, dword ptr [rdx + 0x28]
3E4BC9D 488b1a mov rbx, qword ptr [rdx]
3E4BCA0 4883c208 add rdx, 8
3E4BCA4 488d0c80 lea rcx, [rax + rax*4]
3E4BCA8 498b00 mov rax, qword ptr [r8]
3E4BCAB 488d3cc8 lea rdi, [rax + rcx*8]
3E4BCAF 488b03 mov rax, qword ptr [rbx]
3E4BCB2 488bcb mov rcx, rbx
3E4BCB5 ff5028 call qword ptr [rax + 0x28]
3E4BCB8 4c8bc3 mov r8, rbx
3E4BCBB 488bcf mov rcx, rdi
3E4BCBE 488bd0 mov rdx, rax
3E4BCC1 e8cad6a2fc call 0x879390
3E4BCC6 4c8b8424c0000000 mov r8, qword ptr [rsp + 0xc0]
3E4BCCE 4983c630 add r14, 0x30
3E4BCD2 4883ee01 sub rsi, 1
3E4BCD6 75b8 jne 0x3e4bc90
3E4BCD8 488b9c24b8000000 mov rbx, qword ptr [rsp + 0xb8]
3E4BCE0 41837f0c00 cmp dword ptr [r15 + 0xc], 0
3E4BCE5 48896c2478 mov qword ptr [rsp + 0x78], rbp
3E4BCEA 4c89642470 mov qword ptr [rsp + 0x70], r12
3E4BCEF 4c896c2468 mov qword ptr [rsp + 0x68], r13
3E4BCF4 0f8492010000 je 0x3e4be8c
3E4BCFA e8c10fa3fc call 0x87ccc0
3E4BCFF 4963470c movsxd rax, dword ptr [r15 + 0xc]
3E4BD03 4889442420 mov qword ptr [rsp + 0x20], rax
3E4BD08 4885c0 test rax, rax
3E4BD0B 0f8e7b010000 jle 0x3e4be8c
3E4BD11 488bb424c0000000 mov rsi, qword ptr [rsp + 0xc0]
3E4BD19 4533e4 xor r12d, r12d
3E4BD1C 4533ed xor r13d, r13d
3E4BD1F 90 nop 
3E4BD20 498b87b0000000 mov rax, qword ptr [r15 + 0xb0]
3E4BD27 4d8b37 mov r14, qword ptr [r15]
3E4BD2A 4d03f5 add r14, r13
3E4BD2D 4a630ca0 movsxd rcx, dword ptr [rax + r12*4]
3E4BD31 410fb65634 movzx edx, byte ptr [r14 + 0x34]
3E4BD36 83f9ff cmp ecx, -1
3E4BD39 741e je 0x3e4bd59
3E4BD3B 3b4b0c cmp ecx, dword ptr [rbx + 0xc]
3E4BD3E 7d19 jge 0x3e4bd59
3E4BD40 488bc1 mov rax, rcx
3E4BD43 48c1e004 shl rax, 4
3E4BD47 480303 add rax, qword ptr [rbx]
3E4BD4A 84d2 test dl, dl
3E4BD4C 400f95c5 setne bpl
3E4BD50 488b18 mov rbx, qword ptr [rax]
3E4BD53 4883c008 add rax, 8
3E4BD57 eb0d jmp 0x3e4bd66
3E4BD59 84d2 test dl, dl
3E4BD5B 400f95c5 setne bpl
3E4BD5F 33db xor ebx, ebx
3E4BD61 e85a0fa3fc call 0x87ccc0
3E4BD66 8b38 mov edi, dword ptr [rax]
3E4BD68 418b4638 mov eax, dword ptr [r14 + 0x38]
3E4BD6C 488d0c80 lea rcx, [rax + rax*4]
3E4BD70 488b06 mov rax, qword ptr [rsi]
3E4BD73 488d04c8 lea rax, [rax + rcx*8]
3E4BD77 48898424c8000000 mov qword ptr [rsp + 0xc8], rax
3E4BD7F e83c0fa3fc call 0x87ccc0
3E4BD84 418b4e30 mov ecx, dword ptr [r14 + 0x30]
3E4BD88 3b08 cmp ecx, dword ptr [rax]
3E4BD8A 7411 je 0x3e4bd9d
3E4BD8C 3bcf cmp ecx, edi
3E4BD8E 0f85f4000000 jne 0x3e4be88
3E4BD94 4885db test rbx, rbx
3E4BD97 0f84eb000000 je 0x3e4be88
3E4BD9D 4d637e0c movsxd r15, dword ptr [r14 + 0xc]
3E4BDA1 33ff xor edi, edi
3E4BDA3 4889742428 mov qword ptr [rsp + 0x28], rsi
3E4BDA8 c744243000000000 mov dword ptr [rsp + 0x30], 0
3E4BDB0 48c744243800000000 mov qword ptr [rsp + 0x38], 0
3E4BDB9 4d85ff test r15, r15
3E4BDBC 7e5e jle 0x3e4be1c
3E4BDBE 33f6 xor esi, esi
3E4BDC0 498b0e mov rcx, qword ptr [r14]
3E4BDC3 488d542428 lea rdx, [rsp + 0x28]
3E4BDC8 4803ce add rcx, rsi
3E4BDCB 8b01 mov eax, dword ptr [rcx]
3E4BDCD 89442430 mov dword ptr [rsp + 0x30], eax
3E4BDD1 488b4110 mov rax, qword ptr [rcx + 0x10]
3E4BDD5 4889442438 mov qword ptr [rsp + 0x38], rax
3E4BDDA 83790402 cmp dword ptr [rcx + 4], 2
3E4BDDE 488b4108 mov rax, qword ptr [rcx + 8]
3E4BDE2 750a jne 0x3e4bdee
3E4BDE4 488bcb mov rcx, rbx
3E4BDE7 ffd0 call rax
3E4BDE9 40b501 mov bpl, 1
3E4BDEC eb0e jmp 0x3e4bdfc
3E4BDEE 33c9 xor ecx, ecx
3E4BDF0 4084ed test bpl, bpl
3E4BDF3 480f44cb cmove rcx, rbx
3E4BDF7 ffd0 call rax
3E4BDF9 4032ed xor bpl, bpl
3E4BDFC 488bd8 mov rbx, rax
3E4BDFF 4885c0 test rax, rax
3E4BE02 0f8480000000 je 0x3e4be88
3E4BE08 48ffc7 inc rdi
3E4BE0B 4883c618 add rsi, 0x18
3E4BE0F 493bff cmp rdi, r15
3E4BE12 7cac jl 0x3e4bdc0
3E4BE14 488bb424c0000000 mov rsi, qword ptr [rsp + 0xc0]
3E4BE1C 418b4618 mov eax, dword ptr [r14 + 0x18]
3E4BE20 89442448 mov dword ptr [rsp + 0x48], eax
3E4BE24 498b4628 mov rax, qword ptr [r14 + 0x28]
3E4BE28 4889442450 mov qword ptr [rsp + 0x50], rax
3E4BE2D 418b461c mov eax, dword ptr [r14 + 0x1c]
3E4BE31 4889742440 mov qword ptr [rsp + 0x40], rsi
3E4BE36 83f802 cmp eax, 2
3E4BE39 7505 jne 0x3e4be40
3E4BE3B 488bcb mov rcx, rbx
3E4BE3E eb0e jmp 0x3e4be4e
3E4BE40 83f801 cmp eax, 1
3E4BE43 7543 jne 0x3e4be88
3E4BE45 33c9 xor ecx, ecx
3E4BE47 4084ed test bpl, bpl
3E4BE4A 480f44cb cmove rcx, rbx
3E4BE4E 488b9424c8000000 mov rdx, qword ptr [rsp + 0xc8]
3E4BE56 4c8d442440 lea r8, [rsp + 0x40]
3E4BE5B 498b4620 mov rax, qword ptr [r14 + 0x20]
3E4BE5F ffd0 call rax
3E4BE61 84c0 test al, al
3E4BE63 7423 je 0x3e4be88
3E4BE65 49ffc4 inc r12
3E4BE68 4983c540 add r13, 0x40
3E4BE6C 4c3b642420 cmp r12, qword ptr [rsp + 0x20]
3E4BE71 7d19 jge 0x3e4be8c
3E4BE73 4c8bbc24b0000000 mov r15, qword ptr [rsp + 0xb0]
3E4BE7B 488b9c24b8000000 mov rbx, qword ptr [rsp + 0xb8]
3E4BE83 e998feffff jmp 0x3e4bd20
3E4BE88 32c0 xor al, al
3E4BE8A eb02 jmp 0x3e4be8e
3E4BE8C b001 mov al, 1
3E4BE8E 4c8b6c2468 mov r13, qword ptr [rsp + 0x68]
3E4BE93 4c8b642470 mov r12, qword ptr [rsp + 0x70]
3E4BE98 488b6c2478 mov rbp, qword ptr [rsp + 0x78]
3E4BE9D 4881c480000000 add rsp, 0x80
3E4BEA4 415f pop r15
3E4BEA6 415e pop r14
3E4BEA8 5f pop rdi
3E4BEA9 5e pop rsi
3E4BEAA 5b pop rbx
3E4BEAB c3 ret 
