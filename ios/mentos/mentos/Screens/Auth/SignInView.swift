import SwiftUI
import AuthenticationServices

struct SignInView: View {
    var onSignedIn: (Result<ASAuthorization, Error>) -> Void
    @State private var signInErrorMessage: String?

    var body: some View {
        VStack(spacing: DSSpacing.xl) {
            Spacer()
            VStack(spacing: DSSpacing.s) {
                Text("Mentos").font(.dsTitle)
                Text("Better money habits. Quietly.")
                    .font(.dsBody)
                    .foregroundStyle(DS.Color.textSecondary)
            }

            SignInWithAppleButton(.signIn, onRequest: { _ in }, onCompletion: handleSignIn(result:))
                .signInWithAppleButtonStyle(.automatic)
                .frame(height: 48)
                .clipShape(RoundedRectangle(cornerRadius: DS.Radius.button, style: .continuous))

            if let signInErrorMessage {
                Text(signInErrorMessage)
                    .font(.dsCaption)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
            }

            Spacer()
            Text("By continuing, you agree to our privacy-first approach.")
                .font(.dsCaption)
                .foregroundStyle(DS.Color.textSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(DSSpacing.xl)
        .background(DS.Color.background.ignoresSafeArea())
    }

    private func handleSignIn(result: Result<ASAuthorization, Error>) {
        switch result {
        case .success:
            signInErrorMessage = nil
            onSignedIn(result)
        case .failure:
            signInErrorMessage = "Sign in was not completed. Please try again."
        }
    }
}
