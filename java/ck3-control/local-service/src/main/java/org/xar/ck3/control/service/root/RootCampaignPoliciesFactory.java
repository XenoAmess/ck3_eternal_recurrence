package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.CampaignAdvancePolicy;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.GoalInput;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;

/** Installs the real final campaign and private realm policies over the actual same-Game command producers. */
public final class RootCampaignPoliciesFactory {
    public static final int MAX_CONFIGURATION_BYTES=65_536;
    private RootCampaignPoliciesFactory(){ }
    /** The original versioned deadline document is mandatory. Absence cannot install a no-cap policy. */
    public record BoundDeadline(ExactRef original,byte[] bytes) {
        public BoundDeadline {
            Objects.requireNonNull(original);bytes=Objects.requireNonNull(bytes).clone();
            StrictJson.require(bytes.length>0&&bytes.length<=MAX_CONFIGURATION_BYTES
                    &&original.bytes()==bytes.length&&original.sha256().equals(ActionCodec.sha256(bytes)),
                    "exact bounded original campaign deadline configuration required");
            CampaignDeadlineCodec.decodeConfiguration(bytes,OrdinaryCampaignSchedule::calendar);
        }
        @Override public byte[] bytes(){return bytes.clone();}
        public CampaignDeadline.Configuration configuration(){return CampaignDeadlineCodec.decodeConfiguration(bytes,OrdinaryCampaignSchedule::calendar);}
        private CampaignDeadline.Configuration requireCurrent(ContinuityStorePort.Session same)throws IOException {
            var pin=same.capturePin(original,MAX_CONFIGURATION_BYTES);
            byte[] actual=same.readPinned(pin,MAX_CONFIGURATION_BYTES);same.verifyPin(pin);
            StrictJson.require(Arrays.equals(bytes,actual),"actual campaign deadline original changed");
            return CampaignDeadlineCodec.decodeConfiguration(actual,OrdinaryCampaignSchedule::calendar);
        }
    }
    public record Sources(ExactRef factoryImplementation,ExactRef policyImplementation,BoundDeadline deadline) {
        public Sources {
            Objects.requireNonNull(factoryImplementation);Objects.requireNonNull(policyImplementation);Objects.requireNonNull(deadline);
            StrictJson.require(factoryImplementation.bytes()>0&&policyImplementation.bytes()>0,"actual campaign factory/policy implementation sources required");
        }
    }
    public static final class Prepared {
        private final Sources sources;
        private final Map<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        public Sources sources(){return sources;}
        public synchronized Installed install(RootRuntimeContext context,RootLifeRuntimeFactory.Installed sameLife,
                RootRuntimeCommands sameCommands)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(sameLife);Objects.requireNonNull(sameCommands);
            sameCommands.requireOwner(context,sameLife.commands());
            context.withSession(same->{context.writer().requireSession(same);sources.deadline().requireCurrent(same);return null;});
            Installed previous=installed.get(context);
            if(previous!=null){StrictJson.require(previous.life==sameLife&&previous.commands==sameCommands,"campaign policies cannot replace their original physical command producers");return previous;}
            StrictJson.require(installed.size()<64,"bounded physical campaign policy installation history required");
            var candidate=new Installed(context,sameLife,sameCommands,sources);installed.put(context,candidate);return candidate;
        }
    }
    public static final class Installed {
        private final RootRuntimeContext context;private final RootLifeRuntimeFactory.Installed life;
        private final RootRuntimeCommands commands;private final Sources sources;
        private final CampaignAdvancePolicy advance;private final RealmLifecycle realm;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext context,RootLifeRuntimeFactory.Installed life,RootRuntimeCommands commands,Sources sources){
            this.context=context;this.life=life;this.commands=commands;this.sources=sources;
            realm=new RealmLifecycle(sources.policyImplementation());
            advance=new CampaignAdvancePolicy(sources.policyImplementation(),this::deadline,
                    (request,original,effective,cap)->{
                        try{return commands.rewriteDeadline(request,original,effective,cap);}
                        catch(IOException|UncheckedIOException|IllegalStateException failure){throw unavailable("actual campaign command rewrite unavailable",failure);}
                    },this::goal);
            installation=new RootDomainInstallation("actual-campaign-and-realm-policies",List.of(),List.of(),List.of(),List.of(),
                    List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(advance,realm),
                    List.of(),List.of(),List.of(),List.of());
        }
        public CampaignAdvancePolicy advance(){return advance;}
        public RealmLifecycle realm(){return realm;}
        public RootDomainInstallation installation(){return installation;}
        private Optional<CampaignDeadline.Configuration> deadline(PlanningRequest request){
            try{return context.withSession(same->context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                requireRequest(request,original);var config=sources.deadline().requireCurrent(same);
                // The pinned scoring clock keeps its explicit ID; Goal uses its original episode-run ID.
                context.writer().requireSession(same);return Optional.of(config);
            }));}catch(IOException|UncheckedIOException|IllegalStateException failure){throw unavailable("source-bound campaign deadline is unavailable",failure);}
        }
        private Optional<GoalInput> goal(PlanningRequest request){
            try{return context.withSession(same->context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                requireRequest(request,original);
                var metadata=context.sources().optionalCurrentMetadata(same);
                if(metadata.isEmpty())return Optional.<GoalInput>empty();
                var historical=metadata.orElseThrow();
                var projected=M7CampaignPolicies.projectGoal(request,historical.ownerSourceEpoch(),historical.gameExecutable(),Optional.empty());
                context.writer().requireSession(same);return projected;
            }));}catch(IOException|UncheckedIOException|IllegalStateException failure){throw unavailable("actual source-qualified M7 goal projection is unavailable",failure);}
        }
        private void requireRequest(PlanningRequest expected,PlanningRequest original)throws IOException {
            StrictJson.require(expected==original,"campaign policy left its actual collector planning request");
            context.requireCurrent(expected.deadline());commands.requireOwner(context,life.commands());
            StrictJson.require(expected.before().game().equals(context.game().generation())&&expected.before().machineId().equals(context.game().machineId())
                    &&expected.source().equals(context.source())&&expected.sessionId().equals(context.game().sessionId()),"campaign policy crossed actual Game/source/session");
        }
        private static M7CampaignPolicies.InputUnavailable unavailable(String prefix,Exception failure){
            return new M7CampaignPolicies.InputUnavailable(prefix+": "+failure.getMessage());
        }
    }
}
