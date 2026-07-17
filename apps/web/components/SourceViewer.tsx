import { Highlight, themes } from "prism-react-renderer";

export function SourceViewer({
  content,
  language,
  highlightStart,
  highlightEnd,
}: {
  content: string;
  language: string;
  highlightStart?: number;
  highlightEnd?: number;
}) {
  return (
    <Highlight theme={themes.vsDark} code={content.replace(/\n$/, "")} language={language}>
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <pre
          className={`${className} overflow-x-auto rounded border border-gray-800 p-4 text-sm`}
          style={style}
        >
          {tokens.map((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted =
              highlightStart != null &&
              highlightEnd != null &&
              lineNumber >= highlightStart &&
              lineNumber <= highlightEnd;

            const lineProps = getLineProps({ line });

            return (
              <div
                key={lineNumber}
                {...lineProps}
                className={`${lineProps.className} ${isHighlighted ? "bg-blue-950/60" : ""}`}
              >
                <span className="mr-4 inline-block w-8 select-none text-right text-gray-600">
                  {lineNumber}
                </span>
                {line.map((token, tokenIndex) => (
                  <span key={tokenIndex} {...getTokenProps({ token })} />
                ))}
              </div>
            );
          })}
        </pre>
      )}
    </Highlight>
  );
}
