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
                VStack {
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
                    Text("Message:")
                    TextField("Enter text", text: $text)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .onChange(of: speechTranscriptionManager.currentTranscription, perform: { value in
                            text = value
                        })
                    .onSubmit { sendJsonMessage() }
                }.padding()

                VStack {
                    Button(action: { verifySpeechRecognition() }
                        ) { Text("Verify") }
                    Button(action: { startRecording() }
                        ) { Text("Start") }
                    Button(action: { stopRecording() }
                        ) { Text("Stop") }
                    Button(action: { sendJsonMessage() }
                    ) { Text("Send") }
                    Button(action: { speakText() }
                ) { Text("Speak") }    
                }
                
            }

            VStack {
                ScrollView {
                    VStack(alignment: .leading) {
                        ForEach(webSocketManager.chatLog, id: \.self) { message in
                            Text(message + "\n")
                                .padding(.vertical, 2)
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
                        }
                    }
                    .padding()
                }
                .border(Color.gray, width: 1)                
            }
        }
        // .frame(width: 1200, height: 800)
        .padding()
    }

    private func speakText() {
        // set text equal to all of chatLog as a string
        let _text: String = webSocketManager.latestResponse
        speechSynthesisManager.useSiriVoice = false
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