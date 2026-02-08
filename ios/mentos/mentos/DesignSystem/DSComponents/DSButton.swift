import SwiftUI
import UIKit

enum DSButtonVariant {
    case primary
    case secondary
    case destructive
}

struct DSButton: View {
    var title: String
    var variant: DSButtonVariant = .primary
    var isEnabled: Bool = true
    var action: () -> Void

    var body: some View {
        Button {
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
            action()
        } label: {
            Text(title)
                .font(.dsBody.weight(.semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, DSSpacing.m)
        }
        .buttonStyle(DSButtonStyle(variant: variant))
        .disabled(!isEnabled)
        .accessibilityHint("Activates \(title)")
    }
}

struct DSButtonStyle: ButtonStyle {
    let variant: DSButtonVariant

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(foreground)
            .background(background(configuration: configuration), in: RoundedRectangle(cornerRadius: DS.Radius.button, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: DS.Radius.button, style: .continuous).stroke(border, lineWidth: border == .clear ? 0 : 1))
            .opacity(configuration.isPressed ? 0.85 : 1)
            .animation(DS.Animation.cardEnter, value: configuration.isPressed)
    }

    private var foreground: Color {
        switch variant {
        case .primary: return .white
        case .secondary: return DS.Color.textPrimary
        case .destructive: return .red
        }
    }

    private func background(configuration: Configuration) -> Color {
        switch variant {
        case .primary: return .accentColor
        case .secondary: return DS.Color.surfaceElevated
        case .destructive: return .clear
        }
    }

    private var border: Color {
        variant == .secondary ? DS.Color.separator.opacity(0.4) : .clear
    }
}
