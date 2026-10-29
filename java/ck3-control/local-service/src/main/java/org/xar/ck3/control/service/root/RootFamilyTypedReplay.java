package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;

/** Resolve the identical registered typed producer and its explicitly installed pure replay. */
public final class RootFamilyTypedReplay {
    private RootFamilyTypedReplay() { }
    public static <T> PlanningReadResult.Known<T> read(RootRuntimeContext context,PlanningReadReceipt original,Class<T> expectedType) {
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
            var ref=archive.readReferenceOf(original);var retained=archive.loadRead(ref);
            StrictJson.require(archive.readReferenceOf(retained).equals(ref),"typed family view lacks the exact immutable original read");
            var candidates=context.readCatalog().contracts().stream().filter(contract->contract.contractId().equals(original.contractId())
                    && contract.operation().equals(original.request().operation())).toList();
            StrictJson.require(candidates.size()==1 && context.readCatalog().containsIdentity(candidates.getFirst()),"typed family archive producer is not uniquely installed");
            Object result=candidates.getFirst().replay(retained);
            StrictJson.require(expectedType.isInstance(result),"registered pure replay returned a different typed family value");
            return new PlanningReadResult.Known<>(expectedType.cast(result),retained,ref);
        } catch(IOException failure) {throw new UncheckedIOException("actual typed family original unavailable",failure);}
    }
}
