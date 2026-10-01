// Saves one exact frame of a video as a JPEG poster.
import AVFoundation
import AppKit
let args = CommandLine.arguments
let generator = AVAssetImageGenerator(asset: AVURLAsset(url: URL(fileURLWithPath: args[1])))
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero
let frame = try generator.copyCGImage(at: CMTime(seconds: Double(args[3])!, preferredTimescale: 600), actualTime: nil)
let data = NSBitmapImageRep(cgImage: frame).representation(using: .jpeg, properties: [.compressionFactor: 0.82])!
try data.write(to: URL(fileURLWithPath: args[2]))
print("ok")
