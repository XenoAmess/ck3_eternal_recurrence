package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Private domain mint. The fixed writer authority resolves this exact retained object before reducing. */
public final class LifecycleChild {
    public static final String KIND="JAVA_EPISODE_LIFECYCLE_V1";
    public enum Phase { NEXT_EPISODE_ENTERED, DEATH_RECORDED, SUCCESSOR_COMMITTED, SUCCESSOR_PENDING_FINALIZED, NEXT_EPISODE_COMMITTED }
    private final String token=UUID.randomUUID().toString();
    private final ActionCommand parent;
    private final Phase phase;
    private final DriverSnapshotFacts.Stamp expected;
    private final DriverStateSnapshot.Complete replacement;
    private final OpportunityJson.Obj auxiliary;
    private final WriterContracts.Request request;
    private WriterContracts.Prepared originalPrepared;
    LifecycleChild(ActionCommand parent,Phase phase,DriverSnapshotFacts.Stamp expected,
            DriverStateSnapshot.Complete replacement,OpportunityJson.Obj auxiliary,org.xar.ck3.control.contracts.GameGeneration afterGame,ObjectNode delta,List<ExactRef> evidence) {
        this.parent=Objects.requireNonNull(parent);this.phase=Objects.requireNonNull(phase);this.expected=Objects.requireNonNull(expected);
        this.replacement=Objects.requireNonNull(replacement);this.auxiliary=Objects.requireNonNull(auxiliary);
        ObjectNode row=LifecycleJson.row();row.put("evidence_id",parent.actionId()+":"+phase.name());
        row.set("source",ProposalLifecycleCodec.source(parent.source()));row.put("parent_action_id",parent.actionId());row.put("token",token);
        row.put("parent_body_sha256",org.xar.ck3.control.application.action.ActionCodec.bodySha256(parent));
        row.put("operation",parent.operation().value());row.put("phase",phase.name());row.set("delta",delta.deepCopy());
        ObjectNode game=row.putObject("driver_after_game");game.put("pid",afterGame.pid());game.put("creation_filetime",afterGame.creationFiletime().value().toString());
        ObjectNode stamp=row.putObject("driver_snapshot");stamp.put("expected_version",expected.driverVersion());
        stamp.put("before_sha256",expected.driverSha256());stamp.put("after_sha256",LifecycleJson.sha(replacement.encode()));
        stamp.put("auxiliary_after_sha256",LifecycleJson.sha(org.xar.ck3.control.application.driver.DriverJson.encode(auxiliary)));
        stamp.put("expected_epoch",expected.episodeEpoch());stamp.put("next_epoch",phase==Phase.SUCCESSOR_COMMITTED||phase==Phase.NEXT_EPISODE_COMMITTED?Math.addExact(expected.episodeEpoch(),1):expected.episodeEpoch());
        request=new WriterContracts.Request(KIND,LifecycleJson.bytes(row),evidence);
    }
    public String parentActionId(){return parent.actionId();}
    public WriterContracts.Request request(){return request;}
    public Phase phase(){return phase;}
    public DriverSnapshotFacts.Stamp expected(){return expected;}
    public DriverStateSnapshot.Complete replacement(){return replacement;}
    public OpportunityJson.Obj auxiliary(){return auxiliary;}
    /** The coordinator retains the exact original preview before commit, so return loss never authorizes a second commit. */
    public synchronized void rememberPrepared(WriterContracts.Prepared actual) {
        Objects.requireNonNull(actual);
        org.xar.ck3.control.contracts.StrictJson.require(actual.request().identity().equals(request.identity())
                &&actual.request().kind().equals(request.kind())&&java.util.Arrays.equals(actual.request().details(),request.details())
                &&actual.request().evidence().equals(request.evidence()),"prepared lifecycle request differs from retained private child");
        if(originalPrepared!=null)org.xar.ck3.control.contracts.StrictJson.require(originalPrepared==actual,"original lifecycle Prepared cannot be replaced");
        else originalPrepared=actual;
    }
    public synchronized java.util.Optional<WriterContracts.Prepared> prepared(){return java.util.Optional.ofNullable(originalPrepared);}
    ActionCommand parent(){return parent;}
    String token(){return token;}
}

