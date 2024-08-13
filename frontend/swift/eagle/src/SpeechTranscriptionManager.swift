import Foundation
import AVFoundation
import Accelerate
import Speech

@available(macOS 10.15, *)
class SpeechTranscriptionManager: ObservableObject {
    
    var recognizer: SFSpeechRecognizer!
    var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    var recognitionTask: SFSpeechRecognitionTask?
    let audioEngine = AVAudioEngine()
    var started = false
    private var shouldContinue: Bool = true
    @Published var previousResult: SFSpeechRecognitionResult?
    private var myInputNode: AVAudioInputNode?
    @Published var fullTranscription: String = ""
    @Published var currentTranscription: String = "no text"
    @Published var isFinal: Bool = false
    @Published var isAuthorized: Bool = false
    
    init() {
        recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        isAuthorized = SFSpeechRecognizer.authorizationStatus() == .authorized
    }
    
    func getPermission() {
        if SFSpeechRecognizer.authorizationStatus() == .authorized {
            print("Good to go")
        } else {
            print("Requesting permission")
            SFSpeechRecognizer.requestAuthorization { authStatus in
                DispatchQueue.main.async {
                    switch authStatus {
                    case .authorized:
                        print("Good to go")
                        self.isAuthorized = true
                    default:
                        print("Not authorized")
                        self.isAuthorized = false
                    }
                }
            }
        }
    }

    func stop() {
        if !self.started { return }
        self.shouldContinue = false
        self.started = false
        self.audioEngine.stop()
        self.myInputNode?.removeTap(onBus: 0)
        self.audioEngine.reset()
        
        self.recognitionRequest?.endAudio()
        self.recognitionTask?.cancel()
        self.recognitionTask = nil
        self.recognitionRequest = nil
    }

    func finish() {
        if !self.shouldContinue { return }
        self.shouldContinue = false
    }

    func reset() {
        self.recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
        self.recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        self.recognitionRequest?.shouldReportPartialResults = true
        self.audioEngine.reset()
    }
    
    func start() {
        if self.started { return }
        
        self.recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        self.recognitionRequest?.shouldReportPartialResults = true

        self.myInputNode = self.startAudio()
        
        if let inputNode = self.myInputNode {
            self.startRecognitionTask(inputNode)
        }
        
        self.started = true
        self.shouldContinue = true
    }
    
    private func startAudio() -> AVAudioInputNode? {
        let inputNode = self.audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            self.recognitionRequest?.append(buffer)
        }
        
        do {
            self.audioEngine.prepare()
            try self.audioEngine.start()
            print("Audio started")
        } catch {
            print("AVAudioEngine error: \(error)")
            return nil
        }
        
        return inputNode
    }
    
    private func startRecognitionTask(_ node: AVAudioInputNode) {
        guard let recognitionRequest = self.recognitionRequest else { return }
        
        self.recognitionTask = self.recognizer.recognitionTask(with: recognitionRequest) { result, error in
            var isFinal = false
            
            if let foundResult = result {
                if self.shouldContinue {
                    let formattedResult = foundResult.bestTranscription.formattedString
                    let prevFormattedResult = self.previousResult?.bestTranscription.formattedString ?? ""
                    
                    if formattedResult != prevFormattedResult {
                        if formattedResult.count > self.currentTranscription.count {
                            self.fullTranscription += self.currentTranscription + " "
                        }
                        self.currentTranscription = formattedResult
                    }
                    
                    self.previousResult = foundResult
                    isFinal = foundResult.isFinal
                }
            }
            
            if error != nil || !self.shouldContinue {
                print("Recognition task stopped due to error: \(String(describing: error))")
                self.audioEngine.stop()
                node.removeTap(onBus: 0)
                
                self.recognitionRequest?.endAudio()
                self.recognitionRequest = nil
                self.recognitionTask = nil
                
                self.started = false
            }
        }
    }
}