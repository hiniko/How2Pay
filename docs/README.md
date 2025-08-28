# How2Pay Documentation

Welcome to the comprehensive documentation for How2Pay, a powerful personal finance management CLI tool.

## 📚 Documentation Structure

### [Commands Reference](commands.md)
Complete guide to all available commands with examples and options:
- Schedule commands (`schedule show`, `schedule payee`)  
- Bill management (`bills add`, `bills list`)
- Payee management (`payee add`, `payee list`)
- Configuration commands (`schedule config`)

### [Configuration Guide](configuration.md)
Detailed configuration options and settings:
- Schedule options (cutoff days, projections, weekend adjustments)
- Locale settings (currency, date formats)
- State file management
- Advanced configuration patterns

### [Features Guide](features.md)
In-depth coverage of all features:
- Payment range planning and budget summaries
- Price history and bill increases over time
- Custom bill splitting and percentage assignments
- Payee start dates and lifecycle management
- Export options (PDF, CSV, Terminal)
- Color-coded payee identification

### [Examples](examples.md)
Real-world scenarios and common use cases:
- Setting up a shared household
- Managing temporary income streams
- Handling roommate changes mid-year
- Complex bill splitting scenarios
- Budget planning workflows

### [API Reference](api.md)
Technical documentation for developers:
- Data models and YAML structure
- Scheduler algorithms and logic
- Export formats and customization
- Extension points and customization

## 🚀 Quick Navigation

**New Users**: Start with the main [README](../README.md) for installation and quick start, then explore [Examples](examples.md) for common scenarios.

**Power Users**: Jump to [Features Guide](features.md) for advanced functionality or [Configuration](configuration.md) for customization options.

**Developers**: See [API Reference](api.md) for technical details and extension points.

## 🔍 Search Tips

Each documentation file includes:
- **Table of contents** at the top
- **Search-friendly headings** for easy navigation  
- **Code examples** you can copy and paste
- **Cross-references** to related sections
- **Troubleshooting** sections where applicable

## 💡 Getting Help

If you can't find what you're looking for:

1. Check the [Commands Reference](commands.md) for syntax and options
2. Look at [Examples](examples.md) for similar use cases
3. Review [Configuration](configuration.md) for settings that might help
4. Use the built-in help: `how2pay schedule --help`

## 🔄 Keep Updated

This documentation is maintained alongside the codebase. For the latest features and changes, always refer to the documentation in your installed version.