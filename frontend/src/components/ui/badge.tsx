import { HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-line bg-mist px-2.5 py-0.5 text-xs text-stone-700",
        className,
      )}
      {...props}
    />
  );
}
