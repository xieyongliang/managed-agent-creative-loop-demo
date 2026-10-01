// Renders a slow push-in over a still photo as a 5-second vertical video.
import AVFoundation
import CoreGraphics
import ImageIO

let args = CommandLine.arguments
let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: args[1]) as CFURL, nil)!
let image = CGImageSourceCreateImageAtIndex(source, 0, nil)!
let output = URL(fileURLWithPath: args[2])
let focusX = Double(args[3])!, focusY = Double(args[4])!, startZoom = Double(args[5])!, endZoom = Double(args[6])!, drift = Double(args[7])!
try? FileManager.default.removeItem(at: output)
let W = 720, H = 1280, frames = 152
let writer = try AVAssetWriter(outputURL: output, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
  AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: W, AVVideoHeightKey: H,
  AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 2_200_000, AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel]])
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
  kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: W, kCVPixelBufferHeightKey as String: H])
writer.add(input)
guard writer.startWriting() else { fatalError(String(describing: writer.error)) }
writer.startSession(atSourceTime: .zero)
for i in 0..<frames {
  while !input.isReadyForMoreMediaData { usleep(2000) }
  var made: CVPixelBuffer?
  CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &made)
  let buffer = made!
  CVPixelBufferLockBaseAddress(buffer, [])
  let context = CGContext(data: CVPixelBufferGetBaseAddress(buffer), width: W, height: H, bitsPerComponent: 8,
                          bytesPerRow: CVPixelBufferGetBytesPerRow(buffer), space: CGColorSpaceCreateDeviceRGB(),
                          bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
  context.interpolationQuality = .high
  let t = Double(i) / Double(frames - 1)
  let ease = t * t * (3 - 2 * t)
  let zoom = startZoom + (endZoom - startZoom) * ease
  let size = Double(H) * zoom
  let fx = focusX + drift * (ease - 0.5), fy = 1 - focusY
  let x = min(0, max(Double(W) - size, Double(W) / 2 - fx * size))
  let y = min(0, max(Double(H) - size, Double(H) / 2 - fy * size))
  context.draw(image, in: CGRect(x: x, y: y, width: size, height: size))
  CVPixelBufferUnlockBaseAddress(buffer, [])
  adaptor.append(buffer, withPresentationTime: CMTime(value: CMTimeValue(i), timescale: 30))
}
input.markAsFinished()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
print(writer.status == .completed ? "ok" : "failed \(String(describing: writer.error))")
