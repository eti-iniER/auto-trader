import { BrowserRouter, Routes } from "react-router";

const AppRoutes = () => {
  return <Routes></Routes>;
};

export const App = () => {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
};
