import Foundation

class WebSocketManager: NSObject, ObservableObject {
    private var webSocketTask: URLSessionWebSocketTask?
    @Published var isConnected: Bool = false
    @Published var url: String = "ws://lab-ts:8090/ws" // this should be configurable
    @Published var recievedMessageLog: [String] = []
    @Published var sentMessageLog: [String] = []
    @Published var chatLog: [String] = []
    @Published var latestResponse: String = ""
    @Published var isResponding: Bool = false

    override init() {
        super.init()
        connect()
    }
    
    func connect() {
        let url: URL = URL(string: url)!
        let session: URLSession = URLSession(configuration: .default, delegate: self, delegateQueue: OperationQueue())
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        isConnected = true
        receiveMessage()
    }

    func sendMessage(_ message: String) {
        // parse JSON from message
        let messageObj: [String : Any] = try! JSONSerialization.jsonObject(with: message.data(using: .utf8)!, options: []) as! [String: Any]
        if messageObj["func"] as! String == "chat" {
            chatLog.append(messageObj["message"] as! String)
        }
        sentMessageLog.append(message)
        let message = URLSessionWebSocketTask.Message.string(message)
        webSocketTask?.send(message) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .failure(let error):
                print("WebSocket receive error: \(error)")
            case .success(let message):
                switch message {
                case .string(let text):
                    DispatchQueue.main.async {
                        // parse JSON from text
                        let textObj = try! JSONSerialization.jsonObject(with: text.data(using: .utf8)!, options: []) as! [String: Any]
                        // get the 'message' field from the JSON
                        let message: String = textObj["message"] as! String
                        let mode: String = textObj["mode"] as! String

                        if mode == "chat streaming" {
                            if self?.isResponding == false { // Start of a new message
                                self?.latestResponse = ""
                                self?.chatLog.append("")
                            }
                            self?.isResponding = true
                            let chatLogLength: Int = self?.chatLog.count ?? 0
                            if message != "|" {
                                self?.chatLog[chatLogLength - 1] += message
                                self?.latestResponse += message
                            }
                        }
                        else if mode == "chat streaming finished" {
                            self?.isResponding = false
                        }
                        else {
                            self?.recievedMessageLog.append(mode + ":")
                            self?.recievedMessageLog.append(message)
                        }
                    }
                case .data(let data):
                    print("Received data: \(data.count)")
                @unknown default:
                    fatalError("Received unknown message type")
                }
                self?.receiveMessage() // Continue listening for more messages
            }
        }
    }

    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
    }
}

extension WebSocketManager: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        print("WebSocket connection opened")
        let loginMessage: String = "{\"func\": \"login\", \"username\": \"test_user\"}"
        sendMessage(loginMessage)

    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        print("WebSocket connection closed")
    }
}