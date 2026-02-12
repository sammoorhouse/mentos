import SwiftUI
import AuthenticationServices

struct SignInView: View {
    @EnvironmentObject private var session: SessionStore
    @State private var errorMessage: String?
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 8) {
                Image(systemName: "leaf.circle.fill")
                    .font(.system(size: 56))
                    .foregroundColor(.accentColor)
                Text("Mentos")
                    .font(.largeTitle.bold())
                Text("Smarter spending, less stress")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            SignInWithAppleButton(.signIn) { request in
                request.requestedScopes = [.fullName, .email]
            } onCompletion: { result in
                handle(result: result)
            }
            .signInWithAppleButtonStyle(.black)
            .frame(height: 52)
            .padding(.horizontal, 32)
            .disabled(isLoading)

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
        .background(Color(.systemBackground))
    }

    private func handle(result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let authorization):
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
                  let tokenData = credential.identityToken,
                  let token = String(data: tokenData, encoding: .utf8) else {
                errorMessage = "Unable to read Apple ID token."
                return
            }
            isLoading = true
            Task {
                do {
                    try await session.signIn(identityToken: token)
                    errorMessage = nil
                } catch {
                    errorMessage = "Sign in failed. Please try again."
                }
                isLoading = false
            }
        case .failure:
            errorMessage = "Sign in was cancelled."
        }
    }
}
