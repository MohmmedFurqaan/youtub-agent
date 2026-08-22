import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 btn-2d",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-900 border-slate-200 hover:bg-white hover:border-slate-300",
        destructive: "bg-red-900/80 text-red-100 border-red-800 hover:bg-red-800",
        outline: "border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800 hover:border-slate-600",
        secondary: "bg-slate-800 text-slate-100 border-slate-700 hover:bg-slate-700",
        ghost: "border-transparent text-slate-200 hover:bg-slate-800 hover:text-slate-100",
        primary: "bg-blue-600 text-white border-blue-500 hover:bg-blue-500",
        success: "bg-emerald-600 text-white border-emerald-500 hover:bg-emerald-500",
      },
      size: {
        default: "h-9 px-4 py-2 gap-2",
        sm: "h-8 rounded-md px-3 text-xs gap-1.5",
        lg: "h-10 rounded-md px-8 text-base gap-2",
        icon: "size-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
