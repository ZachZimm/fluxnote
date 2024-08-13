import AVFoundation
import Foundation

class SpeechSynthesisManager: NSObject, ObservableObject {
    private let synthesizer: AVSpeechSynthesizer = AVSpeechSynthesizer()
    @Published var isSpeaking: Bool = false
    var useSiriVoice: Bool = true

    @discardableResult
    func shell(_ command: String) -> String {
        let task = Process()
        let pipe = Pipe()
        
        task.standardOutput = pipe
        task.standardError = pipe
        task.arguments = ["-c", command]
        task.launchPath = "/bin/zsh"
        task.standardInput = nil
        task.launch()
        
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(data: data, encoding: .utf8)!
        
        return output
    }

    func speak(_ text: String) {
        if useSiriVoice {
            // Run speakWithSay in a separate thread to avoid blocking the UI
            DispatchQueue.global(qos: .background).async {
                self.speakWithSay(text)
            }
        }
        else {
            speakWithAVSpeechSynthesis(text)
        }
    }

    private func speakWithSay(_ text: String) {
        // TODO check whether the `say` command has options for rate, etc.
        let _text = text.replacingOccurrences(of: "'", with: "")
        let returnString = shell("say \(_text)")
        print(returnString)
    }

    private func speakWithAVSpeechSynthesis(_ text: String) {
        let utterance: AVSpeechUtterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(identifier: String("com.apple.voice.premium.en-US.Zoe")) // Making a big assumtion that this voice is available
        utterance.rate = 0.5
        synthesizer.speak(utterance)
        isSpeaking = true
    }

    func stopSpeaking() {
        synthesizer.stopSpeaking(at: .immediate)
        isSpeaking = false
    }
}