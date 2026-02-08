import SwiftUI
import AuthenticationServices

struct SignInView: View {
    var onSignedIn: () -> Void

    var body: some View {
        VStack(spacing: DSSpacing.xl) {
            Spacer()
            VStack(spacing: DSSpacing.s) {
                Text("Mentos").font(.dsTitle)
                Text("Better money habits. Quietly.")
                    .font(.dsBody)
                    .foregroundStyle(DS.Color.textSecondary)
            }

            SignInWithAppleButton(.signIn, onRequest: { _ in }, onCompletion: { _ in onSignedIn() })
                .signInWithAppleButtonStyle(.automatic)
                .frame(height: 48)
                .clipShape(RoundedRectangle(cornerRadius: DS.Radius.button, style: .continuous))

            Spacer()
            Text("By continuing, you agree to our privacy-first approach.")
                .font(.dsCaption)
                .foregroundStyle(DS.Color.textSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(DSSpacing.xl)
        .background(DS.Color.background.ignoresSafeArea())
    }
}
