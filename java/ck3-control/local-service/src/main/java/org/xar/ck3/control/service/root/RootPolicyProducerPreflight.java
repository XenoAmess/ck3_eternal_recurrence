package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Pure request/encoding adapter for the versioned public Saved policy paths. It never writes a file, observes a
 * Game, copies a SAVE, acquires storage authority or qualifies a producer. Native originals and
 * current financial capacity still require the original Command/Guard and actual Runtime issuer.
 * Each typed overload retains its exact public schema and phase; neither aliases the other. */
public final class RootPolicyProducerPreflight {
    private RootPolicyProducerPreflight(){ }

    /** Public v1 remains an exact legacy mode; a mapped quote cannot enter this overload. */
    public static RootProfileBootstrapCommand.IssuerDeclarationRequest declarationRequest(
            RootProfileBootstrapCommand.SavedNativePolicyRequest request,RootBootstrapProtocol.Quote quote,
            FileRef quoteOriginal,byte[] capturedLine,String windowId,Path controlRoot,Path declarationTarget,
            long assetCap,long controlCap,long singleCap,int entryCap)throws IOException {
        Objects.requireNonNull(request);
        if(!"xar.java-root-initial-saved-native-policy-bootstrap/v1".equals(request.schema()))
            throw new IOException("exact public Saved-v1 request required");
        return declarationRequest(request.machineId(),request.reviewAtUtc(),request.target(),"INITIAL_SAVED_NATIVE_POLICY",
                quote,quoteOriginal,capturedLine,windowId,controlRoot,declarationTarget,assetCap,controlCap,singleCap,entryCap);
    }
    /** Typed mapped-v2 adapter only. The actual producer owns clone custody and fixed bytes. */
    public static RootProfileBootstrapCommand.IssuerDeclarationRequest declarationRequest(
            RootProfileBootstrapCommand.SavedMaterializedPolicyRequest request,RootBootstrapProtocol.Quote quote,
            FileRef quoteOriginal,byte[] capturedLine,String windowId,Path controlRoot,Path declarationTarget,
            long assetCap,long controlCap,long singleCap,int entryCap)throws IOException {
        Objects.requireNonNull(request);
        if(!"xar.java-root-initial-saved-native-policy-bootstrap/v2".equals(request.schema()))
            throw new IOException("exact public mapped Saved-v2 request required");
        return declarationRequest(request.machineId(),request.reviewAtUtc(),request.target(),"INITIAL_SAVED_MATERIALIZED_POLICY",
                quote,quoteOriginal,capturedLine,windowId,controlRoot,declarationTarget,assetCap,controlCap,singleCap,entryCap);
    }
    /** Checks the captured actual complete frame before the real metadata producer writes it. */
    private static RootProfileBootstrapCommand.IssuerDeclarationRequest declarationRequest(
            String machineId,String reviewAtUtc,String targetName,String expectedPhase,RootBootstrapProtocol.Quote quote,
            FileRef quoteOriginal,byte[] capturedLine,String windowId,Path controlRoot,Path declarationTarget,
            long assetCap,long controlCap,long singleCap,int entryCap)throws IOException {
        Objects.requireNonNull(quote);Objects.requireNonNull(quoteOriginal);
        Objects.requireNonNull(capturedLine);Objects.requireNonNull(controlRoot);Objects.requireNonNull(declarationTarget);
        Path target=Path.of(targetName),asset=target.getParent();
        if(asset==null||target.getFileName()==null)throw new IOException("exact policy file target required");
        if(!(quote instanceof RootBootstrapProtocol.OrdinaryQuote)
                ||!expectedPhase.equals(quote.phase())
                ||!machineId.equals(quote.machineId())||!reviewAtUtc.equals(quote.reviewAtUtc())
                ||!asset.equals(Path.of(quote.assetRoot())))
            throw new IOException("actual quote changed its public producer mode, machine, deadline or target parent");
        policyPlan(quote.outputs(),quote.outputDirectories(),quote.retainedInputs());
        if(!target.getFileName().toString().equals(quote.outputs().getFirst().fileName()))
            throw new IOException("actual policy quote changed the exact public target filename");
        if(!Arrays.equals(capturedLine,RootBootstrapProtocol.quoteLine(quote))
                ||capturedLine.length!=quoteOriginal.bytes()
                ||!DriverJson.sha256(capturedLine).equals(quoteOriginal.sha256()))
            throw new IOException("actual complete canonical LF quote differs from its exact original");
        Path original=Path.of(quoteOriginal.path());
        if(!original.isAbsolute()||!original.normalize().equals(original)||original.startsWith(asset)
                ||!controlRoot.isAbsolute()||!controlRoot.normalize().equals(controlRoot)
                ||!declarationTarget.isAbsolute()||!declarationTarget.normalize().equals(declarationTarget)
                ||!controlRoot.equals(declarationTarget.getParent())
                ||asset.startsWith(controlRoot)||controlRoot.startsWith(asset))
            throw new IOException("quote original/control roots must stay outside the closed policy asset root");
        return new RootProfileBootstrapCommand.IssuerDeclarationRequest(
                "xar.java-root-bootstrap-issuer-declaration-request/v1",machineId,reviewAtUtc,windowId,
                quoteOriginal,controlRoot.toString(),declarationTarget.toString(),assetCap,controlCap,singleCap,entryCap);
    }

    /** Validates typed source selection and calls only the existing public capacity encoder.
     * The caller is the actual Runtime issuer. These bytes alone are neither an issued file nor
     * admission; the real binding producer must still reopen the complete Native Guard. */
    public static byte[] encodeIssuedCapacity(CapacityRelease capacity,Declaration declaration,FileRef declarationRef,
            AssetCensus census,FileRef censusRef,Clock clock)throws IOException {
        Objects.requireNonNull(capacity);Objects.requireNonNull(declaration);Objects.requireNonNull(census);
        Objects.requireNonNull(declarationRef);Objects.requireNonNull(censusRef);Objects.requireNonNull(clock);
        if(!RUNTIME_POLICY_CAPACITY.equals(capacity.schema())||!DECLARATION.equals(declaration.schema())
                ||!CENSUS.equals(census.schema())||!RUNTIME_ISSUER.equals(capacity.issuerTask())
                ||!PURPOSE.equals(capacity.purpose())||!PURPOSE.equals(declaration.purpose()))
            throw new IOException("qualified current-Runtime v7 policy and ordinary declaration/census APIs required");
        policyPlan(declaration.outputs(),declaration.outputDirectories(),declaration.retainedInputs());
        if(!capacity.retainedAllocations().isEmpty()||census.retainedAllocatedUpperBytes()!=0
                ||!declarationRef.equals(capacity.declarationRef())||!declarationRef.equals(census.declarationRef())
                ||!censusRef.equals(capacity.censusRef())||!declaration.assetDirectory().equals(census.assetDirectory())
                ||List.of(capacity.machineId(),declaration.machineId(),census.machineId()).stream().distinct().count()!=1
                ||List.of(capacity.windowId(),declaration.windowId(),census.windowId()).stream().distinct().count()!=1
                ||capacity.jointMaximumChargedBytes()!=Math.addExact(declaration.assetMaximumChargedBytes(),declaration.controlMaximumChargedBytes()))
            throw new IOException("capacity changed actual policy roles, selected source refs, machine/window or root allocation");
        if(Instant.parse(census.observedAtUtc()).isBefore(Instant.parse(declaration.observedAtUtc()))
                ||Instant.parse(capacity.observedAtUtc()).isBefore(Instant.parse(census.observedAtUtc())))
            throw new IOException("capacity must follow its actual declaration and census");
        for(String observed:List.of(declaration.observedAtUtc(),census.observedAtUtc(),capacity.observedAtUtc()))
            if(clock.instant().isBefore(Instant.parse(observed)))throw new IOException("future actual authority observation");
        for(String review:List.of(declaration.reviewAtUtc(),census.reviewAtUtc(),capacity.reviewAtUtc()))
            if(!clock.instant().isBefore(Instant.parse(review))
                    ||Instant.parse(capacity.reviewAtUtc()).isAfter(Instant.parse(review)))
                throw new IOException("expired source or extended policy capacity review");
        return RootBootstrapOutputContract.encode(capacity);
    }
    private static void policyPlan(List<Output> outputs,List<String> directories,List<RetainedInput> retained)throws IOException {
        if(outputs.size()!=1||outputs.getFirst().kind()!=Kind.INITIAL_POLICY||!directories.isEmpty()||!retained.isEmpty())
            throw new IOException("only one exact INITIAL_POLICY without generated directories or production retention");
    }
}
