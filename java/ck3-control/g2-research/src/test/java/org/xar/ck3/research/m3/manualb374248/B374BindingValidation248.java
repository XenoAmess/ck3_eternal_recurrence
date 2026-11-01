package org.xar.ck3.research.m3.manualb374248;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;
import org.xar.ck3.research.m3.b374248.Fa90B374Binding248;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
public final class B374BindingValidation248 {
 private B374BindingValidation248() { }
 private static int checks,groups,events,ramEvents,portEvents,opaqueEffects;
 private static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
 private static String h(long v){return Long.toUnsignedString(v,16);}
 private static String rw(String k,long a,long v){return k+":"+h(a)+":"+h(v);}
 private static final class Ram implements F8a8Api242.Memory {
  final Map<Long,Byte> bytes=new HashMap<>(); final List<String> trace=new ArrayList<>();
  private long raw(long a,int w){long v=0;for(int i=0;i<w;i++){Byte b=bytes.get(a+i);if(b==null)throw new AssertionError("unmapped "+h(a+i));v|=(b.longValue()&255L)<<(8*i);}return v;}
  private void store(long a,int w,long v){for(int i=0;i<w;i++)bytes.put(a+i,(byte)(v>>>(8*i)));}
  void seed8(long a,int v){check((v&~255)==0,"seed8");store(a,1,v);}
  void seed32(long a,int v){store(a,4,Integer.toUnsignedLong(v));}
  void seed64(long a,long v){store(a,8,v);}
  void effect32(long a,int v){trace.add(rw("E32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  void effect64(long a,long v){trace.add(rw("E64",a,v));store(a,8,v);}
  Map<Long,Byte> snapshot(){return Map.copyOf(bytes);}
  @Override public long readPointer(long a){long v=raw(a,8);trace.add(rw("R64",a,v));return v;}
  @Override public int readInt32(long a){long v=raw(a,4);trace.add(rw("R32",a,v));return (int)v;}
  @Override public void writeInt64(long a,long v){trace.add(rw("W64",a,v));store(a,8,v);}
  @Override public void writeInt32(long a,int v){trace.add(rw("W32",a,Integer.toUnsignedLong(v)));store(a,4,Integer.toUnsignedLong(v));}
  @Override public void writeInt16(long a,int v){trace.add(rw("W16",a,v&65535L));store(a,2,v);}
 }
 private abstract static class CallsBase implements B374Inputs.Calls {
  @Override public void call424E364(long x){throw new AssertionError("unexpected normal E364 "+h(x));}
  @Override public void call42552D0(long x){throw new AssertionError("unexpected 52D0 "+h(x));}
  @Override public void call4255910(long x){throw new AssertionError("unexpected 5910 "+h(x));}
  @Override public void call425689C(long x){throw new AssertionError("unexpected 689C "+h(x));}
  @Override public void tail424E364(long x){throw new AssertionError("unexpected tail E364 "+h(x));}
 }
 private abstract static class PortsBase implements Fa90Api245.Ports {
  @Override public void call42568fc(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){throw new AssertionError("unexpected first");}
  @Override public void call42566fc(F8a8Api242.Memory m,long site,long rcx,long rax){throw new AssertionError("unexpected second fallback");}
  @Override public void call4256670(F8a8Api242.Memory m,long site,long rcx,OptionalLong rdx,OptionalLong rax){throw new AssertionError("unexpected third");}
 }
 private static void expectedWrite(Map<Long,Byte> m,long a,int w,long v){for(int i=0;i<w;i++)m.put(a+i,(byte)(v>>>(8*i)));}
 private static void opaque(Ram m,String name,long arg){m.trace.add("C:"+name+":"+h(arg));}
 private static void sameException(Runnable work,RuntimeException marker,String label){try{work.run();}catch(RuntimeException x){check(x==marker,label);return;}throw new AssertionError("no original exception "+label);}
 private static void rejected(Runnable work,String label){try{work.run();}catch(RuntimeException x){checks++;return;}throw new AssertionError("not rejected "+label);}
 private static void complete(Ram m,List<String> expected,Map<Long,Byte> finalBytes,String label){check(m.trace.equals(expected),label+" expected="+expected+" actual="+m.trace);check(m.snapshot().equals(finalBytes),label+" finalbytes");groups++;events+=m.trace.size();for(String event:m.trace){if(event.startsWith("R")||event.startsWith("W"))ramEvents++;else if(event.startsWith("E"))opaqueEffects++;else portEvents++;}}
 private static void directProtocol248(){
  final long base=0x100000000L;
  Ram m=new Ram();
  m.seed64(0x10F8,0x10542F220L);m.seed64(0x1100,0x6000);m.seed32(0x6000,0);
  m.seed64(0x1108,0x70FE);m.seed64(0x1110,0x8080);m.seed64(0x1118,0x9080);m.seed64(0x1120,0xA000);
  for(int i=0;i<6;i++){m.seed64(0x1028L+0x20L*i,0x10542F498L);m.seed64(0x1020L+0x20L*i,0);}
  m.seed8(0x10F7,0xAB);m.seed8(0x1128,0xCD);m.seed8(0x6004,0xEF);
  Map<Long,Byte> expected=new HashMap<>(m.snapshot());
  expectedWrite(expected,0x1110,8,0x8180);expectedWrite(expected,0x1120,8,0xA100);
  int[] normal={0},late={0},tail={0};
  B374Inputs.Calls child=new CallsBase(){
   @Override public void call424E364(long x){
    long[] args={0x7000,0x8100,0x9000,0x6000};
    check(normal[0]<args.length&&x==args[normal[0]],"direct original normal child args");
    normal[0]++;opaque(m,"normal",x);
    if(normal[0]==1){m.effect64(0x1110,0x8180);m.effect64(0x1120,0xA100);}
   }
   @Override public void call425689C(long x){check(x==0xA100,"direct fresh120 child");late[0]++;opaque(m,"689c",x);}
   @Override public void tail424E364(long x){check(x==0x1000,"direct tail object");tail[0]++;opaque(m,"tail",x);}
  };
  Map<Long,Byte> factoryBytes=new HashMap<>(m.snapshot());
  Fa90Api245.Ports bound=Fa90B374Binding248.bind(base,m,child,new PortsBase(){});
  check(m.trace.isEmpty()&&m.snapshot().equals(factoryBytes),"factory zero effect");
  bound.call42566fc(m,0x424FAD3L,0x1000,0xFEDCBA9876543210L);
  check(normal[0]==4&&late[0]==1&&tail[0]==1,"direct exact mature callback counts");
  complete(m,DIRECT_TRACE,expected,"direct fresh sibling view");
  Ram throwing=new Ram();throwing.seed64(0x20F8,0x10542F220L);throwing.seed64(0x2100,0);throwing.seed64(0x2120,0xABCD);
  Map<Long,Byte> exceptionBytes=new HashMap<>(throwing.snapshot());
  RuntimeException marker=new RuntimeException("original mature child");int[] exceptionCalls={0};
  B374Inputs.Calls exceptionChild=new CallsBase(){
   @Override public void call425689C(long x){check(x==0xABCD,"throw child RCX");exceptionCalls[0]++;opaque(throwing,"689c",x);throw marker;}
  };
  Fa90Api245.Ports exceptionBound=Fa90B374Binding248.bind(base,throwing,exceptionChild,new PortsBase(){});
  sameException(()->exceptionBound.call42566fc(throwing,0x424FAD3L,0x2000,Long.MIN_VALUE),marker,"child original exception");
  check(exceptionCalls[0]==1,"exception child once");
  complete(throwing,THROW_TRACE,exceptionBytes,"child exception exact prefix");
 }
 private static void actualFa90Chain248(){
  final long base=0x200000000L;
  Ram m=new Ram();
  m.seed64(0x1090,0x2000);m.seed64(0x205C5DCD8L,0x4000);m.seed32(0x3010,0);
  m.seed64(0x30F8,0x5000);m.seed64(0x30E0,0x6000);m.seed32(0x6000,0);
  m.seed64(0x30F0,0x7000);m.seed32(0x7000,0);m.seed64(0x30E8,0);
  m.seed64(0x3100,0);m.seed64(0x3120,0x8000);
  for(int i=0;i<6;i++){m.seed64(0x3028L+0x20L*i,0x20542F498L);m.seed64(0x3020L+0x20L*i,0);}
  m.seed8(0x108F,0xAB);m.seed8(0x1098,0xCD);m.seed8(0x30DF,0xEF);
  Map<Long,Byte> expected=new HashMap<>(m.snapshot());
  expectedWrite(expected,0x1090,8,0xDEAD);expectedWrite(expected,0x30F8,8,0x5100);
  int[] normals={0},branch={0},late={0},tail={0},first={0},third={0};
  B374Inputs.Calls child=new CallsBase(){
   @Override public void call424E364(long x){
    long[] args={0x7000,0x6000,0x5100};
    check(normals[0]<args.length&&x==args[normals[0]],"actual original normal args");
    normals[0]++;opaque(m,"normal",x);if(normals[0]==1)m.effect64(0x30F8,0x5100);
   }
   @Override public void call42552D0(long x){check(x==0x5100,"actual view freshf8");branch[0]++;opaque(m,"52d0",x);}
   @Override public void call425689C(long x){check(x==0x8000,"actual late child");late[0]++;opaque(m,"689c",x);}
   @Override public void tail424E364(long x){check(x==0x3000,"actual tail object");tail[0]++;opaque(m,"tail",x);}
  };
  PortsBase fallback=new PortsBase(){
   @Override public void call42568fc(F8a8Api242.Memory mem,long site,long rcx,long rdx,long rax){
    check(mem==m,"actual first same RAM");check(site==0x424FAACL&&rcx==0x2000&&rdx==0xDEAD&&rax==0xFEDCBA9876543210L,"actual first knownargs");
    first[0]++;m.trace.add("P:first:424faac:2000:dead:fedcba9876543210");m.effect64(0x1090,0x3000);
   }
   @Override public void call4256670(F8a8Api242.Memory mem,long site,long rcx,OptionalLong rdx,OptionalLong rax){
    check(mem==m,"actual third same RAM");check(site==0x424FAE7L&&rcx==0xDEAD,"actual third knownRCX");
    check(rdx!=null&&rax!=null&&!rdx.isPresent()&&!rax.isPresent(),"actual after second void unknown not zero");
    third[0]++;m.trace.add("P:third:424fae7:dead:empty:empty");
   }
  };
  Fa90Api245.Ports bound=Fa90B374Binding248.bind(base,m,child,fallback);
  Fa90Target424FA90.execute(m,bound,new Fa90Api245.Input(base,0x1000,0xDEAD,0xFEDCBA9876543210L));
  check(first[0]==1&&third[0]==1,"actual passive once");
  check(normals[0]==3&&branch[0]==1&&late[0]==1&&tail[0]==1,"actual mature once exact child counts");
  complete(m,CHAIN_TRACE,expected,"actual Fa90 new edge");
 }
 private static final List<String> DIRECT_TRACE=List.of(
  "R64:10f8:10542f220",
  "R64:1100:6000",
  "R32:6000:0",
  "R64:1108:70fe",
  "C:normal:7000",
  "E64:1110:8180",
  "E64:1120:a100",
  "R64:1110:8180",
  "C:normal:8100",
  "R64:1118:9080",
  "C:normal:9000",
  "R64:1100:6000",
  "C:normal:6000",
  "R64:1120:a100",
  "C:689c:a100",
  "R64:1028:10542f498",
  "R64:1020:0",
  "R64:1048:10542f498",
  "R64:1040:0",
  "R64:1068:10542f498",
  "R64:1060:0",
  "R64:1088:10542f498",
  "R64:1080:0",
  "R64:10a8:10542f498",
  "R64:10a0:0",
  "R64:10c8:10542f498",
  "R64:10c0:0",
  "C:tail:1000");
 private static final List<String> THROW_TRACE=List.of(
  "R64:20f8:10542f220",
  "R64:2100:0",
  "R64:2120:abcd",
  "C:689c:abcd");
 private static final List<String> CHAIN_TRACE=List.of(
  "R64:1090:2000",
  "P:first:424faac:2000:dead:fedcba9876543210",
  "E64:1090:3000",
  "R64:1090:3000",
  "R64:205c5dcd8:4000",
  "R32:3010:0",
  "R64:30f8:5000",
  "R64:30e0:6000",
  "R32:6000:0",
  "R64:30f0:7000",
  "R32:7000:0",
  "C:normal:7000",
  "E64:30f8:5100",
  "R64:30f8:5100",
  "C:52d0:5100",
  "R64:30e8:0",
  "R64:30e0:6000",
  "C:normal:6000",
  "R64:30f8:5100",
  "C:normal:5100",
  "R64:3100:0",
  "R64:3120:8000",
  "C:689c:8000",
  "R64:3028:20542f498",
  "R64:3020:0",
  "R64:3048:20542f498",
  "R64:3040:0",
  "R64:3068:20542f498",
  "R64:3060:0",
  "R64:3088:20542f498",
  "R64:3080:0",
  "R64:30a8:20542f498",
  "R64:30a0:0",
  "R64:30c8:20542f498",
  "R64:30c0:0",
  "C:tail:3000",
  "W64:1090:dead",
  "P:third:424fae7:dead:empty:empty");
 private static void protocol248(){
  Ram captured=new Ram(),foreign=new Ram();
  CallsBase forbiddenChild=new CallsBase(){};
  PortsBase forbiddenFallback=new PortsBase(){};
  rejected(()->Fa90B374Binding248.bind(0,null,forbiddenChild,forbiddenFallback),"null memory");
  rejected(()->Fa90B374Binding248.bind(0,captured,null,forbiddenFallback),"null child");
  rejected(()->Fa90B374Binding248.bind(0,captured,forbiddenChild,null),"null fallback");
  Fa90Api245.Ports guarded=Fa90B374Binding248.bind(0,captured,forbiddenChild,forbiddenFallback);
  rejected(()->guarded.call42566fc(foreign,0x424FAD3L,0,0),"active foreign");
  rejected(()->guarded.call42566fc(captured,0x424FAD2L,0,0),"active site");
  check(captured.trace.isEmpty()&&foreign.trace.isEmpty(),"active rejects zero IO");
  check(captured.bytes.isEmpty()&&foreign.bytes.isEmpty(),"active rejects zero bytes");
  OptionalLong knownZero=OptionalLong.of(0),unknown=OptionalLong.empty();
  RuntimeException marker=new RuntimeException("opaque passive marker");
  int[] counts={0,0};
  PortsBase fallback=new PortsBase(){
   @Override public void call42568fc(F8a8Api242.Memory m,long site,long rcx,long rdx,long rax){
    check(m==foreign,"passive first same received memory");
    check(site==0xFEDCBA9876543210L&&rcx==0x8000000000000001L&&rdx==-1L&&rax==0x123456789ABCDEF0L,"passive first full bits");
    counts[0]++;captured.trace.add("P:first:fedcba9876543210:8000000000000001:ffffffffffffffff:123456789abcdef0");
   }
   @Override public void call4256670(F8a8Api242.Memory m,long site,long rcx,OptionalLong rdx,OptionalLong rax){
    check(m==foreign,"passive third same received memory");counts[1]++;
    if(counts[1]==1){
     check(site==0x123456789ABCDEF0L&&rcx==0xFEDCBA9876543210L,"passive third bits");
     check(rdx==knownZero&&rax==unknown,"passive optional identity known0/unknown");
     captured.trace.add("P:third:123456789abcdef0:fedcba9876543210:known0:empty");
    }else{
     check(counts[1]==2&&site==-1L&&rcx==Long.MIN_VALUE,"passive third throwing args");
     check(rdx==unknown&&rax==knownZero,"passive throwing optional identity");
     captured.trace.add("P:thirdThrow:ffffffffffffffff:8000000000000000:empty:known0");throw marker;
    }
   }
  };
  Fa90Api245.Ports bound=Fa90B374Binding248.bind(0,captured,forbiddenChild,fallback);
  Map<Long,Byte> finalBytes=new HashMap<>(captured.snapshot());
  bound.call42568fc(foreign,0xFEDCBA9876543210L,0x8000000000000001L,-1L,0x123456789ABCDEF0L);
  bound.call4256670(foreign,0x123456789ABCDEF0L,0xFEDCBA9876543210L,knownZero,unknown);
  sameException(()->bound.call4256670(foreign,-1L,Long.MIN_VALUE,unknown,knownZero),marker,"passive exception original identity");
  check(counts[0]==1&&counts[1]==2,"passives exact once each");
  check(foreign.trace.isEmpty()&&foreign.bytes.isEmpty(),"passive zero foreign RAM");
  complete(captured,List.of("P:first:fedcba9876543210:8000000000000001:ffffffffffffffff:123456789abcdef0","P:third:123456789abcdef0:fedcba9876543210:known0:empty","P:thirdThrow:ffffffffffffffff:8000000000000000:empty:known0"),finalBytes,"guards/passive exact protocol");
 }
 public static void main(String[] args){directProtocol248();protocol248();actualFa90Chain248();check(groups==4&&events==73&&ramEvents==51&&portEvents==18&&opaqueEffects==4,"all actual trace counters");System.out.println("B374248_PASS groups="+groups+" orderedEvents="+events+" mixedChecks="+checks+" RAM="+ramEvents+" Ports="+portEvents+" OpaqueEffects="+opaqueEffects+" Native=0 Game=0");}
}
