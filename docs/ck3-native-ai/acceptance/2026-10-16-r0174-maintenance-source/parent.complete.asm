028F7840  48 8b c4                         mov rax, rsp
028F7843  53                               push rbx
028F7844  55                               push rbp
028F7845  48 81 ec 98 00 00 00             sub rsp, 0x98
028F784C  4c 89 70 e0                      mov qword ptr [rax - 0x20], r14
028F7850  48 8b ea                         mov rbp, rdx
028F7853  48 8b 92 c0 01 00 00             mov rdx, qword ptr [rdx + 0x1c0]
028F785A  4c 8b f1                         mov r14, rcx
028F785D  4c 89 78 d8                      mov qword ptr [rax - 0x28], r15
028F7861  48 8b 41 08                      mov rax, qword ptr [rcx + 8]
028F7865  4d 63 c8                         movsxd r9, r8d
028F7868  4c 8b 00                         mov r8, qword ptr [rax]
028F786B  4f 8d 3c c8                      lea r15, [r8 + r9*8]
028F786F  48 85 d2                         test rdx, rdx
028F7872  0f 84 b9 00 00 00                je 0x28f7931
028F7878  33 c0                            xor eax, eax
028F787A  38 82 a3 00 00 00                cmp byte ptr [rdx + 0xa3], al
028F7880  74 10                            je 0x28f7892
028F7882  48 8b 0d c7 23 37 03             mov rcx, qword ptr [rip + 0x33723c7]
028F7889  48 01 8a e8 03 00 00             add qword ptr [rdx + 0x3e8], rcx
028F7890  eb 45                            jmp 0x28f78d7
028F7892  48 8b 8a e8 03 00 00             mov rcx, qword ptr [rdx + 0x3e8]
028F7899  48 85 c9                         test rcx, rcx
028F789C  7e 39                            jle 0x28f78d7
028F789E  48 2b 0d db 23 37 03             sub rcx, qword ptr [rip + 0x33723db]
028F78A5  48 89 8a e8 03 00 00             mov qword ptr [rdx + 0x3e8], rcx
028F78AC  48 8d 8c 24 b0 00 00 00          lea rcx, [rsp + 0xb0]
028F78B4  48 8b 95 c0 01 00 00             mov rdx, qword ptr [rbp + 0x1c0]
028F78BB  48 81 c2 e8 03 00 00             add rdx, 0x3e8
028F78C2  48 89 84 24 b0 00 00 00          mov qword ptr [rsp + 0xb0], rax
028F78CA  48 39 02                         cmp qword ptr [rdx], rax
028F78CD  48 0f 4d ca                      cmovge rcx, rdx
028F78D1  48 8b 09                         mov rcx, qword ptr [rcx]
028F78D4  48 89 0a                         mov qword ptr [rdx], rcx
028F78D7  48 8b 95 c0 01 00 00             mov rdx, qword ptr [rbp + 0x1c0]
028F78DE  38 82 a4 00 00 00                cmp byte ptr [rdx + 0xa4], al
028F78E4  74 3b                            je 0x28f7921
028F78E6  48 8b 0d 9b 23 37 03             mov rcx, qword ptr [rip + 0x337239b]
028F78ED  48 01 8a f0 03 00 00             add qword ptr [rdx + 0x3f0], rcx
028F78F4  4c 8b 85 c0 01 00 00             mov r8, qword ptr [rbp + 0x1c0]
028F78FB  48 8b 15 96 23 37 03             mov rdx, qword ptr [rip + 0x3372396]
028F7902  49 8b 88 f0 03 00 00             mov rcx, qword ptr [r8 + 0x3f0]
028F7909  48 85 c9                         test rcx, rcx
028F790C  78 0a                            js 0x28f7918
028F790E  48 3b ca                         cmp rcx, rdx
028F7911  48 8b c1                         mov rax, rcx
028F7914  48 0f 4f c2                      cmovg rax, rdx
028F7918  49 89 80 f0 03 00 00             mov qword ptr [r8 + 0x3f0], rax
028F791F  eb 10                            jmp 0x28f7931
028F7921  48 39 82 f0 03 00 00             cmp qword ptr [rdx + 0x3f0], rax
028F7928  7e 07                            jle 0x28f7931
028F792A  48 89 82 f0 03 00 00             mov qword ptr [rdx + 0x3f0], rax
028F7931  48 8b cd                         mov rcx, rbp
028F7934  e8 d7 f3 fa ff                   call 0x28a6d10
028F7939  48 8b 9d c0 01 00 00             mov rbx, qword ptr [rbp + 0x1c0]
028F7940  48 85 db                         test rbx, rbx
028F7943  0f 84 5d 01 00 00                je 0x28f7aa6
028F7949  48 89 b4 24 b8 00 00 00          mov qword ptr [rsp + 0xb8], rsi
028F7951  48 8b b3 e0 02 00 00             mov rsi, qword ptr [rbx + 0x2e0]
028F7958  48 89 bc 24 90 00 00 00          mov qword ptr [rsp + 0x90], rdi
028F7960  48 8b bb d0 02 00 00             mov rdi, qword ptr [rbx + 0x2d0]
028F7967  48 2b fe                         sub rdi, rsi
028F796A  0f 84 26 01 00 00                je 0x28f7a96
028F7970  48 85 ff                         test rdi, rdi
028F7973  0f 8e be 00 00 00                jle 0x28f7a37
028F7979  48 83 bd b0 01 00 00 00          cmp qword ptr [rbp + 0x1b0], 0
028F7981  0f 84 0f 01 00 00                je 0x28f7a96
028F7987  48 8b cd                         mov rcx, rbp
028F798A  e8 f1 83 2b 00                   call 0x2bafd80
028F798F  84 c0                            test al, al
028F7991  0f 84 ff 00 00 00                je 0x28f7a96
028F7997  48 8b 85 c0 01 00 00             mov rax, qword ptr [rbp + 0x1c0]
028F799E  48 85 c0                         test rax, rax
028F79A1  74 14                            je 0x28f79b7
028F79A3  83 b8 ec 01 00 00 00             cmp dword ptr [rax + 0x1ec], 0
028F79AA  74 25                            je 0x28f79d1
028F79AC  48 8b 80 e0 01 00 00             mov rax, qword ptr [rax + 0x1e0]
028F79B3  8b 08                            mov ecx, dword ptr [rax]
028F79B5  eb 1f                            jmp 0x28f79d6
028F79B7  48 8b 85 d0 01 00 00             mov rax, qword ptr [rbp + 0x1d0]
028F79BE  48 85 c0                         test rax, rax
028F79C1  74 0e                            je 0x28f79d1
028F79C3  83 78 74 00                      cmp dword ptr [rax + 0x74], 0
028F79C7  74 08                            je 0x28f79d1
028F79C9  48 8b 40 68                      mov rax, qword ptr [rax + 0x68]
028F79CD  8b 08                            mov ecx, dword ptr [rax]
028F79CF  eb 05                            jmp 0x28f79d6
028F79D1  b9 ff ff ff ff                   mov ecx, 0xffffffff
028F79D6  89 8c 24 c0 00 00 00             mov dword ptr [rsp + 0xc0], ecx
028F79DD  48 8d 8c 24 c0 00 00 00          lea rcx, [rsp + 0xc0]
028F79E5  e8 06 f4 0d fe                   call 0x9d6df0
028F79EA  81 78 14 64 6e 61 4c             cmp dword ptr [rax + 0x14], 0x4c616e64
028F79F1  0f 85 9f 00 00 00                jne 0x28f7a96
028F79F7  83 78 10 ff                      cmp dword ptr [rax + 0x10], -1
028F79FB  0f 84 95 00 00 00                je 0x28f7a96
028F7A01  48 8d 88 10 03 00 00             lea rcx, [rax + 0x310]
028F7A08  4c 8b c5                         mov r8, rbp
028F7A0B  48 8b d7                         mov rdx, rdi
028F7A0E  e8 4d 75 f6 ff                   call 0x285ef60
028F7A13  48 8b 85 b0 01 00 00             mov rax, qword ptr [rbp + 0x1b0]
028F7A1A  48 8b 88 78 02 00 00             mov rcx, qword ptr [rax + 0x278]
028F7A21  48 83 79 20 00                   cmp qword ptr [rcx + 0x20], 0
028F7A26  74 6e                            je 0x28f7a96
028F7A28  4c 8b c7                         mov r8, rdi
028F7A2B  ba 03 00 00 00                   mov edx, 3
028F7A30  e8 4b 34 0f ff                   call 0x19eae80
028F7A35  eb 5f                            jmp 0x28f7a96
028F7A37  48 8b 5b 38                      mov rbx, qword ptr [rbx + 0x38]
028F7A3B  48 8d 8c 24 b0 00 00 00          lea rcx, [rsp + 0xb0]
028F7A43  48 f7 df                         neg rdi
028F7A46  4c 8b c3                         mov r8, rbx
028F7A49  48 8b d7                         mov rdx, rdi
028F7A4C  4c 8b ce                         mov r9, rsi
028F7A4F  e8 fc f0 fa ff                   call 0x28a6b50
028F7A54  41 b9 01 00 00 00                mov r9d, 1
028F7A5A  48 8b cd                         mov rcx, rbp
028F7A5D  4c 8b 00                         mov r8, qword ptr [rax]
028F7A60  41 8d 51 02                      lea edx, [r9 + 2]
028F7A64  e8 e7 1e fc ff                   call 0x28b9950
028F7A69  4c 8b c6                         mov r8, rsi
028F7A6C  48 8d 8c 24 b0 00 00 00          lea rcx, [rsp + 0xb0]
028F7A74  4c 2b c3                         sub r8, rbx
028F7A77  4c 8b ce                         mov r9, rsi
028F7A7A  48 8b d7                         mov rdx, rdi
028F7A7D  e8 ce f0 fa ff                   call 0x28a6b50
028F7A82  41 b9 03 00 00 00                mov r9d, 3
028F7A88  48 8b cd                         mov rcx, rbp
028F7A8B  41 8b d1                         mov edx, r9d
028F7A8E  4c 8b 00                         mov r8, qword ptr [rax]
028F7A91  e8 ba 1e fc ff                   call 0x28b9950
028F7A96  48 8b b4 24 b8 00 00 00          mov rsi, qword ptr [rsp + 0xb8]
028F7A9E  48 8b bc 24 90 00 00 00          mov rdi, qword ptr [rsp + 0x90]
028F7AA6  48 8b 85 c0 01 00 00             mov rax, qword ptr [rbp + 0x1c0]
028F7AAD  48 85 c0                         test rax, rax
028F7AB0  74 72                            je 0x28f7b24
028F7AB2  48 8b d5                         mov rdx, rbp
028F7AB5  48 8b c8                         mov rcx, rax
028F7AB8  e8 33 16 06 00                   call 0x29590f0
028F7ABD  48 8b 85 c0 01 00 00             mov rax, qword ptr [rbp + 0x1c0]
028F7AC4  48 85 c0                         test rax, rax
028F7AC7  74 5b                            je 0x28f7b24
028F7AC9  80 b8 aa 04 00 00 00             cmp byte ptr [rax + 0x4aa], 0
028F7AD0  75 52                            jne 0x28f7b24
028F7AD2  48 8b cd                         mov rcx, rbp
028F7AD5  e8 a6 82 fc ff                   call 0x28bfd80
028F7ADA  8b 48 18                         mov ecx, dword ptr [rax + 0x18]
028F7ADD  e8 0e 2c 2b 00                   call 0x2baa6f0
028F7AE2  84 c0                            test al, al
028F7AE4  75 24                            jne 0x28f7b0a
028F7AE6  48 8b cd                         mov rcx, rbp
028F7AE9  e8 62 81 fc ff                   call 0x28bfc50
028F7AEE  8b 48 18                         mov ecx, dword ptr [rax + 0x18]
028F7AF1  e8 fa 2b 2b 00                   call 0x2baa6f0
028F7AF6  84 c0                            test al, al
028F7AF8  75 10                            jne 0x28f7b0a
028F7AFA  48 8b 85 c0 01 00 00             mov rax, qword ptr [rbp + 0x1c0]
028F7B01  c6 80 aa 04 00 00 01             mov byte ptr [rax + 0x4aa], 1
028F7B08  eb 1a                            jmp 0x28f7b24
028F7B0A  48 8b cd                         mov rcx, rbp
028F7B0D  e8 9e 34 2b 00                   call 0x2baafb0
028F7B12  84 c0                            test al, al
028F7B14  48 8b 85 c0 01 00 00             mov rax, qword ptr [rbp + 0x1c0]
028F7B1B  0f 94 c1                         sete cl
028F7B1E  88 88 aa 04 00 00                mov byte ptr [rax + 0x4aa], cl
028F7B24  48 8b 9d c0 01 00 00             mov rbx, qword ptr [rbp + 0x1c0]
028F7B2B  49 8b 16                         mov rdx, qword ptr [r14]
028F7B2E  4c 8b b4 24 88 00 00 00          mov r14, qword ptr [rsp + 0x88]
028F7B36  48 85 db                         test rbx, rbx
028F7B39  74 7a                            je 0x28f7bb5
028F7B3B  48 8b 9b 58 04 00 00             mov rbx, qword ptr [rbx + 0x458]
028F7B42  48 85 db                         test rbx, rbx
028F7B45  74 6e                            je 0x28f7bb5
028F7B47  48 8b 05 aa 0c 3c 03             mov rax, qword ptr [rip + 0x33c0caa]
028F7B4E  f6 80 b0 02 00 00 20             test byte ptr [rax + 0x2b0], 0x20
028F7B55  74 5e                            je 0x28f7bb5
028F7B57  0f 10 0b                         movups xmm1, xmmword ptr [rbx]
028F7B5A  48 8d 8b d0 00 00 00             lea rcx, [rbx + 0xd0]
028F7B61  4c 8b cd                         mov r9, rbp
028F7B64  0f 10 53 10                      movups xmm2, xmmword ptr [rbx + 0x10]
028F7B68  44 8b 41 28                      mov r8d, dword ptr [rcx + 0x28]
028F7B6C  0f 10 5b 20                      movups xmm3, xmmword ptr [rbx + 0x20]
028F7B70  4c 89 7c 24 20                   mov qword ptr [rsp + 0x20], r15
028F7B75  f2 0f 10 43 30                   movsd xmm0, qword ptr [rbx + 0x30]
028F7B7A  0f 11 09                         movups xmmword ptr [rcx], xmm1
028F7B7D  0f 11 51 10                      movups xmmword ptr [rcx + 0x10], xmm2
028F7B81  0f 11 59 20                      movups xmmword ptr [rcx + 0x20], xmm3
028F7B85  f2 0f 11 41 30                   movsd qword ptr [rcx + 0x30], xmm0
028F7B8A  e8 71 35 d0 ff                   call 0x25fb100
028F7B8F  48 8d 53 38                      lea rdx, [rbx + 0x38]
028F7B93  4c 8b c5                         mov r8, rbp
028F7B96  48 8d 8b 08 01 00 00             lea rcx, [rbx + 0x108]
028F7B9D  e8 6e 6a 97 00                   call 0x326e610
028F7BA2  48 8d 93 80 00 00 00             lea rdx, [rbx + 0x80]
028F7BA9  48 8d 8b 50 01 00 00             lea rcx, [rbx + 0x150]
028F7BB0  e8 db b6 cf ff                   call 0x25f3290
028F7BB5  48 8b 8d b8 01 00 00             mov rcx, qword ptr [rbp + 0x1b8]
028F7BBC  4c 8b bc 24 80 00 00 00          mov r15, qword ptr [rsp + 0x80]
028F7BC4  48 85 c9                         test rcx, rcx
028F7BC7  74 0e                            je 0x28f7bd7
028F7BC9  48 8b 81 b8 00 00 00             mov rax, qword ptr [rcx + 0xb8]
028F7BD0  48 89 81 30 01 00 00             mov qword ptr [rcx + 0x130], rax
028F7BD7  48 8b cd                         mov rcx, rbp
028F7BDA  e8 71 f3 fa ff                   call 0x28a6f50
028F7BDF  48 83 bd c0 01 00 00 00          cmp qword ptr [rbp + 0x1c0], 0
028F7BE7  0f 84 a7 00 00 00                je 0x28f7c94
028F7BED  48 8b cd                         mov rcx, rbp
028F7BF0  e8 fb b1 fc ff                   call 0x28c2df0
028F7BF5  81 78 38 4f 62 44 47             cmp dword ptr [rax + 0x38], 0x4744624f
028F7BFC  0f 85 92 00 00 00                jne 0x28f7c94
028F7C02  48 8b 40 40                      mov rax, qword ptr [rax + 0x40]
028F7C06  48 c1 e8 29                      shr rax, 0x29
028F7C0A  a8 01                            test al, 1
028F7C0C  0f 84 82 00 00 00                je 0x28f7c94
028F7C12  45 33 c9                         xor r9d, r9d
028F7C15  48 8d 8c 24 b0 00 00 00          lea rcx, [rsp + 0xb0]
028F7C1D  48 8b d5                         mov rdx, rbp
028F7C20  e8 fb b6 2d 00                   call 0x2bd3320
028F7C25  45 33 c0                         xor r8d, r8d
028F7C28  48 8d 4c 24 30                   lea rcx, [rsp + 0x30]
028F7C2D  48 8b d5                         mov rdx, rbp
028F7C30  e8 2b c3 31 00                   call 0x2c13f60
028F7C35  48 8b 9c 24 b0 00 00 00          mov rbx, qword ptr [rsp + 0xb0]
028F7C3D  48 8b 40 48                      mov rax, qword ptr [rax + 0x48]
028F7C41  48 2b d8                         sub rbx, rax
028F7C44  48 85 db                         test rbx, rbx
028F7C47  7e 2e                            jle 0x28f7c77
028F7C49  48 83 bd b0 01 00 00 00          cmp qword ptr [rbp + 0x1b0], 0
028F7C51  74 41                            je 0x28f7c94
028F7C53  48 8b cd                         mov rcx, rbp
028F7C56  e8 d5 82 2b 00                   call 0x2baff30
028F7C5B  84 c0                            test al, al
028F7C5D  74 35                            je 0x28f7c94
028F7C5F  48 8b 85 c0 01 00 00             mov rax, qword ptr [rbp + 0x1c0]
028F7C66  48 01 98 a0 04 00 00             add qword ptr [rax + 0x4a0], rbx
028F7C6D  48 81 c4 98 00 00 00             add rsp, 0x98
028F7C74  5d                               pop rbp
028F7C75  5b                               pop rbx
028F7C76  c3                               ret 
028F7C77  48 85 c0                         test rax, rax
028F7C7A  74 18                            je 0x28f7c94
028F7C7C  41 b9 03 00 00 00                mov r9d, 3
028F7C82  48 f7 db                         neg rbx
028F7C85  4c 8b c3                         mov r8, rbx
028F7C88  48 8b cd                         mov rcx, rbp
028F7C8B  41 8d 51 01                      lea edx, [r9 + 1]
028F7C8F  e8 bc 1c fc ff                   call 0x28b9950
028F7C94  48 81 c4 98 00 00 00             add rsp, 0x98
028F7C9B  5d                               pop rbp
028F7C9C  5b                               pop rbx
028F7C9D  c3                               ret 
