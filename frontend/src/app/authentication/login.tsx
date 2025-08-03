import { useLogin } from "@/api/hooks/authentication/use-login";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { LoaderWrapper } from "@/components/ui/loader-wrapper";
import { images } from "@/constants/images";
import { paths } from "@/paths";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

const loginSchema = z.object({
  email: z.email("Invalid email address").min(1, "Email is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const Login = () => {
  const login = useLogin();
  const navigate = useNavigate();
  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    login.mutate(data, {
      onSuccess: () => {
        toast.success("Login successful!");
        navigate(paths.dashboard.OVERVIEW);
      },
      onError: (error) => {
        toast.error("Login failed", {
          description: error.message || "An unexpected error occurred.",
        });
      },
    });
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md rounded-md shadow-none">
        <CardHeader className="text-center">
          <div className="flex flex-col items-center space-y-3">
            <img
              src={images.candlestick}
              alt="AutoTrader Logo"
              className="h-16 w-16"
            />
            <div className="space-y-1">
              <CardTitle className="text-2xl font-semibold">Log in</CardTitle>
              <CardDescription className="text-sm text-gray-500">
                Enter your credentials to access your account
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        placeholder="Enter your email"
                        autoComplete="email"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        autoComplete="current-password"
                        placeholder="Enter your password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                className="w-full"
                disabled={form.formState.isSubmitting}
              >
                <LoaderWrapper isLoading={login.isPending}>
                  Log in
                </LoaderWrapper>
              </Button>
              <Button
                asChild
                variant="ghost"
                type="submit"
                className="-mt-3 w-full"
                disabled={form.formState.isSubmitting}
              >
                <Link to={paths.authentication.RESET_PASSWORD}>
                  Forgot password?
                </Link>
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
};
