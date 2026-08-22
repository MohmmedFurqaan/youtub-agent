import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-ring gap-1.5",
  {
    variants: {
      variant: {
        default: "border-slate-700 bg-slate-800 text-slate-200",
        secondary: "border-slate-800 bg-slate-900 text-slate-300",
        destructive: "border-red-900/50 bg-red-950/60 text-red-300",
        outline: "border-slate-700 text-slate-300",
        success: "border-emerald-800/60 bg-emerald-950/60 text-emerald-300",
        warning: "border-amber-800/60 bg-amber-950/60 text-amber-300",
        info: "border-blue-800/60 bg-blue-950/60 text-blue-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
