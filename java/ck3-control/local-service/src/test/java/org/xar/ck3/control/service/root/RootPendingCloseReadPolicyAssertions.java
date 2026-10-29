package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.ReconciliationIdentity;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;


/** Test-only consumers of actual installed policies; no source, Current, command or read authority is constructed. */
public final class RootPendingCloseReadPolicyAssertions {
    private RootPendingCloseReadPolicyAssertions() { }

    public static List<RootReconciliationAuthority.AllowedRead> requireActualCloseIncluded(
            RootApplicationSession root,RootInstalledCatalog actualCatalog,ActionReceipt actualOriginalClose,
            ReconciliationIdentity actualIdentity,Complete actualCurrent,Instant deadline)
            throws IOException,InterruptedException {
        return inspect(root,actualCatalog,actualOriginalClose,actualIdentity,actualCurrent,deadline,true);
    }

    /** Supply a real unrelated unresolved action; the added lifecycle policy must not manufacture a Close read. */
    public static List<RootReconciliationAuthority.AllowedRead> requireUnrelatedAddsNoClose(
            RootApplicationSession root,RootInstalledCatalog actualCatalog,ActionReceipt actualOriginal,
            ReconciliationIdentity actualIdentity,Complete actualCurrent,Instant deadline)
            throws IOException,InterruptedException {
        return inspect(root,actualCatalog,actualOriginal,actualIdentity,actualCurrent,deadline,false);
    }

    private static List<RootReconciliationAuthority.AllowedRead> inspect(RootApplicationSession root,
            RootInstalledCatalog catalog,ActionReceipt original,ReconciliationIdentity identity,
            Complete current,Instant deadline,boolean expectClose)throws IOException,InterruptedException {
        Objects.requireNonNull(root);Objects.requireNonNull(catalog);Objects.requireNonNull(original);
        Objects.requireNonNull(identity);Objects.requireNonNull(current);Objects.requireNonNull(deadline);
        var context=catalog.context();
        require(root.ownedBy(context.core())&&context.actions()==root&&context.adopted()==root.driver()
                &&context.game().generation().equals(root.identity().game()),
                "actual catalog must be the same installed Root/Core/Driver/physical Game");
        return root.withPublicStandaloneRead(deadline,same->{
            var archive=root.archive().withSession(same);
            var ref=archive.receiptReferenceOf(original);
            require(archive.loadReceipt(ref).equals(original),"policy test requires the actual original archived receipt");
            String before=same.head().digest();
            var producer=catalog.remainingDomains().lifecycle().natural().pendingRuntime().reconciliationReads();
            List<RootReconciliationAuthority.AllowedRead> owned=producer.allowed(original,identity,current,deadline);
            List<RootReconciliationAuthority.AllowedRead> combined=catalog.remainingDomains()
                    .reconciliationReads().allowed(original,identity,current,deadline);
            require(before.equals(same.head().digest()),
                    "pure reconciliation policy collection changed the canonical writer head");
            var kind=RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE;
            if(expectClose){
                require(owned.size()==1&&owned.getFirst().kind()==kind,
                        "MISSING_PRIVATE_CLOSE_INPUT: genuine once/cause/attempt/source evidence did not produce one finite Close read");
                var expected=owned.getFirst();
                require(expected.contract().guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                        &&expected.contract().hasPureReplay(),"Close recovery cannot borrow an ordinary/terminal or non-replay read");
                long count=combined.stream().filter(read->read.kind()==kind).count();
                require(count==1&&combined.stream().anyMatch(read->read.kind()==kind
                        &&read.contract()==expected.contract()&&read.arguments().equals(expected.arguments())),
                        "Root aggregate omitted, duplicated or substituted the same installed private Close query");
            }else{
                require(owned.isEmpty()&&combined.stream().noneMatch(read->read.kind()==kind),
                        "unrelated original action acquired a private Close reconciliation read");
            }
            return List.copyOf(combined);
        });
    }
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
