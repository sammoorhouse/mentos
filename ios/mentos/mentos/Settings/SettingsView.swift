import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var session: SessionStore
    @State private var isDisconnecting = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationView {
            List {
                Section(header: Text("Account")) {
                    Text(session.user?.email ?? "Signed in with Apple")
                }

                Section(header: Text("Notifications")) {
                    Toggle("Weekly summaries", isOn: .constant(true))
                    Toggle("Spending alerts", isOn: .constant(true))
                }

                Section {
                    Button(role: .destructive, action: disconnectMonzo) {
                        Text(isDisconnecting ? "Disconnecting..." : "Disconnect Monzo")
                    }
                    .disabled(isDisconnecting)
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .font(.footnote)
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Settings")
        }
    }

    private func disconnectMonzo() {
        isDisconnecting = true
        errorMessage = nil
        Task {
            do {
                try await APIClient.shared.disconnectMonzo()
                await session.refreshSession()
            } catch {
                errorMessage = "Could not disconnect Monzo."
            }
            isDisconnecting = false
        }
    }
}
