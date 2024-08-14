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
        // Run speakWithSay in a separate thread to avoid blocking the UI
        let sentences = self.slitIntoSentences(text)
        DispatchQueue.global(qos: .background).async {
           for sentence in sentences {
               if self.useSiriVoice {
                    let success: Bool = self.speakWithSay(sentence)
                    if success != true { // If the `say` command fails, use AVSpeechSynthesis
                        self.speakWithAVSpeechSynthesis(sentence)
                    }
               } else {
                    self.speakWithAVSpeechSynthesis(sentence)
               }
           } 
        }
    }

    private func speakWithSay(_ text: String) -> Bool {
        // TODO check whether the `say` command has options for rate, etc.
        let _text = text.replacingOccurrences(of: "'", with: "")
        let returnString = shell("say \(_text)")
        print(returnString)
        return true
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

    func isFullSentence(_ sentence: String) -> Bool {
        let message = sentence.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: "\n", with: " ").replacingOccurrences(of: "...", with: ",")
        // if message.count < 5 { return false }
        if message.hasSuffix("...") { return true }
        if message.hasSuffix(".") { return true }
        if message.hasSuffix("!") { return true }
        if message.hasSuffix("?") { return true }
        return false
    }

    func slitIntoSentences(_ message: String) -> [String] {
        var senteces: [String] = []
        let _message: String = message.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: "\n", with: " ").replacingOccurrences(of: "...", with: ",")
        let words = _message.components(separatedBy: " ")
        var sentence = ""
        for word in words {
            sentence += word + " "
            if isFullSentence(sentence) {
                senteces.append(sentence.trimmingCharacters(in: .whitespacesAndNewlines))
                sentence = ""
            }
        }

        return senteces
    }
}