"""Payee color generation system using golden ratio distribution with WCAG compliance."""

import colorsys
import math
from typing import Tuple, Dict


class PayeeColorGenerator:
    """Generate distinct, accessible colors for payees using golden ratio distribution."""
    
    # Golden ratio for even color distribution
    PHI = (1 + math.sqrt(5)) / 2
    GOLDEN_ANGLE = 2 * math.pi / (PHI + 1)  # ~137.5 degrees
    
    def __init__(self):
        self._color_cache = {}
    
    def get_payee_color(self, payee_index: int, format: str = 'hex') -> str:
        """
        Get a color for a payee based on their index in the payees list.
        
        Args:
            payee_index: 0-based index of payee in the state file
            format: 'hex', 'rgb', 'hsl', or 'rich' (Rich console markup)
            
        Returns:
            Color string in requested format
        """
        if payee_index in self._color_cache:
            hue_normalized, saturation, lightness = self._color_cache[payee_index]
        else:
            # Use golden angle to distribute hues evenly
            hue = (payee_index * self.GOLDEN_ANGLE) % (2 * math.pi)
            hue_degrees = (hue * 180 / math.pi) % 360
            
            # Convert to 0-1 range for colorsys
            hue_normalized = hue_degrees / 360
            
            # Adjust lightness based on hue to ensure WCAG compliance
            # Yellow/green hues need to be darker, blue/purple can be lighter
            base_lightness = 0.40
            
            # Hue-based lightness adjustment for better contrast
            hue_360 = hue_degrees
            if 40 <= hue_360 <= 180:  # Yellow to green range - needs to be much darker
                lightness = 0.28
            elif 180 <= hue_360 <= 250:  # Cyan to blue range - needs to be darker too
                lightness = 0.33
            else:  # Red and purple ranges
                lightness = base_lightness
            
            saturation = 0.80  # High saturation for vibrant colors
            
            self._color_cache[payee_index] = (hue_normalized, saturation, lightness)
        
        return self._format_color(hue_normalized, saturation, lightness, format)
    
    def _format_color(self, hue: float, saturation: float, lightness: float, format: str) -> str:
        """Convert HSL to requested format."""
        if format == 'hsl':
            return f"hsl({hue*360:.0f}, {saturation*100:.0f}%, {lightness*100:.0f}%)"
        
        # Convert HSL to RGB
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        r, g, b = [int(c * 255) for c in rgb]
        
        if format == 'rgb':
            return f"rgb({r}, {g}, {b})"
        elif format == 'hex':
            return f"#{r:02x}{g:02x}{b:02x}"
        elif format == 'rich':
            # Rich console color format (for TUI)
            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            raise ValueError(f"Unsupported color format: {format}")
    
    def get_contrast_ratio(self, color1_rgb: Tuple[int, int, int], color2_rgb: Tuple[int, int, int]) -> float:
        """
        Calculate WCAG contrast ratio between two RGB colors.
        
        Returns ratio from 1:1 to 21:1. WCAG AA requires 4.5:1 for normal text.
        """
        def luminance(rgb):
            """Calculate relative luminance according to WCAG."""
            r, g, b = [c / 255.0 for c in rgb]
            
            def gamma_correct(c):
                return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
            
            r_lin, g_lin, b_lin = map(gamma_correct, [r, g, b])
            return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
        
        lum1 = luminance(color1_rgb)
        lum2 = luminance(color2_rgb)
        
        # Ensure lighter color is in numerator
        if lum1 > lum2:
            return (lum1 + 0.05) / (lum2 + 0.05)
        else:
            return (lum2 + 0.05) / (lum1 + 0.05)
    
    def validate_accessibility(self, payee_index: int) -> Dict[str, float]:
        """
        Validate that the payee color meets WCAG contrast requirements.
        
        Returns contrast ratios against common backgrounds.
        """
        color_hex = self.get_payee_color(payee_index, 'hex')
        rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
        
        # Test against common backgrounds
        white_bg = (255, 255, 255)
        light_gray_bg = (248, 249, 250)  # Bootstrap light
        dark_bg = (33, 37, 41)           # Bootstrap dark
        black_bg = (0, 0, 0)
        
        return {
            'white_background': self.get_contrast_ratio(rgb, white_bg),
            'light_background': self.get_contrast_ratio(rgb, light_gray_bg),
            'dark_background': self.get_contrast_ratio(rgb, dark_bg),
            'black_background': self.get_contrast_ratio(rgb, black_bg)
        }
    
    def get_payee_colors_for_state(self, state_file) -> Dict[str, str]:
        """
        Get colors for all payees in a state file.
        
        Args:
            state_file: StateFile object
            
        Returns:
            Dictionary mapping payee names to hex colors
        """
        colors = {}
        for i, payee in enumerate(state_file.payees):
            colors[payee.name] = self.get_payee_color(i, 'hex')
        return colors


def demo_colors():
    """Demonstrate the color system with sample payees."""
    generator = PayeeColorGenerator()
    sample_payees = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    
    print("Payee Color Demonstration")
    print("=" * 50)
    
    for i, name in enumerate(sample_payees):
        hex_color = generator.get_payee_color(i, 'hex')
        rgb_color = generator.get_payee_color(i, 'rgb')
        hsl_color = generator.get_payee_color(i, 'hsl')
        
        accessibility = generator.validate_accessibility(i)
        
        print(f"{name:8} (#{i}): {hex_color} | {rgb_color} | {hsl_color}")
        print(f"         Contrast - White: {accessibility['white_background']:.1f}:1, "
              f"Dark: {accessibility['dark_background']:.1f}:1")
        
        # Check WCAG compliance
        wcag_aa_normal = accessibility['white_background'] >= 4.5
        wcag_aa_large = accessibility['white_background'] >= 3.0
        print(f"         WCAG AA: {'✓' if wcag_aa_normal else '✗'} Normal, "
              f"{'✓' if wcag_aa_large else '✗'} Large Text")
        print()


if __name__ == "__main__":
    demo_colors()