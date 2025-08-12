import "./loader.css";

interface LoaderProps {
  variant?: "light" | "dark";
}

export const Loader = ({ variant = "light" }: LoaderProps) => (
  <div className={variant === "dark" ? "loader-dark" : "loader"} />
);
