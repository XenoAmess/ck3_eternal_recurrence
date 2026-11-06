package org.xar.ck3.control.application.planning.governance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Public state-producer and real temporary bytes only. Session, FileIdentity and archive ports are unissued
 * software DATA fixtures, not a physical writer/Win32 pin/Root/Native qualification or a cadence commit. */
final class FeastStateImmutableHead77Test {
    @TempDir Path directory;

    @Test void emittedHeadSurvivesLaterMutableHeadWhileConflictsStillRefuse() throws Exception {
        var good=new Fixture(directory.resolve("good"));
        var known=assertInstanceOf(Known.class,good.collector.state(good.request));
        assertNotNull(good.copy);assertTrue(known.originals().contains(good.copy));
        ExactRef old=good.headRef;
        assertFalse(known.originals().contains(old),"mutable head must not be emitted as historical evidence");
        byte[] original=Files.readAllBytes(Path.of(old.path()));
        assertArrayEquals(original,Files.readAllBytes(Path.of(good.copy.path())));
        assertEquals(old.bytes(),good.copy.bytes());assertEquals(old.sha256(),good.copy.sha256());
        assertEquals(1,good.archiveScopes);assertEquals(1,good.captures);assertEquals(1,good.reads);
        assertTrue(good.verifications>=2);assertFalse(good.bound);
        good.advance();
        assertThrows(IOException.class,()->good.verify(old));
        good.verify(good.copy);
        assertArrayEquals(original,Files.readAllBytes(Path.of(good.copy.path())));

        var stale=new Fixture(directory.resolve("stale"));
        stale.staleFinance=true;
        assertInstanceOf(Unavailable.class,stale.collector.state(stale.request));
        assertNull(stale.copy,"conflicting current writer point must refuse before preservation");
        assertEquals(0,stale.archiveScopes);

        var during=new Fixture(directory.resolve("during"));during.changeDuringArchive=true;
        assertInstanceOf(Unavailable.class,during.collector.state(during.request));
        assertEquals(1,during.archiveScopes);assertFalse(during.bound);
        assertNotNull(during.copy);during.verify(during.copy);
        System.out.println("FEAST_HEAD_DATA_PASS immutableEvidence=true mutableLaterRejected=true "
                +"staleHeadRefused=true midArchiveHeadRefused=true archiveScopeClosed=true NativeCalls=0 privateRoot=false");
    }

    private static final class Fixture {
        final PlanningRequest request=GovernanceFixtures.request();
        final Path root;
        Head head;
        ExactRef headRef,firstHead,copy;
        boolean staleFinance,changeDuringArchive,bound;
        int archiveScopes,captures,reads,verifications;
        final Session session;
        final ActionPorts.OutcomeArchive archive;
        final FeastObservationCollector collector;
        Fixture(Path root)throws Exception {
            this.root=root;Files.createDirectories(root);advance();firstHead=headRef;
            session=(Session)Proxy.newProxyInstance(Session.class.getClassLoader(),new Class<?>[]{Session.class},(proxy,method,args)->switch(method.getName()) {
                case "head" -> head;
                case "persistedHead" -> {if(staleFinance)yield new ExactRef(root.resolve("different.json").toString(),headRef.bytes(),headRef.sha256());yield headRef;}
                case "requireWriter" -> {assertEquals(root.resolve("writer.lock"),args[0]);yield null;}
                case "capturePin" -> {
                    captures++;ExactRef ref=(ExactRef)args[0];verify(ref);
                    yield new Pin(ref,new FileIdentity("1","2","3",Instant.EPOCH.toString(),ref.bytes()));
                }
                case "verifyPin" -> {verifications++;verify(((Pin)args[0]).reference());yield null;}
                case "readPinned" -> {reads++;ExactRef ref=((Pin)args[0]).reference();verify(ref);yield Files.readAllBytes(Path.of(ref.path()));}
                default -> throw new AssertionError("unissued DATA Session forbids "+method.getName());
            });
            archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->switch(method.getName()) {
                case "inSession" -> {
                    assertSame(session,args[0]);assertFalse(bound);bound=true;archiveScopes++;
                    try {
                        @SuppressWarnings("unchecked") var work=(Function<ActionPorts.OutcomeArchive,Object>)args[1];
                        yield work.apply((ActionPorts.OutcomeArchive)proxy);
                    } finally {bound=false;}
                }
                case "preserveMaterial" -> {
                    assertTrue(bound);byte[] bytes=((RawJson)args[0]).bytes();
                    Path target=root.resolve("immutable-head.json");Files.write(target,bytes);copy=reference(target);
                    if(changeDuringArchive)advance();yield copy;
                }
                default -> throw new AssertionError("unissued DATA archive forbids "+method.getName());
            });
            byte[] body="{\"schema\":\"xar.ck3.activity-feast-stage5-start-private.v1\",\"pending\":null,\"resolved\":null}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            var document=new FinanceStatePort.Document(FinanceStatePort.Domain.FEAST,new ExactRef(root.resolve("feast.json").toString(),body.length,ActionCodec.sha256(body)),body);
            var states=new FinanceStatePort(new FinanceStatePort.SourcePort() {
                public FinanceStatePort.Read readUnderOriginalLock(PlanningRequest actual){return data(actual);}
                public FinanceStatePort.Read readUnderOriginalLock(Session same,PlanningRequest actual){assertSame(session,same);return data(actual);}
                private FinanceStatePort.Head data(PlanningRequest actual){assertSame(request,actual);return new FinanceStatePort.Head(actual.before(),firstHead,List.of(document),List.of(),Optional.empty());}
            },List.of(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.FEAST,GovernanceFixtures.REF,original->FinanceStatePort.Pending.CLEAR)));
            var contracts=new FinanceReadContracts(query->new FinanceReadContracts.Registration(GovernanceFixtures.REF,
                    new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
            PlanningReadPort noNative=new PlanningReadPort() {
                public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest input){throw new AssertionError("no Native READ allowed");}
            };
            var finance=new OrdinaryFinanceCollector(contracts,noNative,states,()->session);
            var borrowed=new GovernanceBorrowedSession(session,root.resolve("writer.lock"),same->assertSame(session,same));
            collector=new FeastObservationCollector(finance,new GovernanceFixtures.Supplier(request),archive,
                    (query,actual,arguments)->{throw new AssertionError("no Activity Native READ allowed");},borrowed);
        }
        void advance()throws IOException {
            long seq=head==null?1:head.state().sequence()+1;
            byte[] raw=("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\""+request.before().machineId()
                    +"\",\"sequence\":"+seq+",\"window_id\":1,\"start_date_raw\":100,\"target_date_raw\":124,\"target_days\":1,"
                    +"\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":100}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            var state=new ContinuityState(request.before().machineId(),seq,new ContinuityState.Origin(1,100,124,1),ContinuityState.Status.RUNNING,0,100,raw);
            head=new Head(state,List.of(),List.of(),List.of(),false);
            Path file=root.resolve("continuity.json");Files.write(file,StrictJson.canonical(state.toJson()));headRef=reference(file);
        }
        void verify(ExactRef ref)throws IOException {
            byte[] raw=Files.readAllBytes(Path.of(ref.path()));
            if(raw.length!=ref.bytes()||!ActionCodec.sha256(raw).equals(ref.sha256()))throw new IOException("finite DATA named-source hash differs");
        }
        static ExactRef reference(Path p)throws IOException {byte[] raw=Files.readAllBytes(p);return new ExactRef(p.toString(),raw.length,ActionCodec.sha256(raw));}
    }
}
