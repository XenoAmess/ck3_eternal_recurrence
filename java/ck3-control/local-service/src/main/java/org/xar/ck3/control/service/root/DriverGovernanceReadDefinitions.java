package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceNativeReads;
import org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryCodec;

/** Two finite actual native reads missing from the original installed governance catalog. */
public final class DriverGovernanceReadDefinitions {
    public static final String COUNCIL_RECEIPT="private-query-assign-councillor-receipt-v1";
    public static final String GOVERNMENT="query-government-runtime-adapter-v1";
    public record Sources(ExactRef council,ExactRef government,ExactRef decoder) {
        public Sources {for(var value:List.of(council,government,decoder))StrictJson.require(value.bytes()>0,"actual finite source required");}
    }
    private final Sources sources;
    private final ReadContract<RawJson> councilReceipt,government;
    private RootRuntimeContext current;
    public DriverGovernanceReadDefinitions(Sources sources) {
        this.sources=Objects.requireNonNull(sources);
        councilReceipt=contract(COUNCIL_RECEIPT,sources.council(),false);government=contract(GOVERNMENT,sources.government(),true);
    }
    public synchronized void bind(RootRuntimeContext context) {
        Objects.requireNonNull(context);StrictJson.require(current==null||current.core()==context.core(),"public driver reads cannot cross Core authority");current=context;
    }
    public Sources sources() {return sources;}
    public ReadContract<RawJson> councilReceipt() {return councilReceipt;}
    public ReadContract<RawJson> government() {return government;}
    public List<RootReadContractCatalog.InstalledRead> installed() {
        return List.of(new RootReadContractCatalog.InstalledRead(councilReceipt,sources.decoder()),new RootReadContractCatalog.InstalledRead(government,sources.decoder()));
    }
    private ReadContract<RawJson> contract(String step,ExactRef nativeSource,boolean governmentRead) {
        return new ReadContract<>("driver-public."+step,new OperationKey(step),Optional.empty(),"driver-public."+step,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,nativeSource,
                request->{StrictJson.require(request.arguments().members().isEmpty(),"this exact native read has no caller wire fields");return new NativeRequest(step,Optional.empty(),new RawJson(new byte[]{'{','}'}));},
                receipt->governmentRead?consumeGovernment(receipt):original(receipt));
    }
    private RawJson consumeGovernment(PlanningReadReceipt receipt) {
        original(receipt);RootRuntimeContext context;
        synchronized(this) {context=Objects.requireNonNull(current,"actual same-Core public read installation required");}
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
            RootGuardEvidence.requireHistory(receipt.before().binding(),archive,same);RootGuardEvidence.requireHistory(receipt.after().binding(),archive,same);
            var before=RootGuardEvidence.loadFrame(receipt.before().binding(),archive,context.frameLoader());
            var after=RootGuardEvidence.loadFrame(receipt.after().binding(),archive,context.frameLoader());
            var input=StrictJson.object().put("schema",GovernmentQueryCodec.CONSUME_SCHEMA).put("expected_revision",receipt.request().before().frame().revision()).put("request_id",receipt.requestId());
            input.set("before_snapshot",snapshot(before,receipt.before().binding(),archive));input.set("after_snapshot",snapshot(after,receipt.after().binding(),archive));
            input.set("command_result",StrictJson.parse(receipt.original().originalFrame().bytes()));
            context.writer().requireSession(same);return new RawJson(GovernmentQueryCodec.consume(StrictJson.canonical(input)));
        }catch(IOException failure){throw new UncheckedIOException("actual archived government query source unavailable",failure);}
    }
    static ObjectNode snapshot(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete frame,GuardEvidence guard,ActionPorts.OutcomeArchive archive)throws IOException {
        var node=CouncilCodec.object(StrictJson.parse(DriverJson.encode(frame.semantic()))).deepCopy();
        var hello=originalHello(guard.capabilityEvidence(),archive);
        var diagnostics=node.get("diagnostics") instanceof ObjectNode existing?existing:node.putObject("diagnostics");diagnostics.set("hello",hello);return node;
    }
    /** Exact original packet lane: archive custody and the sole NativeWire parser validate its framing/role.
     * Only after full HELLO admission is the original JSON payload projected, retaining all original fields. */
    static ObjectNode originalHello(ExactRef original,ActionPorts.OutcomeArchive archive)throws IOException {
        byte[] packet=archive.readOriginalPacket(original);
        if(!(NativeWire.decode(packet) instanceof NativeWire.Hello hello))throw new IOException("government runtime adapter requires its original HELLO packet");
        byte[] verified=hello.packet().value();
        return NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(verified,4,verified.length)));
    }
    static RawJson original(PlanningReadReceipt receipt) {
        GovernanceNativeReads.verifyGuards(receipt);
        var frame=StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
        StrictJson.require(StrictJson.text(frame.get("type")).equals("command_result")&&StrictJson.integer(frame.get("protocol_version"),1,1)==1
                &&StrictJson.text(frame.get("request_id")).equals(receipt.requestId()),"driver original native correlation mismatch");StrictJson.trueValue(frame.get("ok"));
        var token=receipt.original().originalResultToken().orElseThrow();StrictJson.require(receipt.original().nativeOk()&&StrictJson.parse(token.bytes()).equals(frame.get("result")),"driver native token differs from original packet");
        try {
            var outbound=receipt.original().outbound().orElseThrow();var wire=NativeWire.decodeExecuteRequest(outbound.originalPacket());
            StrictJson.require(wire.requestId().equals(receipt.requestId())&&wire.step().equals(receipt.request().operation().value())
                    &&wire.expectedSnapshotRevision().isEmpty()&&wire.expectedRevision().filter(receipt.request().before().frame().identity().nativeRevision()::equals).isPresent()
                    &&StrictJson.parse(wire.normalizedAdditionalFields().value()).equals(StrictJson.object()),"driver original wire differs from actual no-field native read");
        }catch(IOException failure){throw new UncheckedIOException(failure);}
        return token;
    }
}
