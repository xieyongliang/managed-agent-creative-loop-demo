// Adds an audio track to a video without re-encoding the picture.
import AVFoundation

let args = CommandLine.arguments
let video = AVURLAsset(url: URL(fileURLWithPath: args[1])), audio = AVURLAsset(url: URL(fileURLWithPath: args[2]))
let output = URL(fileURLWithPath: args[3])
try? FileManager.default.removeItem(at: output)
let mix = AVMutableComposition()
let picture = video.tracks(withMediaType: .video)[0], sound = audio.tracks(withMediaType: .audio)[0]
let length = video.duration
let pictureTrack = mix.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
try pictureTrack.insertTimeRange(CMTimeRange(start: .zero, duration: length), of: picture, at: .zero)
pictureTrack.preferredTransform = picture.preferredTransform
let soundTrack = mix.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
try soundTrack.insertTimeRange(CMTimeRange(start: .zero, duration: CMTimeMinimum(length, audio.duration)), of: sound, at: .zero)
let export = AVAssetExportSession(asset: mix, presetName: AVAssetExportPresetPassthrough)!
export.outputURL = output
export.outputFileType = .mp4
export.shouldOptimizeForNetworkUse = true
let done = DispatchSemaphore(value: 0)
export.exportAsynchronously { done.signal() }
done.wait()
print(export.status == .completed ? "ok" : "failed \(String(describing: export.error))")
