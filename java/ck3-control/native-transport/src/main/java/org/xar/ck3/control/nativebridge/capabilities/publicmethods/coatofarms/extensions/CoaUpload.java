package org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;

/** The original six source services. Upload bytes remain bounded RAM; only the canonical archive writes files. */
public final class CoaUpload implements FrontendCoaService.NativeAccess {
    public static final Set<Method> METHODS=Set.of(Method.BEGIN,Method.APPEND,Method.COMMIT,Method.ABORT,Method.PROBE,Method.EXPORT);
    public static final String EXPECTATION="xar.coa-original-native-source-result/v1";
    /** Root supplies this installed implementation; a binding value alone never grants action authority. */
    public interface Runtime {
        Binding current(BigInteger expectedRevision,String requiredCapability)throws IOException,InterruptedException;
        ProbeResult probe(EncodedSource source,Binding original,boolean large,boolean apply)throws IOException,InterruptedException;
        ExportResult export(Binding original)throws IOException,InterruptedException;
    }
    private final CoaUploads uploads;
    private final Runtime actual;
    public CoaUpload(CoaUploads sameUploads,Runtime actual){uploads=Objects.requireNonNull(sameUploads);this.actual=Objects.requireNonNull(actual);}
    @Override public Response execute(Request request)throws IOException,InterruptedException {
        Objects.requireNonNull(request);need(METHODS.contains(request.method()),"CoA upload component cannot dispatch another family");
        if(request instanceof Begin begin){
            begin.value().intent().requireSupportedBuild();
            Binding binding=actual.current(begin.value().intent().expectedRevision(),capability(PROBE_STEP));
            return response(upload(uploads.begin(begin.value(),binding)));
        }
        if(request instanceof Append append)return response(upload(uploads.append(append.value())));
        if(request instanceof Abort abort)return response(upload(uploads.abort(abort.key())));
        if(request instanceof Commit commit){
            // Consumed before any source lookup or native call, including all failures and UNKNOWN.
            CoaUploads.Finalized done=uploads.finalizeUpload(commit.value());
            Binding binding=actual.current(commit.value().intent().expectedRevision(),capability(PROBE_STEP));
            need(binding.equals(done.binding()),"coat-of-arms upload crossed its original complete binding");
            ProbeResult result=actual.probe(done.source(),binding,true,commit.value().intent().apply());
            need(result.binding().equals(binding),"native committed result crossed its original binding");
            need(actual.current(commit.value().intent().expectedRevision(),capability(PROBE_STEP)).equals(binding),"coat-of-arms upload crossed its revision binding during apply");
            var wire=empty().put("schema","coat-of-arms-source-upload-commit-v2").put("schema_version",2).put("status","committed");
            wire.set("upload",upload(done.upload()));wire.set("result",probe(result));return response(wire);
        }
        if(request instanceof Probe probe){
            EncodedSource source=EncodedSource.encode(probe.source(),false);
            Binding binding=actual.current(probe.expectedRevision(),capability(PROBE_STEP));
            ProbeResult result=actual.probe(source,binding,false,probe.apply());
            need(result.binding().equals(binding)&&actual.current(probe.expectedRevision(),capability(PROBE_STEP)).equals(binding),"coat-of-arms probe crossed its original complete binding");
            return response(probe(result));
        }
        if(request instanceof Revision export){
            Binding binding=actual.current(export.expectedRevision(),capability(EXPORT_STEP));
            ExportResult result=actual.export(binding);
            need(result.binding().equals(binding)&&actual.current(export.expectedRevision(),capability(EXPORT_STEP)).equals(binding),"coat-of-arms export crossed its original complete binding");
            return response(exported(result));
        }
        throw new IllegalArgumentException("CoA source method/request discriminant mismatch");
    }
    public static String capability(String operation){need(operation.equals(PROBE_STEP)||operation.equals(EXPORT_STEP),"unregistered source operation");return "game.command."+operation;}
    @FunctionalInterface public interface OriginGuard {void require(Session actual,ActionCommand command)throws IOException;}
    /** The identical concrete preparer owns the two finite Menu/Gameplay registrations. */
    public static final class Preparation implements RootExecutableBindings.CoaSourceOriginProof {
        private final ExactRef source;
        private final CoaSourceMaterials materials;
        private final OriginGuard origin;
        private final java.util.function.Supplier<Session> borrowed;
        public Preparation(ExactRef source,CoaSourceMaterials sameMaterials,OriginGuard actualOrigin,java.util.function.Supplier<Session> sameBorrowed){
            this.source=Objects.requireNonNull(source);need(source.bytes()>0,"actual source preparer implementation required");materials=Objects.requireNonNull(sameMaterials);origin=Objects.requireNonNull(actualOrigin);borrowed=Objects.requireNonNull(sameBorrowed);
        }
        @Override public ExactRef coaSourceDefinitionSource(){return source;}
        @Override public void requireCoaSourceOrigin(Session same,ActionCommand command)throws IOException {
            Objects.requireNonNull(same);Objects.requireNonNull(command);capability(command.operation().value());
            need(command.origin() instanceof CommandOrigin.Frontend||command.origin() instanceof CommandOrigin.Gameplay,"CoA source accepts only its original Menu/snapshot or Gameplay profile");
            origin.require(same,command);
            if(command.operation().value().equals(EXPORT_STEP))need(command.arguments().members().isEmpty(),"original native Copy accepts no source or path");
            else {
                var row=object(raw(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(command.arguments())));
                Binding binding=CoaCodec.binding(raw(row.get("binding")));
                materials.material(command,binding);
            }
        }
        @Override public NativeRequest prepare(ActionCommand command){
            try{requireCoaSourceOrigin(borrowed.get(),command);return materials.prepare(command);}
            catch(IOException failure){throw new UncheckedIOException(failure);}
        }
    }
}
