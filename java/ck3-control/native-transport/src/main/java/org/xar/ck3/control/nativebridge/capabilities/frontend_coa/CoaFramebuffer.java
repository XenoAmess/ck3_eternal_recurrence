package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import javax.imageio.ImageIO;

/** Java image-domain implementation of the original bounded CoA comparisons and independent surface/UV calibration. */
public final class CoaFramebuffer {
    private CoaFramebuffer() { }
    /** Computation cancellation is DATA scheduling, never desktop or action permission. */
    @FunctionalInterface public interface SearchBudget {
        void check() throws IOException;
        static SearchBudget until(Clock clock,Instant deadline) {
            Objects.requireNonNull(clock);Objects.requireNonNull(deadline);
            return ()->{if(Thread.currentThread().isInterrupted() || !clock.instant().isBefore(deadline))
                throw new IOException("framebuffer computation deadline elapsed; no result or retry permission");};
        }
    }
    public static final List<Integer> SEARCH_SIDES = List.of(128, 160, 192, 224, 230, 256, 288, 320, 384, 448, 512);
    public record Size(int width, int height) { public Size { require(width > 0 && height > 0 && (long) width * height <= 16_777_216L, "bounded positive image size required"); } }
    public record Rect(int left, int top, int right, int bottom) {
        public Rect { require(left >= 0 && top >= 0 && right > left && bottom > top, "positive image rectangle required"); }
        public int width() { return right - left; } public int height() { return bottom - top; }
    }
    public record Point(double x, double y) { public Point { require(Double.isFinite(x) && Double.isFinite(y), "finite point required"); } }
    public record Affine(double xx, double xy, double x0, double yx, double yy, double y0) {
        public Affine { for (double value : new double[]{xx, xy, x0, yx, yy, y0}) require(Double.isFinite(value), "finite affine map required"); }
        public Point at(double x, double y) { return new Point(xx * x + xy * y + x0, yx * x + yy * y + y0); }
    }
    public static final class Image {
        private final Size size; private final int[] rgba;
        public Image(BufferedImage source) { this.size = new Size(source.getWidth(), source.getHeight()); rgba = source.getRGB(0, 0, size.width(), size.height(), null, 0, size.width()); }
        private Image(Size size, int[] rgba) { this.size = size; this.rgba = rgba.clone(); require(rgba.length == size.width() * size.height(), "pixel array size mismatch"); }
        public Size size() { return size; }
        public int rgb(int x, int y) { return x < 0 || y < 0 || x >= size.width() || y >= size.height() ? 0 : rgba[y * size.width() + x]; }
        public String pixelSha256() { return sha256(rgbBytes()).toUpperCase(java.util.Locale.ROOT); }
        public byte[] rgbBytes() { byte[] bytes = new byte[rgba.length * 3]; for (int i = 0; i < rgba.length; i++) { bytes[i * 3] = (byte) (rgba[i] >>> 16); bytes[i * 3 + 1] = (byte) (rgba[i] >>> 8); bytes[i * 3 + 2] = (byte) rgba[i]; } return bytes; }
        public BufferedImage buffered() { BufferedImage image = new BufferedImage(size.width(), size.height(), BufferedImage.TYPE_INT_ARGB); image.setRGB(0, 0, size.width(), size.height(), rgba, 0, size.width()); return image; }
        public Image crop(Rect rect) { require(rect.right() <= size.width() && rect.bottom() <= size.height(), "crop outside frame"); int[] output = new int[rect.width() * rect.height()]; for (int y = 0; y < rect.height(); y++) System.arraycopy(rgba, (y + rect.top()) * size.width() + rect.left(), output, y * rect.width(), rect.width()); return new Image(new Size(rect.width(), rect.height()), output); }
        public Image resize(int width, int height) {
            Size target=new Size(width,height);if(target.equals(size))return new Image(size,rgba);
            int[] horizontal=new int[width*size.height()];Filter[] xs=filters(size.width(),width),ys=filters(size.height(),height);
            for(int y=0;y<size.height();y++)for(int x=0;x<width;x++)horizontal[y*width+x]=filtered(rgba,y*size.width(),1,xs[x]);
            int[] output=new int[width*height];for(int y=0;y<height;y++)for(int x=0;x<width;x++)output[y*width+x]=filtered(horizontal,x,width,ys[y]);
            return new Image(target,output);
        }
        /** Area integration belongs only to the original global template scale stage. */
        private Image resizeArea(int width,int height) {
            if(width==size.width()&&height==size.height())return new Image(size,rgba);
            int[] out=new int[width*height];double sx=(double)size.width()/width,sy=(double)size.height()/height;
            for(int y=0;y<height;y++)for(int x=0;x<width;x++) {
                double left=x*sx,right=(x+1)*sx,top=y*sy,bottom=(y+1)*sy;int value=0;
                for(int shift:new int[]{0,8,16,24}){double sum=0;
                    for(int iy=(int)Math.floor(top);iy<Math.ceil(bottom);iy++)for(int ix=(int)Math.floor(left);ix<Math.ceil(right);ix++)
                        sum+=((rgb(Math.min(size.width()-1,ix),Math.min(size.height()-1,iy))>>>shift)&255)
                                *Math.max(0,Math.min(right,ix+1)-Math.max(left,ix))*Math.max(0,Math.min(bottom,iy+1)-Math.max(top,iy));
                    value|=Math.max(0,Math.min(255,(int)Math.rint(sum/(sx*sy))))<<shift;
                }out[y*width+x]=value;
            }return new Image(new Size(width,height),out);
        }
        private record Filter(int start,int[] coefficients) { }
        private static Filter[] filters(int source,int target) {
            Filter[] filters=new Filter[target];double scale=(double)source/target,support=Math.max(1,scale);
            for(int i=0;i<target;i++) {double center=(i+.5)*scale;int begin=Math.max(0,(int)(center-support+.5)),end=Math.min(source,(int)(center+support+.5));
                double[] weights=new double[end-begin];double total=0;for(int p=begin;p<end;p++){double weight=Math.max(0,1-Math.abs((p-center+.5)/support));weights[p-begin]=weight;total+=weight;}
                int[] coefficients=new int[weights.length];for(int p=0;p<weights.length;p++)coefficients[p]=(int)(weights[p]/total*(1<<22)+.5);
                filters[i]=new Filter(begin,coefficients);
            }return filters;
        }
        private static int filtered(int[] source,int offset,int stride,Filter filter) {
            int pixel=0;for(int shift:new int[]{0,8,16,24}){long sum=1<<21;for(int p=0;p<filter.coefficients.length;p++)sum+=(long)((source[offset+(filter.start+p)*stride]>>>shift)&255)*filter.coefficients[p];pixel|=(int)Math.max(0,Math.min(255,sum>>22))<<shift;}return pixel;
        }
        private int sample(double x, double y, boolean clamp) {
            int left = (int) Math.floor(x), top = (int) Math.floor(y); double fx = x - left, fy = y - top; int out = 0;
            for (int shift : new int[]{0, 8, 16, 24}) { double value = 0; for (int dy = 0; dy < 2; dy++) for (int dx = 0; dx < 2; dx++) {
                int px = left + dx, py = top + dy; if (clamp) { px = Math.max(0, Math.min(size.width() - 1, px)); py = Math.max(0, Math.min(size.height() - 1, py)); }
                value += ((rgb(px, py) >>> shift) & 255) * (dx == 0 ? 1 - fx : fx) * (dy == 0 ? 1 - fy : fy);
            } out |= Math.max(0, Math.min(255, (int) Math.round(value))) << shift; } return out;
        }
    }
    public record Png(String sha256, String base64, int bytes) {
        public Png { require(sha256 != null && sha256.matches("[0-9A-F]{64}") && base64 != null && bytes > 0, "PNG identity required"); }
    }
    public static Png png(Image image) {
        try { ByteArrayOutputStream output = new ByteArrayOutputStream(); require(ImageIO.write(image.buffered(), "PNG", output), "PNG encoder unavailable"); byte[] bytes = output.toByteArray(); return new Png(sha256(bytes).toUpperCase(java.util.Locale.ROOT), Base64.getEncoder().encodeToString(bytes), bytes.length); }
        catch (IOException failure) { throw new IllegalArgumentException("cannot encode PNG", failure); }
    }
    /** Original crop/frame PNGs carry RGB; normalized visible surfaces alone carry RGBA. */
    public static Png pngRgb(Image image) {
        BufferedImage rgb=new BufferedImage(image.size.width(),image.size.height(),BufferedImage.TYPE_INT_RGB);
        rgb.setRGB(0,0,image.size.width(),image.size.height(),image.rgba,0,image.size.width());return pngBuffered(rgb);
    }
    private static Png pngBuffered(BufferedImage image) {
        try{var output=new ByteArrayOutputStream();require(ImageIO.write(image,"PNG",output),"PNG encoder unavailable");byte[] raw=output.toByteArray();return new Png(sha256(raw).toUpperCase(java.util.Locale.ROOT),Base64.getEncoder().encodeToString(raw),raw.length);}
        catch(IOException failure){throw new IllegalArgumentException("cannot encode PNG",failure);}
    }
    public static Image reference(String encoded, String expectedSha256) {
        require(expectedSha256 != null && expectedSha256.matches("[0-9A-F]{64}"), "reference SHA256 requires uppercase hex"); text(encoded, 4 * ((512 * 1024 + 2) / 3)); require(encoded.length()%4==0,"reference PNG base64 requires original padding"); byte[] bytes = Base64.getDecoder().decode(encoded);
        require(bytes.length > 0 && bytes.length <= 512 * 1024 && sha256(bytes).equalsIgnoreCase(expectedSha256), "bounded reference PNG identity mismatch");
        byte[] signature = new byte[]{(byte)137,80,78,71,13,10,26,10}; require(bytes.length >= 24 && Arrays.equals(Arrays.copyOf(bytes, 8), signature), "reference payload must be PNG");
        // Validate IHDR dimensions before decompression, matching the producer's bounded image contract.
        int width = java.nio.ByteBuffer.wrap(bytes, 16, 4).getInt(), height = java.nio.ByteBuffer.wrap(bytes, 20, 4).getInt();
        require(width == height && width >= 32 && width <= 512, "reference PNG must be a bounded square canonical preview");
        try { BufferedImage decoded = ImageIO.read(new ByteArrayInputStream(bytes)); require(decoded != null && decoded.getWidth() == width && decoded.getHeight() == height, "reference PNG unreadable"); return new Image(decoded); }
        catch (IOException failure) { throw new IllegalArgumentException("reference PNG unreadable", failure); }
    }
    public static final class Mask {
        final Size size; final byte[] values;
        Mask(Size size, byte[] values) { this.size = size; this.values = values.clone(); require(values.length == size.width() * size.height(), "mask size mismatch"); }
        int at(int x, int y) { return x < 0 || y < 0 || x >= size.width() || y >= size.height() ? 0 : values[y * size.width() + x] & 255; }
        public int selectedPixels() { int count = 0; for (byte value : values) if (value != 0) count++; return count; }
        Mask erode(int radius) { return morph(this, radius, false); }
        Mask resize(Size output) { byte[] pixels = new byte[output.width() * output.height()]; for (int y = 0; y < output.height(); y++) for (int x = 0; x < output.width(); x++) pixels[y * output.width() + x] = (byte) at(Math.min(size.width()-1,(int)((x+.5)*size.width()/output.width())), Math.min(size.height()-1,(int)((y+.5)*size.height()/output.height()))); return new Mask(output, pixels); }
        Mask alpha(Image reference) { byte[] pixels = values.clone(); for (int i = 0; i < pixels.length; i++) pixels[i] = (byte) ((pixels[i] & 255) & (reference.rgba[i] >>> 24)); return new Mask(size, pixels); }
        public Png png() {var image=new BufferedImage(size.width(),size.height(),BufferedImage.TYPE_BYTE_GRAY);image.getRaster().setDataElements(0,0,size.width(),size.height(),values.clone());return pngBuffered(image);}
    }
    private static Mask morph(Mask mask, int radius, boolean dilate) {
        byte[] result = new byte[mask.values.length]; for (int y = 0; y < mask.size.height(); y++) for (int x = 0; x < mask.size.width(); x++) {
            int value = dilate ? 0 : 255; for (int dy = -radius; dy <= radius; dy++) for (int dx = -radius; dx <= radius; dx++) {
                int px = x + dx, py = y + dy; int sample = px < 0 || py < 0 || px >= mask.size.width() || py >= mask.size.height() ? (dilate ? 0 : 255) : mask.at(px, py);
                value = dilate ? Math.max(value, sample) : Math.min(value, sample);
            } result[y * mask.size.width() + x] = (byte) value;
        } return new Mask(mask.size, result);
    }
    private record Component(int area, Rect rect, double centerX, double centerY, int label) { }
    private record Components(List<Component> rows, int[] labels) { }
    private static Components components(Mask mask) {
        int width = mask.size.width(), height = mask.size.height(); int[] labels = new int[width * height]; List<Component> rows = new ArrayList<>(); int label = 0;
        for (int index = 0; index < labels.length; index++) {
            if (labels[index] != 0 || mask.values[index] == 0) continue; label++; ArrayDeque<Integer> pending = new ArrayDeque<>(); pending.add(index); labels[index] = label;
            int minX = width, minY = height, maxX = 0, maxY = 0, count = 0; long sumX = 0, sumY = 0;
            while (!pending.isEmpty()) { int here = pending.removeFirst(), x = here % width, y = here / width; count++; sumX += x; sumY += y; minX = Math.min(minX, x); minY = Math.min(minY, y); maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
                for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int px = x + dx, py = y + dy; if (px >= 0 && py >= 0 && px < width && py < height) { int neighbor = py * width + px; if (labels[neighbor] == 0 && mask.values[neighbor] != 0) { labels[neighbor] = label; pending.addLast(neighbor); } } }
            } rows.add(new Component(count, new Rect(minX, minY, maxX + 1, maxY + 1), (double) sumX / count, (double) sumY / count, label));
        } return new Components(List.copyOf(rows), labels);
    }
    public record Surface(String calibrationId, long bridgePid, Size framebufferSize, Rect rect, Mask mask,
            String beginPixelSha256, String completePixelSha256, int componentCount, int changedPixels, int selectedPixels) {
        public Surface { calibrationId = identifier(calibrationId); require(bridgePid > 0 && bridgePid <= 0xffffffffL, "positive uint32 PID required"); Objects.requireNonNull(framebufferSize); Objects.requireNonNull(rect); Objects.requireNonNull(mask); }
    }
    public static String identifier(String value) { require(value != null && value.matches("[A-Za-z0-9][A-Za-z0-9_-]{0,63}"), "calibration ID malformed"); return value; }
    public static Surface deriveSurface(String id, long pid, Image begin, Image complete) {
        require(begin.size.equals(complete.size), "calibration frame sizes differ"); byte[] pixels = new byte[begin.rgba.length]; int changed = 0;
        for (int i = 0; i < pixels.length; i++) if (difference(begin.rgba[i], complete.rgba[i]) >= 48) { pixels[i] = (byte)255; changed++; }
        require(changed >= 512, "two-state calibration changed too few pixels"); Mask input = new Mask(begin.size, pixels); Mask opened = morph(morph(input, 1, false), 1, true); Components found = components(opened);
        List<Component> candidates = found.rows.stream().filter(row -> row.rect.width() >= 32 && row.rect.height() >= 32 && row.area >= 512 && (double) row.rect.width() / row.rect.height() >= .55 && (double) row.rect.width() / row.rect.height() <= 1.8 && (double) row.area / (row.rect.width() * row.rect.height()) >= .12)
                .sorted(Comparator.comparingInt(Component::area).reversed().thenComparing(Comparator.comparingInt((Component row) -> row.rect.width() * row.rect.height()).reversed()).thenComparingInt(row -> row.rect.left()).thenComparingInt(row -> row.rect.top())).toList();
        require(!candidates.isEmpty(), "two-state calibration found no bounded CoA component"); Component selected = candidates.get(0); byte[] full = new byte[pixels.length]; for (int i = 0; i < full.length; i++) if (found.labels[i] == selected.label) full[i] = (byte)255;
        Mask closed = morph(morph(new Mask(begin.size, full), 2, true), 2, false); Rect rect = selected.rect; byte[] crop = new byte[rect.width() * rect.height()]; for (int y = 0; y < rect.height(); y++) for (int x = 0; x < rect.width(); x++) crop[y * rect.width() + x] = (byte)closed.at(x + rect.left(), y + rect.top());
        Mask mask = new Mask(new Size(rect.width(), rect.height()), crop); require(mask.selectedPixels() >= 512, "calibration mask empty");
        return new Surface(id, pid, begin.size, rect, mask, begin.pixelSha256(), complete.pixelSha256(), candidates.size(), changed, mask.selectedPixels());
    }
    public record UvCalibration(Surface surface, Affine affine, List<Point> anchorPositions, List<Point> observedAnchorCenters,
            List<Double> reprojectionErrors, String anchorBasePixelSha256, String anchorsCompletePixelSha256) {
        public UvCalibration { Objects.requireNonNull(surface); Objects.requireNonNull(affine); anchorPositions = List.copyOf(anchorPositions); observedAnchorCenters = List.copyOf(observedAnchorCenters); reprojectionErrors = List.copyOf(reprojectionErrors); require(anchorPositions.size() == 9 && observedAnchorCenters.size() == 9 && reprojectionErrors.size() == 9, "nine anchors required"); }
    }
    public static UvCalibration deriveUv(Surface surface, Image base, Image complete) {
        require(base.size.equals(surface.framebufferSize()) && complete.size.equals(base.size), "anchor frame size drift"); Rect rect = surface.rect(); Size size = surface.mask.size; byte[] pixels = new byte[size.width() * size.height()];
        for (int y = 0; y < size.height(); y++) for (int x = 0; x < size.width(); x++) if (surface.mask.at(x, y) > 0 && difference(base.rgb(x + rect.left(), y + rect.top()), complete.rgb(x + rect.left(), y + rect.top())) >= 48) pixels[y * size.width() + x] = (byte)255;
        Components found = components(morph(morph(new Mask(size, pixels), 1, false), 1, true)); int maxArea = Math.max(16, (int)Math.rint(surface.selectedPixels() * .04));
        List<Component> candidates = found.rows.stream().filter(row -> row.rect.width() >= 3 && row.rect.height() >= 3 && row.area >= 9 && row.area <= maxArea && (double)row.rect.width() / row.rect.height() >= .45 && (double)row.rect.width() / row.rect.height() <= 2.2).sorted(Comparator.comparingDouble(Component::centerY).thenComparingDouble(Component::centerX)).toList();
        require(candidates.size() == 9, "anchor calibration did not isolate exactly nine native markers"); List<Point> observed = new ArrayList<>(), canonical = new ArrayList<>();
        for (int row = 0; row < 3; row++) { List<Component> ordered = candidates.subList(row * 3, row * 3 + 3).stream().sorted(Comparator.comparingDouble(Component::centerX)).toList(); for (int col = 0; col < 3; col++) { Component marker = ordered.get(col); observed.add(new Point((float)(marker.centerX + rect.left()), (float)(marker.centerY + rect.top()))); canonical.add(new Point(.3 + col * .2, .3 + row * .2)); } }
        // All nine markers must fit one affine map; a rejected/outlier marker never grants registration.
        double[][] normal = new double[3][3]; double[] rightX = new double[3], rightY = new double[3];
        require(hasAllInlierModel(canonical,observed),"anchor calibration could not fit all markers to one affine UV map");
        for (int i = 0; i < 9; i++) { double[] v = {(float)canonical.get(i).x(), (float)canonical.get(i).y(), 1}; for (int row = 0; row < 3; row++) { rightX[row] += v[row] * (float)observed.get(i).x(); rightY[row] += v[row] * (float)observed.get(i).y(); for (int col = 0; col < 3; col++) normal[row][col] += v[row] * v[col]; } }
        double[] x = solve(normal, rightX), y = solve(normal, rightY); Affine affine = new Affine(x[0], x[1], x[2], y[0], y[1], y[2]); List<Double> errors = new ArrayList<>();
        for (int i = 0; i < 9; i++) {Point mapped=affine.at((float)canonical.get(i).x(),(float)canonical.get(i).y());float dx=(float)mapped.x()-(float)observed.get(i).x(),dy=(float)mapped.y()-(float)observed.get(i).y();double error=(float)Math.sqrt(dx*dx+dy*dy);require(error<=2.5,"anchor calibration reprojection error exceeds the bounded contract");errors.add(error);}
        return new UvCalibration(surface, affine, canonical, observed, errors, base.pixelSha256(), complete.pixelSha256());
    }
    /** All nine points must be inliers before refinement; an outlier can never be silently dropped. */
    private static boolean hasAllInlierModel(List<Point> canonical,List<Point> observed) {
        for(int a=0;a<7;a++)for(int b=a+1;b<8;b++)for(int c=b+1;c<9;c++) {
            int[] indices={a,b,c};double[][] matrix=new double[3][3];double[] x=new double[3],y=new double[3];
            for(int n=0;n<3;n++){int at=indices[n];matrix[n]=new double[]{(float)canonical.get(at).x(),(float)canonical.get(at).y(),1};x[n]=(float)observed.get(at).x();y[n]=(float)observed.get(at).y();}
            try{double[] sx=solve(matrix,x),sy=solve(matrix,y);boolean all=true;
                for(int n=0;n<9;n++){double px=(float)canonical.get(n).x(),py=(float)canonical.get(n).y();double dx=sx[0]*px+sx[1]*py+sx[2]-(float)observed.get(n).x(),dy=sy[0]*px+sy[1]*py+sy[2]-(float)observed.get(n).y();if(dx*dx+dy*dy>2.25){all=false;break;}}
                if(all)return true;
            }catch(IllegalArgumentException singular){/* Collinear marker triples are not a model. */}
        }return false;
    }
    private static double[] solve(double[][] matrix, double[] target) { double[][] rows = new double[3][4]; for (int y = 0; y < 3; y++) { System.arraycopy(matrix[y], 0, rows[y], 0, 3); rows[y][3] = target[y]; }
        for (int col = 0; col < 3; col++) { int pivot = col; for (int y = col + 1; y < 3; y++) if (Math.abs(rows[y][col]) > Math.abs(rows[pivot][col])) pivot = y; require(Math.abs(rows[pivot][col]) > 1e-12, "singular affine fit"); double[] swap = rows[col]; rows[col] = rows[pivot]; rows[pivot] = swap; double scale = rows[col][col]; for (int x = col; x < 4; x++) rows[col][x] /= scale; for (int y = 0; y < 3; y++) if (y != col) { scale = rows[y][col]; for (int x = col; x < 4; x++) rows[y][x] -= scale * rows[col][x]; } }
        return new double[]{rows[0][3], rows[1][3], rows[2][3]}; }
    private static int difference(int first, int second) { return Math.max(Math.abs((first & 255) - (second & 255)), Math.max(Math.abs((first >>> 8 & 255) - (second >>> 8 & 255)), Math.abs((first >>> 16 & 255) - (second >>> 16 & 255)))); }
    public record Metrics(int maskPixels, double meanAbsoluteError, double colorMse, double edgeLoss, List<List<Optional<Double>>> spatialMeanAbsoluteError8x8) {
        public Metrics { spatialMeanAbsoluteError8x8 = spatialMeanAbsoluteError8x8.stream().map(List::copyOf).toList(); }
        public String contract() { return "masked-srgb8-mae-mse-gradient-l1-spatial-8x8-v1"; }
    }
    public static Metrics metrics(Image reference, Image observed, Mask mask) {
        require(reference.size.equals(observed.size) && reference.size.equals(mask.size), "comparison sizes differ"); int selected = mask.selectedPixels(); require(selected > 0, "comparison mask empty"); double[] firstGradient = gradient(reference), secondGradient = gradient(observed); double mae = 0, mse = 0, edge = 0; double[] pixel = new double[mask.values.length];
        for (int i = 0; i < pixel.length; i++) { for (int shift : new int[]{0,8,16}) { double delta = ((observed.rgba[i] >>> shift & 255) - (reference.rgba[i] >>> shift & 255)) / 255.0; pixel[i] += Math.abs(delta) / 3; if (mask.values[i] != 0) { mae += Math.abs(delta); mse += delta * delta; } } if (mask.values[i] != 0) edge += Math.abs(firstGradient[i] - secondGradient[i]) / 255; }
        List<List<Optional<Double>>> spatial = new ArrayList<>(); int side = reference.size.width();
        for (int gy = 0; gy < 8; gy++) { List<Optional<Double>> row = new ArrayList<>(); for (int gx = 0; gx < 8; gx++) { double sum = 0; int count = 0; for (int y = gy * side / 8; y < (gy + 1) * side / 8; y++) for (int x = gx * side / 8; x < (gx + 1) * side / 8; x++) { int i = y * side + x; if (mask.values[i] != 0) { sum += pixel[i]; count++; } } row.add(count == 0 ? Optional.empty() : Optional.of(sum / count)); } spatial.add(row); }
        return new Metrics(selected, mae / (selected * 3), mse / (selected * 3), edge / selected, spatial);
    }
    private static int reflect(int value, int maximum) { if (maximum == 1) return 0; return value < 0 ? -value : value >= maximum ? 2 * maximum - value - 2 : value; }
    private static double[] gradient(Image image) { int width = image.size.width(), height = image.size.height(); int[] gray = new int[image.rgba.length]; for (int i = 0; i < gray.length; i++) gray[i] = ((image.rgba[i] >>> 16 & 255)*4899 + (image.rgba[i] >>> 8 & 255)*9617 + (image.rgba[i] & 255)*1868 + 8192) >> 14; double[] out = new double[gray.length];
        int[][] kx = {{-1,0,1},{-2,0,2},{-1,0,1}}, ky = {{-1,-2,-1},{0,0,0},{1,2,1}};
        for (int y = 0; y < height; y++) for (int x = 0; x < width; x++) { int dx = 0, dy = 0; for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) { int value = gray[reflect(y + j, height) * width + reflect(x + i, width)]; dx += value * kx[j + 1][i + 1]; dy += value * ky[j + 1][i + 1]; } out[y * width + x] = Math.min(255, (int)Math.hypot(dx, dy)); } return out;
    }
    public record SurfaceCapture(Rect rect, Png crop, Png alignedContent, int captureSide, int surfaceMaskPixels) { }
    public record Comparison(String locatorContract, boolean searchedWholeFramebuffer, boolean referenceUsedForLocalization,
            boolean referenceUsedForRegistration, SurfaceCapture bestMatch, int erosionRadiusPixels, Metrics metrics,
            List<ScaleCandidate> scaleCandidates, Optional<Alignment> alignment) { public Comparison { scaleCandidates = List.copyOf(scaleCandidates); alignment = Objects.requireNonNull(alignment); } }
    private record Aligned(Image image, Mask mask) { }
    private static Aligned align(Image framebuffer, UvCalibration calibration, int side) {
        require(side >= 32 && side <= 512 && framebuffer.size.equals(calibration.surface().framebufferSize()), "capture size or framebuffer drift"); int[] pixels = new int[side * side]; byte[] mask = new byte[pixels.length]; Rect rect = calibration.surface().rect();
        // OpenCV's original warpAffine uses 10-bit affine deltas and a 5-bit linear interpolation table.
        var a=calibration.affine();double denominator=side-1;double xx=a.xx()/denominator,xy=a.xy()/denominator,yx=a.yx()/denominator,yy=a.yy()/denominator;
        for (int y = 0; y < side; y++) for (int x = 0; x < side; x++) {
            int dx=(int)Math.rint(xx*x*1024),dy=(int)Math.rint(yx*x*1024);
            int baseX=(int)Math.rint((xy*y+a.x0())*1024),baseY=(int)Math.rint((yy*y+a.y0())*1024);
            double linearX=((baseX+dx+16)>>5)/32.0,linearY=((baseY+dy+16)>>5)/32.0;
            int nearestX=(baseX+dx+512)>>10,nearestY=(baseY+dy+512)>>10,i=y*side+x;
            pixels[i]=framebuffer.sample(linearX,linearY,false)|0xff000000;
            mask[i]=(byte)calibration.surface().mask().at(nearestX-rect.left(),nearestY-rect.top());
        }
        return new Aligned(new Image(new Size(side, side), pixels), new Mask(new Size(side, side), mask));
    }
    private static Image visible(Aligned aligned) { int[] pixels = aligned.image.rgba.clone(); for (int i = 0; i < pixels.length; i++) pixels[i] = pixels[i] & 0xffffff | (aligned.mask.values[i] & 255) << 24; return new Image(aligned.image.size, pixels); }
    public static SurfaceCapture capture(Image framebuffer, UvCalibration calibration, int side) { Aligned aligned = align(framebuffer, calibration, side); Rect rect = calibration.surface().rect(); return new SurfaceCapture(rect, pngRgb(framebuffer.crop(rect)), png(visible(aligned)), side, aligned.mask.selectedPixels()); }
    public static Comparison compareV3(Image reference, Image framebuffer, UvCalibration calibration) {
        Aligned aligned = align(framebuffer, calibration, reference.size.width()); int radius = Math.max(1, (int)Math.rint(reference.size.width() * .02)); Mask mask = aligned.mask.erode(radius).alpha(reference);
        return new Comparison("two-solid-state-surface-nine-marker-affine-uv-v3", false, false, false, new SurfaceCapture(calibration.surface.rect, pngRgb(framebuffer.crop(calibration.surface.rect)), png(visible(aligned)), reference.size.width(), aligned.mask.selectedPixels()), radius, metrics(reference, aligned.image, mask), List.of(), Optional.empty());
    }
    public static Comparison compareV2(Image reference, Image framebuffer, Surface calibration) {
        require(framebuffer.size.equals(calibration.framebufferSize()), "framebuffer size drift"); Image crop = framebuffer.crop(calibration.rect()); Image normalized = crop.resize(reference.size.width(), reference.size.height()); Mask mask = calibration.mask.resize(reference.size); Aligned aligned = new Aligned(normalized, mask); int radius = Math.max(1, (int)Math.rint(reference.size.width() * .02));
        return new Comparison("two-solid-state-reference-independent-surface-v2", false, false, false, new SurfaceCapture(calibration.rect, pngRgb(crop), png(visible(aligned)), reference.size.width(), mask.selectedPixels()), radius, metrics(reference, normalized, mask.erode(radius).alpha(reference)), List.of(), Optional.empty());
    }
    public record ScaleCandidate(int side, int x, int y, double locatorLoss, int secondDistinctX, int secondDistinctY, double secondDistinctLoss, double distinctMargin) { }
    public record Alignment(int candidateCount, Rect outerRect, Rect contentRect, double contentToOuterRatio, double alignmentLoss) { }
    private static Mask shield(Image image) { int side = image.size.width(); double[][] polygon = {{0,0},{side-1,0},{side-1,Math.rint((side-1)*.72)},{Math.rint((side-1)*.88),Math.rint((side-1)*.88)},{Math.rint((side-1)*.5),side-1},{Math.rint((side-1)*.12),Math.rint((side-1)*.88)},{0,Math.rint((side-1)*.72)}}; byte[] pixels = new byte[side*side];
        for (int y = 0; y < side; y++) for (int x = 0; x < side; x++) { boolean inside = false; for (int i=0,j=polygon.length-1;i<polygon.length;j=i++) if ((polygon[i][1]>y)!=(polygon[j][1]>y) && x < (polygon[j][0]-polygon[i][0])*(y-polygon[i][1])/(polygon[j][1]-polygon[i][1])+polygon[i][0]) inside=!inside; if (inside) pixels[y*side+x]=(byte)(image.rgba[y*side+x]>>>24); }
        // fillPoly includes its rasterized polygon boundary, including the right and bottom edges.
        for(int i=0,j=polygon.length-1;i<polygon.length;j=i++) {
            int x=(int)polygon[j][0],y=(int)polygon[j][1],endX=(int)polygon[i][0],endY=(int)polygon[i][1];
            int dx=Math.abs(endX-x),dy=-Math.abs(endY-y),stepX=x<endX?1:-1,stepY=y<endY?1:-1,error=dx+dy;
            while(true){pixels[y*side+x]=(byte)(image.rgba[y*side+x]>>>24);if(x==endX&&y==endY)break;int twice=2*error;if(twice>=dy){error+=dy;x+=stepX;}if(twice<=dx){error+=dx;y+=stepY;}}
        }
        return new Mask(image.size, pixels); }
    /** Exact exhaustive candidate search, with no reference-driven pruning of accepted scales. Runtime qualification remains separate. */
    public static Comparison compareV1(Image reference, Image framebuffer, List<Integer> searchSides) {
        try{return compareV1(reference,framebuffer,searchSides,()->{});}catch(IOException cancelled){throw new UncheckedIOException(cancelled);}
    }
    /** Exhaustive original candidate domain, cancellable before any public result is published. */
    public static Comparison compareV1(Image reference,Image framebuffer,List<Integer> searchSides,SearchBudget budget)throws IOException {
        Objects.requireNonNull(budget).check();require(!searchSides.isEmpty(), "search sides required"); List<ScaleCandidate> candidates = new ArrayList<>(); double[] frameGradient=gradient(framebuffer);
        for(int side:searchSides){ budget.check();require(side>=32 && side<=Math.min(framebuffer.size.width(),framebuffer.size.height()),"search side outside frame"); Image template=reference.resizeArea(side,side); Mask mask=shield(template); double[] templateGradient=gradient(template); double best=Double.POSITIVE_INFINITY;int bx=0,by=0;
            for(int y=0;y<=framebuffer.size.height()-side;y++)for(int x=0;x<=framebuffer.size.width()-side;x++){if((x&31)==0)budget.check();double loss=locator(framebuffer,frameGradient,template,templateGradient,mask,x,y);if(loss<best){best=loss;bx=x;by=y;}}
            double second=Double.POSITIVE_INFINITY;int sx=0,sy=0;for(int y=0;y<=framebuffer.size.height()-side;y++)for(int x=0;x<=framebuffer.size.width()-side;x++)if(Math.abs(x-bx)>side||Math.abs(y-by)>side){if((x&31)==0)budget.check();double loss=locator(framebuffer,frameGradient,template,templateGradient,mask,x,y);if(loss<second){second=loss;sx=x;sy=y;}}
            candidates.add(new ScaleCandidate(side,bx,by,best,sx,sy,second,second-best)); }
        candidates.sort(Comparator.comparingDouble(ScaleCandidate::locatorLoss).thenComparingInt(ScaleCandidate::side)); ScaleCandidate best=candidates.get(0);Rect outer=new Rect(best.x(),best.y(),best.x()+best.side(),best.y()+best.side());int radius=Math.max(1,(int)Math.rint(reference.size.width()*.025));Mask mask=shield(reference).erode(radius);double bestLoss=Double.POSITIVE_INFINITY;Image bestImage=null;Rect content=null;Metrics bestMetrics=null;int count=0;
        for(double ratio:new double[]{.82,.85,.875,.90,.925,.95,1}){budget.check();int side=Math.max(1,(int)Math.rint(best.side()*ratio));for(double oy:new double[]{-.025,0,.025})for(double ox:new double[]{-.025,0,.025}){int left=outer.left()+(best.side()-side)/2+(int)Math.rint(best.side()*ox),top=outer.top()+(best.side()-side)/2+(int)Math.rint(best.side()*oy);if(left<outer.left()||top<outer.top()||left+side>outer.right()||top+side>outer.bottom())continue;Rect rect=new Rect(left,top,left+side,top+side);Image image=framebuffer.crop(rect).resize(reference.size.width(),reference.size.height());Metrics metrics=metrics(reference,image,mask);double loss=.62*metrics.colorMse()+.38*metrics.edgeLoss();count++;if(loss<bestLoss||(loss==bestLoss&&(content==null||side>content.width()||(side==content.width()&&(left<content.left()||(left==content.left()&&top<content.top())))))){bestLoss=loss;bestImage=image;content=rect;bestMetrics=metrics;}}}
        budget.check();require(bestImage!=null && content!=null && bestMetrics!=null,"no bounded content alignment");return new Comparison("full-client-global-shield-mask-color72-edge28-v1",true,true,true,new SurfaceCapture(outer,pngRgb(framebuffer.crop(outer)),pngRgb(bestImage),reference.size.width(),mask.selectedPixels()),radius,bestMetrics,candidates,Optional.of(new Alignment(count,outer,content,(double)content.width()/best.side(),bestLoss)));
    }
    private static double locator(Image frame,double[] fg,Image template,double[] tg,Mask mask,int x,int y){double square=0,te=0,fe=0,edge=0,tge=0,fge=0;int side=template.size.width();for(int j=0;j<side;j++)for(int i=0;i<side;i++){int ti=j*side+i;if(mask.values[ti]==0)continue;double weight=1;int fi=(y+j)*frame.size.width()+x+i;for(int shift:new int[]{0,8,16}){double t=template.rgba[ti]>>>shift&255,f=frame.rgba[fi]>>>shift&255;square+=weight*(t-f)*(t-f);te+=weight*t*t;fe+=weight*f*f;}edge+=weight*tg[ti]*fg[fi];tge+=weight*tg[ti]*tg[ti];fge+=weight*fg[fi]*fg[fi];}double color=square/Math.sqrt(te*fe),corr=edge/Math.sqrt(tge*fge);if(!Double.isFinite(color))color=1;if(!Double.isFinite(corr))corr=0;return .72f*(float)color+.28f*(1f-(float)corr);}
}
