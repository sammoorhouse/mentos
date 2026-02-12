import SwiftUI
import AuthenticationServices
import UIKit

struct ConnectMonzoView: View {
    @EnvironmentObject private var session: SessionStore
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var authSession: ASWebAuthenticationSession?
    @State private var showManualEntry = false
    @State private var manualCode = ""
    @State private var manualState = ""

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Text("Connect your bank")
                    .font(.title.bold())
                Text("Connect your bank to get insights.")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, 24)

            Button(action: startConnect) {
                Text(isLoading ? "Connecting..." : "Connect Monzo")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .padding(.horizontal, 32)
            .disabled(isLoading)

            Button("Open in Safari instead") {
                startConnectInSafari()
            }
            .font(.footnote)

            Button("Enter code manually") {
                showManualEntry = true
            }
            .font(.footnote)

            if let errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundColor(.red)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
        .sheet(isPresented: $showManualEntry) {
            manualEntrySheet
        }
        .onReceive(NotificationCenter.default.publisher(for: .monzoConnected)) { _ in
            authSession?.cancel()
            authSession = nil
            isLoading = false
            showManualEntry = false
        }
    }

    private func startConnect() {
        isLoading = true
        errorMessage = nil
        Task {
            do {
                let response = try await APIClient.shared.startMonzoConnect()
                guard let authURL = URL(string: response.authUrl) else {
                    errorMessage = "Invalid auth URL."
                    isLoading = false
                    return
                }

                let callbackScheme = "mentos"
                authSession = ASWebAuthenticationSession(url: authURL, callbackURLScheme: callbackScheme) { callbackURL, error in
                    if let error {
                        errorMessage = error.localizedDescription
                        isLoading = false
                        return
                    }
                    guard let callbackURL,
                          let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false),
                          let code = components.queryItems?.first(where: { $0.name == "code" })?.value,
                          let state = components.queryItems?.first(where: { $0.name == "state" })?.value else {
                        errorMessage = "Missing callback data."
                        isLoading = false
                        return
                    }
                    Task {
                        do {
                            try await APIClient.shared.completeMonzoConnect(code: code, stateId: state)
                            await session.refreshSession()
                            session.onboardingState = .needsGoals
                            authSession?.cancel()
                            authSession = nil
                        } catch {
                            errorMessage = "Connection failed. Please try again."
                        }
                        isLoading = false
                    }
                }
                authSession?.presentationContextProvider = PresentationContextProvider.shared
                authSession?.prefersEphemeralWebBrowserSession = true
                authSession?.start()
            } catch {
                errorMessage = "Could not start Monzo connect."
                isLoading = false
            }
        }
    }

    private func startConnectInSafari() {
        isLoading = true
        errorMessage = nil
        Task {
            do {
                let response = try await APIClient.shared.startMonzoConnect()
                guard let authURL = URL(string: response.authUrl) else {
                    errorMessage = "Invalid auth URL."
                    isLoading = false
                    return
                }
                await MainActor.run {
                    UIApplication.shared.open(authURL)
                }
            } catch {
                errorMessage = "Could not start Monzo connect."
            }
            isLoading = false
        }
    }

    private var manualEntrySheet: some View {
        NavigationView {
            Form {
                Section(header: Text("Paste from redirect URL")) {
                    TextField("code", text: $manualCode)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    TextField("state", text: $manualState)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }
                Section(footer: Text("You can find code and state in the redirect URL: mentos://oauth/monzo?code=...&state=...")) {
                    Button("Complete Connection") {
                        completeManual()
                    }
                    .disabled(manualCode.isEmpty || manualState.isEmpty || isLoading)
                }
            }
            .navigationTitle("Manual Connect")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { showManualEntry = false }
                }
            }
        }
    }

    private func completeManual() {
        isLoading = true
        errorMessage = nil
        Task {
            do {
                try await APIClient.shared.completeMonzoConnect(code: manualCode, stateId: manualState)
                await session.refreshSession()
                session.onboardingState = .needsGoals
                showManualEntry = false
                manualCode = ""
                manualState = ""
            } catch {
                errorMessage = "Connection failed. Please try again."
            }
            isLoading = false
        }
    }
}

final class PresentationContextProvider: NSObject, ASWebAuthenticationPresentationContextProviding {
    static let shared = PresentationContextProvider()

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow } ?? ASPresentationAnchor()
    }
}
