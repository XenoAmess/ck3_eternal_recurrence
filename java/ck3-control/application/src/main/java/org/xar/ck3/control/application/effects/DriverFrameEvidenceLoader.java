package org.xar.ck3.control.application.effects;

import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure replay of the actual native packet plus the complete original Driver, using the sole production assembler. */
public final class DriverFrameEvidenceLoader implements NativeEffectEvidence.FrameLoader {
    private final DriverObservationAssembler assembler;
    public DriverFrameEvidenceLoader(DriverObservationAssembler sameProductionAssembler) { this.assembler = java.util.Objects.requireNonNull(sameProductionAssembler); }
    @Override public DriverObservationAssembler.Complete load(NativeEffectEvidence.FrameBasis basis, ActionPorts.OutcomeArchive archive) {
        var full = loadFull(basis, archive);
        var result = assembler.assemble(full.actual(), full.facts(), full.originalEvidence());
        StrictJson.require(result instanceof DriverObservationAssembler.Complete, "archived native/complete Driver no longer rebuild an accepted original semantic frame");
        return (DriverObservationAssembler.Complete) result;
    }
    /** Complete retained native/Driver DATA, including unavailable/dead player scopes. No ordinary identity is invented. */
    public DriverObservationAssembler.FullSnapshot loadFull(NativeEffectEvidence.FrameBasis basis, ActionPorts.OutcomeArchive archive) {
        var manifest = archive.loadFullMaterial(basis.driverFacts()); RootGuardChecks.exact(basis.driverFacts(), manifest.bytes());
        byte[] nativePacket = archive.loadNativeFrame(basis.nativeFrame()); RootGuardChecks.exact(basis.nativeFrame(), nativePacket);
        var actual = DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(), manifest, nativePacket);
        var driverReference = DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(), manifest);
        var driver = archive.loadFullMaterial(driverReference); RootGuardChecks.exact(driverReference, driver.bytes());
        var facts = DriverObservationEvidenceReader.decode(basis.driverFacts(), manifest, driver, actual);
        return assembler.projectFull(actual, facts, basis.nativeFrame());
    }
}
