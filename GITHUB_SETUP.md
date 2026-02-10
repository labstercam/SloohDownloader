# GitHub Repository Configuration

Quick reference for setting up the repository on GitHub after pushing.

## Repository Settings

### About Section
1. Click **Settings** → **General**
2. Add **Description**:
   ```
   Windows bulk downloader for Slooh astronomical images. Multi-threaded downloads with smart tracking and organization.
   ```
3. Add **Website**: 
   ```
   https://github.com/labstercam/SloohDownloader/releases
   ```
4. Add **Topics**:
   - `slooh`
   - `astronomy`
   - `downloader`
   - `ironpython`
   - `windows`
   - `bulk-download`
   - `astronomy-images`
   - `dotnet`

### Features
Enable these under **Settings** → **General**:
- ✅ Issues
- ✅ Releases
- ❌ Wikis (not needed)
- ❌ Discussions (optional)
- ❌ Projects (optional)

### Social Preview
Upload a custom social preview image (1280×640 px) showing:
- Application name
- Brief description
- Main interface screenshot

## Branch Protection (Optional)

For main branch:
1. Go to **Settings** → **Branches**
2. Add rule for `main`:
   - ❌ Require pull request reviews (not needed for solo project)
   - ✅ Include administrators
   - ❌ Require status checks (no CI/CD yet)

## Issue Labels

GitHub auto-creates these, but verify:
- `bug` - Bug reports
- `enhancement` - Feature requests
- `documentation` - Documentation improvements
- `question` - User questions
- `help-wanted` - Community contributions welcome

## README.md Badges

Already included:
- Platform badge (Windows)
- IronPython version
- .NET Framework version
- Status badge

Optional additions:
- GitHub release version badge
- GitHub downloads badge
- GitHub stars badge

## Release Configuration

### First Release (v1.0.0)

1. **Tag**: `v1.0.0`
2. **Title**: "Slooh Image Downloader v1.0.0"
3. **Description**: Use template from RELEASE.md
4. **Assets**: Upload `releases/SloohDownloader-v1.0.0.zip`
5. **Options**:
   - ✅ Set as the latest release
   - ❌ Set as a pre-release
   - ✅ Create a discussion for this release (optional)

## Post-Publishing

### Verify
- [ ] All markdown files render correctly
- [ ] Links work (especially relative links)
- [ ] Screenshots display (after adding them)
- [ ] Issue templates appear when creating issues
- [ ] Release shows correct download link
- [ ] README is clear and welcoming

### Optional: Add Shields
Add more badges to README if desired:
```markdown
![GitHub release](https://img.shields.io/github/v/release/labstercam/SloohDownloader)
![GitHub downloads](https://img.shields.io/github/downloads/labstercam/SloohDownloader/total)
![GitHub stars](https://img.shields.io/github/stars/labstercam/SloohDownloader)
```

### Consider
- **GitHub Actions**: Automated release packaging (future)
- **Dependabot**: Security alerts (GitHub auto-enables)
- **Contributing Guide**: If accepting external contributions

## Quick Commands

### Push to GitHub (First Time)
```powershell
git add .
git commit -m "Initial release v1.0.0"
git push -u origin main
```

### Tag and Release
```powershell
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag to GitHub
git push origin v1.0.0

# Or push all tags
git push --tags
```

Note: Tags can also be created directly in GitHub during release creation.

## Support

Add to README (optional):
- Link to issues for bug reports
- Email for non-public inquiries
- Discussion board for questions

## License Notice

MIT License is already in place. GitHub will auto-detect it.
