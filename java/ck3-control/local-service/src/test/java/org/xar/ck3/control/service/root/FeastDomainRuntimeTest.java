package org.xar.ck3.control.service.root;

import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.contracts.*;
import static org.junit.jupiter.api.Assertions.*;

/** Synthetic persistent producer -> actual owning finance consumer. It grants no publication or native qualification. */
final class FeastDomainRuntimeTest {
    private static final ExactRef SOURCE=new ExactRef("synthetic-source",1,"a".repeat(64));
    private static final ExactRef COMMAND=new ExactRef("synthetic-original-command",1,"b".repeat(64));
    private final FeastDomainRuntime runtime=new FeastDomainRuntime(Path.of("synthetic-writer.lock"),new FeastDomainRuntime.Sources(SOURCE,List.of(SOURCE)));
    private FinanceStatePort.Document original(byte[] body){return new FinanceStatePort.Document(FinanceStatePort.Domain.FEAST,
            new ExactRef("synthetic-body",body.length,ActionCodec.sha256(body)),body);}
    @Test void registrationIdentityIsStrictAcrossRuntimeInstances(){
        var opening = new GovernanceOpeningRuntime(new GovernanceOpeningRuntime.Sources(List.of(SOURCE)));
        assertSame(opening.registration(), opening.registration());
        assertSame(opening, opening.registration().verifier());
        assertSame(runtime.registration(), runtime.registration());
        assertSame(runtime, runtime.registration().verifier());
        var other = new GovernanceOpeningRuntime(new GovernanceOpeningRuntime.Sources(List.of(SOURCE)));
        assertNotSame(opening.registration(), other.registration());
        assertNotSame(opening.registration().verifier(), other.registration().verifier());
    }
    @Test void exactPendingProducerRoundTripsIntoTheSingleOwningReaderWithoutClaimingClear(){
        var pending=new FeastDomainRuntime.Pending("synthetic-episode",COMMAND,"c".repeat(64));var ledger=new FeastDomainRuntime.Ledger(Optional.of(pending),Optional.empty());
        byte[] body=FeastDomainRuntime.encode(ledger);assertEquals(ledger,FeastDomainRuntime.decode(body));
        assertEquals(FinanceStatePort.Pending.PENDING,runtime.financeBinding().decoder().reader().decode(original(body)));
        assertArrayEquals(body,FeastDomainRuntime.encode(FeastDomainRuntime.decode(body)));
    }
    @Test void legacyUnknownMalformedAndMissingPendingCannotDefaultToClear(){
        var body=StrictJson.parse(FeastDomainRuntime.encode(new FeastDomainRuntime.Ledger(Optional.empty(),Optional.empty())));
        var malformed=(com.fasterxml.jackson.databind.node.ObjectNode)body;malformed.put("pending",false);
        assertThrows(IllegalArgumentException.class,()->runtime.financeBinding().decoder().reader().decode(original(StrictJson.canonical(malformed))));
        malformed.putObject("pending").put("episode_run_id","legacy-unknown").put("ack",true);
        assertThrows(IllegalArgumentException.class,()->FeastDomainRuntime.decode(StrictJson.canonical(malformed)));
        malformed.remove("pending");assertThrows(RuntimeException.class,()->FeastDomainRuntime.decode(StrictJson.canonical(malformed)));
    }
    @Test void unresolvedOutcomeCannotBeRepresentedAsResolvedAndSourceBodyIdentityRemainsExact(){
        assertThrows(IllegalArgumentException.class,()->new FeastDomainRuntime.Resolved(SOURCE,COMMAND,ActionReceipt.Outcome.UNRESOLVED));
        byte[] body=FeastDomainRuntime.encode(new FeastDomainRuntime.Ledger(Optional.empty(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new FinanceStatePort.Document(FinanceStatePort.Domain.FEAST,SOURCE,body));
        assertEquals(FinanceStatePort.Pending.CLEAR,runtime.financeBinding().decoder().reader().decode(original(body)));
    }
    @Test void terminalMetadataCannotQualifyItselfOrClaimAnotherActivity(){
        var retained=new FeastDomainRuntime.FinalRetention(SOURCE,0x01000042L,42L);
        var origin=new FeastDomainRuntime.ActivityOrigin(SOURCE,Optional.of(retained));
        var resolved=new FeastDomainRuntime.Resolved(SOURCE,COMMAND,ActionReceipt.Outcome.APPLIED_CONFIRMED,Optional.of(origin));
        var ledger=new FeastDomainRuntime.Ledger(Optional.empty(),Optional.of(resolved));byte[] encoded=FeastDomainRuntime.encode(ledger);
        assertEquals(ledger,FeastDomainRuntime.decode(encoded));
        // A syntactically valid locator is never a final-state proof: the actual Root bridge has not been bound.
        assertThrows(java.io.UncheckedIOException.class,()->runtime.financeBinding().decoder().reader().decode(original(encoded)));
        var changed=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encoded);
        ((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("resolved").get("lifecycle")).put("activity_id",0x02000042L);
        assertThrows(IllegalArgumentException.class,()->FeastDomainRuntime.decode(StrictJson.canonical(changed)));
        assertThrows(IllegalArgumentException.class,()->new FeastDomainRuntime.FinalRetention(SOURCE,0xFFFF_FFFFL,42L));
        assertThrows(IllegalArgumentException.class,()->new FeastDomainRuntime.FinalRetention(new ExactRef("oversized",131073,"d".repeat(64)),1,42));
    }
}
