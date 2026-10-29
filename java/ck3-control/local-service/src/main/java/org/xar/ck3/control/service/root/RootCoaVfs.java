package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCapture;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** One actual Root CoA component; it consumes passive current native originals and never submits an action. */
public final class RootCoaVfs {
    private RootCoaVfs() { }
    public static final class Prepared implements RootFrontendCoaPublicProducts.ComponentPrepared {
        private final CoaVfs.Limits limits;private final Duration timeout;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,RootFrontendCoaPublicProducts.ComponentInstalled> installed=new IdentityHashMap<>();
        public Prepared(CoaVfs.Limits explicitSourceReadLimits,Duration actualObservationTimeout){
            limits=Objects.requireNonNull(explicitSourceReadLimits);timeout=Objects.requireNonNull(actualObservationTimeout);
            if(timeout.isZero()||timeout.isNegative()||timeout.compareTo(Duration.ofMinutes(2))>0)throw new IllegalArgumentException("finite actual Root VFS observation timeout required");
        }
        public Set<Method> methods(){return Set.of(Method.VFS);}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException{Objects.requireNonNull(actual);if(core!=null&&core!=actual)throw new IOException("VFS Prepared cannot bind another actual Core");core=actual;}
        public synchronized RootFrontendCoaPublicProducts.ComponentInstalled install(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);if(core==null||core!=actual.core())throw new IOException("VFS component requires its identical privately bound actual Core");
            var prior=installed.get(actual);if(prior!=null)return prior;if(installed.size()>=64)throw new IOException("VFS per-Game installation bound exhausted");
            var domain=new RootDomainInstallation("actual-coa-vfs-read-component/v1",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
            var component=new Component(actual,limits,timeout);var result=new RootFrontendCoaPublicProducts.ComponentInstalled(domain,component::execute);installed.put(actual,result);return result;
        }
    }
    private record Component(RootRuntimeContext context,CoaVfs.Limits limits,Duration timeout) {
        private Response execute(Request request)throws IOException,InterruptedException {
            if(!(request instanceof Vfs vfs))throw new IllegalArgumentException("VFS component received a foreign original method");
            Instant deadline=context.clock().instant().plus(timeout);context.requireCurrent(deadline);
            var phase=context.withSession(same->context.core().requireFrontendMenu(context).publicPhase());
            if(phase==RootMenuSession.PublicPhase.FRONTEND)return context.withSession(same->context.frontend().withSourceBoundFrontendRead(same,FrameMode.MENU,deadline,
                    actual->capture(same,vfs,deadline)));
            if(!(context.actions() instanceof RootApplicationSession root))throw new IOException("actual VFS gameplay component lacks its real Root application owner");
            return root.executePublicDecision(deadline,(frame,known,same)->new RootApplicationSession.RetainPublicResult<Response>(capture(same,vfs,deadline)),
                    (receipt,archive,same)->{throw new IOException("read-only VFS cannot consume an action result");});
        }
        private Response capture(ContinuityStorePort.Session same,Vfs request,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.requireCurrent(deadline);
            var plan=context.game().launchPlan();var executable=plan.sources().review().gameExecutable();
            if(!executable.sha256().equalsIgnoreCase(org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService.EXE_SHA))throw new IOException("original VFS projection is unavailable on the actual current build; no old observer relabeling");
            var transport=context.transport();var original=transport.diagnostics();
            var received=BridgeDiagnosticsCapture.capture(transport.pipeName(),original,java.util.Optional.empty());
            var session=received.session().orElseThrow(()->new IOException("actual VFS received transport session absent"));
            if(!session.game().equals(context.game().generation())||!session.machineId().equals(context.game().machineId())||!session.sessionId().equals(context.game().sessionId()))throw new IOException("VFS received original belongs to another physical Game/session");
            byte[] hello=original.originalHello().orElseThrow(()->new IOException("actual VFS HELLO original absent")).original().packet().value();
            byte[] mountPacket=original.latestHeartbeat().orElseThrow(()->new IOException("actual VFS original mounted-data heartbeat absent")).original().packet().value();
            ExactRef originalMount=context.archive().preserveArtifact(same,mountPacket,mountPacket.length);
            var qualification=context.sources().verifyPhysicalOrigin(same,session,context.source(),originalMount,original,deadline);qualification.assertCurrent(same);
            var input=new CoaVfs.Input(request,new ExactRef(executable.path(),executable.bytes(),executable.sha256()),received,session,context.source(),limits);
            Response result;Throwable failure=null;
            try{result=CoaVfs.project(input);}
            catch(IOException|RuntimeException|Error originalFailure){failure=originalFailure;throw originalFailure;}
            finally{try{
                qualification.assertCurrent(same);context.requireCurrent(deadline);
                var after=BridgeDiagnosticsCapture.capture(transport.pipeName(),transport.diagnostics(),java.util.Optional.empty());
                if(!received.session().equals(after.session())||!received.privateObservers().physfsMountedData().equals(after.privateObservers().physfsMountedData())
                        ||!Arrays.equals(hello,after.original().originalHello().orElseThrow(()->new IOException("VFS HELLO disappeared")).original().packet().value()))throw new IOException("actual VFS source/ordered mount receipt changed during projection");
            }catch(IOException|RuntimeException drift){if(failure!=null)failure.addSuppressed(drift);else throw drift;}}
            return result;
        }
    }
}
