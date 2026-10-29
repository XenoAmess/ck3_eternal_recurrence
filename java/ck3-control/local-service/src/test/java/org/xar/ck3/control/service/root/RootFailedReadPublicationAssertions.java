package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Requires a real failed native read through the installed public service. It never fabricates an unavailable/token/Driver. */
public final class RootFailedReadPublicationAssertions {
    private RootFailedReadPublicationAssertions() { }

    /** Arrange actual transport failure outside this helper, then invoke the real frozen Army public binding. */
    public static IllegalStateException requirePublicArmyFailure(RootApplicationSession root,
            PublicBindings actualBindings,PublicBindings.Arguments originalArguments)throws IOException,InterruptedException {
        Objects.requireNonNull(root);Objects.requireNonNull(actualBindings);Objects.requireNonNull(originalArguments);
        require(actualBindings.frozen(),"actual complete public registry must already be frozen");
        String predecessor=head(root);IllegalStateException original;
        try {
            actualBindings.lookup(PublicMethod.QUERY_ARMY_STRENGTHS).orElseThrow(()->new AssertionError("actual Army binding missing"))
                    .invoke(originalArguments);
            throw new AssertionError("MISSING_ACTUAL_READ_FAILURE: successful/absent dispatch cannot cover exception publication");
        }catch(IllegalStateException failure){original=failure;}
        requirePublished(root,predecessor);return original;
    }

    /** The supplied work must call the actual installed service; a hand-thrown exception cannot create the checked canonical event. */
    public static IllegalStateException requireCapabilitiesFailure(RootApplicationSession root,Instant deadline,
            RootApplicationSession.PublicCapabilitiesWork<?> actualInstalledService)throws IOException,InterruptedException {
        Objects.requireNonNull(actualInstalledService);String predecessor=head(root);IllegalStateException original;
        try {
            root.withPublicCapabilitiesObservation(deadline,actualInstalledService);
            throw new AssertionError("MISSING_ACTUAL_READ_FAILURE: actual service did not fail");
        }catch(IllegalStateException failure){original=failure;}
        requirePublished(root,predecessor);return original;
    }

    private static String head(RootApplicationSession root)throws IOException {
        return root.writer().locked(same->same.head().digest());
    }
    private static void requirePublished(RootApplicationSession root,String predecessor)throws IOException {
        root.writer().locked(same->{
            var event=same.head().state().toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD);
            require(event!=null&&event.isObject()&&event.path("predecessor_head_sha256").asText().equals(predecessor),
                    "exception escaped before its same-head queued failed read was canonically committed");
            var rows=event.get("read_rows");require(rows!=null&&rows.isArray(),"actual failed publication rows missing");
            var originals=root.archive().withSession(same);int failures=0;
            for(var metadata:rows){
                if(!metadata.path("row_kind").asText().equals(DriverReadHistoryPublisher.FAILED_ROW_KIND))continue;
                failures++;
                var rowReference=ExactRef.fromJson(metadata.get("row"));
                var row=DriverFailedReadHistoryRowProducer.decode(originals.loadMaterial(rowReference).bytes());
                require(!row.ok()&&!row.error().isBlank()&&row.index()==StrictJson.integer(metadata.get("index"),1,StrictJson.MAX_SAFE_INTEGER),
                        "failed READ acquired a successful/result row or changed its original history index");
                require(row.source().attempt().equals(ExactRef.fromJson(metadata.get("attempt")))
                        &&row.source().beforeDriver().equals(ExactRef.fromJson(metadata.get("before_driver"))),
                        "Root dropped/substituted the central original failed-attempt source");
                originals.loadMaterial(row.source().attempt());
            }
            require(failures==1,"one actual failed service call must publish exactly one original error row");
            var after=originals.loadMaterial(ExactRef.fromJson(event.get("after_driver"))).bytes();
            root.driver().authority().withFrozenFacts(same,frozen->{
                require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual published full Driver missing");
                var known=(DriverSnapshotFacts.Known)frozen.state();
                require(Arrays.equals(after,known.driver().encode())&&known.observation().isEmpty(),
                        "failed READ publication must publish actual full history and invalidate the old observation");
                return null;
            });
            return null;
        });
    }
    private static void require(boolean actual,String message){if(!actual)throw new AssertionError(message);}
}
