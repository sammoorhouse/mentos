import SwiftUI

@main
struct MentosApp: App {
    @StateObject private var session = SessionStore()
    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(session)
                .onOpenURL { url in session.handleDeepLink(url) }
        }
    }
}
