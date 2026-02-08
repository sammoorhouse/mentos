import SwiftUI

struct DSShadow: ViewModifier {
    func body(content: Content) -> some View {
        content.shadow(color: .black.opacity(0.06), radius: 6, y: 2)
    }
}

extension View {
    func dsShadow() -> some View { modifier(DSShadow()) }
}
