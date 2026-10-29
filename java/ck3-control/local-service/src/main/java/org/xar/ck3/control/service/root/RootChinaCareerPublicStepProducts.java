package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson;
import org.xar.ck3.control.nativebridge.capabilities.china_career.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract.*;

/** Original six encoded EXECUTE reads, using the identical pre-Core registered native contracts. */
public final class RootChinaCareerPublicStepProducts {
    private RootChinaCareerPublicStepProducts() { }

    /** Parsed caller DATA. Its encoded owner remains explicit even for the played-owner-only query. */
    public record Parsed(Kind kind,String nonce,OptionalInt owner,OptionalInt subject) {
        public Parsed {
            Objects.requireNonNull(kind);CareerJson.nonce(nonce);Objects.requireNonNull(owner);Objects.requireNonNull(subject);
            StrictJson.require(owner.isPresent()==(kind!=Kind.MANAGER_SELECTOR)
                    &&subject.isPresent()==kind.subjectArgument(),"original encoded China career argument shape required");
            owner.ifPresent(value->StrictJson.require(value>0,"positive original owner required"));
            subject.ifPresent(value->StrictJson.require(value>0,"positive original subject required"));
        }
        public Request request(BigInteger revision) {
            return new Request(kind,nonce,revision,kind.ownerArgument()?owner:OptionalInt.empty(),subject);
        }
    }
    public static boolean claims(Kind kind,OperationKey step) {
        return Objects.requireNonNull(step).value().startsWith(Objects.requireNonNull(kind).step()+"-");
    }
    /** Same lowercase ASCII hex and canonical positive int32 grammar as the original six parsers. */
    public static Parsed parse(Kind kind,OperationKey step) {
        try {
            if(!claims(kind,step))throw new IllegalArgumentException("different original prefix");
            String tail=step.value().substring(kind.step().length()+1);
            String[] parts=tail.split("-",kind==Kind.MANAGER_GOVERNANCE?3:kind==Kind.MANAGER_SELECTOR?1:2);
            int count=kind==Kind.MANAGER_GOVERNANCE?3:kind==Kind.MANAGER_SELECTOR?1:2;
            StrictJson.require(parts.length==count,"original encoded component count changed");
            OptionalInt owner=OptionalInt.empty(),subject=OptionalInt.empty();
            if(kind==Kind.MANAGER_GOVERNANCE){subject=OptionalInt.of(id(parts[0]));owner=OptionalInt.of(id(parts[1]));}
            else if(kind!=Kind.MANAGER_SELECTOR)owner=OptionalInt.of(id(parts[0]));
            String hex=parts[count-1];StrictJson.require(hex.matches("(?:[0-9a-f]{2}){1,64}"),"canonical bounded lowercase nonce hex required");
            byte[] bytes=HexFormat.of().parseHex(hex);for(byte value:bytes)StrictJson.require(value>=0,"original ASCII nonce required");
            return new Parsed(kind,CareerJson.nonce(new String(bytes,StandardCharsets.US_ASCII)),owner,subject);
        }catch(IllegalArgumentException|ArithmeticException failure){throw fault(PublicServiceFailure.Kind.UNSUPPORTED_STEP,malformed(kind));}
    }
    private static int id(String text) {
        StrictJson.require(text.matches("[1-9][0-9]{0,9}"),"canonical positive int32 required");
        int value=new BigInteger(text).intValueExact();StrictJson.require(value>0,"positive int32 required");return value;
    }
    private static String malformed(Kind kind) {
        return switch(kind){
            case OWNER->"malformed ZhongGuo Workforce owner v1 query step";
            case CAREER_HC->"malformed ZhongGuo career-HC/workforce v1 query step";
            case COLLECTIVE->"malformed ZhongGuo Workforce collective snapshot v1 query step";
            case NORMAL_EXIT->"malformed ZhongGuo Workforce normal-exit snapshot v1 query step";
            case MANAGER_GOVERNANCE->"malformed ZhongGuo manager-governance snapshot v1 query step";
            case MANAGER_SELECTOR->"malformed ZhongGuo manager/subordinate selector v1 query step";
        };
    }
    private static String unsupported(Kind kind) {
        return switch(kind){
            case OWNER->"native DLL does not advertise the ZhongGuo Workforce owner postcondition query";
            case CAREER_HC->"native DLL does not advertise the ZhongGuo career-HC/workforce postcondition query";
            case COLLECTIVE->"native DLL cannot query the received-self ZhongGuo Workforce collective state";
            case NORMAL_EXIT->"native DLL cannot query the received-self ZhongGuo Workforce normal-exit lifecycle";
            case MANAGER_GOVERNANCE->"native DLL cannot query the ZhongGuo manager-governance lifecycle";
            case MANAGER_SELECTOR->"native DLL cannot query the ZhongGuo manager/subordinate selector";
        };
    }
    public static void requireCapability(Kind kind,NativeWire.Hello originalHello) {
        if(!Objects.requireNonNull(originalHello).capabilities().contains(Objects.requireNonNull(kind).capability()))
            throw fault(PublicServiceFailure.Kind.UNSUPPORTED_STEP,unsupported(kind));
    }

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);RootRuntimeContext context=actual.context();
        var installed=actual.additionalDomains().chinaCareer();
        List<ExactRef> sources=producerSources(actual);
        var result=new ArrayList<RootPublicStepExecution.Product>();
        for(Kind kind:Kind.values())result.add(new RootPublicStepExecution.Read("original.execute.china-career."+kind.name(),
                step->{if(!claims(kind,step))return false;parse(kind,step);return true;},same->requireOwner(actual,context,installed,same),
                (original,frame,known,same,caller,archive)->read(actual,installed,kind,original,frame,known,same,caller,archive),sources));
        return List.copyOf(result);
    }
    private static List<ExactRef> producerSources(RootInstalledCatalog actual)throws IOException {
        var refs=new java.util.LinkedHashSet<ExactRef>();
        for(Class<?> type:List.of(RootChinaCareerPublicStepProducts.class,RootChinaCareerPublicProducts.class,
                RootChinaCareerSourcesFactory.class,RootPublicStepExecution.class))
            refs.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,type));
        for(Class<?> type:List.of(ChinaCareerContract.class,ChinaCareerCodec.class,ChinaCareerService.class,
                org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceNativeReads.class,
                CareerJson.class,CareerGroups.class,CareerProvenance.class,CareerReadiness.class,
                OwnerCareerFrames.class,OwnerGroups.class,CollectiveGroups.class,CollectiveWorkforceFrame.class,
                NormalExitGroups.class,NormalExitWorkforceFrame.class,GovernanceGroups.class,ManagerGovernanceFrame.class,ManagerSelectorFrame.class))
            refs.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,type));
        refs.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.APPLICATION,PublicSnapshotCodec.class));
        refs.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.CONTRACTS,PublicUnsigned64.class));
        return List.copyOf(refs);
    }
    private static void requireOwner(RootInstalledCatalog catalog,RootRuntimeContext context,
            RootChinaCareerPublicProducts.Installed installed,RootRuntimeContext same)throws IOException {
        if(same!=context||catalog.context()!=same||catalog.additionalDomains().chinaCareer()!=installed)
            throw new IOException("original China career EXECUTE escaped its identical installed physical Root");
        if(catalog.domains().stream().noneMatch(domain->domain==installed.installation()))
            throw new IOException("original China career installation is absent from this actual catalog");
        for(var contract:installed.service().registration().all())
            if(!same.readCatalog().containsIdentity(contract)||installed.installation().reads().stream().noneMatch(row->row.contract()==contract))
                throw new IOException("original China career EXECUTE lost its identical installed read contract");
    }

    private static RawJson read(RootInstalledCatalog catalog,RootChinaCareerPublicProducts.Installed installed,Kind kind,
            PlanningRequest original,Complete before,Known known,Session same,
            PublicPlanningCodec.ExecuteRequest caller,OutcomeArchive archive)throws IOException {
        RootRuntimeContext runtime=catalog.context();requireOwner(catalog,runtime,installed,runtime);
        runtime.writer().requireSession(same);caller.requireCurrent(original);
        StrictJson.require(original.before().equals(before.identity())&&original.source().equals(before.source())
                &&original.sessionId().equals(before.sessionId())&&known.stamp().game().equals(before.identity().game())
                &&known.stamp().episodeRunId().equals(before.identity().frame().episodeRunId()),"held original China career planning frame/source/Driver differs");
        Parsed parsed=parse(kind,caller.step());
        return runtime.readiness().current(same,before.identity(),original.deadline(),lease->{
            StrictJson.require(lease.frame().fullBindingSha256().equals(before.fullBindingSha256()),"original China career held complete frame changed");
            NativeWire.Hello hello=runtime.transport().originalHello();byte[] packet=archive.readOriginalPacket(lease.originalHello());
            var digest=NativeRequestChronology.PacketIdentity.of(packet);var transport=runtime.transport().diagnostics().session().orElseThrow(()->new IOException("China career original transport session unavailable"));
            StrictJson.require(digest.bytes()==lease.originalHello().bytes()&&digest.sha256().equals(lease.originalHello().sha256())
                    &&Arrays.equals(packet,hello.packet().value())&&hello.pid()==before.identity().game().pid()
                    &&transport.game().equals(before.identity().game())&&transport.sessionId().equals(before.sessionId())
                    &&hello.connectionGeneration().equals(before.connectionGeneration()),"actual China career HELLO/archive/session changed");
            requireCapability(kind,hello);
            Frame frame=new Frame(before.identity().frame().snapshotId(),before.identity().frame().revision(),
                    before.identity().frame().identity().nativeRevision(),before.connectionGeneration(),
                    before.identity().frame().identity().dateRaw().intValueExact(),before.identity().frame().identity().player().intValueExact(),
                    flag(before,"paused"),flag(before,"map_ready"),before.identity().frame().episodeRunId(),hello,lease.originalHello());
            if(!frame.paused())throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,paused(kind));
            if(kind==Kind.OWNER&&parsed.owner().orElseThrow()!=frame.playerId())
                throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"native ZhongGuo Workforce owner frame is malformed: played owner binding changed");
            Request request=parsed.request(frame.publicRevision());var contract=installed.service().registration().contract(kind);
            var nativeRequest=new PlanningReadRequest(before.identity(),before.source(),before.sessionId(),contract.operation(),
                    ChinaCareerService.arguments(request,frame),original.deadline());
            PlanningReadResult<NativeObservation> observed=runtime.reads().read(same,contract,nativeRequest);
            if(!(observed instanceof PlanningReadResult.Known<NativeObservation> accepted))
                throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"actual registered "+kind.label()+" read unavailable: "+
                        (observed instanceof PlanningReadResult.Unavailable<NativeObservation> unavailable?unavailable.reason():"unknown read result"));
            StrictJson.require(accepted.receipt().request().equals(nativeRequest)&&accepted.receipt().contractId().equals(contract.contractId())
                    &&archive.readReferenceOf(accepted.receipt()).equals(accepted.originalReceipt())
                    &&contract.replay(accepted.receipt()).equals(accepted.value()),"original China career registered receipt/replay changed");
            for(var guard:List.of(accepted.receipt().before(),accepted.receipt().after()))
                StrictJson.require(Arrays.equals(archive.readOriginalPacket(guard.binding().capabilityEvidence()),packet),"original China career read lost held actual HELLO");
            RawJson result=present(parsed,frame,accepted.value(),accepted.receipt().original().originalResultToken().orElseThrow());
            return runtime.readiness().current(same,before.identity(),original.deadline(),after->{
                StrictJson.require(after.frame().fullBindingSha256().equals(before.fullBindingSha256()),"original China career query crossed a complete paused frame");
                requireOwner(catalog,runtime,installed,runtime);return result;
            });
        });
    }
    private static String paused(Kind kind) {
        return switch(kind){
            case OWNER->"native ZhongGuo Workforce owner query requires a paused snapshot";
            case CAREER_HC->"native ZhongGuo career-HC/workforce query requires a paused snapshot";
            case COLLECTIVE->"native ZhongGuo Workforce collective query requires a paused snapshot";
            case NORMAL_EXIT->"native ZhongGuo Workforce normal-exit query requires a paused snapshot";
            case MANAGER_GOVERNANCE->"native ZhongGuo manager-governance query requires a paused snapshot";
            case MANAGER_SELECTOR->"native ZhongGuo manager/subordinate selector requires a paused snapshot";
        };
    }

    /** Pure original EXECUTE projection; the existing typed domain decoder validates the original token. */
    public static RawJson present(Parsed parsed,Frame frame,NativeObservation nativeValue,RawJson originalEnvelope) {
        Request request=parsed.request(frame.publicRevision());
        StrictJson.require(request.kind()==nativeValue.kind()&&frame.binding(request).equals(nativeValue.binding())
                &&ChinaCareerCodec.decodeDomain(parsed.kind(),nativeValue.originalFrame(),nativeValue.binding()).equals(nativeValue.domain()),
                "original EXECUTE payload lost its actual typed request/frame binding");
        if(parsed.kind()==Kind.OWNER)StrictJson.require(parsed.owner().orElseThrow()==frame.playerId(),"original played owner binding changed");
        return ChinaCareerCodec.publicExecuteResult(nativeValue,originalEnvelope);
    }
    private static boolean flag(Complete frame,String field){return frame.semantic().get(field) instanceof OpportunityJson.Bool value&&value.value();}
    private static PublicServiceFailure fault(PublicServiceFailure.Kind kind,String message){return new PublicServiceFailure(kind,message,java.util.Optional.empty());}
}
