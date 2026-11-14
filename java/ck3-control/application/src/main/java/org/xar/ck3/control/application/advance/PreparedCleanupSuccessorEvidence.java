package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Versioned DATA for a distinct sixth cleanup command after the exact fifth
 * original has a prepared-cleanup NoEffect terminal. This codec issues no token,
 * source authority, Native permit, canonical membership or gameplay credit. */
public final class PreparedCleanupSuccessorEvidence {
    public static final String CURSOR_PREFIX="prepared-cleanup-successor/v2: ";
    public static final String PREPARED_SCHEMA="xar.life-prepared-cleanup/v2";
    private static final int MAXIMUM=64*1024;
    private static final Duration OPERATION_WINDOW=Duration.ofMinutes(20);
    private static final Set<String> FIELDS=Set.of("schema","original_parent","original_children","a_terminal",
            "a_proof","authorization","c5_terminal","c5_noeffect_proof","command","command_body_sha256",
            "native_request_id","native_prepared","preparation_nonce","issued_at_utc","deadline_utc");
    private PreparedCleanupSuccessorEvidence() { }

    /** Only identifies the DATA shape. Installed Root must independently verify its actual source and current canonical prefix. */
    public static boolean isSuccessor(PreparedCleanupEvidence.Prepared prepared) {
        return prepared!=null&&prepared.children().size()==5
                &&prepared.children().getLast().state() instanceof ActionState.PreparedCleanupNoEffectConfirmed;
    }

    public static ExactRef preservePrepared(ActionReceipt parent,List<ActionReceipt> children,ActionCommand child6,
            NativeRequest nativePrepared,String preparationNonce,Instant issuedAt,Instant deadline,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Objects.requireNonNull(frames);children=List.copyOf(children);
        require(children.size()==5&&children.getLast().state() instanceof ActionState.PreparedCleanupNoEffectConfirmed,
                "successor cleanup requires five settled originals ending in C5 NoEffect");
        var fifth=children.getLast();var state=(ActionState.PreparedCleanupNoEffectConfirmed)fifth.state();
        var c5=PreparedCleanupNoEffectProof.load(state.proofReference(),archive,frames);
        var row=StrictJson.object();row.put("schema",PREPARED_SCHEMA);row.set("original_parent",archive.receiptReferenceOf(parent).toJson());
        var refs=row.putArray("original_children");for(var child:children)refs.add(archive.receiptReferenceOf(child).toJson());
        row.set("a_terminal",c5.prepared().aTerminalReference().toJson());row.set("a_proof",c5.prepared().aProofReference().toJson());
        row.set("authorization",c5.authorizationReference().toJson());row.set("c5_terminal",archive.receiptReferenceOf(fifth).toJson());
        row.set("c5_noeffect_proof",state.proofReference().toJson());
        row.set("command",archive.preserveMaterial(new RawJson(ActionCodec.encodeCommand(child6))).toJson());
        row.put("command_body_sha256",ActionCodec.bodySha256(child6));row.put("native_request_id",RequestIds.forCommand(child6));
        row.set("native_prepared",archive.preserveRequest(nativePrepared).toJson());requireCanonicalNonce(preparationNonce);
        row.put("preparation_nonce",preparationNonce);row.put("issued_at_utc",issuedAt.toString());row.put("deadline_utc",deadline.toString());
        byte[] bytes=StrictJson.canonical(row);require(bytes.length<=MAXIMUM,"successor cleanup material exceeds its unchanged cap");
        var reference=archive.preserveMaterial(new RawJson(bytes));var decoded=loadPrepared(reference,archive,frames);
        require(decoded.parentReceipt().equals(parent)&&decoded.children().equals(children)&&decoded.command().equals(child6)
                &&decoded.nativePrepared().equals(nativePrepared),"successor cleanup canonical original roundtrip differs");return reference;
    }

    /** Metadata-only descriptor; no receipt loading, effect replay, Prepared or source authority. */
    public record Descriptor(ExactRef reference,ExactRef parentReference,List<ExactRef> childReferences,
            ExactRef aTerminalReference,ExactRef aProofReference,ExactRef authorizationReference,
            ExactRef c5TerminalReference,ExactRef c5NoEffectProofReference,ActionCommand command,
            ExactRef commandReference,String nativeRequestId,NativeRequest nativePrepared,
            ExactRef nativePreparedReference,String preparationNonce,Instant issuedAt,Instant deadline) {
        public Descriptor {
            Objects.requireNonNull(reference);Objects.requireNonNull(parentReference);childReferences=List.copyOf(childReferences);
            Objects.requireNonNull(aTerminalReference);Objects.requireNonNull(aProofReference);Objects.requireNonNull(authorizationReference);
            Objects.requireNonNull(c5TerminalReference);Objects.requireNonNull(c5NoEffectProofReference);Objects.requireNonNull(command);
            Objects.requireNonNull(commandReference);StrictJson.text(nativeRequestId);Objects.requireNonNull(nativePrepared);
            Objects.requireNonNull(nativePreparedReference);requireCanonicalNonce(preparationNonce);
            Objects.requireNonNull(issuedAt);Objects.requireNonNull(deadline);
        }
    }

    /** Strict v2 metadata and original command/preparation only; never loads a C5/A proof.
     * The source-owned caller must establish canonical membership and replay domain proofs. */
    public static Descriptor loadDescriptor(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(archive);Obj row=material(reference,archive);
        require(row.members().keySet().equals(FIELDS)&&new Text(PREPARED_SCHEMA).equals(row.get("schema")),
                "successor cleanup descriptor schema or fields differ");
        var parentReference=exact(row.get("original_parent"));var children=new ArrayList<ExactRef>();
        for(var item:array(row.get("original_children"),"original_children"))children.add(exact(item));
        require(children.size()==5&&children.stream().distinct().count()==5&&children.stream().noneMatch(parentReference::equals)
                &&parentReference.bytes()>0&&children.stream().allMatch(ref->ref.bytes()>0),
                "successor cleanup descriptor requires five distinct original receipt references");
        var aTerminal=exact(row.get("a_terminal"));var aProof=exact(row.get("a_proof"));
        var authorization=exact(row.get("authorization"));var c5Terminal=exact(row.get("c5_terminal"));var c5Proof=exact(row.get("c5_noeffect_proof"));
        require(aTerminal.equals(children.get(3))&&c5Terminal.equals(children.getLast())
                &&aProof.bytes()>0&&authorization.bytes()>0&&c5Proof.bytes()>0,
                "successor cleanup descriptor changed its C4/C5 reference positions");
        var commandReference=exact(row.get("command"));
        require(commandReference.bytes()>0&&commandReference.bytes()<=ActionCodec.MAX_COMMAND_BYTES,
                "successor cleanup descriptor bounded command reference required");
        byte[] commandBytes=archive.loadMaterial(commandReference).bytes();exactBytes(commandReference,commandBytes);
        var command=ActionCodec.decodeCommand(commandBytes);
        require(java.util.Arrays.equals(commandBytes,ActionCodec.encodeCommand(command)),
                "successor cleanup descriptor command is not its full canonical original");
        var nativeReference=exact(row.get("native_prepared"));var nativePrepared=archive.loadRequest(nativeReference);
        require(nativeReference.bytes()>0&&archive.requestReferenceOf(nativePrepared).equals(nativeReference),
                "successor cleanup descriptor native preparation original differs");
        var requestId=text(row.get("native_request_id"),"native_request_id");
        var nonce=text(row.get("preparation_nonce"),"preparation_nonce");requireCanonicalNonce(nonce);
        var issuedAt=instant(row.get("issued_at_utc"),"issued_at_utc");var deadline=instant(row.get("deadline_utc"),"deadline_utc");
        require(requestId.equals(RequestIds.forCommand(command))&&new Text(ActionCodec.bodySha256(command)).equals(row.get("command_body_sha256"))
                &&issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(OPERATION_WINDOW))&&command.deadline().equals(deadline)
                &&nativePrepared.equals(AdvancePrimitives.prepareRequest(command)),
                "successor cleanup descriptor changed its command, deterministic request, preparation or finite original window");
        return new Descriptor(reference,parentReference,children,aTerminal,aProof,authorization,c5Terminal,c5Proof,
                command,commandReference,requestId,nativePrepared,nativeReference,nonce,issuedAt,deadline);
    }

    public static PreparedCleanupEvidence.Prepared loadPrepared(ExactRef reference,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        return loadPreparedChecked(reference,archive,Objects.requireNonNull(frames));
    }
    public static PreparedCleanupEvidence.Prepared loadPreparedOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        return loadPreparedChecked(reference,archive,null);
    }
    private static PreparedCleanupEvidence.Prepared loadPreparedChecked(ExactRef reference,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Obj row=material(reference,archive);
        require(row.members().keySet().equals(FIELDS)&&new Text(PREPARED_SCHEMA).equals(row.get("schema")),
                "successor cleanup schema or fields differ");
        var parentReference=exact(row.get("original_parent"));var parent=receipt(parentReference,archive);
        var references=new ArrayList<ExactRef>();var children=new ArrayList<ActionReceipt>();
        for(var item:array(row.get("original_children"),"original_children")){
            var ref=exact(item);references.add(ref);children.add(receipt(ref,archive));
        }
        require(children.size()==5&&references.stream().distinct().count()==5&&references.stream().noneMatch(parentReference::equals)
                &&children.stream().allMatch(ActionReceipt::settled),"successor cleanup needs five distinct settled original children");
        var c5TerminalReference=exact(row.get("c5_terminal"));var fifth=children.getLast();
        require(c5TerminalReference.equals(references.getLast())&&fifth.state() instanceof ActionState.PreparedCleanupNoEffectConfirmed,
                "successor cleanup C5 terminal is not its exact fifth original");
        var terminalState=(ActionState.PreparedCleanupNoEffectConfirmed)fifth.state();var c5ProofReference=exact(row.get("c5_noeffect_proof"));
        require(terminalState.proofReference().equals(c5ProofReference),"successor cleanup C5 terminal changed its NoEffect proof");
        PreparedCleanupNoEffectProof.verifyArchivedState(fifth,c5ProofReference,terminalState.originalPreparedState(),archive);
        var c5=frames==null?PreparedCleanupNoEffectProof.loadOriginals(c5ProofReference,archive)
                :PreparedCleanupNoEffectProof.load(c5ProofReference,archive,frames);
        require(parent.equals(c5.parentReceipt())&&parentReference.equals(c5.parentReference())
                &&children.subList(0,4).equals(c5.children().subList(0,4))&&references.subList(0,4).equals(c5.childReferences().subList(0,4))
                &&terminalState.originalPreparedState().equals(c5.originalPreparedState())
                &&fifth.command().equals(c5.child5().command())&&fifth.bodySha256().equals(c5.child5().bodySha256())
                &&fifth.sequence()>c5.child5().sequence(),"successor cleanup changed the original parent/five-prefix or C5 prepared terminal relation");
        var aTerminalReference=exact(row.get("a_terminal"));var aProofReference=exact(row.get("a_proof"));
        var authorization=exact(row.get("authorization"));var old=c5.prepared();var aProof=old.aProof();
        require(aTerminalReference.equals(references.get(3))&&aTerminalReference.equals(old.aTerminalReference())
                &&aProofReference.equals(old.aProofReference())&&authorization.equals(old.authorizationReference())
                &&authorization.equals(c5.authorizationReference()),"successor cleanup changed the original C4 A proof or authorization");
        var commandReference=exact(row.get("command"));byte[] commandBytes=archive.loadMaterial(commandReference).bytes();exactBytes(commandReference,commandBytes);
        var command=ActionCodec.decodeCommand(commandBytes);
        require(java.util.Arrays.equals(commandBytes,ActionCodec.encodeCommand(command)),"successor cleanup command is not its complete canonical original");
        var requestReference=exact(row.get("native_prepared"));var nativePrepared=archive.loadRequest(requestReference);
        require(archive.requestReferenceOf(nativePrepared).equals(requestReference),"successor cleanup native preparation reference differs");
        Instant issuedAt=instant(row.get("issued_at_utc"),"issued_at_utc"),deadline=instant(row.get("deadline_utc"),"deadline_utc");
        var requestId=text(row.get("native_request_id"),"native_request_id");var nonce=text(row.get("preparation_nonce"),"preparation_nonce");requireCanonicalNonce(nonce);
        require(requestId.equals(RequestIds.forCommand(command))&&new Text(ActionCodec.bodySha256(command)).equals(row.get("command_body_sha256")),
                "successor cleanup command digest or deterministic native request ID differs");
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(OPERATION_WINDOW))&&command.deadline().equals(deadline)
                &&!issuedAt.isBefore(c5.freshSnapshotAck().custody().orElseThrow().responseReceived().observedAt()),
                "successor cleanup does not have its own finite post-C5 observation operation window");
        var operation=new OperationKey(ClockStatusRead.CANCEL_PREFIX+aProof.original().originalArm().generation().decimal());
        var arguments=new Obj(java.util.Map.of());
        var expected=new ActionCommand(ActionIds.child(parent.command().actionId(),6,operation),command.before(),
                parent.command().source(),parent.command().sessionId(),operation,arguments,
                AdvancePrimitives.expected(command.before(),parent.command().source(),operation,arguments),parent.command().claims(),deadline);
        var originalIds=new HashSet<String>();originalIds.add(RequestIds.forCommand(parent.command()));
        for(var child:children){originalIds.add(RequestIds.forCommand(child.command()));
            ActionTransitions.attempt(child.state()).ifPresent(a->originalIds.add(a.requestId()));
            ActionTransitions.dispatch(child.state()).ifPresent(d->originalIds.add(d.requestId()));}
        originalIds.add(old.nativeRequestId());originalIds.add(c5.freshStatus().receipt().requestId());originalIds.add(c5.freshSnapshotAck().requestId());
        originalIds.add(aProof.freshStatus().receipt().requestId());originalIds.add(aProof.freshSnapshotAck().requestId());
        require(command.equals(expected)&&operation.equals(fifth.command().operation())&&!command.actionId().equals(parent.command().actionId())
                &&children.stream().noneMatch(c->c.command().actionId().equals(command.actionId()))&&!originalIds.contains(requestId)
                &&children.stream().noneMatch(c->c.bodySha256().equals(ActionCodec.bodySha256(command)))
                &&!nonce.equals(old.preparationNonce())&&nativePrepared.equals(AdvancePrimitives.prepareRequest(command)),
                "successor cleanup is not a distinct exact sixth generation-bound CANCEL preparation");
        var identity=command.before();var previous=fifth.command().before();
        require(identity.game().equals(previous.game())&&identity.machineId().equals(previous.machineId())
                &&identity.frame().episodeRunId().equals(previous.frame().episodeRunId())
                &&identity.frame().identity().player().equals(previous.frame().identity().player())
                &&identity.frame().identity().dateRaw().equals(previous.frame().identity().dateRaw()),
                "successor cleanup changed the original owner/episode/player/partial date");
        return new PreparedCleanupEvidence.Prepared(reference,parent,parentReference,children,references,aTerminalReference,aProofReference,
                authorization,aProof,command,commandReference,requestId,nativePrepared,requestReference,nonce,issuedAt,deadline);
    }

    private static ActionReceipt receipt(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        var value=archive.loadReceipt(reference);require(archive.receiptReferenceOf(value).equals(reference),"successor cleanup receipt original differs");return value;
    }
    private static Obj material(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        require(reference.bytes()>0&&reference.bytes()<=MAXIMUM,"successor cleanup bounded material reference required");
        byte[] bytes=archive.loadMaterial(reference).bytes();exactBytes(reference,bytes);return DriverJson.object(bytes,MAXIMUM);
    }
    private static void exactBytes(ExactRef reference,byte[] bytes) {
        require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"successor cleanup original bytes changed");
    }
    private static ExactRef exact(Value value){return ExactRef.fromJson(toNode(object(value,"exact reference")));}
    private static Instant instant(Value value,String key){return Instant.parse(StrictJson.utc(text(value,key)));}
    private static void requireCanonicalNonce(String value) {
        StrictJson.text(value);require(java.util.UUID.fromString(value).toString().equals(value),"successor cleanup canonical immutable UUID nonce required");
    }
}
