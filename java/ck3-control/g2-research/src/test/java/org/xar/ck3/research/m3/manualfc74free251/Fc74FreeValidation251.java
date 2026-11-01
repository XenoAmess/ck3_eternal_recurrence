package org.xar.ck3.research.m3.manualfc74free251;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;
import org.xar.ck3.research.m3.fc74free251.Fc74FreeBinding251;
public final class Fc74FreeValidation251 {
 private Fc74FreeValidation251() { }
 private static int checks,groups,events,ramEvents,portEvents,opaqueEffects;
 private static void check(boolean b,String label){checks++;if(!b)throw new AssertionError(label);}
 private static String h(long v){return Long.toUnsignedString(v,16);}
 private static String rw(String k,long a,long v){return k+":"+h(a)+":"+h(v);}
 private static final class Ram implements Lower61Inputs.Memory {
  final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace=new ArrayList<>();
  private long raw(long a,int w){long v=0;for(int n=0;n<w;n++){Byte b=bytes.get(a+n);if(b==null)throw new AssertionError("unmapped "+h(a+n));v|=(b.longValue()&255L)<<(8*n);}return v;}
  private void store(long a,int w,long v){for(int n=0;n<w;n++)bytes.put(a+n,(byte)(v>>>(8*n)));}
  void seed8(long a,int v){check((v&~255)==0,"seed8width");store(a,1,v);}
  void seed32(long a,int v){store(a,4,Integer.toUnsignedLong(v));}
  void seed64(long a,long v){store(a,8,v);}
  void effect32(long a,int v){trace.add(rw("E32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  void effect64(long a,long v){trace.add(rw("E64",a,v));store(a,8,v);}
  Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
  @Override public long readPointer(long a){long v=raw(a,8);trace.add(rw("R64",a,v));return v;}
  @Override public int readInt32(long a){long v=raw(a,4);trace.add(rw("R32",a,v));return (int)v;}
  @Override public void writeInt64(long a,long v){trace.add(rw("W64",a,v));store(a,8,v);}
  @Override public void writeInt32(long a,int v){trace.add(rw("W32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
 }
 @FunctionalInterface private interface LowerInvoke {long invoke(String role,long... args);}
 private static final class LowerCalls implements Lower61Inputs.Calls {
  private final LowerInvoke invoke;LowerCalls(LowerInvoke invoke){this.invoke=invoke;}
  @Override public int callSlot43DA748(Lower61Inputs.FirstCall known){return (int)invoke.invoke("free",known.rcxRaw(),known.rdxRaw(),known.r8Raw());}
  @Override public long call423B18C(){return invoke.invoke("cell");}
  @Override public int callSlot43DA738(){return (int)invoke.invoke("error");}
  @Override public int call423B0D4(long rcx){return (int)invoke.invoke("map",rcx);}
 }
 @FunctionalInterface private interface OuterInvoke {long invoke(String role,NativeTaskMemory memory,long... args);}
 private static final class OuterPorts implements Fc74Api238.Ports {
  private final OuterInvoke invoke;OuterPorts(OuterInvoke invoke){this.invoke=invoke;}
  @Override public int callIat43da738(NativeTaskMemory m,long s,long t,int e){return (int)invoke.invoke("iat738",m,s,t,(long)e);}
  @Override public long call424e900(NativeTaskMemory m,long s,int e){return invoke.invoke("e900",m,s,(long)e);}
  @Override public int call424e948(NativeTaskMemory m,long s,int e,long d){return (int)invoke.invoke("e948",m,s,(long)e,d);}
  @Override public long call424e2ec(NativeTaskMemory m,long s,long c,long d){return invoke.invoke("e2ec",m,s,c,d);}
  @Override public void call424e364(NativeTaskMemory m,long s,long c){invoke.invoke("free",m,s,c);}
  @Override public void call424f8a8(NativeTaskMemory m,long s,long c){invoke.invoke("f8old",m,s,c);}
  @Override public void call424f8a8(NativeTaskMemory m,long s,long c,long entry){invoke.invoke("f8new",m,s,c,entry);}
  @Override public void callIat43da420(NativeTaskMemory m,long s,long t,int e){invoke.invoke("iat420",m,s,t,(long)e);}
 }
 private static void args(long[] actual,long... expected){check(java.util.Arrays.equals(actual,expected),"typed args expected="+java.util.Arrays.toString(expected)+" actual="+java.util.Arrays.toString(actual));}
 private static void port(Ram m,String prefix,String role,long... values){StringBuilder b=new StringBuilder(prefix).append(':').append(role);for(long value:values)b.append(':').append(h(value));m.trace.add(b.toString());}
 private static void expectedWrite(Map<Long,Byte> map,long a,int width,long v){for(int n=0;n<width;n++)map.put(a+n,(byte)(v>>>(8*n)));}
 private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException actual){check(actual==marker,label);return;}throw new AssertionError("no original exception "+label);}
 private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException actual){checks++;return;}throw new AssertionError("not rejected "+label);}
 private static void complete(Ram m,List<String> expected,Map<Long,Byte> finalBytes,String label){check(m.trace.equals(expected),label+" expected="+expected+" actual="+m.trace);check(m.snapshot().equals(finalBytes),label+" finalbytes");groups++;events+=m.trace.size();for(String e:m.trace){if(e.startsWith("R")||e.startsWith("W"))ramEvents++;else if(e.startsWith("E"))opaqueEffects++;else portEvents++;}}
 private static void protocolCountercases251(){
  {
   Ram m=new Ram(),foreign=new Ram();
   LowerCalls lower=new LowerCalls((role,a)->{throw new AssertionError("null-qualified must not reach lower "+role);});
   OuterPorts forbidden=new OuterPorts((role,memory,a)->{throw new AssertionError("factory callback "+role);});
   rejected(()->Fc74FreeBinding251.bind(0,null,lower,forbidden),"null memory");
   rejected(()->Fc74FreeBinding251.bind(0,m,null,forbidden),"null calls");
   rejected(()->Fc74FreeBinding251.bind(0,m,lower,null),"null fallback");
   check(m.trace.isEmpty()&&foreign.trace.isEmpty()&&m.bytes.isEmpty(),"factory zero Memory/provider effects");
   RuntimeException freeMarker=new RuntimeException("nonqualified free original"),f8Marker=new RuntimeException("passive new4 original");
   int[] cursor={0};
   OuterPorts fallback=new OuterPorts((role,memory,a)->{
    int n=cursor[0]++;
    switch(n){
     case 0->{check(role.equals("iat738")&&memory==foreign,"passive first identity/role");args(a,0x1111,0xFEDCBA9876543210L,(long)(int)0x80000001L);port(m,"P",role,a);return 0xDEADBEEFL;}
     case 1->{check(role.equals("e900")&&memory==null,"passive e900 null identity");args(a,0x2222,-1L);port(m,"P",role,a);return 0xFEDCBA9876543210L;}
     case 2->{check(role.equals("e948")&&memory==m,"passive e948 identity");args(a,0x3333,(long)Integer.MIN_VALUE,0x8000000000000001L);port(m,"P",role,a);return 0x12345678L;}
     case 3->{check(role.equals("e2ec")&&memory==foreign,"passive alloc identity");args(a,0x4444,-1L,0x3C8);port(m,"P",role,a);return 0x8000000000000001L;}
     case 4->{check(role.equals("f8old")&&memory==null,"passive old3 identity");args(a,0x5555,0xFEDCBA9876541111L);port(m,"P",role,a);return 0;}
     case 5->{check(role.equals("f8new")&&memory==m,"passive new4 exact overload");args(a,0x6666,0x8000000000000002L,0xFEDCBA9876543210L);port(m,"P",role,a);return 0;}
     case 6->{check(role.equals("iat420")&&memory==foreign,"passive restore identity");args(a,0x7777,0x8000000000000003L,(long)(int)0xABCDEF01L);port(m,"P",role,a);return 0;}
     case 7->{check(role.equals("free")&&memory==foreign,"nonqualified identity");args(a,0x424FCE8L,0x8000000000000004L);port(m,"P",role,a);return 0;}
     case 8->{check(role.equals("free")&&memory==m,"nonqualified FD0B is not call site");args(a,0x424FD0BL,0xFEDCBA9876542222L);port(m,"P",role,a);return 0;}
     case 9->{check(role.equals("free")&&memory==null,"nonqualified null callback Memory");args(a,0x424FD17L,0x7000);port(m,"P",role,a);throw freeMarker;}
     case 10->{check(role.equals("f8new")&&memory==foreign,"new4 original exception overload");args(a,0x8888,0,-1L);port(m,"P",role,a);throw f8Marker;}
     default->throw new AssertionError("extra passive invocation "+n+":"+role);
    }
   });
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());
   Fc74Api238.Ports bound=Fc74FreeBinding251.bind(0,m,lower,fallback);
   check(m.trace.isEmpty()&&m.snapshot().equals(expected),"base0 bind no heap capture");
   bound.call424e364(m,0x424FD17L,0);
   check(m.trace.isEmpty()&&m.snapshot().equals(expected)&&cursor[0]==0,"qualified null no heap/provider/fallback");
   int v1=bound.callIat43da738(foreign,0x1111,0xFEDCBA9876543210L,(int)0x80000001L);check(v1==(int)0xDEADBEEFL,"int return exact bits");
   long v2=bound.call424e900(null,0x2222,-1);check(v2==0xFEDCBA9876543210L,"lookup full64 return");
   int v3=bound.call424e948(m,0x3333,Integer.MIN_VALUE,0x8000000000000001L);check(v3==0x12345678,"setter int return");
   long v4=bound.call424e2ec(foreign,0x4444,-1L,0x3C8);check(v4==0x8000000000000001L,"allocation full64 return");
   bound.call424f8a8(null,0x5555,0xFEDCBA9876541111L);
   bound.call424f8a8(m,0x6666,0x8000000000000002L,0xFEDCBA9876543210L);
   bound.callIat43da420(foreign,0x7777,0x8000000000000003L,(int)0xABCDEF01L);
   bound.call424e364(foreign,0x424FCE8L,0x8000000000000004L);
   bound.call424e364(m,0x424FD0BL,0xFEDCBA9876542222L);
   sameException(()->bound.call424e364(null,0x424FD17L,0x7000),freeMarker,"nonqualified original fallback exception");
   sameException(()->bound.call424f8a8(foreign,0x8888,0,-1L),f8Marker,"new4 original exception");
   check(cursor[0]==11,"exact eleven separate passive invocations");check(foreign.trace.isEmpty()&&foreign.bytes.isEmpty(),"foreign RAM zero effects");
   complete(m,PROTOCOL_TRACE,expected,"protocol countercases and returns");
  }
  {
   Ram m=new Ram();m.seed64(0x105C5DE30L,0x8000000000000011L);m.seed64(0,0xAABBCCDD00000007L);m.seed8(-1L,0xA5);m.seed8(8,0x5A);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x105C5DE30L,8,0x123456789ABC3333L);expectedWrite(expected,0,4,0xFEDCBA98L);
   int[] cursor={0};
   LowerCalls lower=new LowerCalls((role,a)->{
    int n=cursor[0]++;
    switch(n){
     case 0->{check(role.equals("free"),"first original lower role");args(a,0x8000000000000011L,0,0x800000000000A000L);port(m,"L",role,a);m.effect64(0x105C5DE30L,0xFEDCBA9876543222L);return 0xFFFFFF00L;}
     case 1->{check(role.equals("free"),"second original lower role");args(a,0xFEDCBA9876543222L,0,0xFEDCBA987654B000L);port(m,"L",role,a);return 0;}
     case 2->{check(role.equals("cell"),"failure destination after false BOOL");args(a);port(m,"L",role,a);return 0;}
     case 3->{check(role.equals("error"),"error after destination");args(a);port(m,"L",role,a);return 0x80000001L;}
     case 4->{check(role.equals("map"),"mapping after error");args(a,0x80000001L);port(m,"L",role,a);m.effect64(0x105C5DE30L,0x123456789ABC3333L);return 0xFEDCBA98L;}
     default->throw new AssertionError("extra lower role "+role);
    }
   });
   OuterPorts forbidden=new OuterPorts((role,memory,a)->{throw new AssertionError("qualified free cannot fallback "+role);});
   Map<Long,Byte> beforeFactory=m.snapshot();Fc74Api238.Ports bound=Fc74FreeBinding251.bind(0x100000000L,m,lower,forbidden);
   check(m.trace.isEmpty()&&m.snapshot().equals(beforeFactory),"no factory heap snapshot");
   bound.call424e364(m,0x424FCE8L,0x800000000000A000L);
   bound.call424e364(m,0x424FD17L,0xFEDCBA987654B000L);
   check(cursor[0]==5,"first nonzero success and second failure four roles");
   complete(m,FRESH_TRACE,expected,"same bound fresh heap and mapped Cell0");
  }
  {
   Ram m=new Ram();m.seed64(0x5C5DE30L,0x4444);m.seed64(0x4000,0x1122334455667788L);m.seed8(0x3FFF,0xA5);m.seed8(0x4008,0x5A);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());RuntimeException marker=new RuntimeException("original mapping failure");int[] cursor={0};
   LowerCalls lower=new LowerCalls((role,a)->{
    int n=cursor[0]++;
    switch(n){
     case 0->{check(role.equals("free"),"throw free role");args(a,0x4444,0,0x9000);port(m,"L",role,a);return 0;}
     case 1->{check(role.equals("cell"),"throw destination role");args(a);port(m,"L",role,a);return 0x4000;}
     case 2->{check(role.equals("error"),"throw error role");args(a);port(m,"L",role,a);return 0xFFFFFFFFL;}
     case 3->{check(role.equals("map"),"throw map role");args(a,0xFFFFFFFFL);port(m,"L",role,a);throw marker;}
     default->throw new AssertionError("extra lower after map throw "+role);
    }
   });
   OuterPorts forbidden=new OuterPorts((role,memory,a)->{throw new AssertionError("qualified throw cannot fallback "+role);});
   Fc74Api238.Ports bound=Fc74FreeBinding251.bind(0,m,lower,forbidden);
   sameException(()->bound.call424e364(m,0x424FCE8L,0x9000),marker,"map original exception identity");
   check(cursor[0]==4,"exact four failure roles before map exception");
   complete(m,MAP_THROW_TRACE,expected,"mapping exception no destination write");
  }
 }

 private static void actualFc74Composition251(){
  {
   Ram m=new Ram();m.seed64(0x2043DA738L,0x8000000000001111L);m.seed64(0x2043DA420L,0x1111);m.seed64(0x205C5DE30L,0x1111);m.seed32(0x20542F328L,-1);m.seed8(0x20542F327L,0xA5);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x20542F328L,4,11);expectedWrite(expected,0x205C5DE30L,8,0x2222);expectedWrite(expected,0x2043DA420L,8,0xFEDCBA9876543333L);
   int[] outerCursor={0},lowerCursor={0};
   OuterPorts fallback=new OuterPorts((role,memory,a)->{
    check(memory==m,"actual failure original outer Memory");int n=outerCursor[0]++;
    switch(n){
     case 0->{check(role.equals("iat738"),"actual failure save role");args(a,0x424FC83L,0x8000000000001111L,(long)(int)0xCAFEBABEL);port(m,"P",role,a);return 0x80000011L;}
     case 1->{check(role.equals("e948"),"actual first setter");args(a,0x424FCB9L,-1L,-1L);port(m,"P",role,a);m.effect32(0x20542F328L,7);return 1;}
     case 2->{check(role.equals("e2ec"),"actual allocation role");args(a,0x424FCCCL,1,0x3C8);port(m,"P",role,a);m.effect32(0x20542F328L,9);return 0x7000;}
     case 3->{check(role.equals("e948"),"actual second setter");args(a,0x424FCF2L,9,0x7000);port(m,"P",role,a);m.effect32(0x20542F328L,11);m.effect64(0x205C5DE30L,0x2222);return 0;}
     case 4->{check(role.equals("e948"),"actual reset setter before free");args(a,0x424FD03L,11,0);port(m,"P",role,a);m.effect64(0x2043DA420L,0x8000000000002222L);return 0xFFFFFFFFL;}
     case 5->{check(role.equals("iat420"),"actual finish role");args(a,0x424FD21L,0xFEDCBA9876543333L,(long)(int)0x80000011L);port(m,"P",role,a);return 0;}
     default->throw new AssertionError("extra actual failure passive "+role);
    }
   });
   LowerCalls lower=new LowerCalls((role,a)->{
    check(lowerCursor[0]++==0&&role.equals("free"),"actual nonzero free BOOL skips mapping");args(a,0x2222,0,0x7000);port(m,"L",role,a);m.effect64(0x2043DA420L,0xFEDCBA9876543333L);return 0x80000000L;
   });
   Map<Long,Byte> beforeFactory=m.snapshot();Fc74Api238.Ports bound=Fc74FreeBinding251.bind(0x200000000L,m,lower,fallback);
   check(m.trace.isEmpty()&&m.snapshot().equals(beforeFactory),"actual binding factory no heap read");
   long result=Fc74Target424FC74.execute(m,bound,new Fc74Api238.Input(0x200000000L,(int)0xCAFEBABEL));
   check(result==0&&outerCursor[0]==6&&lowerCursor[0]==1,"actual failed second setter result0 and exact calls");
   complete(m,ACTUAL_FAILURE_TRACE,expected,"actual Fc74 FCE8 nonnull new edge");
  }
  {
   Ram m=new Ram();m.seed64(0x3043DA738L,0xFEDCBA9876544444L);m.seed64(0x3043DA420L,0x2222);m.seed32(0x30542F328L,-1);m.seed8(0x30542F327L,0xA5);
   Map<Long,Byte> expected=new HashMap<>(m.snapshot());expectedWrite(expected,0x3043DA420L,8,0x123456789ABC5555L);
   int[] outerCursor={0};
   OuterPorts fallback=new OuterPorts((role,memory,a)->{
    check(memory==m,"actual normal original outer Memory");int n=outerCursor[0]++;
    switch(n){
     case 0->{check(role.equals("iat738"),"normal save role");args(a,0x424FC83L,0xFEDCBA9876544444L,0x12345678);port(m,"P",role,a);return 0xFFFFFFFEL;}
     case 1->{check(role.equals("e948"),"normal first setter");args(a,0x424FCB9L,-1L,-1L);port(m,"P",role,a);return 1;}
     case 2->{check(role.equals("e2ec"),"normal allocate role");args(a,0x424FCCCL,1,0x3C8);port(m,"P",role,a);return 0x8000000000008000L;}
     case 3->{check(role.equals("e948"),"normal second setter");args(a,0x424FCF2L,-1L,0x8000000000008000L);port(m,"P",role,a);return 1;}
     case 4->{check(role.equals("f8new"),"normal exact four-arg overload");args(a,0x424FD10L,0x8000000000008000L,0xFEDCBA9876548FD0L);port(m,"P",role,a);m.effect64(0x3043DA420L,0x123456789ABC5555L);return 0;}
     case 5->{check(role.equals("iat420"),"normal restore role");args(a,0x424FD21L,0x123456789ABC5555L,-2L);port(m,"P",role,a);return 0;}
     default->throw new AssertionError("extra actual normal passive "+role);
    }
   });
   LowerCalls lower=new LowerCalls((role,a)->{throw new AssertionError("actual FD17null must not reach lower "+role);});
   Fc74Api238.Ports bound=Fc74FreeBinding251.bind(0x300000000L,m,lower,fallback);
   long result=Fc74Target424FC74.execute(m,bound,new Fc74Api238.Input(0x300000000L,0x12345678),0xFEDCBA9876549000L);
   check(result==0x8000000000008000L&&outerCursor[0]==6,"normal original full64 selected block");
   complete(m,ACTUAL_NORMAL_TRACE,expected,"actual four-arg current Entry and FD17null");
  }
 }

 private static final List<String> PROTOCOL_TRACE=List.of(
  "P:iat738:1111:fedcba9876543210:ffffffff80000001",
  "P:e900:2222:ffffffffffffffff",
  "P:e948:3333:ffffffff80000000:8000000000000001",
  "P:e2ec:4444:ffffffffffffffff:3c8",
  "P:f8old:5555:fedcba9876541111",
  "P:f8new:6666:8000000000000002:fedcba9876543210",
  "P:iat420:7777:8000000000000003:ffffffffabcdef01",
  "P:free:424fce8:8000000000000004",
  "P:free:424fd0b:fedcba9876542222",
  "P:free:424fd17:7000",
  "P:f8new:8888:0:ffffffffffffffff");
 private static final List<String> FRESH_TRACE=List.of(
  "R64:105c5de30:8000000000000011",
  "L:free:8000000000000011:0:800000000000a000",
  "E64:105c5de30:fedcba9876543222",
  "R64:105c5de30:fedcba9876543222",
  "L:free:fedcba9876543222:0:fedcba987654b000",
  "L:cell",
  "L:error",
  "L:map:80000001",
  "E64:105c5de30:123456789abc3333",
  "W32:0:fedcba98");
 private static final List<String> MAP_THROW_TRACE=List.of(
  "R64:5c5de30:4444",
  "L:free:4444:0:9000",
  "L:cell",
  "L:error",
  "L:map:ffffffff");
 private static final List<String> ACTUAL_FAILURE_TRACE=List.of(
  "R64:2043da738:8000000000001111",
  "P:iat738:424fc83:8000000000001111:ffffffffcafebabe",
  "R32:20542f328:ffffffff",
  "P:e948:424fcb9:ffffffffffffffff:ffffffffffffffff",
  "E32:20542f328:7",
  "P:e2ec:424fccc:1:3c8",
  "E32:20542f328:9",
  "R32:20542f328:9",
  "P:e948:424fcf2:9:7000",
  "E32:20542f328:b",
  "E64:205c5de30:2222",
  "R32:20542f328:b",
  "P:e948:424fd03:b:0",
  "E64:2043da420:8000000000002222",
  "R64:205c5de30:2222",
  "L:free:2222:0:7000",
  "E64:2043da420:fedcba9876543333",
  "R64:2043da420:fedcba9876543333",
  "P:iat420:424fd21:fedcba9876543333:ffffffff80000011");
 private static final List<String> ACTUAL_NORMAL_TRACE=List.of(
  "R64:3043da738:fedcba9876544444",
  "P:iat738:424fc83:fedcba9876544444:12345678",
  "R32:30542f328:ffffffff",
  "P:e948:424fcb9:ffffffffffffffff:ffffffffffffffff",
  "P:e2ec:424fccc:1:3c8",
  "R32:30542f328:ffffffff",
  "P:e948:424fcf2:ffffffffffffffff:8000000000008000",
  "P:f8new:424fd10:8000000000008000:fedcba9876548fd0",
  "E64:3043da420:123456789abc5555",
  "R64:3043da420:123456789abc5555",
  "P:iat420:424fd21:123456789abc5555:fffffffffffffffe");
 public static void main(String[] args){protocolCountercases251();actualFc74Composition251();check(groups==5&&events==56&&ramEvents==14&&portEvents==33&&opaqueEffects==9,"all current ordered event totals");System.out.println("FC74FREE251_PASS groups="+groups+" orderedEvents="+events+" RAM="+ramEvents+" Ports="+portEvents+" OpaqueEffects="+opaqueEffects+" mixedChecks="+checks+" Native=0 Game=0");}
}
