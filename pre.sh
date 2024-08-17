# Review and commit changes
pre-commit run --all-files
git add .
git commit -m "Fix issues found by pre-commit hooks"

# Re-run pre-commit to verify fixes
pre-commit run --all-files
