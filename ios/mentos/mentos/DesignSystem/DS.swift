import SwiftUI

enum DS {
    enum Color {
        static let background = SwiftUI.Color(uiColor: .systemBackground)
        static let surface = SwiftUI.Color(uiColor: .secondarySystemBackground)
        static let surfaceElevated = SwiftUI.Color(uiColor: .tertiarySystemBackground)
        static let textPrimary = SwiftUI.Color.primary
        static let textSecondary = SwiftUI.Color.secondary
        static let separator = SwiftUI.Color(uiColor: .separator)
        static let accent = SwiftUI.Color.accentColor
    }

    enum Radius {
        static let card: CGFloat = 16
        static let pill: CGFloat = 999
        static let button: CGFloat = 14
    }

    enum Layout {
        static let maxContentWidth: CGFloat = 560
    }

    enum Animation {
        static let spring = SwiftUI.Animation.spring(response: 0.38, dampingFraction: 0.86)
        static let cardEnter = SwiftUI.Animation.easeOut(duration: 0.2)
    }
}

struct DSConstrainedContent<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .frame(maxWidth: DS.Layout.maxContentWidth)
            .frame(maxWidth: .infinity)
    }
}
