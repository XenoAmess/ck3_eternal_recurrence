"""Source-derived checks only; never compiles/loads/executes a native image."""
import copy
import hashlib
import json
import os
import re
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ['XAR_PARENT_SOURCE_REPO']) if 'XAR_PARENT_SOURCE_REPO' in os.environ else HERE.parents[3]
HELD=ROOT/'docs/ck3-native-ai/acceptance/2026-10-16-r0174-maintenance-source'
MASK=(1<<64)-1
STATE=0x100000
ENTRY=0x700008
BASE=0x140000000
TARGET=0x800000

def instructions(text):
    result=[];labels={}
    in_thunk=False
    for original in text.splitlines():
        line=original.split(';',1)[0].strip().lower()
        if line.startswith('xarparententrythunk12004 proc'):
            in_thunk=True
            continue
        if line.startswith('xarparententrythunk12004 endp'):break
        if not in_thunk or not line or line.startswith('.'):continue
        if line.endswith(':'):labels[line[:-1]]=len(result);continue
        if line.startswith('lock '):line=line[5:]
        opcode,_,operands=line.partition(' ')
        result.append((opcode,[p.strip() for p in operands.split(',') if p.strip()]))
    return result,labels

class ThunkModel:
    """Interpret the actual candidate MASM subset, not a second hook function.

    GPRs, full saved flags and original stack/home bytes are modelled. This does
    not encode machine code or implement the real Windows unwinder/XSTATE ABI.
    """
    def __init__(self,text,wire=None,character=TARGET):
        self.code,self.labels=instructions(text)
        names='rax rcx rdx r8 r9 r10 r11 rbx rbp rsi rdi r12 r13 r14 r15 rsp'.split()
        self.reg={n:0x123400000000+i*0x1111 for i,n in enumerate(names)}
        self.reg['rdx']=character;self.reg['rsp']=ENTRY
        self.flags=0xED7;self.zf=False
        self.mem={ENTRY:BASE+0x3978bf8}
        self.mem.update({ENTRY+8*i:0xCAFE0000+i for i in range(1,12)})
        self.mem.update(wire or {})
        self.mem.setdefault(STATE,1)
        self.mem.setdefault(STATE+8,TARGET)
        self.xmm=tuple(bytes([i])*16 for i in range(16))
        self.original=(copy.deepcopy(self.reg),self.flags,copy.deepcopy(self.mem),self.xmm)
        self.pc=0;self.tail_count=0
    def address(self,op):
        op=op.replace('qword ptr ','').strip()
        if op=='gs:[48h]':return 0xFFFF0048
        expr=op[1:-1]
        parts=re.split(r'(?=[+-])',expr)
        total=self.reg[parts[0]]
        for p in parts[1:]:
            sign=-1 if p[0]=='-' else 1
            total+=sign*self.number(p[1:])
        return total&MASK
    @staticmethod
    def number(op):return int(op[:-1],16) if op.endswith('h') else int(op,10)
    def read(self,op):
        if op=='xarparententrystate12004':return STATE
        if op=='gs:[48h]':return 12345
        if '[' in op:return self.mem.get(self.address(op),0)
        if op in self.reg:return self.reg[op]
        if op in ('eax','ecx','edx'):return self.reg['r'+op[1:]]&0xffffffff
        return self.number(op)
    def write(self,op,value):
        value&=MASK
        if '[' in op:self.mem[self.address(op)]=value
        elif op in ('eax','ecx','edx'):self.reg['r'+op[1:]]=value&0xffffffff
        else:self.reg[op]=value
    def arithmetic_flags(self,value):
        self.zf=(value&MASK)==0
        # Deliberately clobber every arithmetic flag. POPFQ must restore the
        # original complete word, not merely the branch condition.
        self.flags=(self.flags^0xCD5)&MASK
    def step(self):
        op,a=self.code[self.pc];self.pc+=1
        if op=='push':
            value=self.read(a[0]);self.reg['rsp']-=8;self.mem[self.reg['rsp']]=value
        elif op=='pushfq':
            self.reg['rsp']-=8;self.mem[self.reg['rsp']]=self.flags
        elif op=='pop':
            value=self.mem[self.reg['rsp']];self.reg['rsp']+=8;self.write(a[0],value)
        elif op=='popfq':
            self.flags=self.mem[self.reg['rsp']];self.reg['rsp']+=8
        elif op=='mov':self.write(a[0],self.read(a[1]))
        elif op=='lea':
            self.write(a[0],STATE if a[1]=='xarparententrystate12004' else self.address(a[1]))
        elif op in ('inc','dec'):
            value=(self.read(a[0])+(1 if op=='inc' else -1))&MASK
            self.write(a[0],value);self.arithmetic_flags(value)
        elif op=='cmp':self.arithmetic_flags(self.read(a[0])-self.read(a[1]))
        elif op=='cmpxchg':
            old=self.read(a[0]);self.arithmetic_flags(self.reg['rax']-old)
            if self.zf:self.write(a[0],self.read(a[1]))
            else:self.reg['rax']=old
        elif op in ('xor','or','shl'):
            left=self.read(a[0]);right=self.read(a[1])
            result=left^right if op=='xor' else left|right if op=='or' else left<<right
            self.write(a[0],result);self.arithmetic_flags(result)
        elif op=='rdtsc':
            self.reg['rax']=0x89abcdef;self.reg['rdx']=0x12345678
        elif op in ('je','jne','jnz','jmp'):
            take=op=='jmp' or (self.zf if op=='je' else not self.zf)
            if take:
                if a[0]=='qword ptr [xarparententryoriginalprefixtarget12004]':
                    self.tail_count+=1;return False
                self.pc=self.labels[a[0]]
        else:raise AssertionError('Unexpected instruction: '+op)
        return True
    def run(self):
        for _ in range(256):
            if not self.step():return self
        raise AssertionError('Unbounded thunk path')
    def assert_transparent(self,test):
        old_reg,old_flags,old_mem,old_xmm=self.original
        test.assertEqual(self.reg,old_reg)
        test.assertEqual(self.flags,old_flags)
        test.assertEqual(self.xmm,old_xmm)
        for p,v in old_mem.items():
            if ENTRY<=p<ENTRY+96:test.assertEqual(self.mem[p],v)
        test.assertEqual(self.tail_count,1)
        test.assertEqual(self.mem.get(STATE+0x100,0),0)

class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asm=(HERE/'candidate-a04/parent_entry_opportunity_12004.asm').read_text()
        cls.cpp=(HERE/'candidate-a04/parent_entry_opportunity_12004.cpp').read_text()
        cls.header=(HERE/'candidate-a04/parent_entry_opportunity_12004.hpp').read_text()
    def test_held_parent_full_raw_and_disassembly_agree(self):
        source=json.loads((HELD/'SOURCE-SPANS.actual.json').read_text(encoding='utf-8'))
        spans=[s for s in source['spans'] if s['label'].startswith('parent-')]
        spans.sort(key=lambda s:s['begin_rva']);raw=b'';cursor=0x28f7840
        for s in spans:
            b=bytes.fromhex(s['raw_hex'])
            self.assertEqual(cursor,s['begin_rva'])
            self.assertEqual(hashlib.sha256(b).hexdigest(),s['sha256'])
            self.assertEqual(len(b),s['bytes']);raw+=b;cursor+=len(b)
        self.assertEqual(len(raw),1118)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
            'c115401592983d13238154255b9b2583fe85222089d71fde10f0e8aae6c9753c')
        assembled=b''
        for line in (HELD/'parent.complete.asm').read_text().splitlines():
            m=re.match(r'^([0-9A-F]+)  ((?:[0-9a-f]{2} )+)',line)
            self.assertIsNotNone(m)
            self.assertEqual(int(m[1],16),0x28f7840+len(assembled))
            assembled+=bytes.fromhex(m[2])
        self.assertEqual(raw,assembled)
    def test_target_entry_preserves_inputs_flags_stack_and_tail_once(self):
        m=ThunkModel(self.asm).run();m.assert_transparent(self)
        self.assertEqual(m.mem[STATE+0x58],2)
        self.assertEqual(m.mem[STATE+0x70],TARGET)
        self.assertEqual(m.mem[STATE+0xd8],ENTRY)
        self.assertEqual(m.mem[STATE+0xe8],BASE+0x3978bf8)
        self.assertEqual(m.mem[STATE+0xf0],12345)
        self.assertEqual(m.mem[STATE+0xf8],0x1234567889abcdef)
    def test_foreign_beyond_old_128_does_not_consume_target_frame(self):
        wire={STATE:1,STATE+8:TARGET}
        for _ in range(257):
            m=ThunkModel(self.asm,wire,character=TARGET+0x1000).run()
            m.assert_transparent(self)
            wire={p:v for p,v in m.mem.items() if STATE<=p<STATE+0x110}
        self.assertEqual(wire[STATE+0x40],257)
        self.assertEqual(wire.get(STATE+0x58,0),0)
        m=ThunkModel(self.asm,wire).run();m.assert_transparent(self)
        self.assertEqual(m.mem[STATE+0x58],2)
    def test_disabled_path_forwards_without_collecting(self):
        m=ThunkModel(self.asm,{STATE:0}).run();m.assert_transparent(self)
        for offset in (0x40,0x48,0x50,0x58):self.assertEqual(m.mem.get(STATE+offset,0),0)
    def test_one_target_frame_is_immutable_and_later_match_counted(self):
        first=ThunkModel(self.asm).run()
        wire={p:v for p,v in first.mem.items() if STATE<=p<STATE+0x110}
        before={p:v for p,v in wire.items() if STATE+0x60<=p<STATE+0x100}
        second=ThunkModel(self.asm,wire).run();second.assert_transparent(self)
        self.assertEqual(second.mem[STATE+0x48],2)
        self.assertEqual(second.mem[STATE+0x50],1)
        self.assertEqual(before,{p:v for p,v in second.mem.items() if STATE+0x60<=p<STATE+0x100})
    def test_counter_wrap_is_visible_not_silent_negative_evidence(self):
        m=ThunkModel(self.asm,{STATE+0x40:MASK},TARGET+8).run()
        m.assert_transparent(self)
        self.assertEqual(m.mem[STATE+0x108],1)
    def test_source_contains_no_argument_dereference_or_call_or_simd(self):
        code,_=instructions(self.asm)
        self.assertFalse(any(op in ('call','ret') for op,_ in code))
        for op,args in code:
            for a in args:
                self.assertNotRegex(a,r'\[(?:rcx|rdx|r8|r9)(?:\+|\])')
                self.assertNotRegex(a,r'\b(?:xmm|ymm|zmm)\d+\b')
        self.assertIn('full_id_read_at_entry=false,native_clock_read_at_entry=false',self.header)
        self.assertIn('actual_payment=false,military_producer=false,payer_identified=false',self.header)
    def test_unwind_frame_model_at_flag_restore_boundaries(self):
        # Check the stack/frame hypothesis for the nonstandard POPFQ boundary.
        # This is NOT RtlVirtualUnwind qualification of emitted pdata/xdata.
        m=ThunkModel(self.asm)
        reached=[]
        for _ in range(256):
            op,args=m.code[m.pc]
            if op=='popfq':
                reached.append('popfq')
                self.assertEqual(m.reg['rbp'],ENTRY-0x50)
                self.assertEqual(m.reg['rsp'],ENTRY-0x10)
                self.assertEqual(m.mem[m.reg['rbp']+0x48],m.original[0]['rbp'])
            if op=='pop' and args==['rbp']:
                reached.append('poprbp');self.assertEqual(m.reg['rsp'],ENTRY-8)
            if not m.step():break
        self.assertEqual(reached,['popfq','poprbp'])
        self.assertEqual(m.reg['rsp'],ENTRY)
        self.assertIn('jmp qword ptr [XarParentEntryOriginalPrefixTarget12004]',self.asm)
        self.assertNotIn('jmp XarParentEntryOriginalPrefix12004',self.asm)
        self.assertIn('extern void (*const XarParentEntryOriginalPrefixTarget12004)()',self.cpp)
    def test_off_precedes_busy_check_and_no_rearm_or_unsafe_unpatch(self):
        stop=self.cpp.split('bool StopAndSnapshot',1)[1].split('bool Uninstall',1)[0]
        self.assertLess(stop.index('InterlockedExchange64(&wire.enabled,0)'),
                        stop.index('if(Atomic(wire.active_thunks))'))
        self.assertIn('out.producer_busy=true;return false;',stop)
        self.assertIn('armed_once||!Identity()',self.cpp)
        uninstall=self.cpp.split('bool Uninstall',1)[1]
        self.assertIn('if(!quiescent||Atomic',uninstall)
        self.assertNotIn('VirtualFree',uninstall)
        self.assertIn('current!=patch&&current!=kPrefix',self.cpp)
        self.assertIn('actual_created==owner.process_create_time_100ns',self.cpp)
    def test_unknown_and_invalid_snapshots_do_not_default_to_zero_counts(self):
        self.assertIn('std::optional<std::uint64_t> foreign_count',self.header)
        self.assertIn('std::optional<std::uint64_t> frame_state',self.header)
        self.assertIn('std::optional<std::uint32_t> full_id_at_entry',self.header)
        self.assertIn('(state!=0&&state!=2)||(overflow!=0&&overflow!=1)',self.cpp)
        stop=self.cpp.split('bool StopAndSnapshot',1)[1].split('bool Uninstall',1)[0]
        self.assertLess(stop.index('Status::invalid_wire_state'),stop.index('out.foreign_count='))
        exact=stop.split('if(!overflow){',1)[1].split('}',1)[0]
        self.assertIn('out.foreign_count=out.raw_foreign_counter_bits',exact)
        self.assertIn('out.matching_pointer_count=out.raw_matching_counter_bits',exact)
        self.assertIn('if(!frame_consistent||!counts_consistent)',self.cpp)
        self.assertIn('out.frame->rdx==owner.character',self.cpp)
    def test_stop_order_accounts_for_inflight_before_enabled_check(self):
        code,_=instructions(self.asm)
        active=next(i for i,(op,a) in enumerate(code) if op=='inc' and a==['qword ptr [r11+100h]'])
        enabled=next(i for i,(op,a) in enumerate(code) if op=='cmp' and a==['qword ptr [r11+00h]','0'])
        self.assertLess(active,enabled)
        # A producer admitted before OFF stays active through the final publish;
        # no close can treat the partial frame as an empty successful sample.
        m=ThunkModel(self.asm)
        while m.pc<=enabled:m.step()
        self.assertEqual(m.mem[STATE+0x100],1)
        m.mem[STATE]=0
        self.assertNotEqual(m.mem[STATE+0x100],0)
        m.run()
        self.assertEqual(m.mem[STATE+0x100],0)
        self.assertEqual(m.mem[STATE+0x58],2)
        # An entry beginning after OFF can only touch active_thunks.
        wire={p:v for p,v in m.mem.items() if STATE<=p<STATE+0x110}
        after=ThunkModel(self.asm,wire).run()
        for o in (0x40,0x48,0x50,0x58):self.assertEqual(after.mem.get(STATE+o,0),wire.get(STATE+o,0))
    def test_state_corruption_is_detected_by_transparency_oracle(self):
        mutant=self.asm.replace('mov r10,[rbp+28h]','mov r10,0')
        m=ThunkModel(mutant).run()
        with self.assertRaises(AssertionError):m.assert_transparent(self)
    def test_prefix_transfer_is_not_epilogue_and_preserves_original_frame(self):
        prefix=self.asm.split('XarParentEntryOriginalPrefix12004 PROC FRAME',1)[1]
        self.assertIn('db 0ffh,064h,024h,008h',prefix)
        self.assertNotIn('jmp qword ptr [XarParentEntryContinuation12004]',prefix)
        # Published Version1 scanner's FF25 and REX.W FF/4 tail forms must NOT
        # match while this prefix still owns its original allocated frame.
        def scanner_tail(b):
            return b[:2]==bytes.fromhex('ff25') or (len(b)>=3 and b[0]==0x48 and b[1]==0xff and (b[2]&0x38)==0x20)
        self.assertFalse(scanner_tail(bytes.fromhex('ff642408')))
        self.assertTrue(scanner_tail(bytes.fromhex('ff2500000000')))
        body=(HELD/'parent.complete.asm').read_text()
        self.assertNotRegex(body,r'\[rsp \+ 0x(?:8|10)\]')
        state=ThunkModel(self.asm).run()
        old=copy.deepcopy(state.reg);entry=old['rsp']
        # Original prefix's native effect, including the existing save slots.
        registers=copy.deepcopy(old);memory={}
        registers['rax']=entry
        registers['rsp']-=8;memory[registers['rsp']]=old['rbx']
        registers['rsp']-=8;memory[registers['rsp']]=old['rbp']
        registers['rsp']-=0x98;memory[entry-0x20]=old['r14']
        before=copy.deepcopy(registers);sp=registers['rsp']
        memory[sp+0x10]=registers['r11']
        registers['r11']=BASE+0x28f7850
        memory[sp+8]=registers['r11']
        registers['r11']=memory[sp+0x10]
        self.assertEqual(registers,before)
        self.assertEqual(sp,entry-0xa8)
        self.assertEqual(memory[sp+8],BASE+0x28f7850)
        self.assertEqual(memory[entry-0x20],old['r14'])

if __name__=='__main__':unittest.main(verbosity=2)
