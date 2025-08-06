import { Login } from "@/app/authentication/login";
import { Register } from "@/app/authentication/register";
import { ResetPassword } from "@/app/authentication/reset-password";
import { Help } from "@/app/dashboard/help";
import { Instruments } from "@/app/dashboard/instruments";
import { Logs } from "@/app/dashboard/logs";
import { Orders } from "@/app/dashboard/orders";
import { Overview } from "@/app/dashboard/overview";
import { Positions } from "@/app/dashboard/positions";
import { Settings } from "@/app/dashboard/settings";
import { Toaster } from "@/components/ui/sonner";
import DashboardLayout from "@/layouts/dashboard";
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
          <Route path="reset-password" element={<ResetPassword />} />
          <Route path="register" element={<Register />} />
        </Route>
        <Route path="dashboard" element={<DashboardLayout />}>
          <Route index element={<Navigate to={paths.dashboard.OVERVIEW} />} />
          <Route path="overview" element={<Overview />} />
          <Route path="orders" element={<Orders />} />
          <Route path="positions" element={<Positions />} />
          <Route path="instruments" element={<Instruments />} />
          <Route path="logs" element={<Logs />} />
          <Route path="settings" element={<Settings />} />
          <Route path="help" element={<Help />} />
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
        <Toaster position="top-center" richColors />
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
};
