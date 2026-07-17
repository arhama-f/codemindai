"use client";

import { usePathname, useRouter } from "next/navigation";

export interface OutlineSymbol {
  name: string;
  kind: string;
  start_line: number;
  end_line: number;
}

export function SymbolOutline({ symbols }: { symbols: OutlineSymbol[] }) {
  const router = useRouter();
  const pathname = usePathname();

  if (symbols.length === 0) {
    return <p className="text-sm text-gray-500">No symbols in this file.</p>;
  }

  return (
    <ul className="flex flex-col gap-1">
      {symbols.map((symbol) => (
        <li key={`${symbol.name}-${symbol.start_line}`}>
          <button
            onClick={() =>
              router.push(`${pathname}?start=${symbol.start_line}&end=${symbol.end_line}`)
            }
            className="block w-full rounded px-2 py-1 text-left text-sm hover:bg-gray-800"
          >
            <span className="font-mono text-blue-400">{symbol.name}</span>{" "}
            <span className="text-gray-500">({symbol.kind})</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
