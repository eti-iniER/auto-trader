"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const segmentedControlVariants = cva(
  "border-input bg-background inline-flex rounded-lg border p-1 gap-1",
  {
    variants: {
      size: {
        default: "h-10",
        sm: "h-8",
        lg: "h-12",
      },
    },
    defaultVariants: {
      size: "default",
    },
  },
);

interface SegmentedControlProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof segmentedControlVariants> {
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  variant?: "default" | "colored";
}

interface SegmentedControlItemProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
  isSelected?: boolean;
  variant?: "default" | "colored";
  size?: "default" | "sm" | "lg";
  selectedClassName?: string;
  unselectedClassName?: string;
}

const SegmentedControl = React.forwardRef<
  HTMLDivElement,
  SegmentedControlProps
>(
  (
    {
      className,
      size,
      value,
      onValueChange,
      disabled,
      variant = "default",
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <div
        ref={ref}
        className={cn(segmentedControlVariants({ size, className }))}
        role="radiogroup"
        {...props}
      >
        {React.Children.map(children, (child) => {
          if (React.isValidElement<SegmentedControlItemProps>(child)) {
            return React.cloneElement(child, {
              isSelected: value === child.props.value,
              onClick: (e: React.MouseEvent<HTMLButtonElement>) => {
                if (!disabled && !child.props.disabled) {
                  onValueChange?.(child.props.value);
                }
                child.props.onClick?.(e);
              },
              disabled: disabled || child.props.disabled,
              variant,
              size: size || "default",
              selectedClassName: child.props.selectedClassName,
              unselectedClassName: child.props.unselectedClassName,
            });
          }
          return child;
        })}
      </div>
    );
  },
);

const SegmentedControlItem = React.forwardRef<
  HTMLButtonElement,
  SegmentedControlItemProps
>(
  (
    {
      className,
      size = "default",
      variant = "default",
      value,
      isSelected,
      selectedClassName,
      unselectedClassName,
      children,
      ...props
    },
    ref,
  ) => {
    const getButtonClasses = () => {
      const baseClasses =
        "flex-1 rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 flex items-center justify-center";

      const sizeClasses = {
        default: "px-4 py-2",
        sm: "px-3 py-1.5 text-xs",
        lg: "px-5 py-3",
      };

      // If custom class names are provided, use them
      if (selectedClassName && unselectedClassName) {
        return cn(
          baseClasses,
          sizeClasses[size],
          isSelected ? selectedClassName : unselectedClassName,
        );
      }

      if (variant === "colored") {
        // Special handling for demo/live coloring
        if (value === "demo") {
          return cn(
            baseClasses,
            sizeClasses[size],
            isSelected
              ? "bg-green-500 text-white shadow-sm hover:bg-green-600"
              : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
          );
        } else if (value === "live") {
          return cn(
            baseClasses,
            sizeClasses[size],
            isSelected
              ? "bg-red-500 text-white shadow-sm hover:bg-red-600"
              : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
          );
        }
      }

      // Default variant
      return cn(
        baseClasses,
        sizeClasses[size],
        isSelected
          ? "bg-primary text-primary-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
      );
    };

    return (
      <button
        ref={ref}
        type="button"
        role="radio"
        aria-checked={isSelected}
        className={cn(getButtonClasses(), className)}
        {...props}
      >
        {children}
      </button>
    );
  },
);

SegmentedControl.displayName = "SegmentedControl";
SegmentedControlItem.displayName = "SegmentedControlItem";

export { SegmentedControl, SegmentedControlItem };
