# Releasing Reconnator

Reconnator follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
The version itself is written as `MAJOR.MINOR.PATCH`; Git tags add a leading
`v`, for example `v2.0.1`.

## Choosing the Next Version

| Change | Version increment | Example |
| --- | --- | --- |
| Incompatible behavior, interface, configuration, or architecture | MAJOR | `2.4.1` to `3.0.0` |
| Backward-compatible capability or feature | MINOR | `2.4.1` to `2.5.0` |
| Backward-compatible bug, security, build, packaging, or documentation fix | PATCH | `2.4.1` to `2.4.2` |

The number of commits does not determine the version increment. Several fixes
can ship together in one patch release.

## Release Checklist

1. Confirm that the release commit is on `main` and the working tree is clean.
2. Update `CHANGELOG.md`: move relevant items from `Unreleased` into a dated
   version section.
3. Update the version shown in `README.md` and any user-facing examples.
4. Run the relevant validation:

   ```bash
   python -m compileall src
   docker build -t reconnator:release-candidate .
   helm lint deploy/helm
   ```

5. Create and push an annotated tag:

   ```bash
   git tag -a v2.0.1 -m "Reconnator v2.0.1"
   git push origin v2.0.1
   ```

6. Create a GitHub Release from the tag, review the generated notes, and mark a
   stable release as the latest release.
7. Verify the GitHub Actions run and the corresponding GHCR image tags.

Stable version tags trigger container publishing. For `v2.0.1`, the expected
image aliases are:

```text
ghcr.io/amiencoy/reconnator:2.0.1
ghcr.io/amiencoy/reconnator:2.0
ghcr.io/amiencoy/reconnator:2
ghcr.io/amiencoy/reconnator:latest
```

Do not move or reuse a published version tag. If a release needs correction,
publish a new patch version.
