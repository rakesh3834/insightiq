import { cn } from "@/lib/utils";
import { forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary: "bg-indigo-600 hover:bg-indigo-500 text-white border-transparent",
  secondary: "bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border-zinc-700",
  ghost: "bg-transparent hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border-transparent",
  danger: "bg-red-600 hover:bg-red-500 text-white border-transparent",
  outline: "bg-transparent hover:bg-zinc-800 text-zinc-300 border-zinc-700",
};

const sizes: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-sm",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "secondary", size = "md", className, children, ...props }, ref) => (
    <button
      ref={ref}
      className={cn("inline-flex items-center gap-2 rounded-lg border font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed", variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  )
);
Button.displayName = "Button";
