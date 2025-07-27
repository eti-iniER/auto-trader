import { Login } from "@/app/authentication/login";
import { Toaster } from "@/components/ui/sonner";
import { RootLayout } from "@/layouts/root";
import { paths } from "@/paths";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";

const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route path="auth">
          <Route path="login" element={<Login />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to={paths.authentication.LOGIN} />} />
    </Routes>
  );
};

const client = new QueryClient();

export const App = () => {
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Toaster position="top-center" />
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
};
