package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Input;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.VerifiedData;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.DecodeMode;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.DefenderStock;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.Selection;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.StockWork;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalStockCodec;

/** One installed Root's actual stock source owner. No Native query or action is issued here. */
public final class RootArmyStockReadRuntime implements ArmyWarSupplementalReads.StockAdmissionPort,AutoCloseable {
    /** Explicit source facts only. Construction does not verify the Release closure or mint Admission. */
    public record Configuration(Input input,RootH2743StockPredicateAdmission.Limits limits,ExactRef pair,ExactRef pins) {
        public Configuration {
            Objects.requireNonNull(input);Objects.requireNonNull(limits);source(pair);source(pins);
            StrictJson.require(Path.of(pair.path()).equals(input.pairPath())&&Path.of(pins.path()).equals(input.pinsPath())
                    &&!input.pairPath().equals(input.pinsPath()),"stock pair and independent pins must retain their exact distinct configured originals");
        }
    }
    public record Sources(ExactRef runtime,ExactRef issuer,ExactRef verifier,ExactRef stockDecoder,ExactRef physical) {
        public Sources {for(ExactRef ref:List.of(runtime,issuer,verifier,stockDecoder,physical))source(ref);}
        public List<ExactRef> closure(){return List.of(runtime,issuer,verifier,stockDecoder,physical);}
    }
    private final RootRuntimeContext context;
    private final Configuration configuration;
    private final Sources sources;
    private final RootManagedSessionScope physical;
    private final ConfiguredOriginals configuredOriginals;
    private RootH2743StockPredicateAdmission owner;
    private IOException bindFailure;
    private boolean closed;
    private boolean resourcesClosed;

    public RootArmyStockReadRuntime(RootRuntimeContext actual,Sources sources,Configuration configuration)throws IOException {
        context=Objects.requireNonNull(actual);this.sources=Objects.requireNonNull(sources);this.configuration=Objects.requireNonNull(configuration);
        requireSources();physical=RootManagedSessionScope.bind(context,sources.closure());
        configuredOriginals=ConfiguredOriginals.retain(configuration);
    }
    public Configuration configuration(){return configuration;}
    public Sources sources(){return sources;}
    /** Called only by the identical catalog family. The central read authority owns all read permission. */
    @Override public DefenderStock withAdmission(Selection selected,PlanningReadReceipt receipt,Complete before,Complete after,
            DecodeMode mode,StockWork work) {
        Objects.requireNonNull(selected);Objects.requireNonNull(receipt);Objects.requireNonNull(before);Objects.requireNonNull(after);
        Objects.requireNonNull(mode);Objects.requireNonNull(work);
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);
            requireOriginal(selected,receipt,before,after,mode);
            if(mode==DecodeMode.ARCHIVED) {
                var archive=context.archive().withSession(same);
                NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
                RootGuardEvidence.requireHistory(receipt.before().binding(),archive,same);
                RootGuardEvidence.requireHistory(receipt.after().binding(),archive,same);
                // Historical DATA uses the original configured pair and pins, never a new live Admission.
                requireConfiguredOriginals();
                VerifiedData data=RootH2743StockPredicateAdmission.verifyDataOnly(configuration.input(),configuration.limits());
                DefenderStock value=work.normalize(data);requireResult(selected,receipt,before,after,value);
                requireConfiguredOriginals();return value;
            }
            synchronized(this){need(!closed,"stock runtime is retired");}
            return context.collector().currentHeldOriginal(same,receipt.request(),lease->{
                Complete actual=lease.frame();
                // An archive-loaded Complete is DATA. Only the collector's exact original object enters Admission.
                need(actual.equals(before),"stock archived before differs from the complete actual held original");
                try {
                    return physical.withScope(()->{
                        physical.requireFrame(same,actual);requireConfiguredOriginals();
                        RootH2743StockPredicateAdmission issuer=owner();
                        return issuer.withAdmission(same,actual,admission->{
                            DefenderStock value=work.normalize(admission.data(same,actual));
                            requireResult(selected,receipt,before,after,value);requireConfiguredOriginals();
                            // The native stock mailbox sequence is distinct from the outer query sequence.
                            issuer.acceptMailbox(admission,same,actual,value.actualMailboxSequence());return value;
                        });
                    });
                } catch(InterruptedException interrupted) {
                    Thread.currentThread().interrupt();throw new IOException("actual stock source scope interrupted",interrupted);
                }
            });
        } catch(IOException unavailable){throw new UncheckedIOException("actual Root stock admission unavailable",unavailable);}
    }
    private void requireOriginal(Selection selected,PlanningReadReceipt receipt,Complete before,Complete after,DecodeMode mode)throws IOException {
        need(ArmyWarSupplementalReads.kind(selected.operation())==ArmyWarSupplementalReads.Kind.DEFENDER_BASELINE
                &&receipt.request().before().equals(selected.original().before())
                &&receipt.request().source().equals(selected.original().source())
                &&receipt.request().sessionId().equals(selected.original().sessionId())
                &&receipt.request().operation().equals(selected.operation())
                &&receipt.request().arguments().equals(ArmyWarSupplementalReads.arguments(selected)),"stock work crossed its original typed read selection");
        need(before.identity().equals(receipt.before().binding().observed())
                &&after.identity().equals(receipt.after().binding().observed()),"stock work replaced its two original guard frames");
        need(before.source().equals(selected.original().source())&&after.source().equals(before.source())
                &&before.sessionId().equals(selected.original().sessionId())&&after.sessionId().equals(before.sessionId()),
                "stock read crossed its original Game/source/session");
        if(mode==DecodeMode.LIVE)need(before.source().equals(context.source())&&before.sessionId().equals(context.game().sessionId())
                &&before.identity().game().equals(context.game().generation()),"stock live read crossed its actual Root Game/source/session");
        RootArmyReadPacketVerifier.require(selected.context(),selected.operation(),ArmyWarSupplementalReads.nativeArguments(),receipt);
    }
    private static void requireResult(Selection selected,PlanningReadReceipt receipt,Complete before,Complete after,DefenderStock result)throws IOException {
        need(result!=null&&result.selection().equals(selected)
                &&result.nativeResult().equals(receipt.original().originalResultToken().orElseThrow())
                &&result.before().equals(new org.xar.ck3.control.application.action.RawJson(org.xar.ck3.control.application.driver.DriverJson.encode(before.semantic())))
                &&result.after().equals(new org.xar.ck3.control.application.action.RawJson(org.xar.ck3.control.application.driver.DriverJson.encode(after.semantic()))),
                "stock normalizer returned another native original or before/after pair");
    }
    private synchronized RootH2743StockPredicateAdmission owner()throws IOException {
        need(!closed,"stock runtime is retired");
        if(bindFailure!=null)throw new IOException("original stock source binding failed; the installed owner cannot be replaced",bindFailure);
        if(owner==null) {
            try {owner=RootH2743StockPredicateAdmission.bind(context,physical,configuration.input(),configuration.limits());}
            catch(IOException failure){bindFailure=failure;throw failure;}
            catch(RuntimeException failure){bindFailure=new IOException("original stock source qualification rejected",failure);throw bindFailure;}
        }
        return owner;
    }
    private void requireConfiguredOriginals()throws IOException {configuredOriginals.requireCurrent();}
    /** Original installation custody only. A fresh same-content path is never a new identity basis.
     * Package scope lets the filesystem regression exercise this exact producer/consumer path
     * without constructing a Game, collector frame or stock admission. */
    static final class ConfiguredOriginals {
        private final List<SharedSourceFiles.Witness> witnesses;
        private ConfiguredOriginals(List<SharedSourceFiles.Witness> witnesses){this.witnesses=List.copyOf(witnesses);}
        static ConfiguredOriginals retain(Configuration configuration)throws IOException {
            Objects.requireNonNull(configuration);var retained=new java.util.ArrayList<SharedSourceFiles.Witness>();
            for(ExactRef original:List.of(configuration.pair(),configuration.pins())) {
                var witness=SharedSourceFiles.observe(Path.of(original.path()));
                need(witness.source().bytes()==original.bytes()&&witness.source().sha256().equals(original.sha256())
                        &&Path.of(witness.source().path()).equals(Path.of(original.path())),"stock pair/pins original differs from its installed exact source");
                SharedSourceFiles.assertUnchanged(witness);retained.add(witness);
            }
            var result=new ConfiguredOriginals(retained);result.requireCurrent();return result;
        }
        void requireCurrent()throws IOException {
            for(SharedSourceFiles.Witness original:witnesses)SharedSourceFiles.assertUnchanged(original);
        }
    }
    private void requireSources()throws IOException {
        var plan=context.game().launchPlan().sources();
        for(Class<?> type:List.of(RootArmyStockReadRuntime.class,RootH2743StockPredicateAdmission.class,
                H2743StockPredicateAdmission.class,ArmyWarSupplementalStockCodec.class,RootManagedSessionScope.class))plan.requireLoadedClass(type);
        for(ExactRef ref:sources.closure()) {
            need(plan.review().completeRuntimeSources().stream().anyMatch(actual->Path.of(actual.path()).equals(Path.of(ref.path()))
                    &&actual.bytes()==ref.bytes()&&actual.sha256().equals(ref.sha256())),"stock implementation source is outside the actual reviewed deployment closure");
        }
    }
    /** Actual Catalog retirement owns this call. Archive DATA replay remains available without reopening live custody. */
    @Override public synchronized void close()throws IOException {
        closed=true;if(resourcesClosed)return;if(owner!=null)owner.close();resourcesClosed=true;
    }
    private static void source(ExactRef ref){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"nonempty exact stock source required");}
    private static void need(boolean ok,String reason)throws IOException {if(!ok)throw new IOException(reason);}
}
