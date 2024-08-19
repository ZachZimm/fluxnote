// The Swift Programming Language
// https://docs.swift.org/swift-book

import Adwaita

struct CounterDemo: View {

    @State var count = 0

    var view: Body {
        VStack {
            HStack {
                CountButton(count: $count, icon: .goPrevious) { $0 -= 1 }
                Text("\(count)")
                    .title1()
                    .frame(minWidth: 100)
                CountButton(count: $count, icon: .goNext) { $0 += 1 }
            }
            .halign(.center)
        }
        .valign(.center)
        .padding()
    }

    private struct CountButton: View {

        @Binding var count: Int
        var icon: Icon.DefaultIcon
        var action: (inout Int) -> Void

        var view: Body {
            Button(icon: .default(icon: icon)) {
                action(&count)
            }
            .circular()
        }
    }

}

struct MyView: View {
    var app: GTUIApp
    var window: GTUIApplicationWindow 

    @State private var displayText: String = Loc.helloWorld 
    @State private var textToggled: Bool = false
    @State private var progressText: String = "Start Progress"
    @State private var progress: Double = 0.0
    let fullProgress: Double = 100.0
    @State private var isProgressing: Bool = false
    var toast: Signal = Signal()
    var view: Body {
        HStack {
            Button("Show Popover") {
                if textToggled {
                    displayText = Loc.helloWorld
                } else {
                    displayText = Loc.buttonClicked
                }
                textToggled.toggle()
            }
            .frame(maxWidth: 140)
            .frame(maxHeight: 50)
            .padding(10, .horizontal.add(.bottom))
            .popover(visible: $textToggled){
                    CounterDemo()
                }

            VStack {
                Button(progressText) {
                    if isProgressing {
                        progressText = "Start Progress"
                        isProgressing = false
                    }
                    else {
                        isProgressing = true
                        if progress == fullProgress {
                            progress = 0.0
                        }
                        progressText = "Process running"
                        Task {
                            Idle(delay: .init(4_000.0 / fullProgress)) {
                                progress += 1.0
                                let done = progress == fullProgress
                                if done {
                                    progressText = "Reset Progress"
                                    isProgressing = false
                                    toast.signal()
                                }
                                return !done
                            }
                        }
                    }
                }
                .insensitive(isProgressing)
                                
                ProgressBar(value: progress, total: fullProgress)
                    .frame(maxWidth: 200)
                    .padding(10, .horizontal.add(.top))
            }
            .card()
            .halign(.center)
            .frame(maxWidth: 300)
            .frame(maxHeight: 75)

        }
        .valign(.center)
        .halign(.center)
        .padding(10)
    }
}

// ^^ This is all just nonsense really, just learning to use the library

struct AppView: View {
    @State var messageLog: String = ""
    @State var userMessage: String = ""

    var view: Body {
        EntryRow("your message", text: $userMessage)
            .onSubmit {
                messageLog += userMessage + "\n"
                userMessage = ""
            }
            .title("Your Message")
            .showApplyButton()
            .card()
            .padding(10)
            .frame(maxWidth: 300)
            .frame(maxHeight: 100)
            
        ScrollView {
            Text(messageLog)
                .title4()
                .padding(10)
                .frame(maxWidth: 450)
                .frame(maxHeight: 650)
                .card()
        }
        .frame(maxWidth: 550)
        .frame(maxHeight: 700)
    }
}

@main
struct GnomeApp: App {

    let id = "com.zzimm.GnomeApp"
    var app: GTUIApp!

    var scene: Scene {
        
        Window(id: "main") { window in
            ToolbarView(app: app, window: window)
            MyView(app: app, window: window)
            AppView()

            
        }
        .defaultSize(width: 450, height: 300)
    }
}

