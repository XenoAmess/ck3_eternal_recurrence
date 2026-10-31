package org.xar.ck3.research.m3.equal196;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Input;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Memory;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Ports;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Bytes16;

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Scratch;
import org.xar.ck3.research.m3.map191.MapInsertC3B960;
public final class MapEqualWitness196 {
    private MapEqualWitness196() { }
    private enum Kind { R8,R16,R32,R64,R128,W8,W16,W32,W64,W128,EQUAL,INSERT_SLOT,REHASH,INSERT_OTHER,DESTROY,CAPACITY,RESERVE,OVERFLOW,TERMINAL }
    private record Cell(long address,int width,long low,long high) { }
    private record Step(Kind kind,long address,long low,long high,List<Long> arguments,long returned,List<Cell> effects) { }
    private record Scene(String name,Input input,List<Cell> initial,List<Step> steps,long expectedReturn,List<Cell> finalCells) { }
    public static void main(String[] args) { run(); }
    private static void run() {
        Scene scene=frameScene();
        Script script=new Script(scene);
        for(Cell cell:scene.initial()) script.seed(cell);
        Ports bound=MapEqualBinding196.bind(scene.input().moduleBase(),script,script);
        long returned=MapInsertC3B960.execute(scene.input(),script,bound);
        if(returned!=scene.expectedReturn()) throw new AssertionError("196 recursive return");
        if(script.cursor!=scene.steps().size()) throw new AssertionError("196 recursive plan not exhausted");
        for(Cell cell:scene.finalCells()) script.verifyFinal(cell);
        int framePorts=script.portCount;
        compatibility();

        Input emptyInput=new Input(0,0,0,0,0,new Scratch(0));
        Scene empty=new Scene("rejection",emptyInput,List.of(),List.of(),0,List.of());
        Script captured=new Script(empty);
        Script foreign=new Script(empty);
        Ports rejecting=MapEqualBinding196.bind(scene.input().moduleBase(),captured,captured);
        boolean foreignRejected=false;
        try {
            rejecting.equal3f6d2b0(foreign,0xC3B9CAL,0x8800112233445500L,0x9900112233445508L,0x77001000L);
        } catch(IllegalArgumentException expected) {
            foreignRejected=true;
        }
        if(!foreignRejected || captured.cursor!=0 || captured.portCount!=0
                || foreign.cursor!=0 || foreign.portCount!=0) throw new AssertionError("196 foreign rejection before observation");
        boolean siteRejected=false;
        try {
            rejecting.equal3f6d2b0(captured,0xC3B9CBL,0x8800112233445500L,0x9900112233445508L,0x77001000L);
        } catch(IllegalArgumentException expected) {
            siteRejected=true;
        }
        if(!siteRejected || captured.cursor!=0 || captured.portCount!=0
                || foreign.cursor!=0 || foreign.portCount!=0) throw new AssertionError("196 site rejection before observation");
        System.out.println("196 groups=5 frameEvents="+scene.steps().size()+" framePorts="+framePorts
                +" finalCells="+scene.finalCells().size()+" compatibilityPorts=2 rejectionGroups=2");
    }
    private static Scene frameScene() {
        long moduleBase=0x1000000L, map=0x2000000L, output=0x3000000L;
        long descriptor=0x4000000L, bodyRsp=0x5000000L;
        long childBodyRsp=bodyRsp-0xB0L;
        long sourceEntryRsp=childBodyRsp-8L;
        long rightHome=sourceEntryRsp+8L, leftHome=sourceEntryRsp+0x10L;
        long globalMaskAddr=moduleBase+0x5CAFCBCL, globalLimitAddr=moduleBase+0x5CB0A58L;
        long leftData=0x6000000L, rightData=0x6001008L, bucket=0x7000000L;
        long scratchFlag=bodyRsp+0xC0L, scratchPtr=bodyRsp+0x20L;
        long leftLow=0x1716151400131211L, leftHigh=0x2726252423222120L;
        long rightLow=0xA7A6A5A400131211L, rightHigh=0xB7B6B5B4B3B2B1B0L;
        List<Cell> initial=List.of(
                c(map+0x14L,4,3L,0L), c(map+8L,8,bucket,0L),
                c(bucket+4L,1,0L,0L), c(map+0x18L,1,0L,0L),
                c(descriptor+0x18L,8,0x10L,0L), c(descriptor,8,leftData,0L),
                c(globalMaskAddr,2,0xFFL,0L), c(globalLimitAddr,2,8L,0L),
                c(leftData,16,leftLow,leftHigh), c(rightData,16,rightLow,rightHigh));
        List<Step> steps=List.of(
                mem(Kind.R32,map+0x14L,3L,0L),
                mem(Kind.R64,map+8L,bucket,0L),
                mem(Kind.R8,bucket+4L,0L,0L),
                mem(Kind.R8,map+0x18L,0L,0L),
                port(Kind.CAPACITY,0xC3BC2FL,List.of(4L,1L),1L,List.of()),
                port(Kind.RESERVE,0xC3BC3EL,List.of(map,1L),0L,List.of(
                        c(map+0x18L,1,2L,0L), c(bucket+4L,1,1L,0L),
                        c(bucket+0x20L,8,0x10L,0L), c(bucket+8L,8,rightData,0L))),
                mem(Kind.W8,scratchFlag,0L,0L),
                mem(Kind.W64,scratchPtr,scratchFlag,0L),
                mem(Kind.R32,map+0x14L,3L,0L),
                mem(Kind.R64,map+8L,bucket,0L),
                mem(Kind.R8,bucket+4L,1L,0L),
                mem(Kind.R64,descriptor+0x18L,0x10L,0L),
                mem(Kind.R64,bucket+0x20L,0x10L,0L),
                mem(Kind.R64,bucket+8L,rightData,0L),
                mem(Kind.R64,descriptor,leftData,0L),
                mem(Kind.R16,globalMaskAddr,0xFFL,0L),
                mem(Kind.W16,rightHome,8L,0L),
                mem(Kind.W16,leftHome,0L,0L),
                mem(Kind.R16,rightHome,8L,0L),
                mem(Kind.R16,leftHome,0L,0L),
                mem(Kind.R16,globalLimitAddr,8L,0L),
                mem(Kind.R16,rightHome,8L,0L),
                mem(Kind.R128,leftData,leftLow,leftHigh),
                mem(Kind.R128,rightData,rightLow,rightHigh),
                mem(Kind.W64,output,bucket,0L),
                mem(Kind.W8,output+8L,0L,0L));
        List<Cell> finalCells=List.of(
                c(output,8,bucket,0L), c(output+8L,1,0L,0L),
                c(scratchFlag,1,0L,0L), c(scratchPtr,8,scratchFlag,0L),
                c(rightHome,2,8L,0L), c(leftHome,2,0L,0L),
                c(map+0x18L,1,2L,0L), c(bucket+4L,1,1L,0L));
        return new Scene("recursive-frame-positive-prefix",new Input(moduleBase,map,output,0,descriptor,new Scratch(bodyRsp)),
                initial,steps,output,finalCells);
    }
    private static void compatibility() {
        Input input=new Input(0,0,0,0,0,new Scratch(0));
        long left=0x8123456789ABCD00L;
        long right=0xFEDCBA9876543208L;
        int firstReturned=0x81234567;
        Scene first=new Scene("default5-to-old4",input,List.of(),
                List.of(port(Kind.EQUAL,0xC3B9CAL,List.of(left,right),firstReturned,List.of())),0,List.of());
        Script oldImplementation=new Script(first);
        int firstActual=oldImplementation.equal3f6d2b0(oldImplementation,0xC3B9CAL,left,right,0x1111222233334444L);
        if(firstActual!=firstReturned || oldImplementation.cursor!=1 || oldImplementation.portCount!=1)
            throw new AssertionError("196 default5 exact old4 delegation");

        int secondReturned=0xF1234500;
        Scene second=new Scene("binding-old4-fallback",input,List.of(),
                List.of(port(Kind.EQUAL,0xC3B9CAL,List.of(right,left),secondReturned,List.of())),0,List.of());
        Script fallback=new Script(second);
        Ports bound=MapEqualBinding196.bind(0x55000000L,fallback,fallback);
        int secondActual=bound.equal3f6d2b0(fallback,0xC3B9CAL,right,left);
        if(secondActual!=secondReturned || fallback.cursor!=1 || fallback.portCount!=1)
            throw new AssertionError("196 binding old4 exact fallback");
    }
    private static Cell c(long a,int w,long l,long h) { return new Cell(a,w,l,h); }
    private static Step mem(Kind k,long a,long l,long h) { return new Step(k,a,l,h,List.of(),0,List.of()); }
    private static Step port(Kind k,long a,List<Long> args,long ret,List<Cell> effects) { return new Step(k,a,0,0,args,ret,effects); }
    private static final class Script implements MapEqualBinding196.Memory, Ports {
        private final List<Step> steps;
        private final Map<Long, Byte> store = new HashMap<>();
        private int cursor = 0;
        private int portCount = 0;

        Script(Scene scene) {
            this.steps = List.copyOf(scene.steps());
        }

        private void seed(Cell cell) {
            applyEffect(cell);
        }

        private void verifyFinal(Cell cell) {
            long addr = cell.address();
            int width = cell.width();
            long low = cell.low();
            long high = cell.high();

            if (width == 2) {
                for(int i=0;i<2;i++) {
                    long a=addr+i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing WORD byte");
                    if (store.get(a).byteValue() != (byte)(low >>> (8*i))) throw new AssertionError("Final WORD mismatch");
                }
            } else if (width == 1) {
                if (!store.containsKey(addr)) throw new AssertionError("Missing byte at " + Long.toHexString(addr));
                byte actual = store.get(addr);
                byte expected = (byte)low;
                if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(addr));
            } else if (width == 4) {
                for (int i = 0; i < 4; i++) {
                    long a = addr + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(low >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
            } else if (width == 8) {
                for (int i = 0; i < 8; i++) {
                    long a = addr + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(low >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
            } else if (width == 16) {
                for (int i = 0; i < 8; i++) {
                    long a = addr + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(low >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
                for (int i = 0; i < 8; i++) {
                    long a = addr + 8 + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(high >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
            } else {
                throw new AssertionError("Unsupported width: " + width);
            }
        }

        private void applyEffect(Cell cell) {
            long addr = cell.address();
            int width = cell.width();
            long low = cell.low();
            long high = cell.high();

            if (width == 2) {
                for(int i=0;i<2;i++) store.put(addr+i,(byte)(low >>> (8*i)));
            } else if (width == 1) {
                store.put(addr, (byte)low);
            } else if (width == 4) {
                for (int i = 0; i < 4; i++) {
                    store.put(addr + i, (byte)(low >>> (8 * i)));
                }
            } else if (width == 8) {
                for (int i = 0; i < 8; i++) {
                    store.put(addr + i, (byte)(low >>> (8 * i)));
                }
            } else if (width == 16) {
                for (int i = 0; i < 8; i++) {
                    store.put(addr + i, (byte)(low >>> (8 * i)));
                }
                for (int i = 0; i < 8; i++) {
                    store.put(addr + 8 + i, (byte)(high >>> (8 * i)));
                }
            } else {
                throw new AssertionError("Unsupported width: " + width);
            }
        }

        private Step nextStep(Kind expectedKind, long expectedAddress) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Step cursor exhausted");
            }
            Step step = steps.get(cursor);
            if (step.kind() != expectedKind) {
                throw new AssertionError("Kind mismatch: expected " + expectedKind + " got " + step.kind());
            }
            if (step.address() != expectedAddress) {
                throw new AssertionError("Address mismatch: expected " + Long.toHexString(expectedAddress) + " got " + Long.toHexString(step.address()));
            }
            cursor++;
            return step;
        }

        private long readBytes(long address, int width) {
            long result = 0;
            for (int i = 0; i < width; i++) {
                long addr = address + i;
                if (!store.containsKey(addr)) {
                    throw new AssertionError("Missing byte at " + Long.toHexString(addr));
                }
                byte b = store.get(addr);
                result |= ((long)b & 0xFFL) << (8 * i);
            }
            return result;
        }

        private void writeBytes(long address, int width, long value) {
            for (int i = 0; i < width; i++) {
                long addr = address + i;
                byte b = (byte)(value >>> (8 * i));
                store.put(addr, b);
            }
        }

        @Override
        public int readUnsigned16(long address) {
            Step step=nextStep(Kind.R16,address);
            long actual=readBytes(address,2);
            if ((step.low() & 0xFFFFL)!=actual) throw new AssertionError("R16 mismatch");
            return (int)actual;
        }
        @Override
        public void write16(long address,int value) {
            Step step=nextStep(Kind.W16,address);
            long actual=value & 0xFFFFL;
            if ((step.low() & 0xFFFFL)!=actual) throw new AssertionError("W16 mismatch");
            writeBytes(address,2,actual);
        }
        @Override
        public long readPointer(long address) {
            Step step = nextStep(Kind.R64, address);
            long actual = readBytes(address, 8);
            if (step.low() != actual) {
                throw new AssertionError("R64 read mismatch at " + Long.toHexString(address));
            }
            return actual;
        }

        @Override
        public int readInt32(long address) {
            Step step = nextStep(Kind.R32, address);
            long actual = readBytes(address, 4);
            if ((step.low() & 0xFFFFFFFFL) != actual) {
                throw new AssertionError("R32 read mismatch at " + Long.toHexString(address));
            }
            return (int)actual;
        }

        @Override
        public void writeInt32(long address, int value) {
            Step step = nextStep(Kind.W32, address);
            long expected = Integer.toUnsignedLong(value);
            if ((step.low() & 0xFFFFFFFFL) != expected) {
                throw new AssertionError("W32 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 4, expected);
        }

        @Override
        public void writeInt64(long address, long value) {
            Step step = nextStep(Kind.W64, address);
            if (step.low() != value) {
                throw new AssertionError("W64 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 8, value);
        }

        @Override
        public int readUnsigned8(long address) {
            Step step = nextStep(Kind.R8, address);
            long actual = readBytes(address, 1);
            if ((step.low() & 0xFFL) != actual) {
                throw new AssertionError("R8 read mismatch at " + Long.toHexString(address));
            }
            return (int)(actual & 0xFF);
        }

        @Override
        public void write8(long address, int value) {
            Step step = nextStep(Kind.W8, address);
            long expected = (long)value & 0xFFL;
            if ((step.low() & 0xFFL) != expected) {
                throw new AssertionError("W8 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 1, expected);
        }

        @Override
        public Bytes16 read128(long address) {
            Step step = nextStep(Kind.R128, address);
            long low = readBytes(address, 8);
            long high = readBytes(address + 8, 8);
            if (step.low() != low || step.high() != high) {
                throw new AssertionError("R128 read mismatch at " + Long.toHexString(address));
            }
            return new Bytes16(low, high);
        }

        @Override
        public void write128(long address, Bytes16 value) {
            Step step = nextStep(Kind.W128, address);
            if (step.low() != value.low() || step.high() != value.high()) {
                throw new AssertionError("W128 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 8, value.low());
            writeBytes(address + 8, 8, value.high());
        }

        @Override
        public int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.EQUAL, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("EQUAL args size mismatch");
            if (args.get(0) != rcx || args.get(1) != rdx) throw new AssertionError("EQUAL args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
            return (int)step.returned();
        }





        @Override
        public void insertSlotC3cf10(Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.INSERT_SLOT, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 4) throw new AssertionError("INSERT_SLOT args size mismatch");
            if (args.get(0) != bucket || args.get(1) != (long) probe
                    || args.get(2) != (long) hash || args.get(3) != descriptor) {
                throw new AssertionError("INSERT_SLOT args mismatch");
            }
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void rehashC3a400(Memory memory, long siteRva, long map) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.REHASH, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 1) throw new AssertionError("REHASH args size mismatch");
            if (args.get(0) != map) throw new AssertionError("REHASH args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void insertC3a5f0(Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.INSERT_OTHER, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 4) throw new AssertionError("INSERT_OTHER args size mismatch");
            if (args.get(0) != map || args.get(1) != result || args.get(2) != (long)hash || args.get(3) != descriptor) throw new AssertionError("INSERT_OTHER args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void destroy856050(Memory memory, long siteRva, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.DESTROY, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 1) throw new AssertionError("DESTROY args size mismatch");
            if (args.get(0) != descriptor) throw new AssertionError("DESTROY args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public int capacity86e160(Memory memory, long siteRva, int ecx, int edx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.CAPACITY, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("CAPACITY args size mismatch");
            if (args.get(0) != (long)ecx || args.get(1) != (long)edx) throw new AssertionError("CAPACITY args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
            return (int)step.returned();
        }

        @Override
        public void reserveC3b700(Memory memory, long siteRva, long map, int edx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.RESERVE, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("RESERVE args size mismatch");
            if (args.get(0) != map || args.get(1) != (long)edx) throw new AssertionError("RESERVE args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void overflow86f210(Memory memory, long siteRva, long rcx, long rdx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.OVERFLOW, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("OVERFLOW args size mismatch");
            if (args.get(0) != rcx || args.get(1) != rdx) throw new AssertionError("OVERFLOW args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void terminal4232cf4(Memory memory, long siteRva) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.TERMINAL, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 0) throw new AssertionError("TERMINAL args size mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }
    }
}
