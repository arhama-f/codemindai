import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  usePathname: () => "/orgs/org-1/repos/repo-1/files/file-1",
}));

import { SymbolOutline } from "@/components/SymbolOutline";

describe("SymbolOutline", () => {
  it("renders a message when there are no symbols", () => {
    render(<SymbolOutline symbols={[]} />);
    expect(screen.getByText(/no symbols/i)).toBeInTheDocument();
  });

  it("renders each symbol's name and kind", () => {
    render(
      <SymbolOutline
        symbols={[
          { name: "divide", kind: "function", start_line: 14, end_line: 16 },
          { name: "UserService", kind: "class", start_line: 3, end_line: 18 },
        ]}
      />,
    );

    expect(screen.getByText("divide")).toBeInTheDocument();
    expect(screen.getByText("(function)")).toBeInTheDocument();
    expect(screen.getByText("UserService")).toBeInTheDocument();
  });

  it("navigates to the symbol's line range when clicked", () => {
    render(
      <SymbolOutline
        symbols={[{ name: "divide", kind: "function", start_line: 14, end_line: 16 }]}
      />,
    );

    fireEvent.click(screen.getByText("divide"));

    expect(pushMock).toHaveBeenCalledWith("/orgs/org-1/repos/repo-1/files/file-1?start=14&end=16");
  });
});
