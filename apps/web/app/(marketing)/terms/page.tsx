import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service — CodeMind AI",
  description: "The terms that govern your use of CodeMind AI.",
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-24 md:py-32">
      <h1 className="mb-2 text-3xl font-semibold tracking-tight md:text-4xl">Terms of Service</h1>
      <p className="mb-10 text-sm text-muted-foreground">Last updated: August 2026</p>
      <article className="prose prose-invert prose-lg max-w-none prose-headings:tracking-tight prose-a:text-primary">
        <p>
          These Terms of Service (&quot;Terms&quot;) govern your access to and use of CodeMind AI
          (the &quot;Service&quot;). By creating an account or using the Service, you agree to be
          bound by these Terms.
        </p>

        <h2>1. The Service</h2>
        <p>
          CodeMind AI indexes source code repositories you connect and provides AI-generated
          answers, findings, and pull request reviews grounded in that code. The Service is
          provided on an &quot;as is&quot; and &quot;as available&quot; basis, and AI-generated
          output should be reviewed before you act on it.
        </p>

        <h2>2. Accounts</h2>
        <p>
          You are responsible for maintaining the security of your account credentials and for
          all activity that occurs under your account. You must provide accurate information when
          creating an account and keep it up to date.
        </p>

        <h2>3. Repository access</h2>
        <p>
          When you connect a GitHub repository, you authorize the Service to read its contents to
          build an index, answer questions, and, where you request it, open pull requests. You
          represent that you have the necessary rights to grant this access.
        </p>

        <h2>4. Billing</h2>
        <p>
          Paid plans are billed in advance on a recurring basis through our payment processor,
          Stripe. Fees are non-refundable except where required by law. You may upgrade,
          downgrade, or cancel a paid plan at any time from your organization&apos;s billing page;
          changes take effect as described at the time of the change.
        </p>

        <h2>5. Acceptable use</h2>
        <p>
          You agree not to use the Service to violate any law, infringe on any third party&apos;s
          rights, or attempt to gain unauthorized access to any part of the Service or its
          underlying infrastructure.
        </p>

        <h2>6. Termination</h2>
        <p>
          You may stop using the Service and delete your account at any time. We may suspend or
          terminate access to the Service for accounts that violate these Terms.
        </p>

        <h2>7. Disclaimers and limitation of liability</h2>
        <p>
          The Service is provided without warranties of any kind, express or implied. To the
          maximum extent permitted by law, CodeMind AI will not be liable for any indirect,
          incidental, or consequential damages arising from your use of the Service.
        </p>

        <h2>8. Changes to these Terms</h2>
        <p>
          We may update these Terms from time to time. Continued use of the Service after an
          update constitutes acceptance of the revised Terms.
        </p>

        <h2>9. Contact</h2>
        <p>
          Questions about these Terms can be sent to{" "}
          <a href="mailto:support@codemindai.com">support@codemindai.com</a>.
        </p>
      </article>
    </main>
  );
}
