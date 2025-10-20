# Contributing to HubbleBubble

Thank you for your interest in contributing to HubbleBubble! This project demonstrates "iron-tight" computational reproducibility in scientific computing, and we welcome contributions that maintain or enhance this standard.

## Core Principle: Reproducibility First

**Any code changes MUST**:
1. ✅ Pass all validation tests
2. ✅ Maintain cryptographic hash matches (or provide justification for changes)
3. ✅ Update baselines if intentionally changing results
4. ✅ Document any changes to reproducibility guarantees

## Quick Start for Contributors

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/HubbleBubble.git
cd HubbleBubble

# 2. Create a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Make your changes
# ... edit files ...

# 5. Test your changes
make validate  # Full validation (~10 min)
python rent/run_rent.py --mode strict  # Strict reproducibility check

# 6. Commit with clear message (see format below)
git add .
git commit -m "feat: Add parallel validation option"

# 7. Push and create pull request
git push origin feature/your-feature-name
```

## Development Workflow

### Before Making Changes

1. **Understand the baseline**: Run the full validation to establish current state
   ```bash
   make validate
   python rent/run_rent.py --mode audit --quick
   ```

2. **Check existing issues**: Search for related issues or discussions

3. **Discuss major changes**: Open an issue first for significant changes

### Making Changes

#### Code Style
- **Python**: Follow PEP 8 (enforced by `black` formatter)
- **Docstrings**: Use NumPy style
- **Line length**: 100 characters max
- **Imports**: Group stdlib, third-party, local (sorted alphabetically)

#### Code Quality
```bash
# Format code
black .

# Check style
pylint rent/ src/

# Type checking (if implemented)
mypy rent/ src/
```

#### Testing Requirements

**All contributions must pass**:

1. **Environment verification**:
   ```bash
   python rent/phase1_provenance/verify_environment.py --mode strict
   ```

2. **Quick validation** (minimum):
   ```bash
   python src/validation/bootstrap.py --iters 100 --out /tmp/test_bootstrap.json
   python src/validation/inject.py --trials 100 --out /tmp/test_inject.json
   ```

3. **Full validation** (before PR):
   ```bash
   make validate
   ```

4. **RENT audit** (strict mode):
   ```bash
   python rent/run_rent.py --mode strict
   ```

### Handling Reproducibility Changes

#### If Your Changes Affect Results

If your change intentionally modifies computational results:

1. **Document why**: Explain in PR description
2. **Show improvements**: Demonstrate enhancement (e.g., bug fix, better accuracy)
3. **Update baselines**: Run update script
   ```bash
   # Generate new baseline hashes
   python rent/tools/update_baseline.py --justify "Fixed numeric precision bug in anchor correction"
   ```
4. **Update tests**: Ensure new results are validated

#### If Hash Mismatches Occur Unexpectedly

1. **Investigate first**: Why did hashes change?
2. **Check determinism**: Run validation multiple times
3. **Review changes**: Did you modify any calculation logic?
4. **Ask for help**: Open a draft PR with findings

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring, no behavior change
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```
feat(validation): Add parallel execution for bootstrap test

- Reduces runtime from 10min to 3min on multi-core systems
- Uses multiprocessing for independent random samples
- Maintains deterministic results with seed=172901
- Updates RENT Phase IV to handle parallel-generated hashes

Closes #42
```

```
fix(environment): Use sys.executable for pip freeze check

- Fixes false-positive warnings when using venv
- Changes subprocess call from 'pip' to 'sys.executable -m pip'
- Resolves issue #15

BREAKING CHANGE: Environment verification now requires Python 3.10+
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated (README, docstrings)
- [ ] Commit messages follow format
- [ ] No merge conflicts with master
- [ ] CHANGELOG.md updated (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update

## Reproducibility Impact
- [ ] No impact on results (hash matches maintained)
- [ ] Results changed intentionally (baseline updated, justified below)
- [ ] New validation test added

## Testing
- [ ] Environment verification passed
- [ ] Quick validation passed
- [ ] Full validation passed
- [ ] RENT audit passed (strict mode)

## Validation Results
```
Paste output from:
python rent/run_rent.py --mode strict
```

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All CI checks pass
```

### Review Process

1. **Automated checks**: CI must pass (all Python versions)
2. **Maintainer review**: At least one approving review required
3. **Reproducibility verification**: Maintainer will run full validation
4. **Merge**: Squash and merge to master

## Types of Contributions Welcome

### High Priority
- 🐛 **Bug fixes**: Especially anything breaking reproducibility
- 📚 **Documentation**: Improvements, clarifications, examples
- ✅ **Tests**: Additional validation, edge cases
- 🔧 **Tooling**: CI/CD, automation, development experience

### Medium Priority
- ⚡ **Performance**: Faster validation without changing results
- 🎨 **Usability**: Better error messages, progress indicators
- 🌍 **Portability**: Windows support, more platforms
- 📊 **Visualization**: Better reports, plots, dashboards

### Lower Priority (Discuss First)
- 🆕 **New features**: Require design discussion
- 🔬 **Scientific methods**: Must maintain compatibility
- 💥 **Breaking changes**: Need strong justification

## Code of Conduct

### Our Standards

- **Be respectful**: Constructive feedback only
- **Be patient**: Contributors have varying experience levels
- **Be collaborative**: Science improves through cooperation
- **Be precise**: Reproducibility requires exactness

### Unacceptable Behavior

- Harassment, discrimination, or personal attacks
- Publishing others' private information
- Intentionally breaking reproducibility without disclosure
- Claiming results without proper testing

## Scientific Integrity

This project is about **reproducible science**. All contributors must:

1. **Never fabricate results**: All outputs must be from actual runs
2. **Disclose all changes**: Transparency is critical
3. **Document assumptions**: Make reasoning clear
4. **Respect authorship**: Acknowledge others' work
5. **Report bugs honestly**: Even if embarrassing

## Getting Help

- 📖 **Documentation**: Start with README.md and METHODOLOGY_DEFENSE.md
- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Search existing issues before creating new ones
- 📧 **Email**: [Maintainer contact from README]

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Acknowledged in release notes
- Credited in scientific outputs (if appropriate)
- Invited to author team (for substantial contributions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License (same as the project).

---

## Quick Reference

### Useful Commands

```bash
# Quick validation (30 seconds)
python src/validation/bootstrap.py --iters 100 --out /tmp/quick.json

# Full validation (10 minutes)
make validate

# Strict reproducibility check
python rent/run_rent.py --mode strict

# Update baseline hashes (after justified change)
python rent/tools/update_baseline.py

# Format code
black rent/ src/

# Check environment
python rent/phase1_provenance/verify_environment.py
```

### Need Help?

- 🆘 Stuck? Open a draft PR and ask questions
- 🤔 Unsure? Create an issue to discuss
- 🔍 Exploring? Check existing issues and PRs

---

**Remember**: The goal isn't perfection on the first try. The goal is **honest, reproducible science**. We'll work together to get there.

Thank you for contributing to reproducible research! 🔬✨
