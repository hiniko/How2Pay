# HTML Assets for PDF Export

This folder contains static assets used for generating professional HTML/PDF exports.

## Files

- `schedule.css` - Professional stylesheet for payment schedule tables
  - Modern gradient headers with color-coded sections
  - Dynamic payee-specific color schemes generated using golden ratio distribution
  - Responsive table design optimized for landscape PDF
  - Print-friendly styling with proper page breaks per month
  - WCAG AA compliant color contrast for accessibility
  - Professional color scheme based on Material Design

## Usage

The CSS is automatically loaded by `ProfessionalHtmlGenerator` when generating PDFs.

## Customization

To modify the PDF styling:
1. Edit `schedule.css` directly
2. No code changes required - styling will be automatically applied to new PDFs

## Color Scheme

- **Month headers**: Red gradient (#e74c3c to #c0392b)
- **Bill headers**: Orange gradient (#f39c12 to #e67e22) 
- **Amount headers**: Green gradient (#27ae60 to #229954)
- **Detail headers**: Purple gradient (#8e44ad to #7d3c98)
- **Income headers**: Teal gradient (#16a085 to #138d75)