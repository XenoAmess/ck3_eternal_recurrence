package org.xar.ck3.control.platform;

import java.io.IOException;
import java.util.HashSet;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild;
import java.util.Objects;
import org.xar.ck3.control.build.NativeBridgeBuild;

/** Fixed adapter from the actual three-stage bridge producer to physical launch custody. */
public final class NativeBridgeLaunchEvidence implements NativeLaunchEvidence.Port {
    @Override public NativeLaunchEvidence.Proof verify(NativeLaunchEvidence.Expected expected) throws IOException {
        Objects.requireNonNull(expected);
        var inputs = expected.inputs();
        // This reader verifies original commands, ENV, complete native/tool inputs, both outputs,
        // original Root authority, and administrative/SYSTEM registration before returning data.
        var actual = NativeBridgeBuild.checkedEvidence(inputs.environmentActual(), inputs.buildActual(), inputs.registrationActual());
        var request = actual.request();
        var selectedSources = new HashSet<>(expected.completeSources());
        if (!request.machineId().equals(expected.machineId()) || !request.sourceRoot().equals(expected.sourceRoot())
                || !expected.sourceRoot().equals(expected.sourceRoot().toAbsolutePath().normalize())
                || selectedSources.size() != expected.completeSources().size()
                || selectedSources.size() != request.completeSources().size()
                || !selectedSources.equals(new HashSet<>(request.completeSources()))
                || !actual.bridgeDll().equals(expected.bridgeDll()) || !actual.injector().equals(expected.injector()))
            throw new IOException("Original native build does not bind the selected machine, complete source tree and exact bridge/injector");
        var proof = new NativeLaunchEvidence.Proof(expected, completeClosure(actual.completeRefs(),expected.completeSources()));
        for (var ref : proof.completeEvidenceClosure()) ref.verify();
        return proof;
    }
    /** Both the original retained proof and the exact current compile view must remain held by launch custody. */
    static List<ControlBuild.FileRef> completeClosure(List<ControlBuild.FileRef> retained, List<ControlBuild.FileRef> current) throws IOException {
        var refs=new LinkedHashMap<String,ControlBuild.FileRef>();
        var all=new ArrayList<ControlBuild.FileRef>(retained); all.addAll(current);
        for(var ref:all) {
            var prior=refs.putIfAbsent(ref.path(),ref);
            if(prior!=null && !prior.equals(ref)) throw new IOException("Conflicting original/current Native evidence reference");
        }
        return List.copyOf(refs.values());
    }
}
