import SwiftUI
import UIKit

enum Tokens {
    enum Color {
        static let accent = SwiftUI.Color(hex: "3EE6B3")

        static let background = SwiftUI.Color(dynamicLight: "F7F9FB", dark: "0B0D10")
        static let surface = SwiftUI.Color(dynamicLight: "FFFFFF", dark: "12151A")
        static let surface2 = SwiftUI.Color(dynamicLight: "F0F3F6", dark: "1A1F26")
        static let surface3 = SwiftUI.Color(dynamicLight: "E7ECF2", dark: "222831")

        static let separator = SwiftUI.Color(dynamicLight: "0B0D10", dark: "FFFFFF").opacity(0.08)
        static let textPrimary = SwiftUI.Color(dynamicLight: "0B0D10", dark: "F2F5F7")
        static let textSecondary = SwiftUI.Color(dynamicLight: "0B0D10", dark: "F2F5F7").opacity(0.65)
        static let textTertiary = SwiftUI.Color(dynamicLight: "0B0D10", dark: "F2F5F7").opacity(0.40)
    }

    enum Spacing {
        static let xs: CGFloat = 4
        static let s: CGFloat = 8
        static let m: CGFloat = 12
        static let l: CGFloat = 16
        static let xl: CGFloat = 24
        static let xxl: CGFloat = 32
    }

    enum Radius {
        static let card: CGFloat = 14
        static let small: CGFloat = 10
        static let pill: CGFloat = 999
    }
}

private extension SwiftUI.Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = Double((int >> 16) & 0xFF) / 255.0
        let g = Double((int >> 8) & 0xFF) / 255.0
        let b = Double(int & 0xFF) / 255.0
        self.init(red: r, green: g, blue: b)
    }

    init(dynamicLight: String, dark: String) {
        self.init(UIColor { traitCollection in
            traitCollection.userInterfaceStyle == .dark ? UIColor(SwiftUI.Color(hex: dark)) : UIColor(SwiftUI.Color(hex: dynamicLight))
        })
    }
}
