import SwiftUI

struct SettingsView: View {
    var body: some View {
        ScrollView {
            VStack(spacing: Tokens.Spacing.l) {
                Surface {
                    VStack(alignment: .leading, spacing: Tokens.Spacing.s) {
                        Text("Debug")
                            .font(Typography.caption)
                            .foregroundStyle(Tokens.Color.textTertiary)
                        Text("Server: http://localhost:8000")
                            .font(Typography.metric)
                            .foregroundStyle(Tokens.Color.textSecondary)
                    }
                }
                Surface {
                    VStack(spacing: Tokens.Spacing.s) {
                        button("Disconnect Monzo", fill: Tokens.Color.surface2, text: Tokens.Color.textSecondary)
                        button("Sign out", fill: Tokens.Color.accent.opacity(0.85), text: Tokens.Color.background)
                    }
                }
            }
            .padding(Tokens.Spacing.l)
        }
        .background(Tokens.Color.background)
        .navigationTitle("Settings")
    }

    private func button(_ title: String, fill: Color, text: Color) -> some View {
        Text(title)
            .font(Typography.body)
            .foregroundStyle(text)
            .frame(maxWidth: .infinity)
            .padding(.vertical, Tokens.Spacing.m)
            .background(fill)
            .clipShape(Capsule())
    }
}
