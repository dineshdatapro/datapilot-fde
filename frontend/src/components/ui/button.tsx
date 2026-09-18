import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../../lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variant = "primary", size = "md", ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-sans text-sm transition-colors disabled:pointer-events-none disabled:opacity-50",
        size === "sm" ? "h-8 px-3" : "h-10 px-4",
        variant === "primary" && "bg-accent text-white hover:bg-[#173d2e]",
        variant === "secondary" && "border border-line bg-white text-ink hover:bg-mist",
        variant === "ghost" && "text-stone-600 hover:bg-mist",
        variant === "danger" && "text-red-700 hover:bg-red-50",
        className,
      )}
      {...props}
    />
  );
});
