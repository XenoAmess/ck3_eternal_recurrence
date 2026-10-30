package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
class RootRuntimeOrdinaryStorageGuardTest {
 @TempDir Path directory;
 private final List<RootRuntimeStorageGuard> guards=new ArrayList<>();
 @AfterEach void closeGuards()throws IOException{for(int i=guards.size()-1;i>=0;i--)guards.get(i).close();}
 private final class Fixture {
  final Path state,artifacts,continuity; final RootApplicationConfiguration app;
  Fixture()throws IOException{
   state=Files.createDirectory(directory.resolve("state"));artifacts=Files.createDirectory(directory.resolve("artifacts"));continuity=Files.createDirectory(state.resolve("continuity"));
   Path input=Files.writeString(directory.resolve("configuration-input.json"),"{}");
   var ref=new ExactRef(input.toString(),Files.size(input),DriverJson.sha256(Files.readAllBytes(input)));
   String machine=WindowsJobProcess.currentMachineId();
   app=new RootApplicationConfiguration(machine,HostMode.COMPLETE_MIGRATION,Instant.now().plusSeconds(3600),ref,new WriterContracts.Layout(continuity.resolve("snapshot.json"),ref,machine),List.of(ref),artifacts,1L<<20);
  }
  RootRuntimeStorageGuard guard(long cap)throws IOException{var g=RootRuntimeStorageGuard.ordinary(app,()->{throw new IOException("no ContinuityWriter before actual bootstrap");},List.of(state,continuity,state,artifacts),cap,Clock.systemUTC());guards.add(g);return g;}
  void init(RootRuntimeStorageGuard g)throws IOException{g.requireInitialization(app.ledger().lock(),List.of(state,continuity,artifacts));}
 }
@Test void test1_cap1MiB_init_writeCreateNew() throws IOException {
  Fixture f = new Fixture();
  var g = f.guard(1024L * 1024L);
  f.init(g);
  var target = f.state.resolve("a.bin");
  var plan = new StorageWriteGuard.WritePlan(f.app.ledger().lock(), List.of(new StorageWriteGuard.FileCreate(target, 8192L)));
  g.write(plan, () -> Files.write(target, new byte[8192], StandardOpenOption.CREATE_NEW));
  assertEquals(8192, Files.size(target));
  assertEquals(0, g.accounting().unresolvedWrites());
  assertEquals(2, g.accounting().roots().size());
  assertEquals(RootRuntimeStorageGuard.Status.ADMITTED, g.accounting().status());
}
@Test void test2_cap64KiB_init_rejectsBeforeCallback() throws IOException {
  Fixture f = new Fixture();
  Files.write(f.state.resolve("a"), new byte[48 * 1024]);
  Files.write(f.artifacts.resolve("b"), new byte[48 * 1024]);
  var g = f.guard(64L * 1024L);
  assertThrows(IOException.class, () -> f.init(g));
  assertTrue(Files.exists(f.state.resolve("a"))); // a.bin/a existed BEFORE guard
  assertTrue(g.accounting().roots().stream().mapToLong(r->r.measuredChargedUpperBytes()).sum()>64L*1024L);
}
@Test void test3_cap64KiB_init_attempt128KiB_FileCreate_IOException() throws IOException {
  Fixture f = new Fixture();
  var g = f.guard(64L * 1024L);
  f.init(g);
  var target = f.state.resolve("x.bin");
  var plan = new StorageWriteGuard.WritePlan(f.app.ledger().lock(), List.of(new StorageWriteGuard.FileCreate(target, 128L * 1024L)));
  var flag = new AtomicBoolean(false);
  assertThrows(IOException.class, () -> g.write(plan, () -> { flag.set(true); return Files.createFile(target); }));
  assertFalse(flag.get());
  assertFalse(Files.exists(target));
}
@Test void test4_cap1MiB_init_partialWrite_thenUncertain() throws IOException {
  Fixture f = new Fixture();
  var g = f.guard(1024L * 1024L);
  f.init(g);
  var target = f.state.resolve("y.bin");
  var plan = new StorageWriteGuard.WritePlan(f.app.ledger().lock(), List.of(new StorageWriteGuard.FileCreate(target, 32L)));
  var flag = new AtomicBoolean(false);
  assertThrows(IOException.class, () -> g.write(plan, () -> { Files.write(target, new byte[4], StandardOpenOption.CREATE_NEW); flag.set(true); throw new IOException("fail"); }));
  assertEquals(RootRuntimeStorageGuard.Status.UNKNOWN_WRITE, g.accounting().status());
  assertTrue(Files.exists(target));
  assertTrue(g.accounting().unresolvedWrites() > 0);
  var target2 = f.state.resolve("z.bin");
  var plan2 = new StorageWriteGuard.WritePlan(f.app.ledger().lock(), List.of(new StorageWriteGuard.FileCreate(target2, 32L)));
  var flag2 = new AtomicBoolean(false);
  assertThrows(IOException.class, () -> g.write(plan2, () -> { flag2.set(true); return null; }));
  assertFalse(flag2.get());
}
@Test void test5_cap1MiB_init_secondGuard_lockConflict() throws IOException {
  Fixture f = new Fixture();
  var g1 = f.guard(1024L * 1024L);
  f.init(g1);
  assertEquals(RootRuntimeStorageGuard.Status.ADMITTED, g1.accounting().status());
  var g2 = f.guard(1024L * 1024L);
  assertThrows(IOException.class, () -> f.init(g2));
  assertEquals(RootRuntimeStorageGuard.Status.ADMITTED, g1.accounting().status());
}
    @Test void sameWriterCannotAcquireAnotherOwnerByChangingDefaultRoot() throws IOException {
        Fixture f=new Fixture();var first=f.guard(1L<<20);f.init(first);
        var second=RootRuntimeStorageGuard.ordinary(f.app,()->{throw new IOException("not constructed");},
                List.of(f.artifacts,f.state),1L<<20,Clock.systemUTC());guards.add(second);
        assertThrows(IOException.class,()->f.init(second));
        assertEquals(RootRuntimeStorageGuard.Status.ADMITTED,first.accounting().status());
    }
    @Test void ordinaryClosedGuardRejectsBeforePhysicalCallback() throws Exception {
        Fixture f=new Fixture();var guard=f.guard(1L<<20);f.init(guard);guard.close();
        assertNoPhysicalCallback(f,guard,"closed.bin");
    }
    @Test void ordinaryReleasedAllocationLockRejectsBeforePhysicalCallback() throws Exception {
        Fixture f=new Fixture();var guard=f.guard(1L<<20);f.init(guard);
        var field=RootRuntimeStorageGuard.class.getDeclaredField("allocationLock");field.setAccessible(true);
        ((java.nio.channels.FileLock)field.get(guard)).release();
        assertNoPhysicalCallback(f,guard,"released.bin");
    }
    @Test void ordinaryClosedAllocationChannelRejectsBeforePhysicalCallback() throws Exception {
        Fixture f=new Fixture();var guard=f.guard(1L<<20);f.init(guard);
        var field=RootRuntimeStorageGuard.class.getDeclaredField("allocationChannel");field.setAccessible(true);
        ((java.nio.channels.FileChannel)field.get(guard)).close();
        try {assertNoPhysicalCallback(f,guard,"channel.bin");}
        finally {
            guards.remove(guard);
            try {guard.close();}catch(java.nio.channels.ClosedChannelException expectedFromClosedTestChannel) { }
        }
    }
    private static void assertNoPhysicalCallback(Fixture f,RootRuntimeStorageGuard guard,String name) throws IOException {
        Path target=f.state.resolve(name);var called=new AtomicBoolean();
        var plan=new StorageWriteGuard.WritePlan(f.app.ledger().lock(),List.of(new StorageWriteGuard.FileCreate(target,1)));
        assertThrows(IOException.class,()->guard.write(plan,()->{called.set(true);return Files.write(target,new byte[]{1},StandardOpenOption.CREATE_NEW);}));
        assertFalse(called.get());assertFalse(Files.exists(target));
    }
@Test void ordinaryGenesisNoWriter() throws Exception {
    Path state = directory.resolve("state"); Files.createDirectories(state);
    Path cont = directory.resolve("continuity"); Files.createDirectories(cont);
    Path art = directory.resolve("artifacts"); Files.createDirectories(art);
    Path snap = cont.resolve("snapshot.json"); Path anc = cont.resolve("anchor.json");
    var plan = new org.xar.ck3.control.continuity.FreshContinuityGenesis.Plan(WindowsJobProcess.currentMachineId(), 1, 10958);
    byte[] req = org.xar.ck3.control.continuity.FreshContinuityGenesis.encode(plan); Path reqP = directory.resolve("fresh-genesis-request.json"); Files.write(reqP, req);
    var ref = new ExactRef(reqP.toString(), req.length, DriverJson.sha256(req));
    var init = new WriterContracts.InitialLayout(snap, anc, WindowsJobProcess.currentMachineId());
    var calls = new java.util.concurrent.atomic.AtomicInteger(0);
    RootRuntimeStorageGuard.WriterAccess wa = () -> { calls.incrementAndGet(); throw new IOException("writer not constructed"); };
    var guard = RootRuntimeStorageGuard.ordinary(init, art, wa, List.of(state, cont, art), 1L << 20, Clock.systemUTC());
    guards.add(guard);
    assertFalse(Files.exists(snap)); assertFalse(Files.exists(anc));
    var res = ContinuityWriter.initializeFresh(plan, ref, init, guard);
    assertEquals(0, res.initialHead().state().sequence()); assertEquals("AWAITING_INITIAL_ENTRY", res.initialHead().state().status().name());
    assertArrayEquals(Files.readAllBytes(anc), Files.readAllBytes(snap)); assertEquals(anc.toString(), res.layout().anchor().path().toString());
    assertEquals(0, calls.get());
    var rd = ContinuityWriter.readFreshInitialization(plan, ref, init);
    assertEquals(0, rd.initialHead().state().sequence());
    byte[] ab = Files.readAllBytes(anc);
    assertThrows(IOException.class, () -> ContinuityWriter.initializeFresh(plan, ref, init, guard));
    assertArrayEquals(ab, Files.readAllBytes(anc)); assertEquals(0, calls.get());
}
}
