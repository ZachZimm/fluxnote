import SwiftUI
import Speech
import Foundation
import AVFoundation
// TODO add error handling

struct ContentView: View {
    @State private var function: String = ""
    @State private var text: String = ""
    @State private var fieldName: String = ""
    @State private var message: String = ""
    @StateObject private var webSocketManager = WebSocketManager()
    private var speechSynthesisManager = SpeechSynthesisManager()
    @StateObject private var speechTranscriptionManager = SpeechTranscriptionManager()

    var body: some View {

        VStack {
            var connectionText: String {
                if webSocketManager.isConnected {
                    return "Connected: \(webSocketManager.url)"
                } else { return "Not connected" }
            }

        Text(connectionText)
            HStack {
                HStack {
                    HStack {
                        Text("Func:")
                        TextField("Enter function", text: $function)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .onSubmit { sendJsonMessage() }
                    }
                    HStack {
                        Text("Field:")
                        TextField("Enter field", text: $fieldName)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .onSubmit { sendJsonMessage() }
                    }
                }.padding()  

                VStack {
                    // Verify button seems to be unnessary
                    // Button(action: { verifySpeechRecognition() }
                    //     ) { Text("Verify") }
                    Button(action: { startRecording() }
                        ) { Text("Start Dictation") }
                    Button(action: { stopRecording() }
                        ) { Text("Stop Dictation") }
                }
                VStack {
                    
                    Button(action: { sendJsonMessage() }
                    ) { Text("Send") }
                    Button(action: { speakText() }
                ) { Text("Speak") }    
                }

            }
            .frame(width: 800)
            VStack {
                Text("Message:")
                VStack {
                TextEditor(text: $text)
                .frame(width: 900, height: 75)
                
                .cornerRadius(6)
                .padding(.all, 3.0)
                .onChange(of: speechTranscriptionManager.currentTranscription, perform: { value in
                        text = value
                    })
                .onSubmit { sendJsonMessage() }
                } 
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color.gray, lineWidth: 2)
                )}
                .padding()

            VStack {
                
                ScrollView {
                    VStack(alignment: .leading) {
                        ForEach(webSocketManager.chatLog, id: \.self) { message in
                            Text(message + "\n\n")
                                .padding(.vertical, 2)
                            .textSelection(.enabled)
                            Divider()
                        }
                    }
                    .padding()
                }
            }
            .frame(width: 800, height: 350)
            .border(Color.gray, width: 1)
            .padding()  

            HStack {
                ScrollView {
                    VStack(alignment: .leading) {
                        ForEach(webSocketManager.sentMessageLog, id: \.self) { message in
                            Text(message)
                                .padding(.vertical, 2)
                            Divider()
                        }
                    }
                    .padding()
                }
                .border(Color.gray, width: 1)

                ScrollView {
                    VStack(alignment: .leading) {
                        ForEach(webSocketManager.recievedMessageLog, id: \.self) { message in
                            Text(message)
                                .padding(.vertical, 2)
                            Divider()
                        }
                    }
                    .padding()
                }
                .border(Color.gray, width: 1)                
            }
        }
        .padding()
    }

    private func speakText() {
        // set text equal to all of chatLog as a string
        let _text: String = webSocketManager.latestResponse
        speechSynthesisManager.useSiriVoice = true 
        speechSynthesisManager.speak(_text)
    }

    private func verifySpeechRecognition() {
        DispatchQueue.main.async {
            speechTranscriptionManager.getPermission()
        }
    }

    private func startRecording() {
        DispatchQueue.main.async {
            speechTranscriptionManager.start()
        }
    }

    private func stopRecording() {
        DispatchQueue.main.async {
            speechTranscriptionManager.finish()
            speechTranscriptionManager.stop()
        }
    }

    private func sendJsonMessage() { // This should probably be in the WebSocketManager class
        var message: String

        if fieldName.isEmpty || text.isEmpty {
            message = "{\"func\": \"\(function)\"}"
        } else {
            message = "{\"func\": \"\(function)\", \"\(fieldName)\": \"\(text)\"}"
        }
        webSocketManager.sendMessage(message)

        text = "" // Reset fields unless function is "chat"
        if function != "chat" {
            function = ""
            fieldName = ""
        }
    }
}