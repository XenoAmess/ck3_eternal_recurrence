package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Actual day-zero business input. It is not a legacy entry receipt or startup qualification. */
public final class FreshCampaignContext {
    public static final String SCHEMA="xar.java.fresh-campaign-domain-input/v2";
    private static final String LEGACY_SCHEMA="xar.java.fresh-campaign-domain-input/v1";
    private static final int MAX_ORIGINAL_BYTES=ContinuityJson.DOMAIN_MAX_BYTES;
    private final RootRuntimeContext context;
    private final DriverObservationAssembler.Complete frame;
    private final Instant deadline;
    private final ContinuityState initialHead;
    private ExactRef original;

    private FreshCampaignContext(RootRuntimeContext context, DriverObservationAssembler.Complete frame,
            Instant deadline, ContinuityState initialHead) {
        this.context=Objects.requireNonNull(context);this.frame=Objects.requireNonNull(frame);
        this.deadline=Objects.requireNonNull(deadline);this.initialHead=Objects.requireNonNull(initialHead);
    }
    public static FreshCampaignContext create(RootRuntimeContext context,ContinuityStorePort.Session same,
            DriverObservationAssembler.Complete frame,Instant deadline)throws IOException {
        Objects.requireNonNull(context).writer().requireSession(same);
        var result=new FreshCampaignContext(context,frame,deadline,same.head().state());
        result.requireCurrent(same);return result;
    }
    public RootRuntimeContext context(){return context;}
    public DriverObservationAssembler.Complete frame(){return frame;}
    public DriverBootstrap.Adopted adopted(){return context.adopted();}
    public ManagedGameSession game(){return context.game();}
    public G2Source source(){return context.source();}
    public String sessionId(){return frame.sessionId();}
    public String episodeId(){return frame.identity().frame().episodeRunId();}
    public Instant deadline(){return deadline;}
    public ObservationIdentity currentObservation(){return frame.identity();}
    public List<ExactRef> evidence(){
        var refs=new LinkedHashSet<ExactRef>();refs.add(frame.originalEvidence());refs.add(adopted().seed().fullDriver());
        if(original!=null)refs.add(original);return List.copyOf(refs);
    }

    /** Same writer and observed campaign, without replaying a historical entry or source graph. */
    public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
        context.writer().requireSession(same);
        if(!frame.source().equals(context.source())||!frame.identity().game().equals(game().generation())
                ||!frame.sessionId().equals(game().sessionId())
                ||!frame.identity().equals(adopted().first().identity()))
            throw new IOException("Fresh campaign input belongs to another actual Game or Driver");
    }
    public void requireInitializationPredecessor(ContinuityStorePort.Session same,WriterContracts.Head predecessor)throws IOException {
        requireCurrent(same);
        if(!predecessor.digest().equals(same.head().digest()))
            throw new IOException("Fresh domain initializer lost its current writer predecessor");
        requireInitialShape(initialHead,predecessor.state());
    }
    static ObjectNode encodeObservation(ObservationIdentity identity) {
        var mapper=ControlBuild.strictMapper();
        ObjectNode node=mapper.valueToTree(identity);
        node.set("game",identity.game().toJson());
        return node;
    }
    static ObservationIdentity decodeObservation(JsonNode value)throws IOException {
        var mapper=ControlBuild.strictMapper();
        var row=StrictJson.object(value,Set.of("machine_id","game","frame","observation_version"));
        var game=GameGeneration.fromJson(row.get("game"));
        var frame=mapper.treeToValue(row.get("frame"),JointBudgetSelector.ProposalFrame.class);
        var machineId=StrictJson.text(row.get("machine_id"));
        var version=StrictJson.integer(row.get("observation_version"),1,StrictJson.MAX_SAFE_INTEGER);
        return new ObservationIdentity(machineId,game,frame,version);
    }
    /** Archives real observed input under its own schema; it never manufactures Start/Entry receipts. */
    public ExactRef preserveOriginal(ContinuityStorePort.Session same)throws IOException {
        requireCurrent(same);
        if(original!=null)return original;
        var mapper=ControlBuild.strictMapper();
        ObjectNode row=StrictJson.object();row.put("schema",SCHEMA);
        row.put("machine_id",game().machineId());row.set("observation",encodeObservation(frame.identity()));
        row.set("source",mapper.valueToTree(source()));row.put("session_id",sessionId());
        row.put("episode_id",episodeId());row.put("deadline",deadline.toString());
        row.set("first_driver",adopted().seed().fullDriver().toJson());
        row.set("native_observation",frame.originalEvidence().toJson());row.set("initial_head",initialHead.toJson());
        var refs=row.putArray("evidence");new LinkedHashSet<>(evidence()).forEach(ref->refs.add(ref.toJson()));
        original=context.archive().withSession(same).preserveMaterial(new RawJson(StrictJson.canonical(row,MAX_ORIGINAL_BYTES)));
        return original;
    }
    public static boolean isOriginal(RootRuntimeContext context,ContinuityStorePort.Session same,ExactRef basis)throws IOException {
        context.writer().requireSession(same);
        var row=StrictJson.parse(context.archive().withSession(same).loadMaterial(basis).bytes(),MAX_ORIGINAL_BYTES);
        var schema=row.path("schema").asText();
        return SCHEMA.equals(schema)||LEGACY_SCHEMA.equals(schema);
    }
    public static Original replayOriginal(RootRuntimeContext context,ContinuityStorePort.Session same,ExactRef basis)throws IOException {
        Objects.requireNonNull(context).writer().requireSession(same);
        var row=StrictJson.object(StrictJson.parse(context.archive().withSession(same).loadMaterial(basis).bytes(),
                MAX_ORIGINAL_BYTES),Set.of("schema","machine_id","observation","source","session_id",
                "episode_id","deadline","first_driver","native_observation","initial_head","evidence"));
        var schema=StrictJson.text(row.get("schema"));
        if(!SCHEMA.equals(schema)&&!LEGACY_SCHEMA.equals(schema))throw new IOException("Fresh campaign input schema required");
        var mapper=ControlBuild.strictMapper();
        var observation=SCHEMA.equals(schema)?decodeObservation(row.get("observation"))
                :mapper.treeToValue(row.get("observation"),ObservationIdentity.class);
        var source=mapper.treeToValue(row.get("source"),G2Source.class);
        String machine=StrictJson.text(row.get("machine_id")),session=StrictJson.text(row.get("session_id"));
        String episode=StrictJson.text(row.get("episode_id"));
        if(!machine.equals(context.game().machineId())||!source.equals(context.source())
                ||!observation.game().equals(context.game().generation())||!session.equals(context.game().sessionId())
                ||!episode.equals(observation.frame().episodeRunId()))
            throw new IOException("Fresh campaign input crossed its real Game or episode");
        var refs=new java.util.ArrayList<ExactRef>();
        var array=row.get("evidence");StrictJson.require(array.isArray(),"fresh evidence array required");
        for(var item:array)refs.add(ExactRef.fromJson(item));
        if(!refs.contains(basis))refs.add(basis);
        return new Original(context,basis,observation,source,session,episode,
                ExactRef.fromJson(row.get("first_driver")),List.copyOf(refs),
                ContinuityState.fromJson(row.get("initial_head"),machine),Instant.parse(StrictJson.text(row.get("deadline"))));
    }
    public static final class Original {
        private final RootRuntimeContext context;
        private final ExactRef basis,firstDriver;
        private final ObservationIdentity observation;
        private final G2Source source;
        private final String sessionId,episodeId;
        private final List<ExactRef> evidence;
        private final ContinuityState entryHead;
        private final Instant deadline;
        private Original(RootRuntimeContext context,ExactRef basis,ObservationIdentity observation,G2Source source,
                String sessionId,String episodeId,ExactRef firstDriver,List<ExactRef> evidence,ContinuityState entryHead,
                Instant deadline) {
            this.context=context;this.basis=basis;this.observation=observation;this.source=source;
            this.sessionId=sessionId;this.episodeId=episodeId;this.firstDriver=firstDriver;
            this.evidence=evidence;this.entryHead=entryHead;this.deadline=deadline;
        }
        public ExactRef basis(){return basis;}
        public ObservationIdentity observation(){return observation;}
        public G2Source source(){return source;}
        public String sessionId(){return sessionId;}
        public String episodeId(){return episodeId;}
        public ExactRef firstDriver(){return firstDriver;}
        public List<ExactRef> evidence(){return evidence;}
        public ContinuityState entryHead(){return entryHead;}
        public Instant deadline(){return deadline;}
        public void requireInitializationPredecessor(ContinuityStorePort.Session same,WriterContracts.Head predecessor)throws IOException {
            context.writer().requireSession(same);
            if(!predecessor.digest().equals(same.head().digest()))
                throw new IOException("Fresh campaign import lost its actual writer predecessor");
            requireInitialShape(entryHead,predecessor.state());
        }
    }
    private static void requireInitialShape(ContinuityState initial,ContinuityState actual)throws IOException {
        ObjectNode before=initial.toJson().deepCopy(),after=actual.toJson().deepCopy();
        var advancing=Set.of("sequence","last_event_identity",DomainBodies.FIELD);before.remove(advancing);after.remove(advancing);
        if(!ContinuityJson.same(before,after))throw new IOException("Fresh domain initialization followed a non-initial campaign transition");
    }
}
