import SwiftUI
import UIKit

private enum DSType {
    static func scaled(
        size: CGFloat,
        weight: UIFont.Weight,
        textStyle: UIFont.TextStyle,
        design: UIFontDescriptor.SystemDesign = .default
    ) -> Font {
        let systemFont = UIFont.systemFont(ofSize: size, weight: weight)
        let descriptor = systemFont.fontDescriptor.withDesign(design) ?? systemFont.fontDescriptor
        let baseFont = UIFont(descriptor: descriptor, size: size)
        let scaledFont = UIFontMetrics(forTextStyle: textStyle).scaledFont(for: baseFont)
        return Font(scaledFont)
    }

    static func scaledMonospace(size: CGFloat, weight: UIFont.Weight, textStyle: UIFont.TextStyle) -> Font {
        let baseFont = UIFont.monospacedSystemFont(ofSize: size, weight: weight)
        let scaledFont = UIFontMetrics(forTextStyle: textStyle).scaledFont(for: baseFont)
        return Font(scaledFont)
    }
}

extension Font {
    static let dsTitle = DSType.scaled(size: 28, weight: .semibold, textStyle: .title2)
    static let dsHeadline = DSType.scaled(size: 20, weight: .semibold, textStyle: .title3)
    static let dsBody = DSType.scaled(size: 16, weight: .regular, textStyle: .body)
    static let dsCaption = DSType.scaled(size: 13, weight: .medium, textStyle: .caption1)
    static let dsMonospace = DSType.scaledMonospace(size: 16, weight: .regular, textStyle: .body)
}
