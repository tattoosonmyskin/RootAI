# Contributing to RootAI v3.0

Thank you for your interest in contributing to RootAI! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/RootAI.git
   cd RootAI
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   pytest tests/ -v
   ```

## Code Style

- Follow PEP 8 guidelines
- Use Black for formatting: `black src/ api/ benchmarks/`
- Use type hints where appropriate
- Write docstrings for all functions and classes

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Add tests for new functionality
4. Run tests and linting
5. Commit with clear messages
6. Push to your fork
7. Create a Pull Request

## Areas for Contribution

- Arabic language processing improvements
- New benchmark datasets
- Performance optimizations
- Documentation improvements
- Bug fixes
- New features

## Questions?

Open an issue or contact the maintainers.
