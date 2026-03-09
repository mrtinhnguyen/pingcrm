import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ScoreBadge } from "./score-badge";

describe("ScoreBadge", () => {
  it("renders Strong for score >= 8", () => {
    render(<ScoreBadge score={9} />);
    expect(screen.getByText("Strong")).toBeInTheDocument();
    expect(screen.getByText("(9)")).toBeInTheDocument();
  });

  it("renders Warm for score 4-7", () => {
    render(<ScoreBadge score={5} />);
    expect(screen.getByText("Warm")).toBeInTheDocument();
    expect(screen.getByText("(5)")).toBeInTheDocument();
  });

  it("renders Cold for score <= 3 without recent interaction", () => {
    render(<ScoreBadge score={2} />);
    expect(screen.getByText("Cold")).toBeInTheDocument();
    expect(screen.getByText("(2)")).toBeInTheDocument();
  });

  it("renders New for score <= 3 with recent interaction", () => {
    const recent = new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString();
    render(<ScoreBadge score={3} lastInteractionAt={recent} />);
    expect(screen.getByText("New")).toBeInTheDocument();
    expect(screen.getByText("(3)")).toBeInTheDocument();
  });

  it("renders Cold for score <= 3 with old interaction", () => {
    const old = new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString();
    render(<ScoreBadge score={2} lastInteractionAt={old} />);
    expect(screen.getByText("Cold")).toBeInTheDocument();
  });

  it("renders Strong at boundary score 8", () => {
    render(<ScoreBadge score={8} />);
    expect(screen.getByText("Strong")).toBeInTheDocument();
    expect(screen.getByText("(8)")).toBeInTheDocument();
  });

  it("renders Warm at boundary score 4", () => {
    render(<ScoreBadge score={4} />);
    expect(screen.getByText("Warm")).toBeInTheDocument();
    expect(screen.getByText("(4)")).toBeInTheDocument();
  });

  it("renders Cold at boundary score 3 without recency", () => {
    render(<ScoreBadge score={3} />);
    expect(screen.getByText("Cold")).toBeInTheDocument();
    expect(screen.getByText("(3)")).toBeInTheDocument();
  });

  it("renders Cold for score 0", () => {
    render(<ScoreBadge score={0} />);
    expect(screen.getByText("Cold")).toBeInTheDocument();
    expect(screen.getByText("(0)")).toBeInTheDocument();
  });

  it("renders Strong for score 10", () => {
    render(<ScoreBadge score={10} />);
    expect(screen.getByText("Strong")).toBeInTheDocument();
    expect(screen.getByText("(10)")).toBeInTheDocument();
  });

  it("shows score in title attribute", () => {
    render(<ScoreBadge score={7} />);
    expect(screen.getByTitle("Relationship score: 7/10")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<ScoreBadge score={5} className="text-lg" />);
    expect(container.firstChild).toHaveClass("text-lg");
  });
});
