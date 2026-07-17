# codemind-demo-todo-app

A small TypeScript demo repository bundled with CodeMind AI. It's served by
`MockGitHubClient` in place of a real GitHub repository so the onboarding →
indexing → ask flow can be exercised end-to-end without GitHub credentials.

Contains: a math utility module (with one intentionally-unguarded `divide`,
planted for a later bug-detection phase), a string utility module, a `User`
model, a `UserService` class, and a `UserCard` React component.
