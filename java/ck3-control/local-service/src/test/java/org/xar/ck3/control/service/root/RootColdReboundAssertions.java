package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual-input regression consumer; it creates no Game, private bootstrap, writer event or restore ticket. */
public final class RootColdReboundAssertions {
    private RootColdReboundAssertions(){ }
    public static void requireActual(ContinuityStorePort.Session same,RootPrivateBootstrap.Original original,
            RootColdReboundRuntime.ColdReboundOrigin actual)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(original);Objects.requireNonNull(actual);
        var context=original.context();context.writer().requireSession(same);String head=same.head().digest();
        original.requireOriginal(same);actual.requireOriginal(same);var data=actual.data();
        require(actual.context()==context&&context.requireColdReboundOrigin(same)==actual
                &&data.pair().equals(original.pair())&&data.owner().game().equals(original.game().generation())
                &&data.owner().machineId().equals(original.game().machineId())&&data.owner().sessionId().equals(original.game().sessionId())
                &&data.source().equals(context.source())&&!data.owner().game().equals(data.pair().frame().game())
                &&data.semantic().frame().frame().episodeRunId().equals(data.pair().frame().frame().episodeRunId())
                &&data.semantic().frame().frame().identity().player().equals(data.pair().frame().frame().identity().player())
                &&data.semantic().frame().frame().identity().dateRaw().equals(data.pair().frame().frame().identity().dateRaw())
                &&data.captureSequence()>=original.commitReceipt().head().sequence()
                &&data.bootstrapEvidence().reference().equals(original.evidence())
                &&actual.newSavedDayCredit()==0&&actual.newCycleCredit()==0,
                "actual cold rebound lost the private issuer, saved-vs-current Game, episode or zero-credit roles");
        byte[] encoded=data.encode();
        require(Arrays.equals(encoded,RootColdReboundRuntime.Data.decode(encoded).encode()),"actual cold original DATA failed its exact JSON round trip");
        var numericConnection=row(encoded);numericConnection.put("connection_generation",9007199254740993L);refuse(numericConnection);
        var booleanSequence=row(encoded);booleanSequence.put("capture_sequence",true);refuse(booleanSequence);
        var numericOrder=row(encoded);((ObjectNode)numericOrder.get("second_read")).put("snapshot_received_order",1);refuse(numericOrder);
        var missing=row(encoded);missing.remove("first_read");refuse(missing);
        var extra=row(encoded);extra.put("qualified",true);refuse(extra);
        var wrongIdentity=row(encoded);
        ((ObjectNode)wrongIdentity.get("pair").get("save").get("identity")).put("file_id",9007199254740993L);refuse(wrongIdentity);
        var oldGame=row(encoded);oldGame.set("owner",org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionToJson(
                new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(data.owner().machineId(),data.pair().frame().game(),data.owner().sessionId())));
        refuse(oldGame);
        // A decoded DATA object is never passed back into a capability constructor or substituted for actual.
        actual.requireOriginal(same);original.requireOriginal(same);
        require(context.requireColdReboundOrigin(same)==actual&&head.equals(same.head().digest()),"cold origin regression wrote or replaced canonical/private state");
    }
    private static ObjectNode row(byte[] bytes) {
        var parsed=StrictJson.parse(bytes,RootColdReboundRuntime.Data.MAXIMUM_BYTES);
        if(!(parsed instanceof ObjectNode row))throw new AssertionError("actual cold DATA object required");return row;
    }
    private static void refuse(ObjectNode invalid) {
        boolean refused=false;
        try {RootColdReboundRuntime.Data.decode(StrictJson.canonical(invalid,RootColdReboundRuntime.Data.MAXIMUM_BYTES));}
        catch(IllegalArgumentException expected){refused=true;}
        require(refused,"invalid cold original JSON fields/types/identity were accepted");
    }
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
