02C142B0  4c 89 44 24 18                               mov qword ptr [rsp + 0x18], r8
02C142B5  48 89 54 24 10                               mov qword ptr [rsp + 0x10], rdx
02C142BA  48 89 4c 24 08                               mov qword ptr [rsp + 8], rcx
02C142BF  55                                           push rbp
02C142C0  53                                           push rbx
02C142C1  56                                           push rsi
02C142C2  57                                           push rdi
02C142C3  41 54                                        push r12
02C142C5  41 55                                        push r13
02C142C7  41 56                                        push r14
02C142C9  41 57                                        push r15
02C142CB  48 8d ac 24 98 fd ff ff                      lea rbp, [rsp - 0x268]
02C142D3  48 81 ec 68 03 00 00                         sub rsp, 0x368
02C142DA  4d 8b e0                                     mov r12, r8
02C142DD  4c 8b fa                                     mov r15, rdx
02C142E0  4c 8b e9                                     mov r13, rcx
02C142E3  48 8b 82 c0 01 00 00                         mov rax, qword ptr [rdx + 0x1c0]
02C142EA  48 85 c0                                     test rax, rax
02C142ED  74 09                                        je 0x2c142f8
02C142EF  0f b6 b8 a9 04 00 00                         movzx edi, byte ptr [rax + 0x4a9]
02C142F6  eb 03                                        jmp 0x2c142fb
02C142F8  40 32 ff                                     xor dil, dil
02C142FB  40 88 bd c8 02 00 00                         mov byte ptr [rbp + 0x2c8], dil
02C14302  49 8b cf                                     mov rcx, r15
02C14305  e8 b6 f7 ca ff                               call 0x28c3ac0
02C1430A  4c 63 48 74                                  movsxd r9, dword ptr [rax + 0x74]
02C1430E  4c 8b 50 68                                  mov r10, qword ptr [rax + 0x68]
02C14312  4b 8d 1c 4a                                  lea rbx, [r10 + r9*2]
02C14316  4d 8b c2                                     mov r8, r10
02C14319  49 8b ca                                     mov rcx, r10
02C1431C  be ae 00 00 00                               mov esi, 0xae
02C14321  4d 85 c9                                     test r9, r9
02C14324  7e 2b                                        jle 0x2c14351
02C14326  66 66 0f 1f 84 00 00 00 00 00                nop word ptr [rax + rax]
02C14330  49 8b d1                                     mov rdx, r9
02C14333  48 d1 ea                                     shr rdx, 1
02C14336  4c 2b ca                                     sub r9, rdx
02C14339  4b 8d 0c 48                                  lea rcx, [r8 + r9*2]
02C1433D  4c 8b ca                                     mov r9, rdx
02C14340  66 41 39 34 50                               cmp word ptr [r8 + rdx*2], si
02C14345  4c 0f 42 c1                                  cmovb r8, rcx
02C14349  49 8b c8                                     mov rcx, r8
02C1434C  48 85 d2                                     test rdx, rdx
02C1434F  75 df                                        jne 0x2c14330
02C14351  45 33 f6                                     xor r14d, r14d
02C14354  48 3b cb                                     cmp rcx, rbx
02C14357  74 1f                                        je 0x2c14378
02C14359  66 3b 31                                     cmp si, word ptr [rcx]
02C1435C  72 1a                                        jb 0x2c14378
02C1435E  49 2b ca                                     sub rcx, r10
02C14361  48 d1 f9                                     sar rcx, 1
02C14364  85 c9                                        test ecx, ecx
02C14366  78 10                                        js 0x2c14378
02C14368  48 63 c9                                     movsxd rcx, ecx
02C1436B  48 8b 80 d0 00 00 00                         mov rax, qword ptr [rax + 0xd0]
02C14372  48 8b 34 c8                                  mov rsi, qword ptr [rax + rcx*8]
02C14376  eb 03                                        jmp 0x2c1437b
02C14378  49 8b f6                                     mov rsi, r14
02C1437B  48 81 c6 a0 86 01 00                         add rsi, 0x186a0
02C14382  49 0f 48 f6                                  cmovs rsi, r14
02C14386  0f 57 c0                                     xorps xmm0, xmm0
02C14389  0f 11 44 24 50                               movups xmmword ptr [rsp + 0x50], xmm0
02C1438E  0f 11 44 24 60                               movups xmmword ptr [rsp + 0x60], xmm0
02C14393  0f 11 44 24 70                               movups xmmword ptr [rsp + 0x70], xmm0
02C14398  0f 11 45 80                                  movups xmmword ptr [rbp - 0x80], xmm0
02C1439C  0f 11 45 90                                  movups xmmword ptr [rbp - 0x70], xmm0
02C143A0  0f 11 45 a0                                  movups xmmword ptr [rbp - 0x60], xmm0
02C143A4  0f 11 45 b0                                  movups xmmword ptr [rbp - 0x50], xmm0
02C143A8  0f 11 45 c0                                  movups xmmword ptr [rbp - 0x40], xmm0
02C143AC  0f 11 45 d0                                  movups xmmword ptr [rbp - 0x30], xmm0
02C143B0  0f 11 45 e0                                  movups xmmword ptr [rbp - 0x20], xmm0
02C143B4  40 88 7c 24 30                               mov byte ptr [rsp + 0x30], dil
02C143B9  48 89 74 24 38                               mov qword ptr [rsp + 0x38], rsi
02C143BE  48 8d 44 24 50                               lea rax, [rsp + 0x50]
02C143C3  48 89 44 24 40                               mov qword ptr [rsp + 0x40], rax
02C143C8  48 8d 45 a0                                  lea rax, [rbp - 0x60]
02C143CC  48 89 44 24 48                               mov qword ptr [rsp + 0x48], rax
02C143D1  49 8b 87 c0 01 00 00                         mov rax, qword ptr [r15 + 0x1c0]
02C143D8  48 85 c0                                     test rax, rax
02C143DB  74 08                                        je 0x2c143e5
02C143DD  48 05 08 01 00 00                            add rax, 0x108
02C143E3  eb 05                                        jmp 0x2c143ea
02C143E5  e8 46 33 cc ff                               call 0x28d7730
02C143EA  48 8b 18                                     mov rbx, qword ptr [rax]
02C143ED  48 63 40 0c                                  movsxd rax, dword ptr [rax + 0xc]
02C143F1  48 8d 3c 83                                  lea rdi, [rbx + rax*4]
02C143F5  48 3b df                                     cmp rbx, rdi
02C143F8  74 54                                        je 0x2c1444e
02C143FA  66 0f 1f 44 00 00                            nop word ptr [rax + rax]
02C14400  8b 03                                        mov eax, dword ptr [rbx]
02C14402  4c 8b 05 5f a7 10 03                         mov r8, qword ptr [rip + 0x310a75f]
02C14409  4d 85 c0                                     test r8, r8
02C1440C  74 26                                        je 0x2c14434
02C1440E  8b c8                                        mov ecx, eax
02C14410  81 e1 ff ff ff 00                            and ecx, 0xffffff
02C14416  41 3b 48 2c                                  cmp ecx, dword ptr [r8 + 0x2c]
02C1441A  73 18                                        jae 0x2c14434
02C1441C  8b d1                                        mov edx, ecx
02C1441E  48 03 d2                                     add rdx, rdx
02C14421  49 8b 48 20                                  mov rcx, qword ptr [r8 + 0x20]
02C14425  48 8b 54 d1 08                               mov rdx, qword ptr [rcx + rdx*8 + 8]
02C1442A  48 85 d2                                     test rdx, rdx
02C1442D  74 05                                        je 0x2c14434
02C1442F  39 42 10                                     cmp dword ptr [rdx + 0x10], eax
02C14432  74 07                                        je 0x2c1443b
02C14434  48 8b 15 1d a7 10 03                         mov rdx, qword ptr [rip + 0x310a71d]
02C1443B  48 8d 4c 24 30                               lea rcx, [rsp + 0x30]
02C14440  e8 2b 09 00 00                               call 0x2c14d70
02C14445  48 83 c3 04                                  add rbx, 4
02C14449  48 3b df                                     cmp rbx, rdi
02C1444C  75 b2                                        jne 0x2c14400
02C1444E  49 8b cf                                     mov rcx, r15
02C14451  e8 9a e9 ca ff                               call 0x28c2df0
02C14456  80 b8 d6 04 00 00 05                         cmp byte ptr [rax + 0x4d6], 5
02C1445D  0f 85 ef 03 00 00                            jne 0x2c14852
02C14463  49 8b 87 c0 01 00 00                         mov rax, qword ptr [r15 + 0x1c0]
02C1446A  48 85 c0                                     test rax, rax
02C1446D  74 08                                        je 0x2c14477
02C1446F  48 05 e0 01 00 00                            add rax, 0x1e0
02C14475  eb 07                                        jmp 0x2c1447e
02C14477  48 8d 05 0a 58 84 02                         lea rax, [rip + 0x284580a]
02C1447E  48 8b 38                                     mov rdi, qword ptr [rax]
02C14481  48 63 40 0c                                  movsxd rax, dword ptr [rax + 0xc]
02C14485  4c 8d 3c 87                                  lea r15, [rdi + rax*4]
02C14489  4c 89 7c 24 30                               mov qword ptr [rsp + 0x30], r15
02C1448E  49 3b ff                                     cmp rdi, r15
02C14491  0f 84 b4 03 00 00                            je 0x2c1484b
02C14497  4c 8b 05 5a 96 10 03                         mov r8, qword ptr [rip + 0x310965a]
02C1449E  4c 8b 0d 3b 96 10 03                         mov r9, qword ptr [rip + 0x310963b]
02C144A5  44 0f b6 b5 c8 02 00 00                      movzx r14d, byte ptr [rbp + 0x2c8]
02C144AD  0f 1f 00                                     nop dword ptr [rax]
02C144B0  8b 07                                        mov eax, dword ptr [rdi]
02C144B2  4d 85 c0                                     test r8, r8
02C144B5  74 26                                        je 0x2c144dd
02C144B7  8b c8                                        mov ecx, eax
02C144B9  81 e1 ff ff ff 00                            and ecx, 0xffffff
02C144BF  41 3b 48 2c                                  cmp ecx, dword ptr [r8 + 0x2c]
02C144C3  73 18                                        jae 0x2c144dd
02C144C5  8b d1                                        mov edx, ecx
02C144C7  48 03 d2                                     add rdx, rdx
02C144CA  49 8b 48 20                                  mov rcx, qword ptr [r8 + 0x20]
02C144CE  48 8b 4c d1 08                               mov rcx, qword ptr [rcx + rdx*8 + 8]
02C144D3  48 85 c9                                     test rcx, rcx
02C144D6  74 05                                        je 0x2c144dd
02C144D8  39 41 10                                     cmp dword ptr [rcx + 0x10], eax
02C144DB  74 03                                        je 0x2c144e0
02C144DD  49 8b c9                                     mov rcx, r9
02C144E0  48 8b 99 d8 02 00 00                         mov rbx, qword ptr [rcx + 0x2d8]
02C144E7  48 63 81 e4 02 00 00                         movsxd rax, dword ptr [rcx + 0x2e4]
02C144EE  4c 8d 24 83                                  lea r12, [rbx + rax*4]
02C144F2  49 3b dc                                     cmp rbx, r12
02C144F5  0f 84 32 03 00 00                            je 0x2c1482d
02C144FB  49 bf 09 e1 d1 c6 11 6b f1 29                movabs r15, 0x29f16b11c6d1e109
02C14505  66 66 66 0f 1f 84 00 00 00 00 00             nop word ptr [rax + rax]
02C14510  8b 03                                        mov eax, dword ptr [rbx]
02C14512  48 83 3d 4e a6 10 03 00                      cmp qword ptr [rip + 0x310a64e], 0
02C1451A  74 2e                                        je 0x2c1454a
02C1451C  4c 8b 05 45 a6 10 03                         mov r8, qword ptr [rip + 0x310a645]
02C14523  8b c8                                        mov ecx, eax
02C14525  81 e1 ff ff ff 00                            and ecx, 0xffffff
02C1452B  41 3b 48 2c                                  cmp ecx, dword ptr [r8 + 0x2c]
02C1452F  73 19                                        jae 0x2c1454a
02C14531  8b d1                                        mov edx, ecx
02C14533  48 03 d2                                     add rdx, rdx
02C14536  49 8b 48 20                                  mov rcx, qword ptr [r8 + 0x20]
02C1453A  4c 8b 6c d1 08                               mov r13, qword ptr [rcx + rdx*8 + 8]
02C1453F  4d 85 ed                                     test r13, r13
02C14542  74 06                                        je 0x2c1454a
02C14544  41 39 45 10                                  cmp dword ptr [r13 + 0x10], eax
02C14548  74 07                                        je 0x2c14551
02C1454A  4c 8b 2d 07 a6 10 03                         mov r13, qword ptr [rip + 0x310a607]
02C14551  41 83 7d 28 ff                               cmp dword ptr [r13 + 0x28], -1
02C14556  0f 85 8b 01 00 00                            jne 0x2c146e7
02C1455C  45 84 f6                                     test r14b, r14b
02C1455F  0f 84 13 01 00 00                            je 0x2c14678
02C14565  45 8b 9d 28 01 00 00                         mov r11d, dword ptr [r13 + 0x128]
02C1456C  45 8b c3                                     mov r8d, r11d
02C1456F  4d 8d 55 18                                  lea r10, [r13 + 0x18]
02C14573  4d 8d 8a fc 00 00 00                         lea r9, [r10 + 0xfc]
02C1457A  4d 3b d1                                     cmp r10, r9
02C1457D  0f 84 f5 00 00 00                            je 0x2c14678
02C14583  49 8d 42 04                                  lea rax, [r10 + 4]
02C14587  8b 50 fc                                     mov edx, dword ptr [rax - 4]
02C1458A  85 d2                                        test edx, edx
02C1458C  74 14                                        je 0x2c145a2
02C1458E  83 78 14 03                                  cmp dword ptr [rax + 0x14], 3
02C14592  75 07                                        jne 0x2c1459b
02C14594  83 38 00                                     cmp dword ptr [rax], 0
02C14597  8b ca                                        mov ecx, edx
02C14599  74 02                                        je 0x2c1459d
02C1459B  8b 08                                        mov ecx, dword ptr [rax]
02C1459D  2b ca                                        sub ecx, edx
02C1459F  44 03 c1                                     add r8d, ecx
02C145A2  48 83 c0 24                                  add rax, 0x24
02C145A6  48 8d 48 fc                                  lea rcx, [rax - 4]
02C145AA  49 3b c9                                     cmp rcx, r9
02C145AD  75 d8                                        jne 0x2c14587
02C145AF  45 3b c3                                     cmp r8d, r11d
02C145B2  0f 84 c0 00 00 00                            je 0x2c14678
02C145B8  49 8b d2                                     mov rdx, r10
02C145BB  49 8b cd                                     mov rcx, r13
02C145BE  e8 1d 81 a1 ff                               call 0x262c6e0
02C145C3  84 c0                                        test al, al
02C145C5  0f 84 ad 00 00 00                            je 0x2c14678
02C145CB  41 b1 01                                     mov r9b, 1
02C145CE  45 33 c0                                     xor r8d, r8d
02C145D1  48 8d 55 f0                                  lea rdx, [rbp - 0x10]
02C145D5  49 8b cd                                     mov rcx, r13
02C145D8  e8 33 78 a1 ff                               call 0x262be10
02C145DD  48 8b 55 f0                                  mov rdx, qword ptr [rbp - 0x10]
02C145E1  41 ba 33 f3 04 b5                            mov r10d, 0xb504f333
02C145E7  4a 8d 04 12                                  lea rax, [rdx + r10]
02C145EB  49 bb 66 e6 09 6a 01 00 00 00                movabs r11, 0x16a09e666
02C145F5  49 3b c3                                     cmp rax, r11
02C145F8  77 27                                        ja 0x2c14621
02C145FA  4a 8d 04 16                                  lea rax, [rsi + r10]
02C145FE  49 3b c3                                     cmp rax, r11
02C14601  77 1e                                        ja 0x2c14621
02C14603  48 0f af d6                                  imul rdx, rsi
02C14607  49 8b c7                                     mov rax, r15
02C1460A  48 f7 ea                                     imul rdx
02C1460D  48 c1 fa 0e                                  sar rdx, 0xe
02C14611  48 8b c2                                     mov rax, rdx
02C14614  48 c1 e8 3f                                  shr rax, 0x3f
02C14618  48 03 d0                                     add rdx, rax
02C1461B  48 89 55 f0                                  mov qword ptr [rbp - 0x10], rdx
02C1461F  eb 6f                                        jmp 0x2c14690
02C14621  4c 8b ce                                     mov r9, rsi
02C14624  48 3b f2                                     cmp rsi, rdx
02C14627  4c 0f 4c ca                                  cmovl r9, rdx
02C1462B  48 8b ce                                     mov rcx, rsi
02C1462E  48 0f 4f ca                                  cmovg rcx, rdx
02C14632  49 8b c7                                     mov rax, r15
02C14635  49 f7 e9                                     imul r9
02C14638  4c 8b c2                                     mov r8, rdx
02C1463B  49 c1 f8 0e                                  sar r8, 0xe
02C1463F  49 8b c0                                     mov rax, r8
02C14642  48 c1 e8 3f                                  shr rax, 0x3f
02C14646  4c 03 c0                                     add r8, rax
02C14649  49 69 c0 a0 86 01 00                         imul rax, r8, 0x186a0
02C14650  4c 2b c8                                     sub r9, rax
02C14653  4c 0f af c9                                  imul r9, rcx
02C14657  4c 0f af c1                                  imul r8, rcx
02C1465B  49 8b c7                                     mov rax, r15
02C1465E  49 f7 e9                                     imul r9
02C14661  48 c1 fa 0e                                  sar rdx, 0xe
02C14665  48 8b c2                                     mov rax, rdx
02C14668  48 c1 e8 3f                                  shr rax, 0x3f
02C1466C  48 03 d0                                     add rdx, rax
02C1466F  49 03 d0                                     add rdx, r8
02C14672  48 89 55 f0                                  mov qword ptr [rbp - 0x10], rdx
02C14676  eb 18                                        jmp 0x2c14690
02C14678  41 b1 01                                     mov r9b, 1
02C1467B  45 33 c0                                     xor r8d, r8d
02C1467E  48 8d 55 f0                                  lea rdx, [rbp - 0x10]
02C14682  49 8b cd                                     mov rcx, r13
02C14685  e8 86 77 a1 ff                               call 0x262be10
02C1468A  48 8b 55 f0                                  mov rdx, qword ptr [rbp - 0x10]
02C1468E  66 90                                        nop 
02C14690  48 01 54 24 50                               add qword ptr [rsp + 0x50], rdx
02C14695  48 8b 45 f8                                  mov rax, qword ptr [rbp - 8]
02C14699  48 01 44 24 58                               add qword ptr [rsp + 0x58], rax
02C1469E  48 8b 45 00                                  mov rax, qword ptr [rbp]
02C146A2  48 01 44 24 60                               add qword ptr [rsp + 0x60], rax
02C146A7  48 8b 45 08                                  mov rax, qword ptr [rbp + 8]
02C146AB  48 01 44 24 68                               add qword ptr [rsp + 0x68], rax
02C146B0  48 8b 45 10                                  mov rax, qword ptr [rbp + 0x10]
02C146B4  48 01 44 24 70                               add qword ptr [rsp + 0x70], rax
02C146B9  48 8b 45 18                                  mov rax, qword ptr [rbp + 0x18]
02C146BD  48 01 44 24 78                               add qword ptr [rsp + 0x78], rax
02C146C2  48 8b 45 20                                  mov rax, qword ptr [rbp + 0x20]
02C146C6  48 01 45 80                                  add qword ptr [rbp - 0x80], rax
02C146CA  48 8b 45 28                                  mov rax, qword ptr [rbp + 0x28]
02C146CE  48 01 45 88                                  add qword ptr [rbp - 0x78], rax
02C146D2  48 8b 45 30                                  mov rax, qword ptr [rbp + 0x30]
02C146D6  48 01 45 90                                  add qword ptr [rbp - 0x70], rax
02C146DA  48 8b 45 38                                  mov rax, qword ptr [rbp + 0x38]
02C146DE  48 01 45 98                                  add qword ptr [rbp - 0x68], rax
02C146E2  e9 26 01 00 00                               jmp 0x2c1480d
02C146E7  41 8b 85 34 01 00 00                         mov eax, dword ptr [r13 + 0x134]
02C146EE  41 39 85 30 01 00 00                         cmp dword ptr [r13 + 0x130], eax
02C146F5  0f 84 12 01 00 00                            je 0x2c1480d
02C146FB  45 33 c9                                     xor r9d, r9d
02C146FE  41 b0 01                                     mov r8b, 1
02C14701  48 8d 55 60                                  lea rdx, [rbp + 0x60]
02C14705  49 8b cd                                     mov rcx, r13
02C14708  e8 03 77 a1 ff                               call 0x262be10
02C1470D  48 8b 55 60                                  mov rdx, qword ptr [rbp + 0x60]
02C14711  41 ba 33 f3 04 b5                            mov r10d, 0xb504f333
02C14717  4a 8d 04 12                                  lea rax, [rdx + r10]
02C1471B  49 bb 66 e6 09 6a 01 00 00 00                movabs r11, 0x16a09e666
02C14725  49 3b c3                                     cmp rax, r11
02C14728  77 23                                        ja 0x2c1474d
02C1472A  4a 8d 04 16                                  lea rax, [rsi + r10]
02C1472E  49 3b c3                                     cmp rax, r11
02C14731  77 1a                                        ja 0x2c1474d
02C14733  48 0f af d6                                  imul rdx, rsi
02C14737  49 8b c7                                     mov rax, r15
02C1473A  48 f7 ea                                     imul rdx
02C1473D  48 c1 fa 0e                                  sar rdx, 0xe
02C14741  48 8b c2                                     mov rax, rdx
02C14744  48 c1 e8 3f                                  shr rax, 0x3f
02C14748  48 03 d0                                     add rdx, rax
02C1474B  eb 5e                                        jmp 0x2c147ab
02C1474D  4c 8b ce                                     mov r9, rsi
02C14750  48 3b f2                                     cmp rsi, rdx
02C14753  4c 0f 4c ca                                  cmovl r9, rdx
02C14757  48 8b ce                                     mov rcx, rsi
02C1475A  48 0f 4f ca                                  cmovg rcx, rdx
02C1475E  49 ba 09 e1 d1 c6 11 6b f1 29                movabs r10, 0x29f16b11c6d1e109
02C14768  49 8b c2                                     mov rax, r10
02C1476B  49 f7 e9                                     imul r9
02C1476E  4c 8b c2                                     mov r8, rdx
02C14771  49 c1 f8 0e                                  sar r8, 0xe
02C14775  49 8b c0                                     mov rax, r8
02C14778  48 c1 e8 3f                                  shr rax, 0x3f
02C1477C  4c 03 c0                                     add r8, rax
02C1477F  49 69 c0 a0 86 01 00                         imul rax, r8, 0x186a0
02C14786  4c 2b c8                                     sub r9, rax
02C14789  4c 0f af c9                                  imul r9, rcx
02C1478D  4c 0f af c1                                  imul r8, rcx
02C14791  49 8b c2                                     mov rax, r10
02C14794  49 f7 e9                                     imul r9
02C14797  48 c1 fa 0e                                  sar rdx, 0xe
02C1479B  48 8b c2                                     mov rax, rdx
02C1479E  48 c1 e8 3f                                  shr rax, 0x3f
02C147A2  48 03 d0                                     add rdx, rax
02C147A5  49 03 d0                                     add rdx, r8
02C147A8  4d 8b fa                                     mov r15, r10
02C147AB  48 89 55 60                                  mov qword ptr [rbp + 0x60], rdx
02C147AF  48 01 55 a0                                  add qword ptr [rbp - 0x60], rdx
02C147B3  48 8b 45 68                                  mov rax, qword ptr [rbp + 0x68]
02C147B7  48 01 45 a8                                  add qword ptr [rbp - 0x58], rax
02C147BB  48 8b 45 70                                  mov rax, qword ptr [rbp + 0x70]
02C147BF  48 01 45 b0                                  add qword ptr [rbp - 0x50], rax
02C147C3  48 8b 45 78                                  mov rax, qword ptr [rbp + 0x78]
02C147C7  48 01 45 b8                                  add qword ptr [rbp - 0x48], rax
02C147CB  48 8b 85 80 00 00 00                         mov rax, qword ptr [rbp + 0x80]
02C147D2  48 01 45 c0                                  add qword ptr [rbp - 0x40], rax
02C147D6  48 8b 85 88 00 00 00                         mov rax, qword ptr [rbp + 0x88]
02C147DD  48 01 45 c8                                  add qword ptr [rbp - 0x38], rax
02C147E1  48 8b 85 90 00 00 00                         mov rax, qword ptr [rbp + 0x90]
02C147E8  48 01 45 d0                                  add qword ptr [rbp - 0x30], rax
02C147EC  48 8b 85 98 00 00 00                         mov rax, qword ptr [rbp + 0x98]
02C147F3  48 01 45 d8                                  add qword ptr [rbp - 0x28], rax
02C147F7  48 8b 85 a0 00 00 00                         mov rax, qword ptr [rbp + 0xa0]
02C147FE  48 01 45 e0                                  add qword ptr [rbp - 0x20], rax
02C14802  48 8b 85 a8 00 00 00                         mov rax, qword ptr [rbp + 0xa8]
02C14809  48 01 45 e8                                  add qword ptr [rbp - 0x18], rax
02C1480D  48 83 c3 04                                  add rbx, 4
02C14811  49 3b dc                                     cmp rbx, r12
02C14814  0f 85 f6 fc ff ff                            jne 0x2c14510
02C1481A  4c 8b 05 d7 92 10 03                         mov r8, qword ptr [rip + 0x31092d7]
02C14821  4c 8b 0d b8 92 10 03                         mov r9, qword ptr [rip + 0x31092b8]
02C14828  4c 8b 7c 24 30                               mov r15, qword ptr [rsp + 0x30]
02C1482D  48 83 c7 04                                  add rdi, 4
02C14831  49 3b ff                                     cmp rdi, r15
02C14834  0f 85 76 fc ff ff                            jne 0x2c144b0
02C1483A  45 33 f6                                     xor r14d, r14d
02C1483D  4c 8b ad b0 02 00 00                         mov r13, qword ptr [rbp + 0x2b0]
02C14844  4c 8b a5 c0 02 00 00                         mov r12, qword ptr [rbp + 0x2c0]
02C1484B  4c 8b bd b8 02 00 00                         mov r15, qword ptr [rbp + 0x2b8]
02C14852  45 33 c0                                     xor r8d, r8d
02C14855  49 8b d7                                     mov rdx, r15
02C14858  48 8d 8d b0 02 00 00                         lea rcx, [rbp + 0x2b0]
02C1485F  e8 ac cc 4a 00                               call 0x30c1510
02C14864  0f 28 44 24 50                               movaps xmm0, xmmword ptr [rsp + 0x50]
02C14869  0f 29 45 60                                  movaps xmmword ptr [rbp + 0x60], xmm0
02C1486D  0f 28 4c 24 60                               movaps xmm1, xmmword ptr [rsp + 0x60]
02C14872  0f 29 4d 70                                  movaps xmmword ptr [rbp + 0x70], xmm1
02C14876  0f 28 44 24 70                               movaps xmm0, xmmword ptr [rsp + 0x70]
02C1487B  0f 29 85 80 00 00 00                         movaps xmmword ptr [rbp + 0x80], xmm0
02C14882  0f 28 4d 80                                  movaps xmm1, xmmword ptr [rbp - 0x80]
02C14886  0f 29 8d 90 00 00 00                         movaps xmmword ptr [rbp + 0x90], xmm1
02C1488D  0f 28 45 90                                  movaps xmm0, xmmword ptr [rbp - 0x70]
02C14891  0f 29 85 a0 00 00 00                         movaps xmmword ptr [rbp + 0xa0], xmm0
02C14898  48 8b bd b0 02 00 00                         mov rdi, qword ptr [rbp + 0x2b0]
02C1489F  48 8b d7                                     mov rdx, rdi
02C148A2  48 8d 4d 60                                  lea rcx, [rbp + 0x60]
02C148A6  e8 e5 0c ca fe                               call 0x18b5590
02C148AB  0f 28 45 a0                                  movaps xmm0, xmmword ptr [rbp - 0x60]
02C148AF  0f 29 45 f0                                  movaps xmmword ptr [rbp - 0x10], xmm0
02C148B3  0f 28 4d b0                                  movaps xmm1, xmmword ptr [rbp - 0x50]
02C148B7  0f 29 4d 00                                  movaps xmmword ptr [rbp], xmm1
02C148BB  0f 28 45 c0                                  movaps xmm0, xmmword ptr [rbp - 0x40]
02C148BF  0f 29 45 10                                  movaps xmmword ptr [rbp + 0x10], xmm0
02C148C3  0f 28 4d d0                                  movaps xmm1, xmmword ptr [rbp - 0x30]
02C148C7  0f 29 4d 20                                  movaps xmmword ptr [rbp + 0x20], xmm1
02C148CB  0f 28 45 e0                                  movaps xmm0, xmmword ptr [rbp - 0x20]
02C148CF  0f 29 45 30                                  movaps xmmword ptr [rbp + 0x30], xmm0
02C148D3  48 8b d7                                     mov rdx, rdi
02C148D6  48 8d 4d f0                                  lea rcx, [rbp - 0x10]
02C148DA  e8 b1 0c ca fe                               call 0x18b5590
02C148DF  4d 85 e4                                     test r12, r12
02C148E2  0f 84 ea 03 00 00                            je 0x2c14cd2
02C148E8  49 63 44 24 08                               movsxd rax, dword ptr [r12 + 8]
02C148ED  48 83 7c c4 50 00                            cmp qword ptr [rsp + rax*8 + 0x50], 0
02C148F3  0f 84 e6 01 00 00                            je 0x2c14adf
02C148F9  4d 8b 24 24                                  mov r12, qword ptr [r12]
02C148FD  48 8b 5c c5 60                               mov rbx, qword ptr [rbp + rax*8 + 0x60]
02C14902  48 f7 db                                     neg rbx
02C14905  48 8d 05 64 5b bf 01                         lea rax, [rip + 0x1bf5b64]
02C1490C  48 89 44 24 30                               mov qword ptr [rsp + 0x30], rax
02C14911  c7 44 24 38 1b 00 00 00                      mov dword ptr [rsp + 0x38], 0x1b
02C14919  c6 44 24 3c 00                               mov byte ptr [rsp + 0x3c], 0
02C1491E  33 d2                                        xor edx, edx
02C14920  41 b8 a8 01 00 00                            mov r8d, 0x1a8
02C14926  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C1492D  e8 de 25 61 01                               call 0x4226f10
02C14932  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14939  e8 a2 50 c7 fd                               call 0x8899e0
02C1493E  90                                           nop 
02C1493F  4c 89 74 24 28                               mov qword ptr [rsp + 0x28], r14
02C14944  48 8d 85 b0 00 00 00                         lea rax, [rbp + 0xb0]
02C1494B  48 89 44 24 20                               mov qword ptr [rsp + 0x20], rax
02C14950  45 33 c9                                     xor r9d, r9d
02C14953  45 33 c0                                     xor r8d, r8d
02C14956  48 8d 54 24 30                               lea rdx, [rsp + 0x30]
02C1495B  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C1495F  e8 bc 1c 20 01                               call 0x3e16620
02C14964  90                                           nop 
02C14965  48 8b b5 b0 00 00 00                         mov rsi, qword ptr [rbp + 0xb0]
02C1496C  48 85 f6                                     test rsi, rsi
02C1496F  74 5f                                        je 0x2c149d0
02C14971  44 8b bd bc 00 00 00                         mov r15d, dword ptr [rbp + 0xbc]
02C14978  45 85 ff                                     test r15d, r15d
02C1497B  7e 1e                                        jle 0x2c1499b
02C1497D  0f 1f 00                                     nop dword ptr [rax]
02C14980  48 8b ce                                     mov rcx, rsi
02C14983  e8 c8 16 c4 fd                               call 0x856050
02C14988  41 ff cf                                     dec r15d
02C1498B  48 83 c6 30                                  add rsi, 0x30
02C1498F  45 85 ff                                     test r15d, r15d
02C14992  7f ec                                        jg 0x2c14980
02C14994  48 8b b5 b0 00 00 00                         mov rsi, qword ptr [rbp + 0xb0]
02C1499B  44 89 b5 bc 00 00 00                         mov dword ptr [rbp + 0xbc], r14d
02C149A2  48 8b 8d c0 00 00 00                         mov rcx, qword ptr [rbp + 0xc0]
02C149A9  48 8b 01                                     mov rax, qword ptr [rcx]
02C149AC  41 b8 08 00 00 00                            mov r8d, 8
02C149B2  48 8b d6                                     mov rdx, rsi
02C149B5  ff 50 10                                     call qword ptr [rax + 0x10]
02C149B8  4c 89 b5 b0 00 00 00                         mov qword ptr [rbp + 0xb0], r14
02C149BF  44 89 b5 b8 00 00 00                         mov dword ptr [rbp + 0xb8], r14d
02C149C6  4c 8b bd b8 02 00 00                         mov r15, qword ptr [rbp + 0x2b8]
02C149CD  0f 1f 00                                     nop dword ptr [rax]
02C149D0  4c 8b c3                                     mov r8, rbx
02C149D3  48 8d 55 40                                  lea rdx, [rbp + 0x40]
02C149D7  49 8b cc                                     mov rcx, r12
02C149DA  e8 41 76 81 ff                               call 0x242c020
02C149DF  48 8b f0                                     mov rsi, rax
02C149E2  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C149E6  e8 65 16 c4 fd                               call 0x856050
02C149EB  4c 8b a5 c0 02 00 00                         mov r12, qword ptr [rbp + 0x2c0]
02C149F2  48 81 ff a0 86 01 00                         cmp rdi, 0x186a0
02C149F9  0f 84 e0 00 00 00                            je 0x2c14adf
02C149FF  49 63 4c 24 08                               movsxd rcx, dword ptr [r12 + 8]
02C14A04  48 8b 5c cc 50                               mov rbx, qword ptr [rsp + rcx*8 + 0x50]
02C14A09  48 f7 db                                     neg rbx
02C14A0C  48 8d 05 7d 5a bf 01                         lea rax, [rip + 0x1bf5a7d]
02C14A13  48 89 44 24 30                               mov qword ptr [rsp + 0x30], rax
02C14A18  c7 44 24 38 20 00 00 00                      mov dword ptr [rsp + 0x38], 0x20
02C14A20  c6 44 24 3c 00                               mov byte ptr [rsp + 0x3c], 0
02C14A25  33 d2                                        xor edx, edx
02C14A27  41 b8 a8 01 00 00                            mov r8d, 0x1a8
02C14A2D  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14A34  e8 d7 24 61 01                               call 0x4226f10
02C14A39  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14A40  e8 9b 4f c7 fd                               call 0x8899e0
02C14A45  90                                           nop 
02C14A46  4c 89 74 24 28                               mov qword ptr [rsp + 0x28], r14
02C14A4B  48 8d 85 b0 00 00 00                         lea rax, [rbp + 0xb0]
02C14A52  48 89 44 24 20                               mov qword ptr [rsp + 0x20], rax
02C14A57  45 33 c9                                     xor r9d, r9d
02C14A5A  45 33 c0                                     xor r8d, r8d
02C14A5D  48 8d 54 24 30                               lea rdx, [rsp + 0x30]
02C14A62  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C14A66  e8 b5 1b 20 01                               call 0x3e16620
02C14A6B  90                                           nop 
02C14A6C  48 83 bd b0 00 00 00 00                      cmp qword ptr [rbp + 0xb0], 0
02C14A74  74 34                                        je 0x2c14aaa
02C14A76  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14A7D  e8 4e 50 c7 fd                               call 0x889ad0
02C14A82  48 8b 8d c0 00 00 00                         mov rcx, qword ptr [rbp + 0xc0]
02C14A89  48 8b 01                                     mov rax, qword ptr [rcx]
02C14A8C  41 b8 08 00 00 00                            mov r8d, 8
02C14A92  48 8b 95 b0 00 00 00                         mov rdx, qword ptr [rbp + 0xb0]
02C14A99  ff 50 10                                     call qword ptr [rax + 0x10]
02C14A9C  4c 89 b5 b0 00 00 00                         mov qword ptr [rbp + 0xb0], r14
02C14AA3  44 89 b5 b8 00 00 00                         mov dword ptr [rbp + 0xb8], r14d
02C14AAA  4c 8b c3                                     mov r8, rbx
02C14AAD  48 8d 55 40                                  lea rdx, [rbp + 0x40]
02C14AB1  48 8b ce                                     mov rcx, rsi
02C14AB4  e8 67 75 81 ff                               call 0x242c020
02C14AB9  33 d2                                        xor edx, edx
02C14ABB  48 8b c8                                     mov rcx, rax
02C14ABE  e8 bd 67 81 ff                               call 0x242b280
02C14AC3  90                                           nop 
02C14AC4  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C14AC8  e8 83 15 c4 fd                               call 0x856050
02C14ACD  4c 8b c6                                     mov r8, rsi
02C14AD0  49 8b d7                                     mov rdx, r15
02C14AD3  48 8d 8d b0 02 00 00                         lea rcx, [rbp + 0x2b0]
02C14ADA  e8 31 ca 4a 00                               call 0x30c1510
02C14ADF  49 63 44 24 08                               movsxd rax, dword ptr [r12 + 8]
02C14AE4  48 83 7c c5 a0 00                            cmp qword ptr [rbp + rax*8 - 0x60], 0
02C14AEA  0f 84 e2 01 00 00                            je 0x2c14cd2
02C14AF0  4d 8b 24 24                                  mov r12, qword ptr [r12]
02C14AF4  48 8b 5c c5 f0                               mov rbx, qword ptr [rbp + rax*8 - 0x10]
02C14AF9  48 f7 db                                     neg rbx
02C14AFC  48 8d 05 b5 59 bf 01                         lea rax, [rip + 0x1bf59b5]
02C14B03  48 89 44 24 30                               mov qword ptr [rsp + 0x30], rax
02C14B08  c7 44 24 38 1f 00 00 00                      mov dword ptr [rsp + 0x38], 0x1f
02C14B10  c6 44 24 3c 00                               mov byte ptr [rsp + 0x3c], 0
02C14B15  33 d2                                        xor edx, edx
02C14B17  41 b8 a8 01 00 00                            mov r8d, 0x1a8
02C14B1D  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14B24  e8 e7 23 61 01                               call 0x4226f10
02C14B29  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14B30  e8 ab 4e c7 fd                               call 0x8899e0
02C14B35  90                                           nop 
02C14B36  4c 89 74 24 28                               mov qword ptr [rsp + 0x28], r14
02C14B3B  48 8d 85 b0 00 00 00                         lea rax, [rbp + 0xb0]
02C14B42  48 89 44 24 20                               mov qword ptr [rsp + 0x20], rax
02C14B47  45 33 c9                                     xor r9d, r9d
02C14B4A  45 33 c0                                     xor r8d, r8d
02C14B4D  48 8d 54 24 30                               lea rdx, [rsp + 0x30]
02C14B52  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C14B56  e8 c5 1a 20 01                               call 0x3e16620
02C14B5B  90                                           nop 
02C14B5C  48 8b b5 b0 00 00 00                         mov rsi, qword ptr [rbp + 0xb0]
02C14B63  48 85 f6                                     test rsi, rsi
02C14B66  74 58                                        je 0x2c14bc0
02C14B68  44 8b bd bc 00 00 00                         mov r15d, dword ptr [rbp + 0xbc]
02C14B6F  45 85 ff                                     test r15d, r15d
02C14B72  7e 1b                                        jle 0x2c14b8f
02C14B74  48 8b ce                                     mov rcx, rsi
02C14B77  e8 d4 14 c4 fd                               call 0x856050
02C14B7C  41 ff cf                                     dec r15d
02C14B7F  48 83 c6 30                                  add rsi, 0x30
02C14B83  45 85 ff                                     test r15d, r15d
02C14B86  7f ec                                        jg 0x2c14b74
02C14B88  48 8b b5 b0 00 00 00                         mov rsi, qword ptr [rbp + 0xb0]
02C14B8F  44 89 b5 bc 00 00 00                         mov dword ptr [rbp + 0xbc], r14d
02C14B96  48 8b 8d c0 00 00 00                         mov rcx, qword ptr [rbp + 0xc0]
02C14B9D  48 8b 01                                     mov rax, qword ptr [rcx]
02C14BA0  41 b8 08 00 00 00                            mov r8d, 8
02C14BA6  48 8b d6                                     mov rdx, rsi
02C14BA9  ff 50 10                                     call qword ptr [rax + 0x10]
02C14BAC  4c 89 b5 b0 00 00 00                         mov qword ptr [rbp + 0xb0], r14
02C14BB3  44 89 b5 b8 00 00 00                         mov dword ptr [rbp + 0xb8], r14d
02C14BBA  66 0f 1f 44 00 00                            nop word ptr [rax + rax]
02C14BC0  4c 8b c3                                     mov r8, rbx
02C14BC3  48 8d 55 40                                  lea rdx, [rbp + 0x40]
02C14BC7  49 8b cc                                     mov rcx, r12
02C14BCA  e8 51 74 81 ff                               call 0x242c020
02C14BCF  48 8b f0                                     mov rsi, rax
02C14BD2  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C14BD6  e8 75 14 c4 fd                               call 0x856050
02C14BDB  48 81 ff a0 86 01 00                         cmp rdi, 0x186a0
02C14BE2  0f 84 ea 00 00 00                            je 0x2c14cd2
02C14BE8  48 8b 85 c0 02 00 00                         mov rax, qword ptr [rbp + 0x2c0]
02C14BEF  48 63 48 08                                  movsxd rcx, dword ptr [rax + 8]
02C14BF3  48 8b 5c cd a0                               mov rbx, qword ptr [rbp + rcx*8 - 0x60]
02C14BF8  48 f7 db                                     neg rbx
02C14BFB  48 8d 05 d6 58 bf 01                         lea rax, [rip + 0x1bf58d6]
02C14C02  48 89 44 24 30                               mov qword ptr [rsp + 0x30], rax
02C14C07  c7 44 24 38 24 00 00 00                      mov dword ptr [rsp + 0x38], 0x24
02C14C0F  c6 44 24 3c 00                               mov byte ptr [rsp + 0x3c], 0
02C14C14  33 d2                                        xor edx, edx
02C14C16  41 b8 a8 01 00 00                            mov r8d, 0x1a8
02C14C1C  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14C23  e8 e8 22 61 01                               call 0x4226f10
02C14C28  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14C2F  e8 ac 4d c7 fd                               call 0x8899e0
02C14C34  90                                           nop 
02C14C35  4c 89 74 24 28                               mov qword ptr [rsp + 0x28], r14
02C14C3A  48 8d 85 b0 00 00 00                         lea rax, [rbp + 0xb0]
02C14C41  48 89 44 24 20                               mov qword ptr [rsp + 0x20], rax
02C14C46  45 33 c9                                     xor r9d, r9d
02C14C49  45 33 c0                                     xor r8d, r8d
02C14C4C  48 8d 54 24 30                               lea rdx, [rsp + 0x30]
02C14C51  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C14C55  e8 c6 19 20 01                               call 0x3e16620
02C14C5A  90                                           nop 
02C14C5B  48 83 bd b0 00 00 00 00                      cmp qword ptr [rbp + 0xb0], 0
02C14C63  74 34                                        je 0x2c14c99
02C14C65  48 8d 8d b0 00 00 00                         lea rcx, [rbp + 0xb0]
02C14C6C  e8 5f 4e c7 fd                               call 0x889ad0
02C14C71  48 8b 8d c0 00 00 00                         mov rcx, qword ptr [rbp + 0xc0]
02C14C78  48 8b 01                                     mov rax, qword ptr [rcx]
02C14C7B  41 b8 08 00 00 00                            mov r8d, 8
02C14C81  48 8b 95 b0 00 00 00                         mov rdx, qword ptr [rbp + 0xb0]
02C14C88  ff 50 10                                     call qword ptr [rax + 0x10]
02C14C8B  4c 89 b5 b0 00 00 00                         mov qword ptr [rbp + 0xb0], r14
02C14C92  44 89 b5 b8 00 00 00                         mov dword ptr [rbp + 0xb8], r14d
02C14C99  4c 8b c3                                     mov r8, rbx
02C14C9C  48 8d 55 40                                  lea rdx, [rbp + 0x40]
02C14CA0  48 8b ce                                     mov rcx, rsi
02C14CA3  e8 78 73 81 ff                               call 0x242c020
02C14CA8  33 d2                                        xor edx, edx
02C14CAA  48 8b c8                                     mov rcx, rax
02C14CAD  e8 ce 65 81 ff                               call 0x242b280
02C14CB2  90                                           nop 
02C14CB3  48 8d 4d 40                                  lea rcx, [rbp + 0x40]
02C14CB7  e8 94 13 c4 fd                               call 0x856050
02C14CBC  4c 8b c6                                     mov r8, rsi
02C14CBF  48 8b 95 b8 02 00 00                         mov rdx, qword ptr [rbp + 0x2b8]
02C14CC6  48 8d 8d c0 02 00 00                         lea rcx, [rbp + 0x2c0]
02C14CCD  e8 3e c8 4a 00                               call 0x30c1510
02C14CD2  0f 28 45 60                                  movaps xmm0, xmmword ptr [rbp + 0x60]
02C14CD6  41 0f 11 45 00                               movups xmmword ptr [r13], xmm0
02C14CDB  0f 28 4d 70                                  movaps xmm1, xmmword ptr [rbp + 0x70]
02C14CDF  41 0f 11 4d 10                               movups xmmword ptr [r13 + 0x10], xmm1
02C14CE4  0f 28 85 80 00 00 00                         movaps xmm0, xmmword ptr [rbp + 0x80]
02C14CEB  41 0f 11 45 20                               movups xmmword ptr [r13 + 0x20], xmm0
02C14CF0  0f 28 8d 90 00 00 00                         movaps xmm1, xmmword ptr [rbp + 0x90]
02C14CF7  41 0f 11 4d 30                               movups xmmword ptr [r13 + 0x30], xmm1
02C14CFC  0f 28 85 a0 00 00 00                         movaps xmm0, xmmword ptr [rbp + 0xa0]
02C14D03  41 0f 11 45 40                               movups xmmword ptr [r13 + 0x40], xmm0
02C14D08  48 8b 45 f0                                  mov rax, qword ptr [rbp - 0x10]
02C14D0C  49 01 45 00                                  add qword ptr [r13], rax
02C14D10  48 8b 45 f8                                  mov rax, qword ptr [rbp - 8]
02C14D14  49 01 45 08                                  add qword ptr [r13 + 8], rax
02C14D18  48 8b 45 00                                  mov rax, qword ptr [rbp]
02C14D1C  49 01 45 10                                  add qword ptr [r13 + 0x10], rax
02C14D20  48 8b 45 08                                  mov rax, qword ptr [rbp + 8]
02C14D24  49 01 45 18                                  add qword ptr [r13 + 0x18], rax
02C14D28  48 8b 45 10                                  mov rax, qword ptr [rbp + 0x10]
02C14D2C  49 01 45 20                                  add qword ptr [r13 + 0x20], rax
02C14D30  48 8b 45 18                                  mov rax, qword ptr [rbp + 0x18]
02C14D34  49 01 45 28                                  add qword ptr [r13 + 0x28], rax
02C14D38  48 8b 45 20                                  mov rax, qword ptr [rbp + 0x20]
02C14D3C  49 01 45 30                                  add qword ptr [r13 + 0x30], rax
02C14D40  48 8b 45 28                                  mov rax, qword ptr [rbp + 0x28]
02C14D44  49 01 45 38                                  add qword ptr [r13 + 0x38], rax
02C14D48  48 8b 45 30                                  mov rax, qword ptr [rbp + 0x30]
02C14D4C  49 01 45 40                                  add qword ptr [r13 + 0x40], rax
02C14D50  48 8b 45 38                                  mov rax, qword ptr [rbp + 0x38]
02C14D54  49 01 45 48                                  add qword ptr [r13 + 0x48], rax
02C14D58  49 8b c5                                     mov rax, r13
02C14D5B  48 81 c4 68 03 00 00                         add rsp, 0x368
02C14D62  41 5f                                        pop r15
02C14D64  41 5e                                        pop r14
02C14D66  41 5d                                        pop r13
02C14D68  41 5c                                        pop r12
02C14D6A  5f                                           pop rdi
02C14D6B  5e                                           pop rsi
02C14D6C  5b                                           pop rbx
02C14D6D  5d                                           pop rbp
02C14D6E  c3                                           ret 
