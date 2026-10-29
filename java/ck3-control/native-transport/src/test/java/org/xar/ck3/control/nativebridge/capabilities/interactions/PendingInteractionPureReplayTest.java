package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.nio.charset.StandardCharsets;
import java.math.BigInteger;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionFixtures.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** The original installed pending parser is explicitly read-only in both live and archived paths. */
final class PendingInteractionPureReplayTest {
    @Test void sameInstalledContractReplaysOriginalSignedInstanceAndRejectsWrongContract() throws Exception {
        var context=context();var contract=PendingInteractionContracts.pending(SOURCE);assertTrue(contract.hasPureReplay());
        var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),
                InteractionArguments.app(InteractionArguments.body(context).put("pending_id",PENDING)),context.deadline());
        String id="known-pending-original";var guard=new PlanningReadGuard(new GuardEvidence(context.before(),context.source(),context.sessionId(),BigInteger.ONE,contract.operation(),SOURCE,SOURCE,"declared-only",NOW,context.deadline()),true,true,true,"b".repeat(64));
        var token=wire(context,"spar_with_knight_interaction");token.remove(java.util.List.of("queried_snapshot_id","queried_revision","queried_native_revision"));token.put("backend_id","native-headless");var packet=F.objectNode().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);packet.set("result",token);
        byte[] bytes=packet.toString().getBytes(StandardCharsets.UTF_8);var original=new NativeActionPort.AckReceived(id,true,Optional.of(encode(token)),new RawJson(bytes),NativeWire.packet(bytes));
        var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,original);
        PendingContext live=contract.decode(receipt),archived=contract.replay(receipt);assertEquals(live,archived);assertEquals(PENDING,archived.instance().value());
        var other=new PlanningReadReceipt(request,"different-exact-contract",id,guard,guard,original);assertThrows(IllegalArgumentException.class,()->contract.replay(other));
    }
}
