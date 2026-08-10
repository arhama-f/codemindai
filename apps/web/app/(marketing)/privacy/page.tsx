import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — CodeMind AI",
  description: "How CodeMind AI collects, uses, and protects your data.",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-24 md:py-32">
      <h1 className="mb-2 text-3xl font-semibold tracking-tight md:text-4xl">Privacy Policy</h1>
      <p className="mb-10 text-sm text-muted-foreground">Last updated: August 2026</p>
      <article className="prose prose-invert prose-lg max-w-none prose-headings:tracking-tight prose-a:text-primary">
        <p>
          This Privacy Policy describes how CodeMind AI (&quot;we&quot;, &quot;us&quot;) collects,
          uses, and protects information when you use the Service.
        </p>

        <h2>1. Information we collect</h2>
        <p>
          <strong>Account information:</strong> your name, email address, and password (stored as
          a salted hash), or your Google/GitHub account identifier if you sign in via OAuth.
        </p>
        <p>
          <strong>Repository content:</strong> source code, file paths, and metadata from
          repositories you connect, used to build the index, dependency graph, and AI-generated
          answers and findings.
        </p>
        <p>
          <strong>Billing information:</strong> handled directly by our payment processor,
          Stripe. We do not store your card details.
        </p>
        <p>
          <strong>Usage data:</strong> log data such as IP address, browser type, and pages
          visited, used to operate and secure the Service.
        </p>

        <h2>2. How we use information</h2>
        <p>
          We use collected information to provide and improve the Service, including indexing
          repositories, generating AI answers and findings, processing payments, sending
          transactional emails (via Resend), and securing accounts.
        </p>

        <h2>3. AI processing</h2>
        <p>
          Repository content and questions you ask are sent to our AI provider to generate
          answers, findings, and proposed fixes. This content is used to serve your request and is
          not used to train third-party foundation models.
        </p>

        <h2>4. Data sharing</h2>
        <p>
          We share data with service providers who help us operate the Service — including
          Stripe (payments), Resend (transactional email), Google and GitHub (OAuth
          authentication), and our AI provider (repository analysis) — solely for the purposes
          described above. We do not sell your data.
        </p>

        <h2>5. Data retention</h2>
        <p>
          We retain account and repository index data for as long as your account is active. You
          can delete a connected repository or your account at any time, which removes the
          associated indexed data.
        </p>

        <h2>6. Your rights</h2>
        <p>
          You may access, correct, or delete your account information at any time from your
          account settings, or by contacting us directly.
        </p>

        <h2>7. Security</h2>
        <p>
          We use industry-standard measures, including encryption in transit and hashed
          credentials, to protect your information. No method of transmission or storage is
          completely secure, and we cannot guarantee absolute security.
        </p>

        <h2>8. Changes to this policy</h2>
        <p>
          We may update this Privacy Policy from time to time. Continued use of the Service after
          an update constitutes acceptance of the revised policy.
        </p>

        <h2>9. Contact</h2>
        <p>
          Questions about this policy can be sent to{" "}
          <a href="mailto:privacy@codemindai.com">privacy@codemindai.com</a>.
        </p>
      </article>
    </main>
  );
}
