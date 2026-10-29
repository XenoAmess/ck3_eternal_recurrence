package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.army.RegularMaaPrivatePermission;

/** Definition/qualification rejection vectors. Synthetic file pins grant no Root or Game permission. */
final class RegularMaaPrivatePermissionTest {
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    @TempDir Path directory;
    private ExactRef source(String name)throws IOException {
        Path path=directory.resolve(name);byte[] value=name.getBytes(java.nio.charset.StandardCharsets.UTF_8);Files.write(path,value);
        return new ExactRef(path.toString(),value.length,ActionCodec.sha256(value));
    }
    private RegularMaaPrivatePermission.Sources sources()throws IOException {return new RegularMaaPrivatePermission.Sources(source("python"),source("mailbox"),source("create"),source("binding4"));}
    private static NativeRequest request() {
        return new NativeRequest("maa-regular-personal-create-private-v1",Optional.empty(),new RawJson(StrictJson.canonical(StrictJson.object()
                .put("expected_snapshot_revision",9).put("expected_public_revision",10).put("expected_date_raw",10660101)
                .put("expected_player_character_id",29829).put("type_index",50).put("action_id","original-native-call"))));
    }
    private static GuardEvidence guard(ExactRef original) {
        var now=Instant.parse("2026-10-24T00:00:00Z");var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var identity=new ProposalLifecycle.ObservationIdentity("software-only-machine",game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.valueOf(9),BigInteger.valueOf(10660101)),"before9",BigInteger.TEN,"episode-original"),1);
        return new GuardEvidence(identity,new G2Source(identity.machineId(),now.toString(),"1.20.0.4",original),"held-original",BigInteger.ONE,
                new OperationKey(request().step()),original,original,"software-only-definition-test",now,now.plusSeconds(30));
    }
    private static NativeWire.Hello hello(String sha) {return new NativeWire.Hello(42,BigInteger.ONE,"test-bridge",sha,"test-adapter","ready",true,List.of(),new NativeWire.Bytes(new byte[]{1}));}
    private static NativePipeEndpoint.Config config(GuardEvidence guard) {return new NativePipeEndpoint.Config("\\\\.\\pipe\\maa-private-vector",guard.source().machineId(),guard.origin().game(),guard.sessionId(),"test-bridge",SHA,"test-adapter");}
    @Test void definitionsDoNotInvokeQualificationAndMissingRealQualificationFailsBeforeDispatch()throws IOException {
        var sources=sources();var calls=new AtomicInteger();
        var permission=RegularMaaPrivatePermission.permission(sources,(config,hello,guard,request)->{calls.incrementAndGet();throw new IOException("actual exact-build source qualification unavailable");});
        assertEquals(0,calls.get());assertEquals(request().step(),permission.operation().value());assertEquals(sources.nativeMailbox(),permission.originalProducerSource());
        assertEquals(RegularMaaPrivatePermission.PERMISSION,permission.permissionKey());var guard=guard(sources.nativeMailbox());
        assertThrows(IOException.class,()->permission.verify(config(guard),hello(SHA),guard,request()));assertEquals(1,calls.get());
        assertThrows(IllegalArgumentException.class,()->permission.verify(config(guard),hello("a".repeat(64)),guard,request()));assertEquals(1,calls.get());
        Files.writeString(Path.of(sources.nativeCreate().path()),"changed original source");
        assertThrows(IOException.class,()->permission.verify(config(guard),hello(SHA),guard,request()));assertEquals(1,calls.get());
    }
}
