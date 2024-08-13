swiftc -o Eagle.app/Contents/MacOS/Eagle \
    src/Eagle.swift \
    src/WebSocketManager.swift \
    src/SpeechSynthesisManager.swift \
    src/SpeechTranscriptionManager.swift  \
    src/ContentView.swift \
    -target arm64-apple-macosx13.0
