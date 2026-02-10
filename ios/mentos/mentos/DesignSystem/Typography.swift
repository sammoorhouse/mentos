import SwiftUI

enum Typography {
    static let display = Font.system(size: 32, weight: .semibold).leading(.tight)
    static let title = Font.system(size: 22, weight: .semibold)
    static let body = Font.system(size: 16, weight: .regular)
    static let caption = Font.system(size: 13, weight: .medium)
    static let metric = Font.system(size: 18, weight: .semibold, design: .monospaced)
}

extension View {
    func trackingDisplay() -> some View { tracking(-0.4) }
    func trackingTitle() -> some View { tracking(-0.2) }
    func trackingCaption() -> some View { tracking(0.2) }
}
